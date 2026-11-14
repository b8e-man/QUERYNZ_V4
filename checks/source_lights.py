"""The source lights (Arthur, 4 November 2026): one light for every register
on the board's search pane, with a one-line reason in plain words.

  red     updates not working: the last run of a job that keeps the source
          current failed; or no good run inside that job's cadence and a
          grace; or the fetch gate holds (ruling 141) a host the lane names
          as its own (`hosts`), or every host the lane reads; or, for a lane
          the ingest MCP feeds, the last pull caught a record or met new
          fields in the lane's corpus, or the provider's copy of a corpus it
          reads has had nothing new for over three times its source's
          cadence (ruling 159)
  orange  updates working, the corpus not whole: the gate holds some of the
          many hosts the lane reads under its positions (a council of 78),
          the rest still asked; a reader or backfill with
          pieces outstanding, documents waiting on a reader in the lane's
          published documents view, the lane's own count short of the
          source's, an update job of the lane switched off in the catalogue
          while another still runs (the register holds what the switched-off
          job last gathered: 9 November 2026, the nine sources the boxes
          stopped gathering), the provider's copy of a corpus it reads older
          than its source's cadence, or a declared gap (`checks/source_gaps.toml`). A declared gap that names a held
          host (`hosts`) says that hold in its own words: the gate's line for
          it is not repeated, red or orange (a person declared what cannot be
          read while the host is held; only a person clears the hold)
  green   updates working, nothing outstanding, no declared gap
  grey    no update job on a clock (loaded by the merge gate's staging
          step, or on demand)

The registers are read from `products/board/catalogue.py` as a file (its
REGISTERS and NOT_HELD tuples, by ast; checks may not import products), so
a register the board adds shows grey until `LANES` names its jobs. The
cadence of a job is its own (`every_s`, or a day for `at_utc`) or, for a job
with no clock, the job that queues it (`then`): it is late when that job
finished and it has not run since. A job new to its clock (the scheduler's
timetable row says so) is judged from the slot it was put on the clock at.

`compute()` is pure: it takes the facts and the clock. `gather()` reads
them: the scheduler's queue and timetable (read login), the gate's refusals,
the last pull's run record, and two published views.

    python -m checks.source_lights            compute and write <live>/checks/source-lights.json
    python -m checks.source_lights --print    compute and print, writing nothing

The provider's freshness (ruling 159). Every reading of the MCP's `corpora`
by qv4-mcp-pull is kept per corpus in `mcpsource.freshness`
(support/mcpsource/freshness.py). A copy is judged by the provider's own
`newest_arrival`, never by our pull, against its source's cadence in
`checks/mcp_cadence.toml` (days, measured or a marked default, a reason, a
declared pause): older than the cadence, orange; three times, red. A corpus
the last pull did not reach is not red for that alone (its budget spent:
the estate-* corpora come last). Each MCP-fed light carries a short `fresh`
line for the board, and the job rewrites the provider's list,
`<work>/handover/mcp-stale.md`: every corpus past its cadence, dated, at most
a page.

The `qv4-source-lights` job runs it every 30 minutes. The board reads the
file (products/board/lights.py). Tests: checks/tests/test_source_lights.py."""
from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime as dt
import json
import os
import sys
import tomllib
import zoneinfo

from support import fetchgate
from support.scheduler import registry as reg

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
LIGHTS_FILE = os.path.join(LIVE, "checks", "source-lights.json")
GAPS_FILE = os.path.join(HERE, "source_gaps.toml")
CADENCE_FILE = os.path.join(HERE, "mcp_cadence.toml")
STALE_FILE = os.environ.get("QV4_MCP_STALE") or "/home/user/querynzv4-work/handover/mcp-stale.md"
STALE_JSON = os.path.splitext(STALE_FILE)[0] + ".json"           # the same list, for the provider's tool
ASKS_DIR = os.path.join(os.path.dirname(STALE_FILE), "asks")      # a lane's own request to the provider (ruling 165)


def lane_asks(folder: str = None) -> list:
    """Every lane's request file under <handover>/asks/: what the source lists that neither copy holds. A file that
    does not read is skipped, never guessed."""
    out = []
    d = folder or ASKS_DIR
    for n in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if not n.endswith(".json"):
            continue
        try:
            with open(os.path.join(d, n), encoding="utf-8") as f:
                o = json.load(f)
        except (OSError, ValueError):
            continue
        for x in (o.get("asks") if isinstance(o, dict) and isinstance(o.get("asks"), list) else [o]):   # one or several
            if isinstance(x, dict) and x.get("corpus") and isinstance(x.get("missing"), int) and x["missing"] > 0:
                out.append(x)
    return out
STALE_CLOSING = os.path.splitext(STALE_FILE)[0] + ".closing.md"  # the integrator's closing section, when kept apart
CATALOGUE = os.path.join(REPO, "products", "board", "catalogue.py")
JOB = "qv4-source-lights"
MCP_PULL = "qv4-mcp-pull"
GRACE_S = 6 * 3600          # past a job's cadence and its own deadline, before it counts as late
DAY_S = 86400
ZONE = zoneinfo.ZoneInfo("Pacific/Auckland")
RED, ORANGE, GREEN, GREY = "red", "orange", "green", "grey"
LIGHTS = (RED, ORANGE, GREEN, GREY)


@dataclasses.dataclass(frozen=True)
class Lane:
    update: tuple = ()      # the jobs that keep the source current: capture, pull, load, refresh, watch
    read: tuple = ()        # its readers and backfills (pieced): outstanding pieces make it orange, a failed run red
    corpora: tuple = ()     # the ingest MCP's corpora the lane reads (qv4-mcp-pull's run record, per corpus)
    hosts: tuple = ()       # hosts its own capture asks (as the code names them; "www." is ignored)
    asks: tuple = ()        # the jobs that ask those hosts, where not every update job does: a hold lights the lane only
                            # while one of them is switched on (a load over what a stopped capture landed asks nothing)
    positions: tuple = ()   # legal positions whose `hosts:` lines it reads under (docs/legal/positions/)
    waiting: tuple = ()     # (pub view, SQL condition) counting its documents waiting on a reader
    coverage: str = ""      # a key of COVERAGE: the lane's own count against the source's
    note: str = ""          # why there is no update job
    mcp_hosts: tuple = ()   # hosts its positions name that its own run no longer asks: the MCP provider collects them


