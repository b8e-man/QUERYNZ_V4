"""The comparison with the frozen site (plan 4.5).

Each day the frozen product publishes a version under `var/pi-snapshot/v/`
in the live old folder (read only, as release_compare reads it) and the
watcher records a listing of the captured documents at that release. The
rebuilt site builds a version under `<live>/site/v/<stamp>/` from that
listing, so both sides had the same inputs and timing is not a difference.
This module pairs the two, reads every published file of the ten kinds on
both sides into figures (comparison_figures), differs them with no
tolerance on money, groups every difference by its cause, and writes the
day's result:

    <live>/checks/comparison/days/<frozen version>.json         the result, by cause
    <live>/checks/comparison/days/<frozen version>.diffs.jsonl  every difference with its cause
    <live>/checks/comparison/ledger.jsonl                       one line per day

A cause is one entry in CAUSES: a card in cards/, which side is right and
why, and a rule that recognises its differences. A difference no rule
recognises is "uncarded". A clean day has no uncarded difference and no
difference under a cause whose card says the new side is wrong (`right`
is "frozen"); passing is seven clean days in a row. A cause whose card
file is missing, or dropped, counts as uncarded: the card is the record.

    python -m checks.comparison run              compare today's pair and record it
    python -m checks.comparison run --frozen V --new W   a chosen pair
    python -m checks.comparison show             the last day, by cause
    python -m checks.comparison causes           the causes and their cards

The board item (`check`) reads the ledger: red when it is stale, missing
or the last day has uncarded differences. Stdlib only; writes only under
its state folder. Tests: checks/tests/test_comparison.py."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter, defaultdict

from checks import comparison_figures as F
from checks.comparison_figures import ABSENT, NOT_HELD

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
FROZEN_VERSIONS = os.path.join(OLD_LIVE, "var", "pi-snapshot", "v")
FROZEN_RELEASES = os.path.join(OLD_LIVE, "var", "pi-snapshot", "RELEASES.jsonl")
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
NEW_SITE = os.environ.get("QV4_SITE_OUT") or os.path.join(LIVE, "site")
STATE_DIR = os.path.join(LIVE, "checks", "comparison")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(REPO, "cards")
TEMPLATE = os.path.join(REPO, "products", "templates", "ftm", "ftm.json")
KINDS = ("home", "parties", "electorates", "pickers", "subject", "electorate", "donor", "board-member",
         "size-bands", "cite")
WINDOW_HOURS = 26
PASS_DAYS = 7
NAME = "comparison"
SAMPLE_PER_CAUSE = 40


# ── the two sides ─────────────────────────────────────────────────────────────

def frozen_current(releases: str = None, versions: str = None) -> str | None:
    """The frozen site's newest published version: the last `publish` row."""
    releases = releases or FROZEN_RELEASES
    last = None
    try:
        with open(releases, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("action") == "publish" and row.get("version"):
                    last = row["version"]
    except OSError:
        return None
    if last and os.path.isdir(os.path.join(versions or FROZEN_VERSIONS, last)):
        return last
    return None


def new_versions(site: str = None) -> list:
    """[(stamp, listing version)] of the rebuilt site's versions, oldest first."""
    root = os.path.join(site or NEW_SITE, "v")
    out = []
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return out
    for n in names:
        try:
            with open(os.path.join(root, n, "SNAPSHOT.json"), encoding="utf-8") as f:
                m = json.load(f)
        except (OSError, ValueError):
            continue
        out.append((n, (m.get("listing") or {}).get("version")))
    return out


def pair(frozen: str = None, site: str = None, releases: str = None, versions: str = None) -> dict:
    """Today's pair: the frozen current version and the newest rebuilt
    version built from its listing. `new` is None when none has been."""
    frozen = frozen or frozen_current(releases, versions)
    built = [s for s, lv in new_versions(site) if lv == frozen]
    return {"frozen": frozen, "new": built[-1] if built else None,
            "newest_new": (new_versions(site) or [(None, None)])[-1]}


def kind_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] != "data" or len(parts) < 2:
        return ""
    name = parts[1][:-5] if len(parts) == 2 and parts[1].endswith(".json") else parts[1]
    return name if name in KINDS else ""


def files_of(root: str) -> dict:
    """{relative path: kind} for every file of the ten kinds under a version."""
    out = {}
    for dirpath, dirs, names in os.walk(root):
        dirs.sort()
        for n in sorted(names):
            rel = os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/")
            k = kind_of(rel)
            if k:
                out[rel] = k
    return out


def load(root: str, rel: str):
    with open(os.path.join(root, rel), encoding="utf-8") as f:
        return json.load(f)


# ── matching files ────────────────────────────────────────────────────────────

def match_files(old: dict, new: dict) -> list:
    """[(kind, old rel or None, new rel or None)]. Paths match exactly; a
    person page whose key differs only in the hash (the frozen site wrote
    the name one way, the register another) is matched by its slug."""
    out = []
    common = set(old) & set(new)
    for rel in sorted(common):
        out.append((old[rel], rel, rel))
    old_only = {r: k for r, k in old.items() if r not in common}
    new_only = {r: k for r, k in new.items() if r not in common}
    by_slug = defaultdict(list)
    for r, k in new_only.items():
        if k == "subject" and r.split("/")[2] == "person":
            by_slug[F.slug_of_path(r)].append(r)
    for r, k in sorted(old_only.items()):
        if k == "subject" and r.split("/")[2] == "person":
            cands = by_slug.get(F.slug_of_path(r)) or []
            if len(cands) == 1:
                out.append((k, r, cands[0]))
                del new_only[cands[0]]
                by_slug[F.slug_of_path(r)] = []
                continue
        out.append((k, r, None))
    for r, k in sorted(new_only.items()):
        out.append((k, None, r))
    return out


def match_donors(old_root: str, new_root: str, matched: list) -> list:
    """Pair the donor pages only one side has by their spellings: the two
    folds give one donor two display names ('3EYES Construction Ltd' and
    '3Eyes Construction Limited'), so the same page sits at two paths."""
    old_only = [(k, o, n) for k, o, n in matched if k == "donor" and n is None]
    new_only = [(k, o, n) for k, o, n in matched if k == "donor" and o is None]
    if not old_only or not new_only:
        return matched
    index = defaultdict(set)
    for _, _, n in new_only:
        try:
            doc = load(new_root, n)
        except (OSError, ValueError):
            continue
        for sp in (doc.get("identity") or {}).get("spellings") or [doc.get("name")]:
            index[F.spelling_key(sp)].add(n)
    pairs = {}
    taken = set()
    for _, o, _ in old_only:
        try:
            doc = load(old_root, o)
        except (OSError, ValueError):
            continue
        hits = set()
        for sp in (doc.get("identity") or {}).get("spellings") or [doc.get("name")]:
            hits |= index.get(F.spelling_key(sp), set())
        hits -= taken
        if len(hits) == 1:
            n = hits.pop()
            pairs[o] = n
            taken.add(n)
    out = []
    for k, o, n in matched:
        if k == "donor" and o in pairs:
            out.append((k, o, pairs[o]))
        elif k == "donor" and n in taken:
            continue
        else:
            out.append((k, o, n))
    return out


# ── differences ───────────────────────────────────────────────────────────────

def diff_file(kind: str, old_rel: str | None, new_rel: str | None, old_doc, new_doc, added: dict = None) -> list:
    """Every difference between one file on the two sides, as dicts
    {figure, old, new}; a file one side lacks is one difference `file`."""
    if old_doc is None or new_doc is None:
        return [{"figure": "file", "old": "present" if old_doc is not None else ABSENT,
                 "new": "present" if new_doc is not None else ABSENT}]
    out = []
    if old_rel != new_rel:
        out.append({"figure": "path", "old": old_rel, "new": new_rel})
    if kind in ("cite", "board-member"):
        return out
    fo, mo = F.figures(kind, old_rel, "old", old_doc)
    fn, mn = F.figures(kind, new_rel, "new", new_doc)
    if kind == "electorates" and F.slug_of_path(old_rel) == "all":
        fo = {k: v for k, v in fo.items() if not k.startswith(("counts/", "totals/"))}
        fn = {k: v for k, v in fn.items() if not k.startswith(("counts/", "totals/"))}
    secs = {}
    section_kind = (old_rel or new_rel).split("/")[2] if kind == "subject" else kind
    F.sections(old_doc, new_doc, mo | mn, secs, (added or {}).get(section_kind, set()))
    for k, (o, n) in secs.items():
        if o != n:
            out.append({"figure": k, "old": o, "new": n})
    for fid in sorted(set(fo) | set(fn)):
        o, n = fo.get(fid, ABSENT), fn.get(fid, ABSENT)
        if fid.endswith("/listed") and (o is ABSENT or n is ABSENT):
            o, n = (o is True), (n is True)
        if isinstance(o, tuple) and n is ABSENT or isinstance(n, tuple) and o is ABSENT:
            o, n = (o if isinstance(o, tuple) else ()), (n if isinstance(n, tuple) else ())
        if not F.same(fid, o, n):
            d = {"figure": fid, "old": o, "new": n}
            if isinstance(o, tuple) and isinstance(n, tuple):
                co, cn = Counter(o), Counter(n)
                d["old_only"] = sorted((co - cn).elements())
                d["new_only"] = sorted((cn - co).elements())
                d["old"], d["new"] = f"{len(o)} rows", f"{len(n)} rows"
            out.append(d)
    return out


# ── causes ────────────────────────────────────────────────────────────────────
# Each: id, the card in cards/ (its file name without .md), which side is
# right ("frozen": the new side is wrong or short; "new": the frozen site is
# wrong; "neither": a difference of definition, neither side wrong), the
# lane that owns it, and the rule. A rule sees the difference with its kind,
# path, both documents, the other differences of the same file and the
# day's context (see `context`); it returns true, or the id of another
# cause when the difference follows one found elsewhere.

WINDOW_FROM = "2017"
AGGREGATES = ("window", "races", "band", "declared_total", "expenses_total", "by_receiver", "open_year_disclosures")
#: the frozen home lists these totals over its electorates; the rebuilt home the same
ELECTORATE_TOTALS = {"totals/electorate_declared": "declared", "totals/electorate_spend": "spend"}


def _party_of_path(d) -> str:
    doc = d.get("new_doc") or d.get("old_doc") or {}
    return doc.get("party") or doc.get("subject") or ""


