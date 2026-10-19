"""The reading: the held files → this lane's rows, each stamped with its
reader, its document's profile and version, and read from text. Nothing
here calls a model, so the fast tier runs the same code.

  elections     every general election and by-election the results index lists, and 2026 from its nominations
  electorates   per election: the Commission's name, joined to Stats NZ's where its boundary set is held
  candidates    per election: one row per candidacy (an electorate, a list place, or both), votes where counted
  members       who the official result returned, and the by-election winners: a window per seat
  figures       the Commission's own printed figures the outside check compares with (contract: the lane)
  files         every file taken and what was done with it
  set_aside     the catch log: one line for every item that did not become a row

Items in equal items out plus items set aside: every file is read, held
and not read, or a catch-log line; every row on a read page is a row or a
catch-log line; a page that fails its own printed totals publishes
nothing.

Keys are the Commission's own identities, not the bytes: an election's
year and kind, an electorate's name, a candidate's name in it. A results
page is re-rendered with a fresh script token at every capture, so its
hash changes while its rows do not; the hash and the place are the
citation, carried on every row (contract: the register row, 1 and 2).

    read(docs)    docs: [(folder, sha256, name, captured at, bytes)] → Result
"""
import datetime as dt
import os
import re
from dataclasses import dataclass, field

from keys import names as K
from keys import parties as KP
from support import profiles
from registers.house import electorates as EL
from registers.house import elections as EX
from registers.house import nominations as NO
from registers.house import recognise
from registers.house import results as RS

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = "registers.house 1"
NEXT_GENERAL = "ge-2026"


@dataclass
class Result:
    elections: list = field(default_factory=list)
    electorates: list = field(default_factory=list)
    candidates: list = field(default_factory=list)
    members: list = field(default_factory=list)
    figures: list = field(default_factory=list)
    files: list = field(default_factory=list)          # (sha256, name, profile or kind, status)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request house-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def slug(s: str) -> str:
    return EX.slug(s or "")


def _year(name: str):
    m = re.search(r"electionresults[-_](\d{4})", name)
    return m.group(1) if m else None


def _party(label):
    if not label:
        return None, None
    reg, basis = KP.party_name(label)
    return reg, basis


class _Reader:
    def __init__(self, loaded_at):
        self.out = Result()
        self.loaded_at = loaded_at
        self.keys = set()

    def stamp(self, sha, slug_, place, page=1):
        return {"document": sha, "page": page, "place": place, "reader": READER, "profile": slug_,
                "profile_version": profile_version(slug_), "read_from": "text", "loaded_at": self.loaded_at}

    def add(self, table, row):
        k = row["key"]
        if k in self.keys:
            self.out.set_aside.append((k, table, f"a second row under the key {k}: {row['place']} (the first is kept)"))
            return False
        self.keys.add(k)
        getattr(self.out, table).append(row)
        return True

    def aside(self, item, stage, why):
        self.out.set_aside.append((item, stage, why))


def read(docs: list, loaded_at: str = None) -> Result:
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    r = _Reader(loaded_at)
    out = r.out
    by_profile = {}
    for folder, sha, name, captured, data in docs:
        what, why = recognise.recognise(data, name)
        if what in recognise.PROFILES:
            by_profile.setdefault(what, []).append((folder, sha, name, captured, data))
            out.files.append((sha, f"{folder}/{name}", what, "read"))
        elif what in recognise.NOT_READ:
            out.files.append((sha, f"{folder}/{name}", what, "held, not read"))
        else:
            out.files.append((sha, f"{folder}/{name}", what or "not recognised", "failed read" if what else "not recognised"))
            r.aside(f"{folder}/{name}", "capture", why)

    elections = _elections(r, by_profile)
    _results(r, by_profile, elections)
    _by_elections(r, by_profile, elections)
    _nominations(r, by_profile)
    _windows(r, elections)
    out.counts = {"files": len(out.files), "elections": len(out.elections), "electorates": len(out.electorates),
                  "candidates": len(out.candidates), "members": len(out.members), "figures": len(out.figures),
                  "set_aside": len(out.set_aside)}
    return out


# --- the elections ------------------------------------------------------------