MERGE_GATE = "loaded by the merge gate's staging step"
#: register -> its lane, read from each lane's spec `jobs:` line and support/scheduler/jobs.toml (4 November 2026)
LANES = {
    "party_returns": Lane(read=("qv4-read-pages",), note=MERGE_GATE),
    "disclosures": Lane(update=("qv4-disclosures-load",), read=("qv4-disclosures-read",),
                        corpora=("estate-disclosures",)),
    "parties": Lane(note=MERGE_GATE),
    "party_finance": Lane(read=("qv4-read-pages-expenses",), note=MERGE_GATE),
    "house": Lane(note=MERGE_GATE),
    "mp_interests": Lane(note=MERGE_GATE),
    "parliament": Lane(update=(MCP_PULL, "qv4-parliament-load"), read=("qv4-parliament-read",),
                       corpora=("parliament-wayback", "parliament-written-questions", "parliament-bills",
                                "parliament-bills-historical", "parliament-sops", "parliament-sc-reports",
                                "parliament-sc-submissions", "parliament-papers", "parliament-sc-evidence")),
    "hansard": Lane(update=(MCP_PULL, "qv4-hansard-load"), read=("qv4-hansard-read",),
                    corpora=("parliament-hansard-debates", "parliament-hansard-index")),
    "beehive": Lane(update=(MCP_PULL, "qv4-beehive-load"), read=("qv4-beehive-read",), corpora=("beehive",)),
    "ministers_diaries": Lane(update=(MCP_PULL, "qv4-ministers-diaries-load"), corpora=("parliament-diaries",)),
    "expenses": Lane(note=MERGE_GATE),
    "companies": Lane(update=("qv4-companies-monitor", "qv4-companies-history"),
                      hosts=("companiesoffice.govt.nz", "api.business.govt.nz"), positions=("nzbn-register-entities",)),
    "societies": Lane(update=("qv4-societies-capture",), hosts=("api.business.govt.nz",)),
    "charities": Lane(update=("qv4-charities-capture", "qv4-charities-load"), hosts=("www.odata.charities.govt.nz",),
                      positions=("charities-register",),
                      mcp_hosts=("www.charities.govt.nz",)),   # 14 Nov 2026: its six pages are the MCP's (estate-charities-pages@2026-11-13)
    "candidate_returns": Lane(update=("qv4-candidate-returns-load",), read=("qv4-read-pages-candidates",),
                              corpora=("estate-candidate_returns",)),
    "gazette": Lane(update=("qv4-gazette-capture", "qv4-gazette-load"), hosts=("gazette.govt.nz", "api.digitalnz.org"),
                    positions=("new-zealand-gazette", "digitalnz-api")),
    "party_boards": Lane(update=("qv4-party-boards-load",)),
    "overseas_investment": Lane(update=("qv4-overseas-investment-capture", "qv4-overseas-investment-load"),
                                hosts=("linz.govt.nz",), positions=("overseas-investment-decisions",)),
    "grants": Lane(update=("qv4-grants-capture", "qv4-grants-load"),
                   positions=("dia-gambling-and-lottery-grants", "class-4-society-grant-publications")),
    "commerce_commission": Lane(update=("qv4-commerce-commission-capture", "qv4-commerce-commission-load"),
                                hosts=("comcom.govt.nz",), positions=("commerce-commission-case-register",),
                                asks=("qv4-commerce-commission-capture",), corpora=("estate-commerce_commission",)),
    "fma": Lane(update=("qv4-fma-capture", "qv4-fma-load"), hosts=("fma.govt.nz",),
                positions=("fma-warnings-and-enforcement",), corpora=("estate-fma",)),
    "worksafe": Lane(update=("qv4-worksafe-capture", "qv4-worksafe-load"), hosts=("worksafe.govt.nz",),
                     positions=("worksafe-prosecutions-and-undertakings",), asks=("qv4-worksafe-capture",),
                     corpora=("estate-worksafe",)),
    "tenders": Lane(update=("qv4-tenders-load",),        # 11 November 2026: the refresh is off; the files are the MCP's
                    hosts=("mbie.govt.nz", "data.govt.nz", "catalogue.data.govt.nz"), asks=("qv4-tenders-refresh",),
                    positions=("government-procurement-award-notices",)),
    "sanctions": Lane(update=("qv4-sanctions-capture", "qv4-sanctions-load"), positions=("sanctions-lists",),
                      hosts=("scsanctions.un.org",)),
    "limited_partnerships": Lane(update=("qv4-limited-partnerships-capture", "qv4-limited-partnerships-load"),
                                 positions=("limited-partnerships-register",)),
    "building_practitioners": Lane(update=("qv4-building-practitioners-capture",
                                           "qv4-building-practitioners-register-capture", "qv4-building-practitioners-load"),
                                   hosts=("kete-lbp.mbie.govt.nz",), positions=("building-practitioners-register",),
                                   asks=("qv4-building-practitioners-capture", "qv4-building-practitioners-register-capture"),
                                   corpora=("estate-building_practitioners",)),
    "linz": Lane(update=("qv4-linz-capture", "qv4-linz-load"), positions=("linz-data-service",)),
    "real_estate_authority": Lane(update=("qv4-real-estate-authority-capture", "qv4-real-estate-authority-load"),
                                  hosts=("publicregister.rea.govt.nz",), positions=("real-estate-authority-decisions",),
                                  asks=("qv4-real-estate-authority-capture",), corpora=("estate-real_estate_authority",)),
    "courts": Lane(update=(MCP_PULL, "qv4-courts-load", "qv4-courts-jdo-capture", "qv4-courts-era-capture",
                           "qv4-courts-finder-capture"),
                   read=("qv4-courts-read", "qv4-courts-pages"),
                   corpora=("courts", "estate-courts-jdo", "estate-courts-era", "estate-courts-finder"),
                   hosts=("justice.govt.nz", "determinations.era.govt.nz"),
                   positions=("court-judgments", "specialist-court-and-authority-decisions"),
                   waiting=(("court_documents", "outcome LIKE 'waiting%'"),),
                   asks=("qv4-courts-jdo-capture", "qv4-courts-era-capture")),
    "iwi_directory": Lane(update=("qv4-iwi-directory-capture", "qv4-iwi-directory-load"),
                          positions=("iwi-and-hapu-directory",), corpora=("estate-iwi_directory",),
                          mcp_hosts=("tkm.govt.nz",)),   # 14 November 2026: the walk is answered from the copy
    "contract_disclosures": Lane(update=("qv4-contract-disclosures-refresh", "qv4-contract-disclosures-load"),
                                 hosts=("catalogue.data.govt.nz", "acc.co.nz")),
    "council_minutes": Lane(update=("qv4-council-minutes-capture", "qv4-council-minutes-load"),
                            read=("qv4-council-minutes-read", "qv4-council-minutes-pages"),
                            hosts=("*.infocouncil.biz",), positions=("council-meeting-platform-infocouncil",),
                            asks=("qv4-council-minutes-capture",), corpora=("estate-council_minutes",)),
    "councillor_interests": Lane(update=("qv4-councillor-interests-capture", "qv4-councillor-interests-load"),
                                 read=("qv4-councillor-interests-read",), positions=("councillors-registers-of-interests",),
                                 asks=("qv4-councillor-interests-capture",), corpora=("estate-councillor_interests",)),
    "local_elections": Lane(update=("qv4-local-elections-listings", "qv4-local-elections-files", "qv4-local-elections-load"),
                            positions=("local-election-candidate-returns",), coverage="local_elections",
                            asks=("qv4-local-elections-listings", "qv4-local-elections-files"),
                            corpora=("estate-local_elections",)),
    "links": Lane(update=("qv4-links-build", "qv4-sightings-forms", "qv4-sightings-beehive", "qv4-sightings-hansard",
                          "qv4-sightings-parliament", "qv4-sightings-courts")),
    "insolvency": Lane(update=("qv4-insolvency-removals", "qv4-insolvency-capture", "qv4-insolvency-load"),
                       positions=("insolvency-register",)),
    "papers_past": Lane(update=("qv4-papers-past-ingest", "qv4-papers-past-index")),
    # not held
    "openlaw": Lane(note="no job installed (ruling 137 dropped it)"),
    "hdc_decisions": Lane(note="no job installed (a ruling on the Commissioner's terms is owed)"),
    "tenancy_tribunal": Lane(update=("qv4-tenancy-tribunal-capture",), hosts=("forms.justice.govt.nz",),
                             positions=("tenancy-tribunal-decisions",), asks=("qv4-tenancy-tribunal-capture",),
                             corpora=("estate-tenancy_tribunal",)),
    "settlement_commitments": Lane(update=("qv4-settlement-commitments-watch",), positions=("treaty-settlement-commitments",),
                                   corpora=("estate-settlement_commitments",),
                                   mcp_hosts=("tehaeata.govt.nz",)),   # 14 November 2026: the watch is answered from the copy
    "council_procurement": Lane(update=("qv4-council-procurement-watch",), hosts=("vendorpanel.nz",),
                                positions=("council-procurement-platforms",)),
}