def _fig_party(d) -> str:
    parts = d["figure"].split("/")
    return parts[1] if parts and parts[0] in ("party", "registered") and len(parts) > 2 else _party_of_path(d)


def _year(d) -> str:
    for p in reversed(d["figure"].split("/")):
        if p.isdigit() and len(p) == 4:
            return p
    return ""


def _is_not_held(d) -> bool:
    return d["new"] == NOT_HELD


def _party_year_unread(d, ctx) -> bool:
    return (_fig_party(d), _year(d)) in ctx["unread_party_years"]


def _is_section(d) -> bool:
    return d["figure"].startswith("section/")


def _parts_prefix(d) -> tuple | None:
    """Where an aggregate's parts are named by its own path, the prefixes
    they share: a race's total sums that race's candidates; an electorate's
    window total on the home page sums its years; the home page's
    electorate totals sum its electorates; a party's funding sums its card,
    its candidates' donations and its public money; the donor categories
    sum every party card. None where the parts are the page's other
    figures (a party card's window, a donor's receivers)."""
    parts = d["figure"].split("/")
    if d["kind"] == "electorate" and parts[0] == "race" and len(parts) == 3:
        return (f"race/{parts[1]}/candidate/",)
    if d["kind"] == "electorate" and d["figure"] == "money/declared_total":
        return ("race/",)
    if d["kind"] != "home":
        return None
    if parts[0] == "electorates" and len(parts) == 3:
        return (f"electorates/{parts[1]}/{parts[2]}/",)
    if d["figure"] in ELECTORATE_TOTALS:
        return ("electorates/",)
    if parts[0] == "party_funding" and len(parts) > 2:
        return (f"party/{parts[1]}/", f"race_donations/{parts[1]}/", f"race_public/{parts[1]}/")
    if parts[0] == "race_public" and len(parts) > 2:
        return (f"party/{parts[1]}/public_money",)
    if parts[0] == "donor_categories":
        return ("party/",)
    if d["figure"] == "race_spend/total":
        return ("race_spend/",)
    return None


def _aggregate(d, ctx):
    """A window, race, band, receiver or total figure that differs because a
    part of it differs on the same page: it takes that part's cause when
    every differing part has one, else it is uncarded with them. A race's
    parts are its own candidates, an electorate's its own years."""
    parts = d["figure"].split("/")
    last = parts[-1]
    prefix = _parts_prefix(d)
    is_agg = prefix or any(a in parts for a in AGGREGATES) or last in ("total", "rows")
    if not is_agg:
        return False
    if not prefix and _year(d) and last.isdigit() and parts[-2] in ("by_year", "declared", "named", "disclosed", "over_line", "spend"):
        return False
    if prefix:
        want = ELECTORATE_TOTALS.get(d["figure"])
        for x in d["file_diffs"]:
            if x is d or _is_section(x) or not x["figure"].startswith(prefix):
                continue
            if want and x["figure"].split("/")[2] != want:
                continue
            return True
        return False
    party = _fig_party(d)
    for x in d["file_diffs"]:
        if x is d or _is_section(x) or _fig_party(x) != party or x["figure"].endswith("/listed"):
            continue
        xp = x["figure"].split("/")
        if any(a in xp for a in AGGREGATES) or xp[-1] in ("total", "rows"):
            continue
        return True
    return False


RACE_PRIORITY = ("candidate-returns-not-held", "candidacy-missing-on-the-rebuilt-side", "candidate-name-differs",
                 "person-split-by-name-form", "race-2017-against-race-2026", "candidates-from-the-results")


def _follows_race(d, ctx):
    """An electorate's money for one year on the home page, or in a year
    file, follows the causes of that race's candidate figures on the
    electorate page (which the comparison reads first); a 2017 year is the
    frozen site's race outside the window. The all-years file's total
    follows every race of the electorate."""
    parts = d["figure"].split("/")
    if d["kind"] == "home" and parts[0] == "electorates" and len(parts) == 4:
        el, years = F.fold(parts[1]), [parts[3]]
    elif d["kind"] == "electorates" and parts[0] == "electorate" and parts[-1] == "declared_total":
        doc = d.get("new_doc") or d.get("old_doc") or {}
        y = str(doc.get("year") or "")
        el = F.fold(parts[1])
        years = [y] if y.isdigit() else sorted({yy for e, yy in ctx["race_causes"] if e == el})
        if not years:
            return False
    else:
        return False
    if years == ["2017"]:
        return "race-2017-against-race-2026"
    causes = set()
    for y in years:
        causes |= ctx["race_causes"].get((el, y), set())
    if not causes or None in causes:
        return False
    for c in RACE_PRIORITY:
        if c in causes:
            return c
    return sorted(causes)[0]


CANDIDATE_SECTIONS = ("race_donations", "race_spend", "party_transfers")


def _home_candidate_section(d, ctx):
    """The home page's race donations, race spend and party transfers sum
    the candidates' returns over every race: a 2017 year is the frozen
    site's race outside the window; any other year or total follows the
    candidate-returns lane's coverage while a race somewhere is short."""
    parts = d["figure"].split("/")
    if d["kind"] != "home" or parts[0] not in CANDIDATE_SECTIONS or len(parts) < 3:
        return False
    if _year(d) == "2017":
        return "race-2017-against-race-2026"
    if any("candidate-returns-not-held" in v for v in ctx["race_causes"].values()):
        return "candidate-returns-not-held"
    return False


def _frozen_withheld_expenses(d, ctx) -> bool:
    """The frozen page shows no expenses for a candidate though its own
    summary figure (`stated_expenses`) is the one the rebuilt page shows:
    the frozen site withheld a figure it could not reconcile. The person
    page's candidacy follows its electorate page (read first)."""
    if not d["figure"].endswith("/expenses") or d["old"] is not None or not isinstance(d["new"], int):
        return False
    parts = d["figure"].split("/")
    if d["kind"] == "subject" and parts[0] == "candidacy":
        return (parts[1], parts[2], F.person_key((d.get("old_doc") or {}).get("subject"))) in ctx["withheld_expenses"]
    if d["kind"] != "electorate":
        return False
    y, key = parts[1], parts[3]
    for r in (d.get("old_doc") or {}).get("races") or []:
        if str(r.get("year") or str(r.get("election", ""))[-4:]) != y:
            continue
        for c in r.get("candidates") or []:
            if F.person_key(c.get("display") or c.get("candidate")) == key and F.cents(c.get("stated_expenses")) == d["new"]:
                return True
    return False


def _candidacy_verdict(key: str, year: str, el: str, ctx) -> str:
    """Why a frozen candidacy (person key, year, electorate fold) is on no
    matching rebuilt page: 'form' when the rebuilt race has the same
    surname and first given name on another page, 'given' when the same
    surname under another given name, else 'lacks'."""
    people = ctx["new_people"].get((year, el), set())
    if key in people:
        return "form"
    sur = key.split()[0] if key else ""
    if sur and any(k.split()[0] == sur and k != key for k in people):
        return "given"
    return "lacks"


VERDICT_CAUSE = {"form": "person-split-by-name-form", "given": "candidate-name-differs",
                 "lacks": "candidacy-missing-on-the-rebuilt-side"}


def _candidacy_missing(d, ctx):
    """A frozen candidacy a matched rebuilt person page lacks (2020 on): the
    house lane lacks the row, or holds it under another name form or given
    name (house-2's count: of 139, 35 lacked and 104 held otherwise)."""
    if d["kind"] == "subject" and d["figure"].startswith("candidacy/") and d["new"] == ABSENT and _year(d) >= "2020":
        el = d["figure"].split("/")[2]
        if el == "list":
            return False
        return VERDICT_CAUSE[_candidacy_verdict(F.person_key((d.get("old_doc") or {}).get("subject")), _year(d), el, ctx)]
    if d["kind"] == "electorate" and "/candidate/" in d["figure"] and d["new"] == ABSENT and _year(d) >= "2020":
        return "candidacy-missing-on-the-rebuilt-side"
    return False


def _old_person_missing(d, ctx):
    """A frozen person page with an electorate candidacy from 2020 and no
    rebuilt page: the frozen site's second page for one person, a name
    form, another given name, or a row the house lane lacks."""
    if not (d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT):
        return False
    rows = [r for r in _old_person_rows(d) if int(r.get("year") or 0) >= 2020 and r.get("electorate")]
    if not rows:
        return False
    key = F.person_key((d.get("old_doc") or {}).get("subject"))
    if ctx["old_people"][key] > 1:
        return "duplicate-person-page-on-the-frozen-side"
    verdicts = {_candidacy_verdict(key, str(r.get("year")), F.fold(r.get("electorate")), ctx) for r in rows}
    if "lacks" in verdicts:
        return "candidacy-missing-on-the-rebuilt-side"
    if "given" in verdicts:
        return "candidate-name-differs"
    return "person-split-by-name-form"


def _public_money_pair(d) -> tuple:
    """(frozen, rebuilt) public_money of the party a figure belongs to."""
    old_doc, new_doc = d.get("old_doc") or {}, d.get("new_doc") or {}
    if d["kind"] == "home":
        party = _fig_party(d)
        o = next((p.get("public_money") for p in old_doc.get("parties") or [] if p.get("party") == party), None)
        n = next((p.get("public_money") for p in new_doc.get("parties") or [] if p.get("party") == party), None)
        return o or {}, n or {}
    return ((old_doc.get("party_window") or {}).get("headline") or {}).get("public_money") or {}, (new_doc.get("card") or {}).get("public_money") or {}


def _public_money_extra_years(d) -> bool:
    """The rebuilt side has an election year of public money the frozen
    side lacks for this party, and agrees on the years both have."""
    o, n = _public_money_pair(d)
    oy, ny = o.get("by_year") or {}, n.get("by_year") or {}
    if not ny:
        return False
    for y in oy:
        if F.cents(oy[y]) not in (0, None) and F.cents(oy[y]) != F.cents(ny.get(y)):
            return False
    return bool(set(ny) - {y for y in oy if F.cents(oy[y]) not in (0, None)})


def _old_person_rows(d) -> list:
    return ((d.get("old_doc") or {}).get("candidacies") or {}).get("rows") or []