def _elections(r, by_profile) -> dict:
    got = {}
    for folder, sha, name, captured, data in by_profile.get("ec-results-elections-index", []):
        es, aside = EX.index(data)
        for place, why in aside:
            r.aside(f"{sha}/{place}", "elections", why)
        for e in es:
            row = {"key": e.key, "kind": e.kind, "name": e.name, "electorate": e.electorate, "polled_on": e.polled_on,
                   "polled_basis": "stated on the results index", "results_href": e.href,
                   **r.stamp(sha, "ec-results-elections-index", e.place)}
            if r.add("elections", row):
                got[e.key] = row
    for folder, sha, name, captured, data in by_profile.get("ec-candidate-lists-release", []):
        year = re.search(r"(\d{4}) General Election", data.decode("utf-8", "replace"))
        if year:
            key = f"ge-{year.group(1)}"
            if key not in got:
                row = {"key": key, "kind": "general", "name": f"{year.group(1)} General Election", "electorate": None,
                       "polled_on": None, "polled_basis": "not yet polled: no held file states the day",
                       "results_href": None, **r.stamp(sha, "ec-candidate-lists-release", "the release's title")}
                if r.add("elections", row):
                    got[key] = row
    return got


# --- 2020 and 2023: the results ------------------------------------------------

def _stats(r, by_profile):
    stats = []
    for folder, sha, name, captured, data in by_profile.get("statsnz-electorates-2020", []):
        stats += [(code, nm, layer, sha) for code, nm, layer in EL.statsnz(data)]
    return stats


def _results(r, by_profile, elections):
    stats = _stats(r, by_profile)
    abbrev = {}                                 # (year, abbreviation) → {party names the Commission paired it with}
    pages = {}
    for folder, sha, name, captured, data in by_profile.get("ec-results-electorate-page", []):
        pages.setdefault(_year(name), []).append((sha, name, data))
    for year in sorted(pages):
        ekey = f"ge-{year}"
        if ekey not in elections:
            for sha, name, _ in pages[year]:
                r.aside(name, "results", f"no election {ekey} on the results index")
            continue
        listed, list_doc = [], None
        for sha, name, data in sorted(pages[year], key=lambda p: p[1]):
            listed = RS.electorate_list(data)
            if listed:
                list_doc = sha
                break
        joined = EL.join([n for _, n in listed], [s[:3] for s in stats]) if year in ("2020", "2023") else {}
        stats_doc = {s[1]: s[3] for s in stats}
        read_pages = {}
        party_of = {}
        for sha, name, data in pages[year]:
            e = RS.electorate_page(data)
            bad = e.problems()
            if bad:
                r.aside(f"{sha}/{name}", "results", "the page fails its own totals: " + "; ".join(bad))
                continue
            read_pages[e.name] = (sha, name, e)
            for place, cand, party, votes, cancelled in e.candidates:
                party_of[(e.name, K.person_key(cand))] = party
        for number, ename in listed:
            j = joined.get(ename)
            sha, name, e = read_pages.get(ename, (None, None, None))
            ekey_e = f"{ekey}/{slug(ename)}"
            row = {"key": ekey_e, "election": ekey, "name": ename, "number": number,
                   "statsnz_code": j[0] if j else None, "statsnz_name": j[1] if j else None,
                   "layer": j[2] if j else None, "statsnz_document": stats_doc.get(j[1]) if j else None,
                   "join_basis": j[3] if j else ("not joined" if year in ("2020", "2023") else "boundary set not held"),
                   "votes_counted": e.votes_counted if e else None,
                   "candidate_total": e.candidate_total if e else None,
                   "candidate_informals": e.candidate_informals if e else None,
                   "party_total": e.party_total if e else None, "party_informals": e.party_informals if e else None,
                   "poll_cancelled": bool(e and e.candidates and all(c[4] for c in e.candidates)),
                   "result_held": e is not None,
                   **(r.stamp(sha, "ec-results-electorate-page", f"{name} h2") if e else
                      r.stamp(list_doc, "ec-results-electorate-page", f"the electorate selector, option {number}"))}
            r.add("electorates", row)
            if year in ("2020", "2023") and not j:
                r.aside(ekey_e, "electorates", f"{ename}: no Stats NZ 2020 name equals it")
            if e is None:
                r.aside(ekey_e, "results", f"{ename} {year}: the electorate's result page is not held (a failed read); "
                                           f"its candidates and votes are missing")
                continue
            for place, cand, party, votes, cancelled in e.candidates:
                reg, basis = _party(party)
                r.add("candidates", {
                    "key": f"{ekey}/{slug(cand)}/{slug(ename)}", "election": ekey, "name": cand,
                    "display_name": K.person_name(cand).display, "name_key": K.person_key(cand),
                    "party": party, "party_registered": reg, "party_basis": basis or "no party printed",
                    "electorate": ekey_e, "list_place": None, "list_document": None, "list_place_cite": None,
                    "votes": votes, "poll_cancelled": cancelled, "joined_basis": None,
                    **r.stamp(sha, "ec-results-electorate-page", f"{name} partyCandidatesResultsTable row {place}")})
        for f, sha, name, captured, data in by_profile.get("ec-results-electorate-status", []):
            if _year(name) != year:
                continue
            for ename, cand, ab in RS.status(data):
                if (ename, K.person_key(cand)) not in party_of:
                    continue                    # the electorate's page is not held: nothing to pair with
                p = party_of[(ename, K.person_key(cand))] or "∅"
                abbrev.setdefault((year, ab), set()).add(p)
        for f, sha, name, captured, data in by_profile.get("ec-results-overall", []):
            if _year(name) != year:
                continue
            for party, (es, ls, ts) in RS.overall(data).items():
                if (es, ls, ts) == (0, 0, 0):
                    continue
                for what, v in (("electorate seats", es), ("list seats", ls), ("total seats", ts)):
                    r.out.figures.append({"key": f"{ekey}/seats/{slug(party)}/{slug(what)}", "election": ekey,
                                          "what": what, "party": party, "value": v,
                                          **r.stamp(sha, "ec-results-overall", f"overall-results-table, {party}, {what}")})
        _successful(r, by_profile, year, ekey, read_pages)
    r.abbrev = {k: next(iter(v)) for k, v in abbrev.items() if len(v) == 1}
    for k, v in abbrev.items():
        if len(v) > 1:
            r.aside(f"{k[0]} {k[1]}", "results", f"the abbreviation {k[1]} is paired with {sorted(v)}: not used")