#: the lane's own count against the source's: key -> SQL returning (held, listed, failed) on pub
COVERAGE = {
    "local_elections": ("SELECT coalesce(sum(files_held), 0), coalesce(sum(returns_listed), 0), coalesce(sum(files_failed), 0) "
                        "FROM pub.local_election_returns_coverage", "return files held"),
}


# ── the registers, read from the board's catalogue as a file ─────────────────

def registers(path: str = None) -> list:
    """[(register, plain name, held in the catalogue's REGISTERS)] in the
    catalogue's order: REGISTERS, then NOT_HELD."""
    tree = ast.parse(open(path or CATALOGUE, encoding="utf-8").read())
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("REGISTERS", "NOT_HELD"):
            found[node.targets[0].id] = ast.literal_eval(node.value)
    return [(r, plain, True) for r, plain in found.get("REGISTERS", ())] + \
           [(r, plain, False) for r, plain in found.get("NOT_HELD", ())]


# ── the declared gaps ────────────────────────────────────────────────────────

def gaps(path: str = None) -> list:
    """Every [[gap]] of the declaration file: register, reason, since, source."""
    try:
        with open(path or GAPS_FILE, "rb") as f:
            raw = tomllib.load(f)
    except OSError:
        return []
    out = []
    for g in raw.get("gap") or []:
        for k in ("register", "reason", "since", "source"):
            if not g.get(k):
                raise ValueError(f"a gap in {path or GAPS_FILE} names no {k}: {g}")
        hosts = g.get("hosts") or []
        if isinstance(hosts, str) or not all(isinstance(h, str) and h for h in hosts):
            raise ValueError(f"a gap's hosts in {path or GAPS_FILE} is a list of host names: {g}")
        out.append({**{k: str(g[k]) for k in ("register", "reason", "since", "source")}, "hosts": tuple(hosts)})
    return out


# ── hosts ────────────────────────────────────────────────────────────────────

def position_hosts(folder: str = None) -> dict:
    """position name -> its hosts, every one (fetchgate.positions keeps one class per host)."""
    import re
    folder = folder or fetchgate.POSITIONS_DIR
    out = {}
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return out
    for n in names:
        if n.endswith(".md"):
            with open(os.path.join(folder, n), encoding="utf-8") as f:
                m = re.search(r"^hosts:\s*(.+)$", f.read(), re.M)
            if m:
                out[n[:-3]] = tuple(h.strip().lower() for h in m.group(1).split(",") if h.strip())
    return out


def _bare(host: str) -> str:
    host = (host or "").lower().strip().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def lane_hosts(lane: Lane, positions: dict) -> set:
    hosts = {_bare(h) for h in lane.hosts} | {_bare(h) for p in lane.positions for h in positions.get(p, ())}
    return hosts - {_bare(h) for h in lane.mcp_hosts}


def host_matches(held: str, hosts: set) -> bool:
    """The gate holds a host exactly (refused_by), so a held host stops the
    lane where the lane asks that host; `*.x` names every host under x."""
    h = _bare(held)
    return any(h == x or (x.startswith("*.") and h.endswith(x[1:])) for x in hosts)


# ── the clock ────────────────────────────────────────────────────────────────

def when(t) -> str:
    """A time in plain words, NZ time: '4 Nov 00:30'."""
    if t is None:
        return "never"
    if isinstance(t, str):
        t = dt.datetime.fromisoformat(t)
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    t = t.astimezone(ZONE)
    return f"{t.day} {t:%b %H:%M}"


def cadence_s(jt) -> int:
    """A job's own cadence: every_s, or a day for at_utc (once or more a day); 0 for none."""
    if jt.every_s:
        return jt.every_s
    return DAY_S if jt.at_utc else 0


def parents(job: str, registry: dict) -> list:
    """The jobs whose `then` queues this one."""
    return [n for n, jt in registry.items() if job in jt.then and jt.enabled]


def on_a_clock(job: str, registry: dict, seen=None) -> bool:
    """A clock of its own, or a chain back to one."""
    seen = seen or set()
    if job in seen or job not in registry:
        return False
    seen.add(job)
    if cadence_s(registry[job]):
        return True
    return any(on_a_clock(p, registry, seen) for p in parents(job, registry))


def late(job: str, facts: dict, now: dt.datetime) -> str | None:
    """Why the job is late, or None. A job with a clock: no good run inside
    its cadence, its deadline and the grace (from the slot it went on the
    clock at, if it is new to it). A job queued by another: that job finished
    well and this one has not run since, past its deadline and the grace."""
    registry = facts["registry"]
    jt = registry[job]
    grace = dt.timedelta(seconds=max(jt.needs.deadline_s, 3600) + GRACE_S)
    open_rows = [r for r in facts["open"] if r["job"] == job]
    every = cadence_s(jt)
    if every:
        # the MCP pull's queue row fails on a corpus's new field; that is judged per corpus, so any run counts here
        ref = (facts["last_finished"] if job == MCP_PULL else facts["last_done"]).get(job)
        ref = ref["finished_at"] if ref else None
        tt = facts["timetable"].get(job)
        if tt and tt.get("last_slot") and any(w in (tt.get("last_by") or "") for w in ("new to the clock", "timetable changed")):
            ref = max(ref, tt["last_slot"]) if ref else tt["last_slot"]
        if ref is None:
            return f"{job} has had no good run on the scheduler"
        if now - ref > dt.timedelta(seconds=every) + grace:
            return f"{job} has not run well since {when(ref)} (it runs {every_words(jt)})"
        return None
    if open_rows:
        return None
    lasts = [facts["last_done"].get(p) for p in parents(job, registry)]
    lasts = [x["finished_at"] for x in lasts if x]
    if not lasts:
        return None
    parent_at = max(lasts)
    mine = facts["last_finished"].get(job)
    if (mine is None or mine["finished_at"] < parent_at) and now - parent_at > grace:
        return f"{job} has not run since the job before it finished at {when(parent_at)}"
    return None