def _same_surname_other_side(d) -> bool:
    """A candidate figure one side lacks, where the other side's race has a
    candidate of the same surname: the given names differ."""
    parts = d["figure"].split("/")
    y, key = parts[1], parts[3]
    sur = key.split()[0]
    other_doc = d.get("new_doc") if d["new"] == ABSENT else d.get("old_doc")
    for r in (other_doc or {}).get("races") or []:
        ry = str(r.get("year") or str(r.get("election", ""))[-4:])
        if ry != y:
            continue
        for c in r.get("candidates") or []:
            k = F.person_key(c.get("display") or c.get("candidate"))
            if k != key and k.split()[0] == sur:
                return True
    return False


def _old_person_empty(d) -> bool:
    doc = d.get("old_doc") or {}
    boards = doc.get("party_boards")
    boards_empty = not boards or (isinstance(boards, dict) and not any(v for v in boards.values() if isinstance(v, list)))
    return not ((doc.get("candidacies") or {}).get("rows")) and not doc.get("positions") and boards_empty \
        and not doc.get("donations_made_total")


def _old_person_years(d) -> list:
    rows = ((d.get("old_doc") or {}).get("candidacies") or {}).get("rows") or []
    return [int(r.get("year") or 0) for r in rows]


def _rows_add_up(d) -> bool:
    """The rebuilt page's rows for the year sum to its own named figure."""
    new_doc = d.get("new_doc") or {}
    y = _year(d)
    named = F.cents(((new_doc.get("card") or {}).get("named_by_year") or {}).get(y))
    total = sum(F.cents(r.get("amount")) or 0 for r in new_doc.get("donations_received") or [] if str(r.get("year")) == y)
    return named is not None and named == total


def _donor_rows(doc, year: str) -> dict:
    return F.donor_rows("old", doc or {}).get(year, {}) if doc else {}


def _classify_row(row, ctx, side: str, mine: str) -> str:
    """Why one party row (year, cents, party) sits on one side only."""
    y, c, party = row
    if y < WINDOW_FROM:
        return "before-the-window"
    if (party, y) in ctx["left_out_names"]:
        return "two-returns-chosen-by-nobody"
    if (party, y) in ctx["unheld_names"]:
        return "return-with-no-reading"
    if (party, y) in ctx["unread_names"]:
        return "part-a-rows-not-read"
    other_all = (ctx["new_rows"] if side == "old" else ctx["old_rows"]).get(row, set())
    if mine in other_all and ctx["new_multi"].get(mine, 0) > 1:
        return "rebuilt-splits-a-donor-across-two-pages"
    other = other_all - {mine}
    if other:
        words = {w for w in mine.split() if len(w) > 2 and w not in STOPWORDS}
        return "fold-differs" if any(words & set(o.split()) for o in other) else "frozen-reattributed-a-vehicle"
    return "rows-only-the-frozen-side-has" if side == "old" else "rows-only-the-rebuilt-side-has"


STOPWORDS = {"the", "and", "ltd", "limited", "trust", "family", "via", "inc", "incorporated", "estate"}
#: party-years the lane holds under a label `keys` resolves to no registration (card three-party-labels-resolve-to-no-registration)
UNRESOLVED_LABELS = {("Te Pāti Māori", "2021"), ("Animal Justice Party Aotearoa New Zealand", "2023"),
                     ("New Zealand Outdoors & Freedom Party", "2023")}
ROW_PRIORITY = ("rebuilt-splits-a-donor-across-two-pages", "two-returns-chosen-by-nobody", "return-with-no-reading",
                "part-a-rows-not-read", "fold-differs",
                "frozen-reattributed-a-vehicle", "before-the-window", "rows-only-the-frozen-side-has",
                "rows-only-the-rebuilt-side-has")


def _side_rows(doc, side: str, year: str = None, source: str = "party") -> list:
    out = []
    for y, by in F.donor_rows(side, doc or {}).items():
        if year and y != year:
            continue
        for c, r in by.get(source, []):
            out.append((y, c, F.fold(r)))
    return out


def _disclosure_verdict(d, ctx):
    """A donor page one side has whose rows are large-donation
    declarations: the frozen site read the donor's name off the scan, the
    lane takes the Commission's table, so the names and the pages differ."""
    doc = d.get("old_doc") or d.get("new_doc") or {}
    side = "old" if d.get("old_doc") else "new"
    rows = _side_rows(doc, side, None, "disclosure")
    if not rows or _side_rows(doc, side):
        return False
    if all(y >= "2023" for y, _, _ in rows):
        return "disclosure-donor-names-read-differently"
    return False


def _rows_verdict(d, ctx, year: str = None):
    """The cause the party rows of a donor page give, both sides: the first
    in priority among the causes of the rows only one side has; False when
    a row has none, or there are none."""
    old_doc, new_doc = d.get("old_doc") or {}, d.get("new_doc") or {}
    old_rows, new_rows = _side_rows(old_doc, "old", year), _side_rows(new_doc, "new", year)
    co, cn = Counter(old_rows), Counter(new_rows)
    causes = set()
    for row in (co - cn).elements():
        causes.add(_classify_row(row, ctx, "old", F.fold(old_doc.get("name"))))
    for row in (cn - co).elements():
        causes.add(_classify_row(row, ctx, "new", F.fold(new_doc.get("name"))))
    if not causes:
        return None
    for c in ROW_PRIORITY:
        if c in causes:
            return c
    return False


def _donor_by_year(d, ctx):
    """A donor page's by-year figure: the rows behind it say why."""
    if d["kind"] != "donor" or not d["figure"].startswith("by_year/"):
        return False
    y = _year(d)
    if y < WINDOW_FROM:
        return "before-the-window"
    verdict = _rows_verdict(d, ctx, y)
    if verdict:
        return verdict
    if verdict is False:
        return False
    old, new = _donor_rows(d.get("old_doc"), y), _donor_rows(d.get("new_doc"), y)
    mine_old, mine_new = F.fold((d.get("old_doc") or {}).get("name")), F.fold((d.get("new_doc") or {}).get("name"))
    for c, r in new.get("candidate", []):
        if ctx["old_rows"].get((y, c, F.fold(r)), set()) - {mine_old}:
            return "fold-differs"
    for c, r in old.get("candidate", []):
        if ctx["new_rows"].get((y, c, F.fold(r)), set()) - {mine_new}:
            return "fold-differs"
    if old.get("candidate"):
        return "candidate-returns-not-held"
    if not old and new.get("disclosure") and y < "2023":
        return "frozen-reads-the-2023-regime-only"
    if old.get("disclosure") or new.get("disclosure"):
        return "disclosure-counted-by-coverage"
    return False


def _donor_file(d, ctx):
    """A donor page only one side has: its history says why."""
    if d["kind"] != "donor" or d["figure"] != "file":
        return False
    doc = d.get("old_doc") or d.get("new_doc") or {}
    rows = doc.get("history") or []
    if not rows:
        return False
    years = [int(h.get("year") or 0) for h in rows]
    srcs = {h.get("source") for h in rows}
    if d["old"] == ABSENT and ctx["new_multi"].get(F.fold(doc.get("name")), 0) > 1:
        return "rebuilt-splits-a-donor-across-two-pages"
    if d["old"] == ABSENT and srcs <= {"candidate"}:
        return "frozen-wrote-no-page-for-a-candidate-donor"
    verdict = _rows_verdict(d, ctx)
    if d["new"] == ABSENT:
        if srcs <= {"candidate"}:
            return "candidate-returns-not-held"
        if max(years) < int(WINDOW_FROM):
            return "before-the-window"
        if verdict == "before-the-window" and "candidate" in srcs:
            return "candidate-returns-not-held"
        return verdict or _disclosure_verdict(d, ctx) or False
    if srcs <= {"disclosure"} and max(years) < 2023:
        return "frozen-reads-the-2023-regime-only"
    if verdict is None and srcs <= {"return"} and all(h.get("counts") is False for h in rows):
        return "two-returns-chosen-by-nobody"
    return verdict or _disclosure_verdict(d, ctx) or False


def _follows_donor(d, ctx):
    """A donor's total on the home page, in the picker or in a party page's
    top ten follows its page."""
    if not ((d["kind"] in ("home", "pickers") and d["figure"].startswith("donors/"))
            or (d["kind"] == "subject" and d["figure"].startswith("top_donors/"))):
        return False
    name = d["figure"].split("/")[1]
    cause = ctx["donor_causes"].get(F.fold(name))
    if d["figure"].endswith("/listed"):
        return cause or ("donor-pickers-cut-after-folding" if d["kind"] == "pickers" else "aggregate-of-a-differing-part")
    return cause or False


def _person_received(d, ctx):
    """A candidate's donations received on the person page come from the
    candidate's return: short on the rebuilt side where the lane has not
    read it (the candidate-returns cause); more is a question."""
    if d["kind"] != "subject" or not d["figure"].startswith("donations_received/"):
        return False
    if d["figure"].endswith("/rows"):
        return "candidate-returns-not-held" if not d.get("new_only") else False
    if isinstance(d["old"], int) and (d["new"] in (None, ABSENT) or isinstance(d["new"], int) and d["new"] < d["old"]):
        return "candidate-returns-not-held"
    return False


