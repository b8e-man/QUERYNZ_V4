"""Electorate money: the candidate-returns lane's rows joined to the house
lane's candidates (plan 4.1: "totals come from the Commission's own
spreadsheet, joined on year, electorate and surname"), computed once per
build for the electorate pages, the year files, the home page, the person
pages and the donor pages.

The headline figure follows the template's rule 8: where the lane's reading
of the return and the Commission's own table differ, the Commission's
figure is the headline and the return's is shown beside it. A return the
results do not list a candidate for (the house lane's gaps, or a
by-election it does not hold) is kept and shown as not joined, never
dropped and never guessed. Nothing here folds a donor: candidate-return
donor names are shown as filed (ruling 253), and the donor pages fold them
only by the links' shared reading of the same spelling (figures.donors).
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from products.published_site import figures as F


def fold(s) -> str:
    """A label folded for joining: case, spaces, punctuation and macrons aside."""
    if not s:
        return ""
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def surname_of(printed: str) -> str:
    """'MURALIDHAR, Mahesh' -> 'muralidhar'; 'Chlöe SWARBRICK' -> 'swarbrick'."""
    if not printed:
        return ""
    if "," in printed:
        return fold(printed.split(",", 1)[0])
    words = printed.split()
    caps = [w for w in words if len(w) > 1 and w.isupper()]
    return fold(caps[-1] if caps else words[-1])


def current(rows: list) -> list:
    return [r for r in rows if not r.get("replaced_by") and r.get("status") != "replaced"]


def headline(r: dict) -> dict:
    """The return's three money figures with the Commission's table as the headline where it has one."""
    out = {}
    for ours, theirs, name in (("donations", "commission_donations", "declared"), ("expenses", "commission_expenses", "expenses"), ("loans", "commission_loans", "loans")):
        own = F.money(r[ours]) if r.get(ours) is not None else None
        com = F.money(r[theirs]) if r.get(theirs) is not None else None
        if com is not None:
            agrees = own is not None and abs(own - com) < 0.005
            out[name] = com
            out[name + "_basis"] = "the Commission's candidate-returns table" + ("" if agrees else (f"; the return as read says ${own:,.2f}" if own is not None else "; the return's figure is not read"))
            out[name + "_ours"] = own
            out[name + "_agrees"] = agrees
        else:
            out[name] = own
            out[name + "_basis"] = "the return as read; the Commission's table has no figure for it" if own is not None else "not read"
            out[name + "_ours"] = own
            out[name + "_agrees"] = None
    out["nil"] = out["declared"] == 0.0 if out["declared"] is not None else None
    out["read_from"] = r.get("read_from")
    out["weaker"] = r.get("read_from") == "pixels"
    return out


class CandidateMoney:
    def __init__(self):
        self.by_candidate = {}            # candidate key -> {"return": row, "figures": headline(), "donors": [rows]}
        self.unjoined = defaultdict(list)  # (year, electorate fold) -> [{"return": row, "figures": ..., "donors": [...]}]
        self.candidates = {}              # candidate key -> candidate row (the house lane's)
        self.returns = 0
        self.joined = 0

    def of(self, candidate_key: str):
        return self.by_candidate.get(candidate_key)

    def candidate_of(self, candidate_key: str):
        return self.candidates.get(candidate_key)

    def unjoined_for(self, year: int, electorate_name: str) -> list:
        return self.unjoined.get((int(year), fold(electorate_name)), [])

    def years_of(self, electorate_name: str) -> set:
        """The years the lane holds unjoined returns for in an electorate."""
        f = fold(electorate_name)
        return {y for (y, e) in self.unjoined if e == f}

    def rows(self):
        """Every joined return with its candidate key, plus the unjoined ones with None."""
        for k, x in self.by_candidate.items():
            yield k, x
        for xs in self.unjoined.values():
            for x in xs:
                yield None, x


def candidate_money(tables, idx: F.PartyIndex, elections: dict, years: list) -> CandidateMoney:
    """Join every current candidate return in the window to the one
    candidate of the same surname in the same electorate at the election of
    that year. Two candidates of one surname in one race would be ambiguous:
    neither is joined and both returns are shown as not joined."""
    cm = CandidateMoney()
    e_year = {k: F.year_of(e.get("polled_on")) for k, e in elections.items()}
    e_name = {}
    for e in tables.get("pub.electorates"):
        if e.get("election") in elections:
            e_name[e["key"]] = e.get("name")
    index = defaultdict(list)
    for c in tables.get("pub.candidates"):
        if c.get("election") not in elections or not c.get("electorate"):
            continue
        y = e_year.get(c["election"])
        if y:
            index[(y, fold(e_name.get(c["electorate"])), surname_of(c.get("name")))].append(c)
            cm.candidates[c["key"]] = c
    donors = defaultdict(list)
    for d in current(tables.get("pub.candidate_return_donors")):
        donors[d.get("return_key")].append(d)
    for r in current(tables.get("pub.candidate_return_totals")):
        if r.get("year") is None or int(r["year"]) not in years:
            continue
        cm.returns += 1
        x = {"return": r, "figures": headline(r), "donors": sorted(donors.get(r["key"], []), key=lambda d: (d.get("ordinal") or 0, d.get("key")))}
        hits = index.get((int(r["year"]), fold(r.get("electorate")), fold(r.get("surname"))), [])
        if len(hits) == 1 and hits[0]["key"] not in cm.by_candidate:
            cm.by_candidate[hits[0]["key"]] = x
            cm.joined += 1
        else:
            x["why"] = ("no candidate of this surname in the results for this race (the house lane's gap, or a contest it does not hold)" if not hits
                        else "ambiguous: more than one candidate of this surname in the race, or a second return for one candidate; neither is joined")
            cm.unjoined[(int(r["year"]), fold(r.get("electorate")))].append(x)
    return cm


def donor_lines(entries: list, display_of) -> list:
    """The per-donor lines of several returns grouped by the donor's filed
    name, exactly as filed (never folded), each line citing its return;
    `entries` are (candidate row or None, x) pairs for one race."""
    groups = {}
    for c, x in entries:
        r = x["return"]
        for d in x["donors"]:
            name = (d.get("donor") or "").strip() or "(unreadable)"
            g = groups.setdefault(name, {"name": name, "total": 0.0, "n": 0, "to": []})
            g["total"] = F.money(g["total"] + F.money(d.get("amount")))
            g["n"] += 1
            g["to"].append({"ref": f"candidate_returns:{d['key']}", "candidate": display_of(c, r), "candidate_key": c["key"] if c else None,
                            "party_filed": r.get("party"), "amount": F.money(d.get("amount")), "dates": d.get("dates"), "contributions": d.get("contributions"),
                            "read_from": d.get("read_from"), "document": d["document"], "page": d.get("page"), "ordinal": d.get("ordinal")})
    return sorted(groups.values(), key=lambda g: (-g["total"], g["name"]))


def display(c, r) -> str:
    if c:
        return c.get("display_name") or c.get("name") or ""
    return f"{(r.get('given_names') or '').strip()} {(r.get('surname') or '').strip()}".strip()