def every_words(jt) -> str:
    if jt.every_s:
        h = jt.every_s / 3600
        return f"every {h:g} hours" if h < 48 else f"every {h / 24:g} days"
    return "daily"


# ── the provider's freshness (ruling 159) ────────────────────────────────────

def cadences(path: str = None) -> dict:
    """corpus -> {days, basis, reason, paused_until (a date or None)} from checks/mcp_cadence.toml."""
    with open(path or CADENCE_FILE, "rb") as f:
        raw = tomllib.load(f)
    out = {}
    for c in raw.get("corpus") or []:
        for k in ("corpus", "basis", "reason"):
            if not c.get(k):
                raise ValueError(f"a cadence in {path or CADENCE_FILE} names no {k}: {c}")
        days = c.get("days")
        if not isinstance(days, int) or isinstance(days, bool) or days < 0:
            raise ValueError(f"a cadence's days is a whole number of days, 0 for a closed corpus: {c}")
        if c["basis"] not in ("measured", "default"):
            raise ValueError(f"a cadence's basis is measured or default: {c}")
        if c["corpus"] in out:
            raise ValueError(f"{c['corpus']} has two cadences in {path or CADENCE_FILE}")
        until = c.get("paused_until")
        if until is not None:
            until = dt.date.fromisoformat(str(until))
        out[c["corpus"]] = {"days": days, "basis": c["basis"], "reason": str(c["reason"]), "paused_until": until}
    return out


def publishes(days: int) -> str:
    """A cadence in plain words."""
    return {1: "daily", 2: "about daily", 3: "every few days", 7: "about weekly", 8: "about weekly",
            14: "about fortnightly", 30: "about monthly", 31: "about monthly", 92: "about quarterly"}.get(
        days, f"about every {days} days")


def copy_state(corpus: str, facts: dict, now: dt.datetime) -> dict:
    """How fresh the provider's copy of one corpus is: {state, corpus, newest, age_days, days, over_days, paused,
    row}. state: "red" (older than three times its cadence), "orange" (older than its cadence), "fresh", "paused"
    (a declared pause), "closed" (days 0), "uncadenced" (no line in mcp_cadence.toml) or "unmeasured" (no reading
    of `corpora` holds it). Judged by the provider's `newest_arrival`, never by our pull; after a declared pause
    the age counts from the pause's end."""
    cad = facts.get("cadence", {}).get(corpus)
    row = facts.get("freshness", {}).get(corpus)
    out = {"corpus": corpus, "cadence": cad, "row": row, "newest": row and row.get("newest_arrival")}
    if cad is None:
        return {**out, "state": "uncadenced"}
    if cad["days"] == 0:
        return {**out, "state": "closed"}
    until = cad.get("paused_until")
    if until and now.astimezone(ZONE).date() < until:
        return {**out, "state": "paused"}
    if row is None or row.get("newest_arrival") is None:
        return {**out, "state": "unmeasured"}
    since = row["newest_arrival"]
    if until:
        since = max(since, dt.datetime.combine(until, dt.time(), ZONE))
    age = (now - since).total_seconds() / DAY_S
    state = RED if age > 3 * cad["days"] else ORANGE if age > cad["days"] else "fresh"
    return {**out, "state": state, "age_days": age, "over_days": age - cad["days"]}


def _stale_line(x: dict) -> str:
    cad = x["cadence"]
    line = (f"the provider's copy of {x['corpus']} has had nothing new since {when(x['newest'])}; "
            f"its source publishes {publishes(cad['days'])}")
    if x["state"] == RED:
        line += f" ({x['age_days']:.0f} days, over three times that)"
    return line


def red_stale_copy(c: "Ctx") -> list:
    return [_stale_line(x) for x in (copy_state(k, c.facts, c.now) for k in c.lane.corpora) if x["state"] == RED]


def orange_stale_copy(c: "Ctx") -> list:
    return [_stale_line(x) for x in (copy_state(k, c.facts, c.now) for k in c.lane.corpora) if x["state"] == ORANGE]


def fresh_line(lane: Lane, facts: dict, now: dt.datetime) -> str:
    """One short line for the board: the stalest judged copy the lane reads; "" for a lane the MCP does not feed."""
    if not lane.corpora:
        return ""
    xs = [copy_state(k, facts, now) for k in lane.corpora]
    judged = [x for x in xs if x["state"] in (RED, ORANGE, "fresh")]
    if judged:
        x = max(judged, key=lambda x: x["age_days"])
        n = x["row"].get("arrivals_last_24h")
        return (f"provider's copy: newest {when(x['newest'])}"
                + (f", {n:,} in its last day" if n else "")
                + f"; its source publishes {publishes(x['cadence']['days'])}")
    paused = [x for x in xs if x["state"] == "paused"]
    if paused:
        until = min(x["cadence"]["paused_until"] for x in paused)
        return f"provider's copy: not judged until {until.day} {until:%b} (a declared pause, checks/mcp_cadence.toml)"
    if any(x["state"] == "unmeasured" for x in xs):
        return "provider's copy: no freshness measure yet"
    return ""


def stale_corpora(facts: dict, now: dt.datetime) -> list:
    """Every corpus past its cadence, the most overdue first: what the provider is asked to refresh."""
    xs = [copy_state(k, facts, now) for k in sorted(facts.get("freshness", {}))]
    return sorted((x for x in xs if x["state"] in (RED, ORANGE)), key=lambda x: -x["over_days"])


def no_collector(facts: dict, now: dt.datetime) -> list:
    """Corpora not yet past their cadence but with no lane in the provider's `pipeline` and nothing new in the last
    24 hours: no collector is visible, so a stop shows now, not a cadence later (10 November 2026: thirteen estate-*
    corpora had no lane and no arrival for one to eleven days while their cadences called four of them fresh)."""
    stale = {x["corpus"] for x in stale_corpora(facts, now)}
    out = []
    for k in sorted(facts.get("freshness", {})):
        x = copy_state(k, facts, now)
        row = x["row"] or {}
        if (k in stale or x["state"] != "fresh" or not row.get("pipeline_read") or row.get("pipeline_lane")
                or row.get("arrivals_last_24h")):
            continue
        out.append(x)
    return out


PAGE_ROWS = 30      # never more than a page
ASKED = "a running collector at the cadence, or word that it is a one-time copy"
CLOSING_TITLE = "For the provider: closing the loop"
REPAIRED_KEEP_DAYS = 7     # a repair stays in the feed this long after the fresh arrival that showed it


def closing_section(previous_page: str = None, template: str = None) -> str:
    """The integrator's closing section, carried through verbatim: the template file when there is one
    (<handover>/mcp-stale.closing.md), else the section of that title in the page as last written; "" for none."""
    for text, whole in ((template, True), (previous_page, False)):
        if not text:
            continue
        if whole:
            return text.strip("\n") + "\n"
        lines = text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#") and line.lstrip("#").strip() == CLOSING_TITLE:
                return "\n".join(lines[i:]).strip("\n") + "\n"
    return ""