CAUSES = [
    # ── follows another figure ──
    dict(id="follows", card=None, right=None, owner=None, why="", match=_donor_by_year),
    dict(id="follows", card=None, right=None, owner=None, why="", match=_donor_file),
    dict(id="follows", card=None, right=None, owner=None, why="", match=_follows_donor),
    dict(id="follows", card=None, right=None, owner=None, why="", match=_follows_race),
    dict(id="follows", card=None, right=None, owner=None, why="", match=_home_candidate_section),
    dict(id="follows", card=None, right=None, owner=None, why="", match=_person_received),
    # ── the new side is short: a lane has not published, or has not read ──
    dict(id="candidate-returns-not-held", card="electorate-money-waits-on-the-candidate-returns-lane", right="frozen",
         owner="candidate-returns",
         why="the frozen site shows candidate donations and expenses from the Commission's candidate-return summaries and the candidates' own returns for every candidate who filed; the candidate-returns lane publishes the returns it has read (385 totals, 713 scans waiting on the page reader, ruling 62), so a candidate figure, an electorate's year and a donor known only from a candidate's return are 'not held' or absent on the new side where the return is not read yet",
         match=lambda d, ctx: (d["kind"] == "home" and d["figure"].startswith("electorates/") and F.not_held((d.get("new_doc") or {}).get("electorates")))
         or (_is_not_held(d) and (d["kind"] in ("electorate", "electorates") or d["figure"].startswith("electorates/") or d["figure"] in ("totals/electorate_spend", "totals/electorate_declared") or d["figure"].endswith("/declared") or d["figure"].endswith("/expenses")))
         or (d["kind"] == "donor" and d["figure"].startswith("by_receiver/") and any(h.get("source") == "candidate" and F.fold(h.get("receiver")) == F.fold(d["figure"].split("/", 1)[1]) for h in (d.get("old_doc") or {}).get("history") or []))
         or (d["kind"] == "subject" and d["figure"] == "donations_made/total" and _is_not_held(d))),
    dict(id="nil-return-is-a-zero", card="a-nil-candidate-return-is-a-zero-on-the-rebuilt-side-and-a-blank-on-the-frozen", right="new",
         owner="comparison",
         why="where a candidate's return declares nil donations the rebuilt page shows $0.00 with the return cited and the frozen page left the cell blank; a nil read from the return is a figure",
         match=lambda d, ctx: d["kind"] in ("electorate", "subject") and d["figure"].endswith("/declared")
         and d["figure"].startswith(("race/", "candidacy/")) and d["old"] is None and d["new"] == 0),
    dict(id="frozen-withheld-expenses", card="the-frozen-site-withheld-a-candidate-s-expenses-it-could-not-reconcile", right="new",
         owner="comparison",
         why="the frozen electorate page shows no expenses for a candidate whose summary figure it holds (Epsom 2023: $20,895.09 in `stated_expenses`, `expenses` empty, because its own reading of the return did not reconcile); the rebuilt page shows the Commission's figure, and the return as the lane read it agrees",
         match=_frozen_withheld_expenses),
    dict(id="cancelled-poll-row-has-no-money", card="the-frozen-person-page-shows-no-money-for-the-cancelled-port-waikato-poll", right="new",
         owner="comparison",
         why="the frozen person page lists Port Waikato 2023 as '(Poll Cancelled)' with no donations and no expenses; the candidate's return for that contest is held and the Commission's table carries its figures, which the rebuilt candidacy shows",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("candidacy/2023/port waikato/")
         and d["figure"].endswith(("/declared", "/expenses")) and d["old"] is None and isinstance(d["new"], int)),
    dict(id="frozen-wrote-no-page-for-a-candidate-donor", card="the-frozen-site-wrote-no-page-for-some-candidate-return-donors", right="new",
         owner="comparison",
         why="a donor whose only rows are in candidates' returns has a rebuilt page citing each return and no frozen page at all, though the frozen site held candidate rows for its other donors; the rebuilt side gives every donor with money a page",
         match=lambda d, ctx: False),
    dict(id="rebuilt-splits-a-donor-across-two-pages", card="the-rebuilt-site-writes-two-donor-pages-for-one-name", right="frozen",
         owner="site",
         why="the rebuilt site has two donor pages under one name and one spelling ('Alan Wilderland' at `alan-wilderland` and at `alan-wilderland-alan-wilderland`), each with part of the history; the frozen site has one page with all of it, so the matched rebuilt page is short the rows its twin carries and the twin has no frozen counterpart",
         match=lambda d, ctx: False),
    dict(id="part-a-rows-not-read", card="part-a-rows-are-read-on-a-minority-of-the-returns-held", right="frozen",
         owner="party-returns",
         why="the party-returns lane has read the Part A (named donor) rows on 38 of the 152 returns held; a party-year whose rows are not read publishes its declared total and no named rows, so every named, over-the-line, placed and per-donor figure for that party-year is short on the new side, and the window and race figures that sum them follow",
         match=lambda d, ctx: _party_year_unread(d, ctx) and "disclosed/" not in d["figure"]),
    dict(id="board-members-not-held", card="party-boards-have-no-lane", right="frozen", owner="site",
         why="the frozen site read party boards and leaders from the parties' own websites and published a board-member page for each; no lane holds them, so the new side has no board-member kind, every party page's board and leaders are 'not held', and a person page's board roles too",
         match=lambda d, ctx: d["kind"] == "board-member" or d["figure"].startswith(("board/", "party_boards/", "leaders/")) and _is_not_held(d)),
    dict(id="expenses-and-member-donations-wait-on-the-links", card="the-links-have-not-read-the-expenses-registers-or-joined-a-member-to-a-donor", right="frozen", owner="links",
         why="the frozen person page shows a member's public expenses from the Parliamentary Service and ministerial releases, and the member's donations to their party under the frozen fold; the rebuilt page says 'not held' for the expenses (pub.names has no row for the expenses registers) and shows no donations made until the links confirm a member to a donor row (site-2's card)",
         match=lambda d, ctx: d["kind"] == "subject" and "/person/" in d["path"] and (d["figure"].startswith("public_expenses/") and _is_not_held(d)
                                                                                     or d["figure"] == "donations_made/total" and isinstance(d["old"], int) and d["old"] > 0 and d["new"] in (0, None, ABSENT))),
    dict(id="party-rules-not-held", card="party-rules-are-not-in-this-lane-s-folders", right="frozen", owner="party-finance",
         why="the frozen party page quotes the party's rules by topic from its constitution; no lane publishes party rules yet (party-finance's card), so the rebuilt page says 'not held'",
         match=lambda d, ctx: d["figure"].startswith("rules/") and _is_not_held(d)),
    dict(id="interests-tree-not-held", card="the-interests-tree-waits-on-the-links-anchoring-interests-to-companies", right="frozen", owner="links",
         why="the frozen person page anchored a member's declared directorships and business interests to companies and drew a tree with its exposure; the rebuilt page says 'not held' because the links do not yet read the interests register against the companies register (the queue asks whether it belongs in this template)",
         match=lambda d, ctx: d["figure"].startswith(("interests_tree/", "exposure/", "industry_exposure/")) and _is_not_held(d)),
    dict(id="interests-counted-differently", card="the-two-readings-of-the-interests-register-count-positions-and-properties-differently", right="neither", owner="interests-expenses",
         why="a member's positions and properties are counted from the Register of Pecuniary Interests by two readings: the frozen site's (one line per anchored body, aliases folded) and the lane's (one line per declaration across the editions in the window, cited to page and line); the counts differ on a third of the member pages and neither is shown wrong without the register open",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] in ("positions/n", "properties/n") and isinstance(d["old"], int) and isinstance(d["new"], int)),
    dict(id="sighted-by-coverage", card="a-disclosure-counts-only-in-a-year-no-return-covers", right="neither", owner="site",
         why="the frozen party page's sighted total counts the declarations it joined under its own rule; the rebuilt page sights a declaration only where a return covers its year and carries the rest as the open year's total (ruling 193), so the two sighted totals differ on every party with declarations",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "disclosures/sighted_total"),
    dict(id="statements-by-period", card="the-party-page-lists-statements-by-period-the-frozen-listed-files", right="new", owner="party-finance",
         why="the frozen party page listed one line per statement file, so a statement held as two documents (Labour's 2024 statement, two files) made two lines; the rebuilt page lists one line per balance date with its documents, and lists every statement the party-finance lane holds, which for most parties is one more than the frozen page had",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "financials/n"),
    dict(id="financial-statements-not-on-party-page", card="financial-statements-are-not-yet-on-the-party-page", right="frozen",
         owner="site",
         why="the party-finance lane publishes financial statements, and the template reads them, but the party page does not show them yet (the site's status names it as next); the frozen page lists each statement",
         match=lambda d, ctx: d["figure"].startswith("financials/") and _is_not_held(d)),
    dict(id="section-not-in-template", card="page-sections-the-template-does-not-carry", right="frozen",
         owner="site",
         why="the frozen home, party and person pages carry sections (party transfers, race spend, party funding, promoter spend, top donors, donor categories, electorate spend, positions, interests, expenses, properties, industry exposure) the Follow the Money template does not yet produce; each is a whole section absent on the new side",
         match=lambda d, ctx: _is_section(d) and d["new"] == ABSENT),
    dict(id="section-only-on-the-new-side", card="sections-the-rebuilt-pages-add", right="neither", owner="site",
         why="the rebuilt pages add sections the frozen pages did not have (loans, disclosures as rows, candidacies with votes, by-race figures); nothing on the frozen side is contradicted",
         match=lambda d, ctx: _is_section(d) and d["old"] == ABSENT),
    # ── the frozen site is wrong, or short ──
    dict(id="frozen-reads-the-2023-regime-only", card="the-frozen-site-shows-no-large-declarations-before-2023", right="new",
         owner="disclosures",
         why="the frozen site's disclosure figures carry the over-$20,000 regime from 2023 only; the disclosures lane holds every regime from 2017 and the new pages show each year, so a disclosed figure for a year before 2023 exists only on the new side",
         match=lambda d, ctx: "disclosed/" in d["figure"] and d["old"] == ABSENT and _year(d) < "2023" or d["kind"] == "home" and d["figure"].startswith("donors_sighted/")),
    dict(id="unresolved-party-labels", card="the-parties-lane-joins-labels-the-frozen-site-left-unfolded", right="new", owner="parties",
         why="the frozen parties page counts 60 returns ($2.57 M) under labels it could not fold to a party; the parties lane joins all but three of them to a registration by its name roster, so the unresolved count and money are smaller on the new side and the money sits under its party",
         match=lambda d, ctx: d["figure"].startswith(("unresolved_returns/", "junk_labels/"))),
    dict(id="votes-from-the-results", card="the-rebuilt-pages-carry-vote-counts-the-frozen-site-never-read", right="new", owner="house",
         why="the frozen site has no vote count for any candidate (the results site refused its reads); the house lane read the official results from the held files, so a candidacy's votes exist only on the new side",
         match=lambda d, ctx: d["figure"].endswith("/votes") and d["old"] in (None, ABSENT) and isinstance(d["new"], int)),
    # ── differences of definition: neither side wrong ──
    dict(id="before-the-window", card="donor-pages-start-at-the-window", right="neither", owner="site",
         why="the frozen donor page lists a donor's whole history back to 1996 and sums it; the rebuilt page starts at the template's window (2017), so a year before 2017 is on the frozen side only and the all-time total differs by those years",
         match=lambda d, ctx: _year(d) and _year(d) < WINDOW_FROM and d["kind"] in ("donor", "subject", "home", "parties", "size-bands")),
    dict(id="disclosure-counted-by-coverage", card="a-disclosure-counts-only-in-a-year-no-return-covers", right="neither", owner="site",
         why="the rebuilt donor page counts a large-donation disclosure only in a year no annual return covers and sights it otherwise (ruling 193: never summed into a return); the frozen page's by-year figures count disclosures differently, so a donor's year with a disclosure differs while the return rows agree",
         match=lambda d, ctx: False),
    dict(id="person-page-key", card="a-person-page-is-keyed-by-the-name-as-the-register-prints-it", right="neither", owner="site",
         why="the frozen site keyed a person page by the name in title case ('Aaron Stallard'); the rebuilt site keys it by the name as the results print it ('Aaron STALLARD'), so the slug is the same and the hash differs; the same person is found at a different file",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "path"),
    dict(id="cite-key", card="a-citation-is-keyed-by-its-document-not-by-an-old-row-id", right="neither", owner="site",
         why="the frozen site keyed each citation file by the old row id (cdon-461330), which changed nightly; the rebuilt site keys it by the register, the document hash and the place on the page, so no citation path is shared and the two sets are compared by count",
         match=lambda d, ctx: d["kind"] == "cite"),
    dict(id="race-2017-against-race-2026", card="the-frozen-site-shows-the-2017-race-the-rebuilt-site-the-2026-one", right="neither", owner="site",
         why="the frozen electorate pages carry the 2017, 2020 and 2023 elections and the rebuilt ones 2020, 2023 and 2026 (ruling 361: a race is every year since the election before it, and the 2026 race is the one running); so 2017's electorates, the 2017 race on each page and the 2017 year file are on the frozen side only, and 2026's on the new side only",
         match=lambda d, ctx: d["kind"] in ("electorate", "electorates") and (_year(d) in ("2017", "2025", "2026") or (d["figure"] == "file" and (d.get("old_doc") or d.get("new_doc") or {}).get("year") in (2017, 2025, 2026)) or (d["kind"] == "electorate" and d["figure"] == "file"))),
    dict(id="candidates-from-the-results", card="an-electorate-page-lists-every-candidate-who-stood", right="neither", owner="site",
         why="the frozen electorate page lists the candidates in the Commission's candidate-return summary (those who filed); the rebuilt page lists every candidate in the official result, so the count and the elected name's form differ while naming the same race",
         match=lambda d, ctx: d["kind"] in ("electorate", "electorates") and (d["figure"].endswith("/candidates") or d["figure"].endswith("/elected") or d["figure"] == "counts/candidates" or d["figure"].endswith("/held") or d["figure"].endswith("/listed"))),
    dict(id="home-lists-every-party-with-money", card="the-rebuilt-home-page-lists-every-party-with-money", right="neither", owner="site",
         why="the frozen home page lists the 17 registered parties; the rebuilt one lists every party with money in the window, registered or not (29), under the same figures; the party pages and the size-bands kind follow the same list",
         match=lambda d, ctx: (d["kind"] in ("home", "size-bands") and d["figure"].startswith("party/") and d["figure"].endswith("/listed") and d["old"] is False)
         or (d["kind"] == "size-bands" and d["figure"] == "file")
         or (d["kind"] in ("size-bands", "subject") and d["figure"] == "file" and d["old"] == ABSENT and "/party/" in (d["path"] + "/") or d["kind"] == "size-bands" and d["figure"] == "file" and d["old"] == ABSENT)),
    dict(id="historic-parties-window", card="historic-parties-are-summed-over-the-window-not-all-time", right="neither", owner="site",
         why="the frozen parties page sums deregistered parties' itemised donations over all time (29 parties, $4.86 M); the rebuilt page sums their declared totals inside the window (14 parties, $2.03 M); the window is the template's, the frozen figure predates it",
         match=lambda d, ctx: d["figure"].startswith("historic/")),
    dict(id="named-in-2026-is-disclosed", card="the-frozen-site-counts-open-year-disclosures-as-named-money", right="neither", owner="site",
         why="the frozen site adds the open year's large-donation disclosures into a party's named and over-the-line window figures and into the 2026 race; the rebuilt site shows them as disclosures beside the returns (ruling 193: never summed into a return), so the named window, the over-the-line window and the 2026 race differ by exactly that money",
         match=lambda d, ctx: _fig_party(d) and (d["figure"].endswith("races/2026/named") or d["figure"].endswith("races/2026/over_line") or d["figure"].endswith("races/2026/total") or d["figure"].endswith("window/named") or d["figure"].endswith("window/over_line") or d["figure"].endswith("window/total"))),
    dict(id="donor-pickers-cut-after-folding", card="the-donor-picker-is-cut-after-folding-and-knows-no-candidate-donors", right="neither", owner="site",
         why="the frozen picker lists 1,345 of 2,152 donors, cut at 1,500 before folding (a hole on record) and drawn from party and candidate returns; the rebuilt picker lists every folded donor with money in the window from party returns and disclosures, so the lists and their counts differ",
         match=lambda d, ctx: d["kind"] == "pickers" and d["figure"].startswith("counts/")),
    dict(id="fold-differs", card="the-two-folds-cut-donor-names-differently", right="new", owner="site",
         why="the frozen site folded a compound or coupled filed name into one donor ('Craig & Shayne Greenlees' with 'Craig Greenlees'; 'Align Farm Investments Limited, BDO Christchurch Limited' into Align Farm); the rebuilt site keeps the donor as the Commission filed it (ruling 253) and folds spelling alone, so the same rows sit under different pages and the by-year figures of both differ",
         match=lambda d, ctx: False),
    dict(id="donor-page-display-name", card="a-donor-page-is-keyed-by-the-fold-s-display-name", right="neither", owner="site",
         why="a folded donor's page is keyed by the display name the fold chose ('3EYES Construction Ltd' on the frozen site, '3Eyes Construction Limited' on the rebuilt one), so one donor's page sits at two paths; the pages are matched by their spellings and compared",
         match=lambda d, ctx: d["kind"] == "donor" and d["figure"] == "path"),
    dict(id="frozen-drops-part-a-rows", card="the-frozen-site-drops-part-a-rows-its-own-total-includes", right="new", owner="comparison",
         why="on a party page the frozen site lists fewer Part A rows for a year than its own named total for that year sums (ACT 2019: one row of $160,000 against a named total of $188,000; the rebuilt page has the second row, $28,000, Gibbs via J B Gibbs Trust); the rebuilt rows add up to the named total, the frozen rows do not",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("rows/") and _year(d) and d.get("old_only") == [] and bool(d.get("new_only")) and _rows_add_up(d)),
    dict(id="frozen-keeps-example-lines", card="the-frozen-site-keeps-a-form-s-example-lines-as-rows", right="new", owner="comparison",
         why="the frozen party page lists a return's printed example lines ('$0.00', 'dd/mm/yyyy') as donation rows of nothing; the rebuilt lane drops them at load (ruling 190), so a year has rows on the frozen side only and all of them are zero",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("rows/") and _year(d) and d.get("old_only") and not d.get("new_only") and all(c == 0 for c in d["old_only"])),
    dict(id="list-only-candidacies-not-shown", card="list-only-candidacies-are-not-on-the-rebuilt-person-page", right="frozen", owner="site",
         why="the frozen person page lists a candidacy on the party list alone (no electorate) with its list place; the rebuilt page lists electorate candidacies only, so a list-only year is on the frozen side only",
         match=lambda d, ctx: d["kind"] == "subject" and "/list/" in d["figure"] and d["new"] == ABSENT),
    dict(id="house-lane-lacks-a-result", card="candidacies-the-frozen-site-shows-and-the-house-lane-lacks", right="frozen", owner="house",
         why="the frozen electorate page names the winner of a race the rebuilt page shows with no result held (Mana and Rongotai 2020, whose result pages the old estate holds only as its job's fetch errors); house-2 reads the two leaders from the status page, and what is left is the race's other candidates, which the lane lacks",
         match=lambda d, ctx: d["kind"] in ("electorate", "electorates") and d["figure"].endswith("/elected") and d["old"] and d["new"] in (None, ABSENT) and _year(d) not in ("2017", "2026")),
    dict(id="frozen-missed-a-winner", card="the-frozen-site-names-no-winner-where-the-results-do", right="new", owner="comparison",
         why="the frozen electorate page shows no winner for a race the official result decides (Nelson 2020 and 2023, Rachel Boyack): its name join failed; the rebuilt page names the winner from the house lane's seats",
         match=lambda d, ctx: d["kind"] in ("electorate", "electorates") and d["figure"].endswith("/elected") and d["new"] and d["old"] in (None, ABSENT) and _year(d) not in ("2017", "2026")),
    dict(id="renamed-party-folds-public-money", card="a-renamed-party-s-public-money-is-summed-under-one-name", right="new", owner="parties",
         why="the parties lane treats a renamed party as one party (the plan's rule) and names it by its registration, so its broadcasting allocation and expenses across both names sum under the current name (Conservative Party NZ carries New Conservative's 2023 money) and the home page's public-money list carries the registered name where the frozen used the Commission's label (Advance NZ, Freedoms NZ, Social Credit); each year's list sums to the allocation on both sides, and the count of parties allocated nothing follows the lane's roster",
         match=lambda d, ctx: "public_money/" in d["figure"] and _public_money_extra_years(d)
         or d["kind"] == "home" and (d["figure"].startswith("race_public/") and ABSENT in (d["old"], d["new"])
                                     or d["figure"].startswith("public_money/") and d["figure"].endswith("_n"))),
    dict(id="expense-returns-reconciled-differently", card="the-two-readings-of-the-party-expense-returns-disagree-on-which-reconcile", right="neither", owner="party-finance",
         why="the home page counts party expense returns whose own total differs from the Commission's figure: the frozen site found three (two in 2020, one in 2023, $118,345.53 between them), the party-finance lane two (2020 only, $98,345.53); the 2023 return's $20,000 is read to reconcile by one reading and not the other",
         match=lambda d, ctx: d["kind"] == "home" and d["figure"].startswith("party_spend/") and "unreconciled" in d["figure"]),
    dict(id="promoter-people-counted-differently", card="the-promoter-register-s-people-are-counted-differently", right="neither", owner="party-finance",
         why="the home page counts the people named on the promoter register: 247 on the frozen site, 303 on the rebuilt one, and the named promoters 7 against 21; the lane reads every registration page held, the frozen site read a list, and neither count has been checked against the register's own page",
         match=lambda d, ctx: d["kind"] == "home" and d["figure"] in ("promoter_spend/people_n", "promoter_spend/named_n")),
    dict(id="unmatched-declarations", card="eighteen-declarations-sit-under-labels-the-parties-lane-could-not-join", right="frozen", owner="parties",
         why="the parties page counts the Commission's declarations whose party label joins no registration: 15 on the frozen site, 18 on the rebuilt one (Advance NZ, DemocracyNZ, Freedoms New Zealand, New Zealand People's Party, NewZeal, ONE Party, Sustainable New Zealand Party), so the lane's join reaches three fewer than the frozen fold did",
         match=lambda d, ctx: d["kind"] == "parties" and d["figure"].startswith("unmatched_disclosures/")),
    dict(id="size-band-placed-money", card="the-two-sides-place-a-return-s-money-into-bands-differently", right="new", owner="comparison",
         why="for New Zealand First 2022 the frozen size-bands page places $317,287.13 against its own declared total of $317,287.83 while saying it reconciles; the rebuilt page places the declared total to the cent, so the frozen figure is 70 cents short of its own total",
         match=lambda d, ctx: d["kind"] == "size-bands" and d["figure"].endswith("/placed") and isinstance(d["old"], int) and isinstance(d["new"], int)),
    dict(id="candidacies-from-the-results", card="an-electorate-page-lists-every-candidate-who-stood", right="neither", owner="site",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("candidacy/") and d["old"] == ABSENT and _year(d) >= "2020"),
    dict(id="candidacies-2017", card="the-frozen-site-shows-the-2017-race-the-rebuilt-site-the-2026-one", right="neither", owner="site",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("candidacy/") and _year(d) == "2017" and d["new"] == ABSENT),
    dict(id="new-person-pages", card="an-electorate-page-lists-every-candidate-who-stood", right="neither", owner="site",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["old"] == ABSENT and "/person/" in d["path"]),
    dict(id="party-not-on-frozen-home", card="the-rebuilt-home-page-lists-every-party-with-money", right="neither", owner="site",
         why="", match=lambda d, ctx: d["kind"] in ("home", "size-bands", "subject") and _fig_party(d) and _fig_party(d) not in ctx["old_parties"] and d["old"] == ABSENT),
    dict(id="nz-first-2019-misread-total", card="nz-first-2019-the-frozen-site-shows-a-misread-total", right="new", owner="party-returns",
         why="the frozen site shows New Zealand First's 2019 declared total as $368,535.17; the return's parts add to $369,535.17, which the lane publishes and the Commission's table carries, so one digit of the frozen figure is misread",
         match=lambda d, ctx: _fig_party(d) == "New Zealand First Party" and _year(d) == "2019"
         and (d["figure"].endswith("/declared/2019") or d["figure"] in ("year/2019/declared_total", "year/2019/placed"))
         and isinstance(d["old"], int) and isinstance(d["new"], int)),
    dict(id="party-label-resolves-to-no-registration", card="three-party-labels-resolve-to-no-registration", right="frozen", owner="keys",
         why="the party-returns lane holds the return (Te Pāti Māori 2021, $13,144.00, equal to the frozen figure) under a label `keys` does not resolve to a registration ('The Maori Party (Te Pati Maori)'), so the rebuilt party-year publishes with no key and the home, party and size-band pages show nothing for it",
         match=lambda d, ctx: (_fig_party(d), _year(d)) in UNRESOLVED_LABELS and (_fig_party(d), _year(d)) in ctx["unheld_party_years"]),
    dict(id="two-returns-chosen-by-nobody", card="a-party-year-with-two-returns-held-is-chosen-by-nobody", right="frozen", owner="site",
         why="", match=lambda d, ctx: (_fig_party(d), _year(d)) in ctx["left_out_party_years"]),
    dict(id="return-with-no-reading", card="party-years-the-frozen-site-totals-and-the-lane-holds-no-total-for", right="frozen", owner="party-returns",
         why="", match=lambda d, ctx: (_fig_party(d), _year(d)) in ctx["unheld_party_years"]),
    dict(id="rebuilt-holds-more-returns", card="the-rebuilt-lane-holds-declared-totals-the-frozen-site-lacked", right="new", owner="party-returns",
         why="the frozen site held a parsed return total for under half the party-years since 2019 (a hole on record); the party-returns lane reads every return held, so a declared total, its rows and its size-band year exist on the rebuilt side only for the party-years the frozen site never parsed",
         match=lambda d, ctx: d["old"] in (ABSENT, None) and d["new"] not in (ABSENT, None, NOT_HELD) and _year(d) >= WINDOW_FROM and (("/declared/" in d["figure"]) or d["figure"].startswith("rows/") or (d["kind"] == "size-bands" and d["figure"].startswith("year/")) or (d["kind"] == "subject" and d["figure"].startswith("card/named/")) or ("/named/" in d["figure"]))),
    dict(id="rows-only-the-frozen-side-has", card="part-a-rows-the-frozen-site-has-and-no-rebuilt-page-carries", right="frozen", owner="party-returns",
         why="in a party-year both sides read, the frozen donor page carries a Part A row that no rebuilt donor page has under any name (Kelly, Andrew: $25,000 to National in 2023); the rebuilt reading of that return is short a row, or the frozen row was a parsing artefact: each needs the return opened",
         match=lambda d, ctx: False),
    dict(id="frozen-reattributed-a-vehicle", card="the-frozen-site-moved-a-vehicle-s-donation-to-its-owner", right="new", owner="site",
         why="the frozen site's vehicle fold put a company's or trust's donation on its owner's page (Rank Group's money on Graeme Hart's); ruling 253 withdrew that: a donation is from the donor the Commission's return names, so the rebuilt site keeps the row under the filed name and the two pages' years differ by it",
         match=lambda d, ctx: False),
    dict(id="disclosure-donor-names-read-differently", card="the-frozen-site-read-declaration-donor-names-off-the-scans", right="new", owner="disclosures",
         why="the frozen site took a large declaration's donor name from its own OCR of the scan and some are mangled (five Toorak Chambers pages, 'Charles Dave' with no party); the disclosures lane takes the name from the Commission's table, so a declaration-only donor page sits under another name on each side",
         match=lambda d, ctx: False),
    dict(id="national-2023-counted-twice", card="national-2023-the-frozen-site-counts-one-declaration-twice", right="new", owner="disclosures",
         why="", match=lambda d, ctx: "disclosed/2023" in d["figure"] and _fig_party(d) == "The New Zealand National Party"),
    dict(id="declaration-dated-by-the-day-received", card="two-declarations-sit-in-2023-on-the-frozen-site-and-2024-on-the-rebuilt-one", right="frozen", owner="site",
         why="New Zealand First: the frozen site shows $888,141.69 of large donations in 2023 and nothing in 2024, the rebuilt site $831,141.69 and $57,000; Labour: $744,672.35 against $724,304.35 and $20,368. In each case one declaration is bucketed by the day the Commission received it on the frozen side and by the day the party received the gift on the rebuilt one, the lane's rule",
         match=lambda d, ctx: "disclosed/" in d["figure"] and _fig_party(d) in ("New Zealand First Party", "New Zealand Labour Party") and _year(d) in ("2023", "2024")),
    dict(id="candidate-name-differs", card="a-candidate-s-given-name-differs-between-the-return-summary-and-the-results", right="new", owner="house",
         why="in Napier 2020 the frozen page (from the Commission's candidate-return summary) lists Ian Gaskin and the rebuilt page (from the official results) Camden Gaskin; the results are the record of who stood, so the rebuilt name is taken as right and the summary's name is for the lane to look at; a frozen person page's candidacy, or whole page, that the rebuilt race holds under another given name (Dave/David Kennedy) is the same cause",
         match=lambda d, ctx: d["kind"] == "electorate" and "/candidate/" in d["figure"] and _year(d) >= "2020" and _same_surname_other_side(d)),
    dict(id="unregistered-label-not-on-candidacy", card="an-unregistered-party-label-is-not-on-the-rebuilt-candidacy", right="frozen", owner="house",
         why="the frozen person page shows a candidacy's party as filed, 'Independent' or an unregistered label ('Future Youth Party'); the rebuilt candidacy names the registered party only and shows nothing for the rest",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"].endswith("/party") and d["figure"].startswith("candidacy/") and d["new"] is None and d["old"] not in (None, ABSENT)),
    dict(id="candidacy-missing-on-the-rebuilt-side", card="candidacies-the-frozen-site-shows-and-the-house-lane-lacks", right="frozen", owner="house",
         why="the frozen person page lists a candidacy (an electorate contest of 2020, 2023 or 2026) that no rebuilt person page carries under any name form, or an electorate page lists a candidate the rebuilt race lacks; the house lane has no row for it (Mana and Rongotai 2020). A candidacy the rebuilt race holds under the same surname and first given name on another page, or under another given name, goes to those causes' cards instead",
         match=_candidacy_missing),
    dict(id="old-person-list-only-or-early", card="list-only-candidacies-are-not-on-the-rebuilt-person-page", right="frozen", owner="site",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT and _old_person_rows(d) and all(int(r.get("year") or 0) < 2020 or r.get("electorate") is None for r in _old_person_rows(d))),
    dict(id="old-person-no-result", card="candidacies-the-frozen-site-shows-and-the-house-lane-lacks", right="frozen", owner="house",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT and _old_person_rows(d) and all((str(r.get("year")), F.fold(r.get("electorate"))) in ctx["no_result"] for r in _old_person_rows(d) if int(r.get("year") or 0) >= 2020 and r.get("electorate"))),
    dict(id="old-person-candidacy-missing", card="candidacies-the-frozen-site-shows-and-the-house-lane-lacks", right="frozen", owner="house",
         why="", match=_old_person_missing),
    dict(id="frozen-person-page-with-nothing-on-it", card="the-frozen-site-has-person-pages-with-nothing-on-them", right="new", owner="comparison",
         why="a frozen person page with no candidacy, no position, no board role and no donation made; the rebuilt site makes no page for a person it holds nothing about",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT and _old_person_empty(d)),
    dict(id="rows-only-the-rebuilt-side-has", card="part-a-rows-only-the-rebuilt-side-carries", right="new", owner="comparison",
         why="in a party-year both sides read, a rebuilt donor page carries a Part A row no frozen donor page has under any name; the rebuilt rows reconcile to the return's Part A total where the frozen rows do not (the ACT 2019 case), so the frozen reading dropped them",
         match=lambda d, ctx: False),
    dict(id="duplicate-person-page-on-the-frozen-side", card="the-frozen-site-has-two-pages-for-one-person", right="new", owner="comparison",
         why="the frozen site keyed person pages by the name as each source wrote it, so one person has two pages ('Adrian Rurawhe' and 'Adrian Paki Rurawhe'; 'Carmel Sepuloni' and 'Carmel Jean Sepuloni'); the rebuilt site has one page per name key, so the second frozen page has no counterpart",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT and ctx["old_people"][F.person_key((d.get("old_doc") or {}).get("subject"))] > 1),
    dict(id="person-split-by-name-form", card="the-rebuilt-site-splits-one-candidate-across-two-name-forms", right="frozen", owner="house",
         why="the results print a candidate under different name forms in different elections ('Anthony Vickers Odering' in 2020, 'Anthony Odering' in 2023); the house lane keys a person by the printed name, so the rebuilt site has two pages where the frozen site joined them; a candidacy is then on the frozen page and absent from the matching rebuilt page",
         match=lambda d, ctx: d["kind"] == "subject" and d["figure"].startswith("candidacy/") and d["new"] == ABSENT and _year(d) >= "2020" and F.person_key((d.get("old_doc") or {}).get("subject")) in ctx["new_people"].get((_year(d), d["figure"].split("/")[2]), set())),
    dict(id="house-lane-lacks-a-result", card="candidacies-the-frozen-site-shows-and-the-house-lane-lacks", right="frozen", owner="house",
         why="", match=lambda d, ctx: (d["kind"] == "subject" and d["figure"].startswith("candidacy/") and d["new"] == ABSENT and (_year(d), d["figure"].split("/")[2]) in ctx["no_result"])
         or (d["kind"] == "electorate" and d["new"] == ABSENT and (_year(d), F.fold((d.get("old_doc") or {}).get("electorate"))) in ctx["no_result"])),
    dict(id="frozen-person-page-before-the-window", card="the-frozen-site-shows-the-2017-race-the-rebuilt-site-the-2026-one", right="neither", owner="site",
         why="", match=lambda d, ctx: d["kind"] == "subject" and d["figure"] == "file" and d["new"] == ABSENT and _old_person_years(d) and max(_old_person_years(d)) < 2020),
    dict(id="sitting-members-roster", card="who-left-the-house-mid-term-is-not-in-the-results-files", right="frozen", owner="house",
         why="the frozen picker lists the 54th Parliament's members as parliament.nz rosters them, departures removed and list replacements added from the Gazette; the house lane's members carry no end date and no list replacement, so the rebuilt picker lists members who have left (Grant Robertson, Kelvin Davis, Efeso Collins) and lacks those who came in off the list (Camilla Belich, Glen Bennett, Nancy Lu)",
         match=lambda d, ctx: d["kind"] == "pickers" and d["figure"].startswith("mps/") or d["figure"].endswith("/seats") and d["kind"] in ("home", "subject") or d["kind"] == "subject" and d["figure"] == "mps/n" or d["kind"] == "parties" and d["figure"] == "unaffiliated_sitting/n"),
    dict(id="aggregate-of-a-differing-part", card="an-aggregate-follows-its-parts", right="neither", owner="comparison",
         why="a window, race, band, receiver, total or ranking figure differs because one of the figures it sums or orders differs on the same page for a cause of its own; it clears when they do and is not counted again",
         match=_aggregate),
]
CAUSE_IDS = {c["id"] for c in CAUSES if c["card"]}