def _successful(r, by_profile, year, ekey, read_pages):
    for f, sha, name, captured, data in by_profile.get("ec-results-successful-candidates", []):
        if _year(name) != year:
            continue
        for n, (party, cand, seat, number) in enumerate(RS.successful(data), 1):
            if party is None:
                r.aside(f"{sha}/row {n}", "members", f"{cand}: no party heading above the row")
                continue
            route = "list" if seat == "List Seat" else "electorate"
            ekey_e = f"{ekey}/{slug(seat)}" if route == "electorate" else None
            key = f"{ekey}/seat/{slug(seat)}" if route == "electorate" else f"{ekey}/seat/list/{slug(party)}/{slug(cand)}"
            ckey = f"{ekey}/{slug(cand)}/{slug(seat)}" if route == "electorate" else None
            if route == "electorate" and seat not in read_pages:
                ckey = None
            reg, basis = _party(party)
            r.add("members", {"key": key, "election": ekey, "name": cand, "display_name": K.person_name(cand).display,
                              "name_key": K.person_key(cand), "party": party, "party_registered": reg,
                              "party_basis": basis, "route": route, "electorate": ekey_e, "candidate": ckey,
                              "from_on": None, "from_basis": None, "to_by": None, "to_basis": None, "ended_on": None,
                              **r.stamp(sha, "ec-results-successful-candidates", f"successful_candidates_table row {n}")})


# --- by-elections ---------------------------------------------------------------