def _lane_words(row: dict) -> str:
    if row.get("pipeline_lane"):
        return row["pipeline_lane"] + (f" ({row['pipeline_status']})" if row.get("pipeline_status") else "")
    return "no lane in pipeline.yaml" if row.get("pipeline_read") else "not known (`pipeline` did not answer)"


def _iso(t) -> str:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds") if t else None


def request_id(corpus: str, newest) -> str:
    """Stable per corpus and staleness episode: the episode ends with a fresh arrival, which moves newest_arrival."""
    return f"{corpus}@{_iso(newest)}"


def provider_feed(facts: dict, now: dt.datetime, previous: dict = None, asks_dir: str = None) -> dict:
    """The machine-readable list (schema 1; Arthur, 10 November 2026): one object per stale corpus, and `repaired`:
    corpora stale on the last run whose newest arrival has moved since, so fresh arrivals, never the provider's word,
    confirm a repair. Kept REPAIRED_KEEP_DAYS after the arrival that showed it."""
    stale = []
    for x in stale_corpora(facts, now):
        row, cad = x["row"], x["cadence"]
        stale.append({"corpus": x["corpus"], "newest_arrival": _iso(x["newest"]), "records": row.get("records"),
                      "arrivals_last_24h": row.get("arrivals_last_24h"), "cadence_days": cad["days"],
                      "cadence_measured": cad["basis"] == "measured", "days_overdue": round(x["over_days"], 1),
                      "pipeline_lane": row.get("pipeline_lane"), "asked": ASKED,
                      "request_id": request_id(x["corpus"], x["newest"])})
    stale.sort(key=lambda o: o["corpus"])
    now_stale = {o["corpus"] for o in stale}
    fresh = facts.get("freshness", {})
    repaired = {}
    prev = previous if isinstance(previous, dict) else {}
    for o in prev.get("repaired") or []:          # still inside the keeping period, and not stale again
        try:
            kept = (now - dt.datetime.fromisoformat(o["repaired_at"])).total_seconds() < REPAIRED_KEEP_DAYS * DAY_S
        except (KeyError, TypeError, ValueError):
            continue
        if kept and o.get("corpus") not in now_stale:
            repaired[o["corpus"]] = o
    for o in prev.get("stale") or []:
        c = o.get("corpus")
        row = fresh.get(c)
        was = o.get("newest_arrival")
        if c in now_stale or not row or not row.get("newest_arrival") or not was:
            continue
        try:
            moved = row["newest_arrival"] > dt.datetime.fromisoformat(was)
        except (TypeError, ValueError):
            continue
        if moved:                                  # fresh arrivals since the run that listed it
            repaired[c] = {"corpus": c, "request_id": o.get("request_id"), "stale_newest_arrival": was,
                           "repaired_at": _iso(row["newest_arrival"]), "seen_at": _iso(now)}
    at = [r["at"] for r in fresh.values() if r.get("at")]
    quiet = [{"corpus": x["corpus"], "newest_arrival": _iso(x["newest"]), "records": x["row"].get("records"),
              "cadence_days": x["cadence"]["days"], "pipeline_lane": None,
              "asked": "a lane in pipeline for this corpus, or word that it is a one-time copy",
              "request_id": request_id(x["corpus"], x["newest"])} for x in no_collector(facts, now)]
    short = [{k: o.get(k) for k in ("corpus", "source", "listed", "missing", "earliest_take_down", "by_take_down_month",
                                    "orders", "asked", "request_id", "written_at")} for o in lane_asks(asks_dir)]
    return {"schema_version": 1, "measured_at": _iso(max(at)) if at else None, "written_at": _iso(now),
            "stale": stale, "no_collector": quiet, "repaired": sorted(repaired.values(), key=lambda o: o["corpus"]),
            "short_of_source": short}


def provider_list(facts: dict, now: dt.datetime, closing: str = "", feed: dict = None) -> str:
    """The provider's list (ruling 159): dated, plain, at most a page. Arthur passes it on. `closing` (the
    integrator's section) is carried through verbatim at the end."""
    rows = stale_corpora(facts, now)
    at = [r["at"] for r in facts.get("freshness", {}).values() if r.get("at")]
    t = now.astimezone(ZONE)
    out = [f"# The ingest MCP's stale copies, {t.day} {t:%B %Y} {t:%H:%M} NZ time", "",
           "Each corpus here has had no new record for longer than its source's usual gap between publications. "
           "The dates are the MCP's own (`corpora`: newest arrival)"
           + (f", read {when(max(at))}" if at else "") + ". The cadences and their reasons are in "
           "checks/mcp_cadence.toml. This file is rewritten every half hour; the same list is in mcp-stale.json.", ""]
    if not rows:
        out.append("Nothing is stale: every corpus is inside its cadence." if at else
                   "No reading of `corpora` is held yet, so nothing can be judged.")
    else:
        out += ["| Corpus | Newest arrival | Its source publishes | Days overdue | Provider's pipeline lane |",
                "| --- | --- | --- | --- | --- |"]
        for x in rows[:PAGE_ROWS]:
            over = x["over_days"]
            out.append(f"| {x['corpus']} | {when(x['newest'])} | {publishes(x['cadence']['days'])} "
                       f"(every {x['cadence']['days']} days) | {'under 1' if over < 1 else f'{over:.0f}'} | "
                       f"{_lane_words(x['row'])} |")
        if len(rows) > PAGE_ROWS:
            out.append(f"\nAnd {len(rows) - PAGE_ROWS} more.")
        out += ["", f"What is asked, for each: {ASKED}."]
    quiet = no_collector(facts, now)
    if quiet:
        out += ["", "No collector visible: not yet past its cadence, but no lane in the provider's pipeline and nothing "
                "new in the last 24 hours.", "",
                "| Corpus | Newest arrival | Its source publishes |", "| --- | --- | --- |"]
        for x in quiet[:PAGE_ROWS]:
            out.append(f"| {x['corpus']} | {when(x['newest'])} | {publishes(x['cadence']['days'])} |")
        out += ["", "What is asked, for each: a lane in pipeline for it, or word that it is a one-time copy."]
    short = (feed or {}).get("short_of_source") or []
    if short:
        out += ["", "Short of the source's own list: the source lists these, and neither our register nor the MCP's copy "
                "holds them. The ids, soonest to be taken down first, are in mcp-stale.json (`short_of_source`).", "",
                "| Corpus | Source lists | Neither holds | First taken down |", "| --- | --- | --- | --- |"]
        for o in short:
            out.append(f"| {o['corpus']} | {o.get('listed') or '?':,} | {o['missing']:,} | {o.get('earliest_take_down') or '?'} |"
                       if isinstance(o.get("listed"), int) else
                       f"| {o['corpus']} | ? | {o['missing']:,} | {o.get('earliest_take_down') or '?'} |")
        out += [""] + [f"What is asked for {o['corpus']}: {o.get('asked') or ASKED}." for o in short]
    rep = (feed or {}).get("repaired") or []
    if rep:
        out += ["", "Repaired (new records have arrived since it was listed): "
                + ", ".join(f"{o['corpus']} ({when(o['repaired_at'])})" for o in rep) + "."]
    text = "\n".join(out) + "\n"
    return text + ("\n" + closing if closing else "")