def context(new_root: str, new_files: dict) -> dict:
    """What the rules need from the whole new version: the party-years whose
    Part A rows are not read (declared total held, named rows none)."""
    unread = set()
    for rel, k in new_files.items():
        if k == "subject" and rel.split("/")[2] == "party":
            try:
                card = load(new_root, rel).get("card") or {}
            except (OSError, ValueError):
                continue
            for y, v in (card.get("declared_by_year") or {}).items():
                if v is not None and (card.get("named_by_year") or {}).get(y) is None:
                    unread.add((card.get("party"), str(y)))
    left_out, unheld = set(), set()
    try:
        for p in F.parties_by_name(load(new_root, "data/home.json").get("parties")):
            for y in (p.get("window") or {}).get("years_left_out") or []:
                left_out.add((p.get("party"), str(y)))
            for y, v in (p.get("declared_by_year") or {}).items():
                if v is None and (p.get("party"), str(y)) not in left_out and str(y) < "2026":
                    unheld.add((p.get("party"), str(y)))
    except (OSError, ValueError):
        pass
    new_people, no_result = defaultdict(set), set()
    for rel, k in new_files.items():
        if k == "subject" and "/person/" in rel:
            try:
                doc = load(new_root, rel)
            except (OSError, ValueError):
                continue
            pk = F.person_key(doc.get("subject"))
            for c in doc.get("candidacies") or []:
                el = str(c.get("election") or "")
                m = __import__("re").search(r"(20\d\d|19\d\d)", el)
                new_people[(m.group(1) if m else el, F.fold(str(c.get("electorate") or "").split("/")[-1]))].add(pk)
        elif k == "electorate":
            try:
                doc = load(new_root, rel)
            except (OSError, ValueError):
                continue
            for r in doc.get("races") or []:
                if r.get("result_held") is False:
                    no_result.add((str(r.get("year") or str(r.get("election", ""))[-4:]), F.fold(doc.get("electorate"))))
    rows_index, new_multi = defaultdict(set), Counter()
    for rel, k in new_files.items():
        if k == "donor":
            try:
                doc = load(new_root, rel)
            except (OSError, ValueError):
                continue
            new_multi[F.fold(doc.get("name"))] += 1
            for h in doc.get("history") or []:
                if h.get("source") in ("return", "disclosure", "candidate"):
                    receiver = h.get("receiver") if h.get("source") == "candidate" else h.get("party_name")
                    rows_index[(str(h.get("year")), F.cents(h.get("amount")), F.fold(receiver))].add(F.fold(doc.get("name")))
    return {"unread_party_years": unread, "donor_causes": {}, "new_rows": rows_index, "old_parties": set(),
            "new_multi": new_multi, "race_causes": {}, "withheld_expenses": set(),
            "left_out_party_years": left_out, "unheld_party_years": unheld, "new_people": new_people,
            "no_result": no_result, "old_people": Counter(), "old_rows": defaultdict(set),
            "unread_names": {(F.fold(p), y) for p, y in unread}, "left_out_names": {(F.fold(p), y) for p, y in left_out},
            "unheld_names": {(F.fold(p), y) for p, y in unheld}}