def _by_elections(r, by_profile, elections):
    abbrev = getattr(r, "abbrev", {})
    for f, sha, name, captured, data in by_profile.get("ec-byelection-result-page", []):
        e = RS.by_election_page(data)
        hit = [x for x in elections.values() if x["kind"] == "by-election" and x["electorate"] == e.name
               and x["polled_on"] and x["polled_on"][:4] in name]
        if len(hit) != 1:
            r.aside(f"{sha}/{name}", "by-elections", f"{e.name}: not one by-election on the index matches the page")
            continue
        bkey = hit[0]["key"]
        bad = e.problems()
        if bad:
            r.aside(f"{sha}/{name}", "by-elections", "the page fails its own totals: " + "; ".join(bad))
            continue
        ekey_e = f"{bkey}/{slug(e.name)}"
        r.add("electorates", {"key": ekey_e, "election": bkey, "name": e.name, "number": None,
                              "statsnz_code": None, "statsnz_name": None, "layer": None, "statsnz_document": None,
                              "join_basis": "joined through the general election it falls in", "votes_counted": e.candidate_total,
                              "candidate_total": e.candidate_total, "candidate_informals": e.candidate_informals,
                              "party_total": None, "party_informals": None, "poll_cancelled": False, "result_held": True,
                              **r.stamp(sha, "ec-byelection-result-page", f"{name} h2")})
        year = hit[0]["polled_on"][:4]
        known = {ab: p for (y, ab), p in sorted(abbrev.items()) if y <= year}
        top = max(e.candidates, key=lambda c: c[3] or -1)
        if sum(1 for c in e.candidates if c[3] == top[3]) > 1:
            r.aside(ekey_e, "by-elections", "two candidates share the most votes: no member read")
            top = None
        for place, cand, ab, votes, _ in e.candidates:
            party = known.get(ab)
            party = None if party == "∅" else party
            reg, basis = _party(party)
            ckey = f"{bkey}/{slug(cand)}/{slug(e.name)}"
            r.add("candidates", {
                "key": ckey, "election": bkey, "name": cand, "display_name": K.person_name(cand).display,
                "name_key": K.person_key(cand), "party": party or ab, "party_registered": reg,
                "party_basis": (f"the abbreviation {ab}, paired with {party} by the Commission's electorate status pages"
                                if party else f"printed as the abbreviation {ab}; no Commission pairing held"),
                "electorate": ekey_e, "list_place": None, "list_document": None, "list_place_cite": None,
                "votes": votes, "poll_cancelled": False, "joined_basis": None,
                **r.stamp(sha, "ec-byelection-result-page", f"{name} by_election_table row {place}")})
            if top and cand == top[1]:
                r.add("members", {"key": f"{bkey}/seat/{slug(e.name)}", "election": bkey, "name": cand,
                                  "display_name": K.person_name(cand).display, "name_key": K.person_key(cand),
                                  "party": party or ab, "party_registered": reg,
                                  "party_basis": basis if party else f"printed as the abbreviation {ab}",
                                  "route": "by-election", "electorate": ekey_e, "candidate": ckey,
                                  "from_on": None, "from_basis": None, "to_by": None, "to_basis": None, "ended_on": None,
                                  **r.stamp(sha, "ec-byelection-result-page",
                                            f"{name} by_election_table row {place}: the most votes")})
    for x in elections.values():
        if x["kind"] == "by-election" and not any(m["election"] == x["key"] for m in r.out.members) \
                and x["polled_on"] >= "2020-10-17":
            r.aside(x["key"], "by-elections", f"{x['name']}: its result page is not held (the old job was challenged "
                                              f"or never read it); its candidates and member are missing")


# --- 2026: the nominations ---------------------------------------------------------