def _write(text: str, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def write_provider_list(text: str, path: str = None) -> str:
    return _write(text, path or STALE_FILE)


def write_provider_feed(feed: dict, path: str = None) -> str:
    return _write(json.dumps(feed, ensure_ascii=False, indent=1, sort_keys=True) + "\n", path or STALE_JSON)


def _read(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def provider_outputs(facts: dict, now: dt.datetime, page_path: str = None, json_path: str = None,
                     template_path: str = None) -> tuple:
    """(page, feed) from the facts, the last feed (for repairs) and the closing section (template, or the last page)."""
    page_path, json_path = page_path or STALE_FILE, json_path or STALE_JSON
    try:
        previous = json.loads(_read(json_path) or "null")
    except ValueError:
        previous = None
    feed = provider_feed(facts, now, previous)
    closing = closing_section(_read(page_path), _read(template_path or STALE_CLOSING))
    return provider_list(facts, now, closing, feed), feed


# ── the lights ───────────────────────────────────────────────────────────────

def corpus_reds(lane: Lane, facts: dict) -> list:
    """For a lane the ingest MCP feeds: the last pull's record, per corpus."""
    if not lane.corpora:
        return []
    rec = facts.get("mcp_run")
    last = facts["last_finished"].get(MCP_PULL)
    if rec is None:
        return [f"{MCP_PULL}'s last run failed at {when(last['finished_at'])}"] if last and last["state"] == "failed" else []
    out = []
    at = when(rec.get("ended") or rec.get("started"))
    detail = str(rec.get("detail") or "")
    for c in lane.corpora:
        if f"{c}_to" not in rec:
            # red only when the run says it failed on this corpus, or on `corpora` itself. A corpus the run did not
            # reach (its budget spent: the estate-* corpora come last in the pull's list) is not a failure; the
            # copy's freshness is judged by the provider's newest arrival instead (ruling 159)
            if not rec.get("ok", True) and (f"{c}: FAILED" in detail or "`corpora` failed" in detail):
                out.append(f"{MCP_PULL} failed on the {c} corpus ({at})")
            continue
        if rec.get(f"{c}_caught"):
            out.append(f"{MCP_PULL} caught {rec[f'{c}_caught']:,} {c} record(s) it could not land ({at})")
        if rec.get(f"{c}_drift"):
            out.append(f"{MCP_PULL} met {rec[f'{c}_drift']:,} new field(s) in the {c} corpus no register carries ({at})")
    return out


@dataclasses.dataclass(frozen=True)
class Ctx:
    register: str
    lane: Lane
    update: list            # its update jobs in the catalogue and switched on
    read: list              # its readers, the same
    clocked: list           # its update jobs on a clock, or chained to one
    facts: dict
    now: dt.datetime


# each rule takes the context and returns its reasons; a light is the first colour with any (mutant-tested)

def held_hosts(c: Ctx) -> tuple:
    """(the gate's holds that stop the lane, the holds that thin it), each [(host, row)]. Only for a lane with an
    update job switched on (a lane that asks nothing is not stopped by a hold), and never a hold a declared gap of the
    register names (its reason says it). A hold stops the lane when the host is one the lane names as its own, or when
    every host the lane reads is held; a hold on one of the many hosts its positions name (a council's site among 78)
    leaves the rest asked: the corpus is not whole, the updates still work."""
    registry = c.facts["registry"]
    asking = [j for j in c.lane.asks if j in c.update and "--from-mcp" not in tuple(getattr(registry.get(j), "command", ()) or ())]
    if not c.update or (c.lane.asks and not asking):   # a capture reading the MCP's copy asks no host (10 November 2026)
        return [], []
    hosts = lane_hosts(c.lane, c.facts["positions"])
    own = {_bare(h) for h in c.lane.hosts}
    declared = {_bare(h) for g in c.facts["gaps"] if g["register"] == c.register for h in g.get("hosts", ())}
    held = [(h, row) for h, row in sorted(c.facts["refusals"].items())
            if host_matches(h, hosts) and _bare(h) not in declared]
    every = {x for x in hosts if not x.startswith("*.")} <= {_bare(h) for h, _ in held}
    stop = [(h, row) for h, row in held if every or host_matches(h, own)]
    return stop, [x for x in held if x not in stop]


def _held_line(host, row) -> str:
    return f"the fetch gate holds {host} since {when(row.get('at'))}: {row.get('why')}"


def red_held_host(c: Ctx) -> list:
    return [_held_line(h, row) for h, row in held_hosts(c)[0]]


def orange_held_host(c: Ctx) -> list:
    thin = held_hosts(c)[1]
    n = len(lane_hosts(c.lane, c.facts["positions"]))
    return [_held_line(h, row) + f" (one of the {n} hosts the lane reads; the rest are still asked)" for h, row in thin]


def red_failed_run(c: Ctx) -> list:
    out = []
    for j in c.update + c.read:
        last = c.facts["last_finished"].get(j)
        if j != MCP_PULL and last and last["state"] == "failed":
            out.append(f"{j}'s last run failed at {when(last['finished_at'])}")
    return out


def red_corpus(c: Ctx) -> list:
    return corpus_reds(c.lane, c.facts)


def red_late(c: Ctx) -> list:
    return [w for w in (late(j, c.facts, c.now) for j in c.clocked) if w]


def orange_pieces(c: Ctx) -> list:
    return [f"{r['job']} has {r['pieces_total'] - r['pieces_done']:,} of {r['pieces_total']:,} pieces to go"
            for r in c.facts["open"]
            if r["job"] in c.update + c.read and (r["pieces_total"] or 0) > (r["pieces_done"] or 0)]


def orange_waiting(c: Ctx) -> list:
    n = c.facts["waiting"].get(c.register)
    return [f"{n:,} document(s) waiting on a reader"] if n else []


def orange_short_count(c: Ctx) -> list:
    cov = c.facts["coverage"].get(c.register)
    if not (cov and c.lane.coverage and cov[1] > cov[0]):
        return []
    return [f"{cov[0]:,} of {cov[1]:,} {COVERAGE[c.lane.coverage][1]}"
            + (f" ({cov[2]:,} failed)" if len(cov) > 2 and cov[2] else "")]


def orange_switched_off(c: Ctx) -> list:
    """An update job of the lane switched off in the catalogue while another still runs: the running one (a load, a
    pull) keeps the light from grey, but the register holds only what the switched-off job last gathered."""
    registry = c.facts["registry"]
    off = [j for j in c.lane.update if j in registry and not registry[j].enabled]
    if not (off and c.update):
        return []
    last = max((c.facts["last_done"][j]["finished_at"] for j in off if j in c.facts["last_done"]), default=None)
    return [f"{', '.join(off)} switched off in the catalogue, so the register holds what it last gathered"
            + (f" ({when(last)})" if last else "")]


def orange_gap(c: Ctx) -> list:
    return [f"{g['reason']} (declared {g['since']})" for g in c.facts["gaps"] if g["register"] == c.register]


def green_up_to_date(c: Ctx) -> list:
    last = max((c.facts["last_done"][j]["finished_at"] for j in c.update if j in c.facts["last_done"]), default=None)
    return [f"up to date: last good update {when(last)}"]


RED_RULES = [red_held_host, red_failed_run, red_corpus, red_stale_copy, red_late]
ORANGE_RULES = [orange_held_host, orange_switched_off, orange_stale_copy, orange_pieces, orange_waiting, orange_short_count,
                orange_gap]
GREEN_RULES = [green_up_to_date]


def light_of(register: str, held: bool, facts: dict, now: dt.datetime) -> dict:
    out = _light_of(register, held, facts, now)
    lane = LANES.get(register)
    fresh = fresh_line(lane, facts, now) if lane else ""
    return {**out, "fresh": fresh} if fresh else out


def _light_of(register: str, held: bool, facts: dict, now: dt.datetime) -> dict:
    registry = facts["registry"]
    lane = LANES.get(register)
    if lane is None:
        return _light(register, GREY, ["no update job: the lights do not know this register yet"])
    update = [j for j in lane.update if j in registry and registry[j].enabled]
    read = [j for j in lane.read if j in registry and registry[j].enabled]
    c = Ctx(register, lane, update, read, [j for j in update if on_a_clock(j, registry)], facts, now)
    reds = [w for rule in RED_RULES for w in rule(c)]
    if reds:
        return _light(register, RED, reds)
    if not c.clocked:
        off = [j for j in lane.update if j in registry and not registry[j].enabled]
        why = lane.note or ("loaded on demand, no update job on a clock" if update
                            else f"{', '.join(off)} switched off in the catalogue" if off else "none named")
        return _light(register, GREY, [f"no update job: {why}"])
    oranges = [w for rule in ORANGE_RULES for w in rule(c)]
    if oranges:
        return _light(register, ORANGE, oranges)
    greens = [w for rule in GREEN_RULES for w in rule(c)]
    if greens:
        return _light(register, GREEN, greens)
    return _light(register, GREY, ["no rule gave a light"])


def _light(register: str, light: str, reasons: list) -> dict:
    reason = reasons[0] + (f" (and {len(reasons) - 1} more)" if len(reasons) > 1 else "")
    return {"register": register, "light": light, "reason": reason, "reasons": reasons}


def compute(facts: dict, now: dt.datetime = None, regs: list = None) -> dict:
    now = now or dt.datetime.now(dt.timezone.utc)
    regs = regs if regs is not None else registers()
    lights = [light_of(r, held, facts, now) for r, _, held in regs]
    out = {"computed_at": now.astimezone(dt.timezone.utc).isoformat(timespec="seconds"), "lights": lights}
    out["sources"] = sources(lights, facts, now, {r: plain for r, plain, _ in regs})
    return out


# ── every source, for the board's Sources tab (Arthur, 14 November 2026) ─────
# "I want each source to be a link and I want a 1 line explanation of why its light is the colour it is when i hover":
# a row for each register, each corpus the provider reports, each news site the old copy holds, and each request to
# the provider still waiting; each with the publisher's link (checks/source_links.toml) and one line that begins with
# its light's word.

LINKS_FILE = os.path.join(REPO, "checks", "source_links.toml")
WORDS = {RED: "Red", ORANGE: "Orange", GREEN: "Green", GREY: "Grey"}


def links(path: str = None) -> dict:
    try:
        with open(path or LINKS_FILE, "rb") as f:
            raw = tomllib.load(f)
    except OSError:
        return {"registers": {}, "corpora": {}, "requests": [], "other_means": [], "covered": {}}
    return {"registers": raw.get("registers") or {}, "corpora": raw.get("corpora") or {},
            "requests": raw.get("requests") or [], "other_means": (raw.get("news") or {}).get("other_means") or [],
            "covered": raw.get("covered") or {}}


def other_means(host: str, patterns: list) -> bool:
    """A news site of the old copy gathered another way: its name, `*.x` (every host under x) or `x.*` (every host
    beginning `x.`)."""
    h = _bare(host)
    for p in patterns:
        p = _bare(p)
        if h == p or (p.startswith("*.") and h.endswith(p[1:])) or (p.endswith(".*") and h.startswith(p[:-1])):
            return True
    return False


def pulled(registry: dict) -> set:
    """The corpora qv4-mcp-pull copies: its command's --corpus names."""
    job = registry.get(MCP_PULL)
    cmd = list(getattr(job, "command", None) or ())
    return {cmd[i + 1] for i, a in enumerate(cmd[:-1]) if a == "--corpus"}


def _one(light: str, words: str) -> str:
    return f"{WORDS[light]}: {words}"


def _day(d) -> str:
    return f"{d.day} {d:%b}"


def corpus_url(corpus: str, ln: dict) -> str:
    c = ln["corpora"]
    if corpus in c:
        return c[corpus]
    if corpus.startswith("parliament-") and "parliament" in c:
        return c["parliament"]
    if corpus.startswith("estate-"):
        return ln["registers"].get(corpus[len("estate-"):].replace("-", "_"), "")
    return ""


def copy_row(corpus: str, facts: dict, now: dt.datetime, taken: set, readers: dict, ln: dict) -> dict:
    x = copy_state(corpus, facts, now)
    row = x["row"] or {}
    n = row.get("records")
    held = f"{n:,} records" if isinstance(n, int) else "records not counted"
    if corpus not in taken:
        light, words = GREY, f"the provider holds it ({held}); our pull does not copy it yet"
    elif not readers.get(corpus) and corpus in ln.get("covered", {}):
        light, words = GREY, f"copied ({held}), read by no register: {ln['covered'][corpus]}"
    elif not readers.get(corpus):
        light, words = ORANGE, f"copied ({held}), but no register reads it yet"
    elif x["state"] in (RED, ORANGE):
        light, words = x["state"], _stale_line(x)
    elif x["state"] == "fresh":
        light, words = GREEN, (f"newest arrival {when(x['newest'])}, inside its source's {publishes(x['cadence']['days'])} "
                               f"cadence; read by {', '.join(readers[corpus])}")
    elif x["state"] == "paused":
        light, words = GREY, f"a declared pause until {_day(x['cadence']['paused_until'])} (checks/mcp_cadence.toml)"
    elif x["state"] == "closed":
        light, words = GREEN, f"a closed set ({held}): nothing more is published"
    elif x["state"] == "uncadenced":
        light, words = GREY, f"copied and read ({held}), but no cadence is declared to judge it by"
    else:
        light, words = GREY, "copied and read, but the provider has given no freshness measure yet"
    return {"kind": "copy", "name": corpus, "label": corpus, "url": corpus_url(corpus, ln), "light": light,
            "line": _one(light, words)}


def news_row(site: dict, copy: dict, now: dt.datetime) -> dict:
    """A news site from the old copy: green when its newest article is within a week, else orange; the provider's
    estate-news copy (asked 13 November) is what walks it forward."""
    newest = site.get("newest")
    host = site["host"]
    n = site.get("articles") or 0
    if not newest:
        light, words = GREY, f"{n:,} articles held, none dated"
    else:
        d = dt.date.fromisoformat(newest)
        age = (now.astimezone(ZONE).date() - d).days
        span = f"{n:,} articles, {site.get('earliest') or '?'} to {newest}"
        if age <= 7:
            light, words = GREEN, f"{span}: newest {age} days old"
        else:
            words = f"{span}: nothing newer held ({age} days)"
            if copy.get("asked"):
                words += f"; the provider was asked on {_day(copy['asked'])} to walk it forward"
            light = ORANGE
    return {"kind": "news", "name": host, "label": host, "url": f"https://{host}", "light": light,
            "line": _one(light, words)}


def request_rows(ln: dict, facts: dict, now: dt.datetime) -> list:
    out, today = [], now.astimezone(ZONE).date()
    fresh = facts.get("freshness", {})
    for r in ln["requests"]:
        corpus = r.get("corpus") or ""
        row = fresh.get(corpus) if corpus else None
        until = r.get("until_records")
        standing = r.get("standing") is True
        if not standing and row is not None and (until is None or (row.get("records") or 0) > until):
            continue   # landed: the corpus's own row speaks for it
        due, asked = r.get("due"), r.get("asked")
        if standing and row is not None and row.get("records"):
            light = ORANGE
            words = (f"asked {_day(asked)}; copies arriving ({row['records']:,} records in {corpus} so far)"
                     + (f", the provider's date {_day(due)}" if due else "") + "; open until the provider reports it done")
        elif due and today > due:
            light, words = RED, f"asked {_day(asked)}, due {_day(due)}, nothing has landed"
        else:
            light = ORANGE
            words = f"asked {_day(asked)}; " + (f"the provider's date for the first copies is {_day(due)}" if due
                                                 else "the provider has not given a date yet")
        out.append({"kind": "request", "name": r["id"], "label": r["title"], "url": r.get("url") or "",
                    "light": light, "line": _one(light, words)})
    return out


def sources(lights: list, facts: dict, now: dt.datetime, plain: dict = None, ln: dict = None) -> list:
    ln = ln if ln is not None else links()
    plain = plain or {}
    positions = facts.get("positions") or {}
    out = []
    for x in lights:
        lane = LANES.get(x["register"])
        url = ln["registers"].get(x["register"], "")
        if not url and lane:
            hosts = sorted(lane_hosts(lane, positions) | {_bare(h) for h in lane.mcp_hosts})
            hosts = [h for h in hosts if not h.startswith("*.")]
            url = f"https://{hosts[0]}" if hosts else ""
        out.append({"kind": "register", "name": x["register"], "label": plain.get(x["register"], x["register"]),
                    "url": url, "light": x["light"], "line": _one(x["light"], x["reason"])})
    taken = pulled(facts.get("registry") or {})
    readers = {}
    for register, lane in LANES.items():
        for k in lane.corpora:
            readers.setdefault(k, []).append(register)
    for corpus in sorted(set(facts.get("freshness", {})) | taken):
        out.append(copy_row(corpus, facts, now, taken, readers, ln))
    asked = {}
    for r in ln["requests"]:
        if r.get("corpus") == "estate-news" and r.get("asked"):
            asked = {"asked": min(r["asked"], asked.get("asked", r["asked"]))}
    for site in facts.get("news") or []:
        if not other_means(site["host"], ln.get("other_means") or []):
            out.append(news_row(site, asked, now))
    out.extend(request_rows(ln, facts, now))
    return out


# ── the facts ────────────────────────────────────────────────────────────────

def empty_facts(registry: dict = None) -> dict:
    return {"registry": registry if registry is not None else reg.load(), "last_finished": {}, "last_done": {},
            "open": [], "timetable": {}, "refusals": {}, "positions": {}, "mcp_run": None, "waiting": {},
            "coverage": {}, "gaps": [], "freshness": {}, "cadence": {}, "news": []}


def gather(conn, schema: str = "scheduler") -> dict:
    """Read every fact, on a read login. Each published count is one query."""
    from support import jobrun
    facts = empty_facts()

    def last(states):
        rows = conn.execute(f"SELECT DISTINCT ON (job) job, state, finished_at FROM {schema}.queue "
                            f"WHERE state = ANY(%s) AND finished_at IS NOT NULL ORDER BY job, finished_at DESC",
                            (list(states),)).fetchall()
        return {j: {"state": s, "finished_at": f} for j, s, f in rows}

    facts["last_finished"] = last(("done", "failed"))
    facts["last_done"] = last(("done",))
    facts["open"] = [{"job": j, "state": s, "pieces_done": d, "pieces_total": t} for j, s, d, t in conn.execute(
        f"SELECT job, state, pieces_done, pieces_total FROM {schema}.queue WHERE state IN ('queued', 'leased')").fetchall()]
    facts["timetable"] = {j: {"last_slot": s, "last_by": b} for j, s, b in conn.execute(
        f"SELECT job, last_slot, last_by FROM {schema}.timetable").fetchall()}
    facts["refusals"] = fetchgate.refusals()
    facts["positions"] = position_hosts()
    facts["mcp_run"] = jobrun.last_run(MCP_PULL)
    for register, lane in LANES.items():
        for view, cond in lane.waiting:
            n = conn.execute(f"SELECT count(*) FROM pub.{view} WHERE {cond}").fetchone()[0]
            facts["waiting"][register] = facts["waiting"].get(register, 0) + int(n)
        if lane.coverage:
            facts["coverage"][register] = tuple(int(x) for x in conn.execute(COVERAGE[lane.coverage][0]).fetchone())
    facts["gaps"] = gaps()
    from support.mcpsource import freshness
    facts["freshness"] = freshness.latest(conn)
    facts["cadence"] = cadences()
    from support.oldcopy import news_sites
    facts["news"] = news_sites.read()   # written by qv4-news-sites on the owner login; counts and dates only
    return facts


def write(result: dict, path: str = None) -> str:
    path = path or LIGHTS_FILE
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return path


def summary(result: dict) -> str:
    counts = {k: sum(1 for x in result["lights"] if x["light"] == k) for k in LIGHTS}
    lines = [f"source lights at {result['computed_at']}: " + ", ".join(f"{k} {v}" for k, v in counts.items())]
    for k in (RED, ORANGE, GREY, GREEN):
        for x in result["lights"]:
            if x["light"] == k:
                lines.append(f"  {k:<6} {x['register']:<24} {x['reason']}")
                if x.get("fresh"):
                    lines.append(f"  {'':<6} {'':<24} {x['fresh']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the source lights on the board's search pane")
    ap.add_argument("--print", action="store_true", help="print, write nothing")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    import support.db as db
    from support import jobrun
    started = dt.datetime.now().astimezone()
    with db.connect(db.READ_KEY, a.database, autocommit=True) as conn:
        conn.execute("SET statement_timeout = 60000")
        facts = gather(conn)
        result = compute(facts)
    print(summary(result))
    stale, feed = provider_outputs(facts, dt.datetime.fromisoformat(result["computed_at"]))
    if a.print:
        print("\n" + stale, end="")
        return 0
    write(result)
    write_provider_list(stale)
    write_provider_feed(feed)
    counts = {k: sum(1 for x in result["lights"] if x["light"] == k) for k in LIGHTS}
    jobrun.record(JOB, True, ", ".join(f"{k} {v}" for k, v in counts.items()), started, counts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