def old_parties(old_root: str) -> set:
    try:
        return {p.get("party") for p in load(old_root, "data/home.json").get("parties") or []}
    except (OSError, ValueError):
        return set()


def old_context(old_root: str, old_files: dict, ctx: dict) -> None:
    """What the rules need from the frozen version: how many person pages
    share one person key, and every party row by year, amount and party."""
    for rel, k in old_files.items():
        if k == "subject" and "/person/" in rel:
            try:
                ctx["old_people"][F.person_key(load(old_root, rel).get("subject"))] += 1
            except (OSError, ValueError):
                continue
        elif k == "donor":
            try:
                doc = load(old_root, rel)
            except (OSError, ValueError):
                continue
            for h in doc.get("history") or []:
                if h.get("source") in ("party", "disclosure", "candidate"):
                    ctx["old_rows"][(str(h.get("year")), F.cents(h.get("amount")), F.fold(h.get("receiver")))].add(F.fold(doc.get("name")))


def sections_added(template: str = None) -> dict:
    """{kind: keys} the template declares as the rebuilt pages' own
    (`sections_added` in ftm.json, read only); person and party pages are
    the subject kind's two halves."""
    try:
        with open(template or TEMPLATE, encoding="utf-8") as f:
            added = json.load(f).get("sections_added") or {}
    except (OSError, ValueError):
        return {}
    return {k: set(v) for k, v in added.items() if isinstance(v, list)}