def _nominations(r, by_profile):
    wbk = by_profile.get("ec-electorate-candidates-workbook", [])
    lst = by_profile.get("votenz-party-lists-page", [])
    rel = by_profile.get("ec-candidate-lists-release", [])
    if not wbk and not lst:
        return
    year = "2026"
    for _, sha, name, _, data in rel:
        m = re.search(r"(\d{4}) General Election", data.decode("utf-8", "replace"))
        year = m.group(1) if m else year
        figs = NO.release(data)
        for k, v in figs.items():
            if k == "parties" or v is None:
                continue
            r.out.figures.append({"key": f"ge-{year}/nominations/{slug(k)}", "election": f"ge-{year}", "what": k,
                                  "party": None, "value": v, **r.stamp(sha, "ec-candidate-lists-release", f"the release: {k}")})
        for party, (lc, ec) in figs["parties"].items():
            for what, v in (("list candidates", lc), ("electorate candidates", ec)):
                r.out.figures.append({"key": f"ge-{year}/nominations/{slug(party)}/{slug(what)}", "election": f"ge-{year}",
                                      "what": what, "party": party, "value": v,
                                      **r.stamp(sha, "ec-candidate-lists-release", f"the release's table: {party}, {what}")})
    ekey = f"ge-{year}"
    ele, lists = [], []
    wsha = lsha = None
    for _, sha, name, _, data in wbk:
        rows, aside = NO.workbook(data)
        wsha = sha
        ele += rows
        for n, why in aside:
            r.aside(f"{sha}/row {n}", "nominations", why)
    for _, sha, name, _, data in lst:
        lsha = sha
        lists += NO.party_lists(data)
    joined, used = NO.join(ele, lists)
    for n, ename in enumerate(sorted({x[2] for x in ele}), 1):
        r.add("electorates", {"key": f"{ekey}/{slug(ename)}", "election": ekey, "name": ename, "number": None,
                              "statsnz_code": None, "statsnz_name": None, "layer": None, "statsnz_document": None,
                              "join_basis": "boundary set not held: Stats NZ's 2025 electorates need a key (card)",
                              "votes_counted": None, "candidate_total": None, "candidate_informals": None,
                              "party_total": None, "party_informals": None, "poll_cancelled": False, "result_held": False,
                              **r.stamp(wsha, "ec-electorate-candidates-workbook",
                                        f"sheet1 column B, first row naming it")})
    for row, nm, ename, party in ele:
        reg, basis = _party(party)
        j = joined.get(row)
        lp = lists[j[0]] if j else None
        r.add("candidates", {
            "key": f"{ekey}/{slug(nm)}/{slug(ename)}", "election": ekey, "name": nm,
            "display_name": K.person_name(nm).display, "name_key": K.person_key(nm), "party": party,
            "party_registered": reg, "party_basis": basis or "no party printed", "electorate": f"{ekey}/{slug(ename)}",
            "list_place": lp[1] if lp else None, "list_document": lsha if lp else None,
            "list_place_cite": f"{lp[0]} item {lp[1]}" if lp else None, "votes": None, "poll_cancelled": False,
            "joined_basis": j[1] if j else None,
            **r.stamp(wsha, "ec-electorate-candidates-workbook", f"sheet1 row {row}")})
    for i, (party, place, nm) in enumerate(lists):
        if i in used:
            continue
        reg, basis = _party(party)
        r.add("candidates", {
            "key": f"{ekey}/{slug(nm)}/list-{slug(party)}", "election": ekey, "name": nm,
            "display_name": K.person_name(nm).display, "name_key": K.person_key(nm), "party": party,
            "party_registered": reg, "party_basis": basis, "electorate": None, "list_place": place,
            "list_document": lsha, "list_place_cite": f"{party} item {place}", "votes": None, "poll_cancelled": False,
            "joined_basis": None, **r.stamp(lsha, "votenz-party-lists-page", f"{party} item {place}")})
    for _, sha, name, _, data in by_profile.get("ec-party-lists-pdf", []):
        from support.docread.pages import page_text
        pairs = NO.pdf_pairs([page_text(data, p) for p in range(1, 7) if page_text(data, p).strip()])
        have = {}
        for pl, nm in pairs:
            have.setdefault(pl, []).append(nm)
        same = wrapped = 0
        for party, place, nm in lists:
            got = have.get(place, [])
            if nm in got:
                same += 1
                got.remove(nm)
            elif any(nm.startswith(g) for g in got):
                wrapped += 1
                g = next(g for g in got if nm.startswith(g))
                got.remove(g)
                r.aside(f"{sha}/{party} {place}", "nominations",
                        f"the PDF prints {g!r} at place {place}, the rest of {nm!r} wrapped to the next line")
            else:
                r.aside(f"{sha}/{party} {place}", "nominations", f"{nm!r} at place {place} is not on the PDF")
        r.out.figures.append({"key": f"{ekey}/nominations/pdf-places-equal", "election": ekey,
                              "what": "pdf places equal", "party": None, "value": same + wrapped,
                              **r.stamp(sha, "ec-party-lists-pdf", "every 'N SURNAME, Given' pair on the text layer")})


# --- windows ---------------------------------------------------------------------------

def _windows(r, elections):
    """A seat's window, from the polling days the Commission states: from
    the poll that returned the member, to (at the latest) the next poll
    that filled the same seat: the next general election, or a by-election
    in that electorate. The day a seat actually ended (dissolution, a
    resignation, a death) is in no held file, so `ended_on` stays empty
    (contract: dates, 3)."""
    general = sorted((e for e in elections.values() if e["kind"] == "general" and e["polled_on"]),
                     key=lambda e: e["polled_on"])
    bys = [e for e in elections.values() if e["kind"] == "by-election"]
    for m in r.out.members:
        e = elections.get(m["election"])
        if not e or not e["polled_on"]:
            continue
        m["from_on"] = e["polled_on"]
        m["from_basis"] = (f"the polling day of {e['name']}, stated on the results index; the term begins "
                           f"on the return of the writ, which no held file states")
        start = e["polled_on"]
        nxt = next((g for g in general if g["polled_on"] > start), None)
        ends = []
        if nxt:
            ends.append((nxt["polled_on"], f"{nxt['name']} polled"))
        elif NEXT_GENERAL in elections:
            m["to_basis"] = f"sitting at the last held file; {elections[NEXT_GENERAL]['name']} not yet polled"
        if m["route"] != "list":
            ename = r_name(r, m["electorate"])
            for b in bys:
                if b["electorate"] == ename and b["polled_on"] > start and (not nxt or b["polled_on"] < nxt["polled_on"]):
                    ends.append((b["polled_on"], f"{b['name']} polled for the seat"))
        if ends:
            day, why = min(ends)
            m["to_by"] = day
            m["to_basis"] = (f"{why}: the seat ended by then at the latest; the day it ended is in no held file"
                             if "By-election" in why else f"{why}: the term ended at the dissolution before it, "
                                                           f"which no held file dates")


def r_name(r, ekey_e):
    for e in r.out.electorates:
        if e["key"] == ekey_e:
            return e["name"]
    return None