#: words that mark a residence inside a filed name (hard limits 11 and 15):
#: a name segment carrying one is withheld from everything this module
#: records, since a figure id or a file name is built from published names
RESIDENCE_WORDS = ("retirement village", "rest home", "resthome", "lifecare", "care home", "retirement")
WITHHELD = "[name withheld: residence fragment]"


def withhold(text):
    """A figure id, path or value with any name segment that carries a
    residence word replaced by WITHHELD; other values pass through."""
    if not isinstance(text, str):
        return text
    low = text.lower()
    if not any(w in low for w in RESIDENCE_WORDS):
        return text
    out = []
    for seg in text.split("/"):
        out.append(WITHHELD if any(w in seg.lower() for w in RESIDENCE_WORDS) else seg)
    return "/".join(out)


def card_state(card: str, cards_dir: str = None) -> str | None:
    """The `state:` line of a card, or None when there is no such card."""
    try:
        with open(os.path.join(cards_dir or CARDS, card + ".md"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("state:"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        return None
    return "open"


def assign(d: dict, ctx: dict, causes=None) -> str | None:
    """The first rule that recognises the difference names its cause; a rule
    may name another cause's id instead (the difference follows one)."""
    causes = causes or CAUSES
    ids = {c["id"] for c in causes if c.get("card")}
    for c in causes:
        try:
            r = c["match"](d, ctx)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        if isinstance(r, str) and r in ids:
            return r
        if r is True:
            return c["id"] if c.get("card") else None
    return None


# ── a day ─────────────────────────────────────────────────────────────────────

def compare(old_root: str, new_root: str, causes=None, cards_dir: str = None) -> dict:
    """The whole comparison of two version folders, grouped by cause."""
    old_files, new_files = files_of(old_root), files_of(new_root)
    ctx = context(new_root, new_files)
    ctx["old_parties"] = old_parties(old_root)
    old_context(old_root, old_files, ctx)
    causes = causes or CAUSES
    by_id = {c["id"]: c for c in causes}
    kinds = {k: {"old": 0, "new": 0, "matched": 0, "figures": 0, "differences": 0} for k in KINDS}
    for k in old_files.values():
        kinds[k]["old"] += 1
    for k in new_files.values():
        kinds[k]["new"] += 1
    grouped = defaultdict(lambda: {"n": 0, "kinds": Counter(), "sample": []})
    uncarded, records = [], []
    total = 0
    order = {"donor": 0}
    added = sections_added()
    matched = match_donors(old_root, new_root, match_files(old_files, new_files))
    matched = sorted(matched, key=lambda m: (order.get(m[0], 1), m[1] or m[2]))
    for kind, orel, nrel in matched:
        odoc = load(old_root, orel) if orel else None
        ndoc = load(new_root, nrel) if nrel else None
        if orel and nrel:
            kinds[kind]["matched"] += 1
        diffs = diff_file(kind, orel, nrel, odoc, ndoc, added)
        if odoc is not None and ndoc is not None and kind not in ("cite", "board-member"):
            fo, _ = F.figures(kind, orel, "old", odoc)
            kinds[kind]["figures"] += len(fo)
        for d in diffs:
            d.update(kind=kind, path=orel or nrel, old_doc=odoc, new_doc=ndoc, file_diffs=diffs)
        assigned = []
        for d in diffs:
            cid = assign(d, ctx, causes)
            if cid and card_state(by_id[cid]["card"], cards_dir) in (None, "dropped"):
                cid = None
            assigned.append(cid)
            rec = {"kind": kind, "path": withhold(d["path"]), "figure": withhold(d["figure"]),
                   "old": withhold(F.show(d["figure"], d["old"])), "new": withhold(F.show(d["figure"], d["new"]))}
            for extra in ("old_only", "new_only"):
                if d.get(extra):
                    rec[extra] = d[extra][:12]
            total += 1
            kinds[kind]["differences"] += 1
            records.append(dict(rec, cause=cid or "uncarded"))
            g = grouped[cid or "uncarded"]
            g["n"] += 1
            g["kinds"][kind] += 1
            if len(g["sample"]) < SAMPLE_PER_CAUSE:
                g["sample"].append(rec)
            if not cid:
                uncarded.append(rec)
        if kind == "donor":
            name = F.fold((odoc or ndoc or {}).get("name"))
            ids = [cid for d, cid in zip(diffs, assigned) if not d["figure"].startswith("section/")]
            ctx["donor_causes"][name] = None if (not ids or None in ids) else ids[0]
        elif kind == "electorate":
            el = F.fold((odoc or ndoc or {}).get("electorate"))
            for d, cid in zip(diffs, assigned):
                parts = d["figure"].split("/")
                if parts[0] == "race" and len(parts) > 3 and parts[2] == "candidate":
                    ctx["race_causes"].setdefault((el, parts[1]), set()).add(cid)
                    if cid == "frozen-withheld-expenses":
                        ctx["withheld_expenses"].add((parts[1], el, parts[3]))
    by_cause = {}
    for cid, g in sorted(grouped.items(), key=lambda kv: -kv[1]["n"]):
        c = by_id.get(cid)
        by_cause[cid] = {"n": g["n"], "kinds": dict(g["kinds"]), "sample": g["sample"],
                         "card": c["card"] if c else None, "right": c["right"] if c else None,
                         "owner": c["owner"] if c else None}
    new_wrong = sum(v["n"] for k, v in by_cause.items() if v["right"] == "frozen")
    n_uncarded = by_cause.get("uncarded", {}).get("n", 0)
    return {"frozen_dir": old_root, "new_dir": new_root, "kinds": kinds, "differences": total,
            "by_cause": by_cause, "uncarded": n_uncarded, "new_wrong": new_wrong,
            "clean": n_uncarded == 0 and new_wrong == 0,
            "explained": n_uncarded == 0,
            "unread_party_years": len(ctx["unread_party_years"]), "records": records}


def run(frozen: str = None, new: str = None, *, state_dir: str = None, site: str = None,
        versions: str = None, releases: str = None, now: dt.datetime = None, cards_dir: str = None) -> dict:
    """Compare today's pair (or the named one), write the day file and the
    ledger line, and return the day's result."""
    now = now or dt.datetime.now().astimezone()
    state_dir = state_dir or STATE_DIR
    versions = versions or FROZEN_VERSIONS
    p = pair(frozen, site, releases, versions)
    frozen = p["frozen"]
    new = new or p["new"]
    day = {"ran_at": now.isoformat(timespec="seconds"), "frozen": frozen, "new": new, "newest_new": p["newest_new"][0]}
    if not frozen:
        day.update(ok=False, note="no published frozen version found")
    elif not new:
        day.update(ok=False, note=f"no rebuilt version built from listing {frozen} (newest rebuilt: "
                                  f"{p['newest_new'][0]} from listing {p['newest_new'][1]})")
    else:
        r = compare(os.path.join(versions, frozen), os.path.join((site or NEW_SITE), "v", new), cards_dir=cards_dir)
        day.update(ok=True, **r)
    write_day(day, state_dir)
    return day


def write_day(day: dict, state_dir: str) -> None:
    """The day record (grouped, with samples) and beside it every
    difference with its cause, one JSON line each (`<version>.diffs.jsonl`),
    so a card's full list is on disk; figures only, never a page's text."""
    os.makedirs(os.path.join(state_dir, "days"), exist_ok=True)
    name = (day.get("frozen") or "none").replace("/", "_")
    path = os.path.join(state_dir, "days", f"{name}.json")
    records = day.pop("records", None)
    if records is not None:
        with open(path[:-5] + ".diffs.jsonl.tmp", "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        os.replace(path[:-5] + ".diffs.jsonl.tmp", path[:-5] + ".diffs.jsonl")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(day, f, ensure_ascii=False, indent=1, default=str)
    os.replace(path + ".tmp", path)
    line = {"ran_at": day["ran_at"], "frozen": day.get("frozen"), "new": day.get("new"), "ok": day.get("ok"),
            "differences": day.get("differences"), "uncarded": day.get("uncarded"), "new_wrong": day.get("new_wrong"),
            "clean": bool(day.get("clean")), "explained": bool(day.get("explained")),
            "by_cause": {k: v["n"] for k, v in (day.get("by_cause") or {}).items()}, "note": day.get("note")}
    with open(os.path.join(state_dir, "ledger.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")


def ledger(state_dir: str = None) -> list:
    """The ledger, one line per frozen version (the last run of each wins),
    oldest first."""
    path = os.path.join(state_dir or STATE_DIR, "ledger.jsonl")
    last = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                last[row.get("frozen") or row["ran_at"]] = row
    except OSError:
        return []
    return [last[k] for k in sorted(last)]


def streak(rows: list) -> int:
    """Clean days in a row at the end of the ledger."""
    n = 0
    for row in reversed(rows):
        if row.get("clean"):
            n += 1
        else:
            break
    return n


# ── the board item ────────────────────────────────────────────────────────────

def check(*, now: dt.datetime = None, state_dir: str = None) -> dict:
    now = now or dt.datetime.now().astimezone()
    rows = ledger(state_dir)
    items = []
    if not rows:
        items.append({"name": "day", "ok": False, "detail": "the comparison has never run"})
        return {"check": NAME, "ok": False, "items": items, "alarms": []}
    last = rows[-1]
    try:
        ran = dt.datetime.fromisoformat(last["ran_at"])
        if ran.tzinfo is None:
            ran = ran.replace(tzinfo=now.tzinfo)
        age = (now - ran).total_seconds() / 3600
    except (ValueError, KeyError):
        age = float("inf")
    if age > WINDOW_HOURS:
        items.append({"name": "day", "ok": False, "detail": f"last ran {age:.0f} h ago (window {WINDOW_HOURS} h)"})
    elif not last.get("ok"):
        items.append({"name": "day", "ok": False, "detail": last.get("note") or "the run failed"})
    else:
        by = last.get("by_cause") or {}
        causes = ", ".join(f"{k} {v}" for k, v in list(by.items())[:6])
        items.append({"name": "day", "ok": last.get("uncarded", 1) == 0,
                      "detail": f"{last['frozen']} vs {last['new']}: {last.get('differences')} difference(s), "
                                f"{last.get('uncarded')} uncarded, {last.get('new_wrong')} under a card saying the new side is wrong"
                                f"{'; ' + causes if causes else ''}"})
    s = streak(rows)
    items.append({"name": "clean-days", "ok": True,
                  "detail": f"{s} clean day(s) in a row of {PASS_DAYS} needed; {sum(1 for r in rows if r.get('explained'))} of {len(rows)} day(s) fully explained"})
    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": []}


# ── printing ──────────────────────────────────────────────────────────────────

def render(day: dict, full: bool = False) -> str:
    if not day.get("ok"):
        return f"{day.get('frozen')} vs {day.get('new')}: {day.get('note')}"
    lines = [f"frozen {day['frozen']} vs rebuilt {day['new']}: {day['differences']} difference(s); "
             f"{day['uncarded']} uncarded; {day['new_wrong']} under a card saying the new side is wrong; "
             f"{'CLEAN' if day['clean'] else 'not clean'}",
             f"{'kind':<14}{'frozen':>8}{'new':>8}{'matched':>9}{'figures':>9}{'diffs':>8}"]
    for k, v in day["kinds"].items():
        lines.append(f"{k:<14}{v['old']:>8}{v['new']:>8}{v['matched']:>9}{v['figures']:>9}{v['differences']:>8}")
    lines.append("")
    for cid, c in day["by_cause"].items():
        lines.append(f"{c['n']:>7}  {cid:<40} right: {c['right'] or '-':<8} owner: {c['owner'] or '-':<18} "
                     f"{', '.join(f'{k} {n}' for k, n in c['kinds'].items())}")
        for s in c["sample"][: (12 if full else 3)]:
            extra = ""
            if s.get("old_only") or s.get("new_only"):
                extra = f"  frozen-only {s.get('old_only', [])[:6]} new-only {s.get('new_only', [])[:6]}"
            lines.append(f"           {s['kind']} {s['path'].split('/')[-1]} {s['figure']}: {s['old']} -> {s['new']}{extra}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="the comparison with the frozen site (plan 4.5)")
    ap.add_argument("cmd", choices=["run", "show", "causes"])
    ap.add_argument("--frozen")
    ap.add_argument("--new")
    ap.add_argument("--full", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "causes":
        for c in CAUSES:
            if not c.get("card"):
                continue
            print(f"{c['id']:<40} right: {c['right']:<8} owner: {c['owner']:<18} card: {c['card']} "
                  f"[{card_state(c['card']) or 'NO CARD'}]")
        return 0
    if a.cmd == "show":
        rows = ledger()
        if not rows:
            print("the comparison has never run")
            return 1
        name = rows[-1]["frozen"].replace("/", "_")
        with open(os.path.join(STATE_DIR, "days", f"{name}.json"), encoding="utf-8") as f:
            print(render(json.load(f), full=a.full))
        print(f"\n{streak(rows)} clean day(s) in a row; {len(rows)} day(s) in the ledger")
        return 0
    day = run(a.frozen, a.new)
    print(render(day, full=a.full))
    return 0 if day.get("ok") and day.get("explained") else 1


if __name__ == "__main__":
    sys.exit(main())
