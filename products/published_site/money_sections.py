"""The money sections of the frozen home page, the parties page and the
party page that the first tranche of the template did not carry (plan 4.4;
the comparison's card `page-sections-the-template-does-not-carry`), each
computed from the shared figures and the candidate money, with its basis.

Nothing here reads a new view: every figure is a sum over rows the pages
already cite. The keys are the frozen site's, so the comparison reads the
two sides under one name; the definitions are this template's and each
section says what it sums.
"""
from __future__ import annotations

import re
from collections import defaultdict

from products.published_site import candidate_money as CM
from products.published_site import figures as F
from products.published_site import paths

COMMITTEE_WORDS = ("electorate committee", "electorate", "branch", "regional council", "electoral committee", "club", "fundraising", "lec")
GENERIC = {"the", "party", "new", "zealand", "nz", "of", "aotearoa", "incorporated", "inc", "and", "te"}


def _fold_party(s: str) -> str:
    t = CM.fold(s)
    t = re.sub(r"^the ", "", t)
    t = re.sub(r" (incorporated|inc|nzlp)$", "", t)
    t = re.sub(r"\bnz\b", "new zealand", t)
    return t.strip()


class PartyNames:
    """Which party a filed donor name is: the party itself (its registered
    name, first name, abbreviation or a name the parties lane published,
    folded) or a committee, branch or club of it (every distinctive word of
    one party's name or abbreviation present, a committee word present, and
    no other party fitting). Anything else is nobody's: the row stays under
    its filed name."""

    def __init__(self, idx: F.PartyIndex, party_names: list):
        self.exact = {}
        self.distinct = defaultdict(list)
        for key, p in idx.by_key.items():
            for n in (p.get("name"), p.get("first_name"), p.get("abbreviation")):
                if n:
                    self.exact.setdefault(_fold_party(n), key)
                    words = {w for w in CM.fold(n).split() if w not in GENERIC}
                    if words and all(len(w) >= 4 or w == "act" for w in words) and words not in self.distinct[key]:
                        self.distinct[key].append(words)
        for n in party_names:
            if n.get("party") and n.get("name"):
                self.exact.setdefault(_fold_party(n["name"]), n["party"])

    def of(self, filed: str) -> tuple:
        """(party key, tier) with tier 'party' | 'committee', or (None, None)."""
        f = _fold_party(filed)
        if f in self.exact:
            return self.exact[f], "party"
        if any(w in f for w in COMMITTEE_WORDS):
            fw = set(f.split())
            hits = {key for key, sets in self.distinct.items() if any(ws <= fw for ws in sets)}
            if len(hits) == 1:
                return next(iter(hits)), "committee"
        return None, None


def candidate_rows(ctx) -> list:
    """Every joined candidate return as one row: year, the candidate's party key (from the results), the headline figures."""
    out = []
    for name, races in ctx.contests().items():
        for r in races:
            if r.get("kind") != "general":
                continue
            for c in r["candidates"]:
                if c["return_held"]:
                    out.append({"year": r["year"], "electorate": name, "party": ctx.idx.key(c.get("party")) if c.get("party") else None,
                                "party_name": c.get("party") or c.get("party_filed") or "no party listed", "registered": bool(c.get("party")),
                                "declared": c["declared"] or 0.0, "expenses": c["expenses"] or 0.0, "display": c["display"]})
    return out


def party_transfers(ctx) -> list:
    pn = PartyNames(ctx.idx, ctx.tables.get("pub.party_names"))
    by = {}
    for d in ctx.donors.values():
        for r in d.rows:
            if r["source"] != "candidate":
                continue
            key, tier = pn.of(r["donor_filed"])
            if not key:
                continue
            p = by.setdefault(key, {"name": ctx.idx.name(key), "key": key, "total": 0.0, "rows": 0, "by_year": defaultdict(float), "spellings": set(),
                                    "direct": {"total": 0.0, "rows": 0}, "committees": {"total": 0.0, "rows": 0, "spellings": set()}, "party_funds": True,
                                    "to_own_candidates": 0, "to_other_candidates": 0, "rows_detail": []})
            p["rows_detail"].append({"ref": r["ref"], "year": r["year"], "receiver": r["receiver"], "candidate_key": r.get("candidate_key"), "electorate": r.get("electorate"),
                                     "party_filed": r.get("party_filed"), "donor_filed": r["donor_filed"], "tier": tier, "amount": r["amount"], "dates": r.get("dates"),
                                     "document": r["document"], "page": r.get("page"), "ordinal": r.get("ordinal"), "read_from": r.get("read_from")})
            p["total"] = F.money(p["total"] + r["amount"])
            p["rows"] += 1
            p["by_year"][str(r["year"])] += r["amount"]
            p["spellings"].add(r["donor_filed"])
            t = p["direct"] if tier == "party" else p["committees"]
            t["total"] = F.money(t["total"] + r["amount"])
            t["rows"] += 1
            if tier == "committee":
                t["spellings"].add(r["donor_filed"])
            p["to_own_candidates" if r.get("party") == key else "to_other_candidates"] += 1
    out = []
    for p in by.values():
        p["by_year"] = {y: F.money(v) for y, v in sorted(p["by_year"].items())}
        p["spellings"] = sorted(p["spellings"])
        p["committees"]["spellings"] = sorted(p["committees"]["spellings"])
        out.append(p)
    return sorted(out, key=lambda p: (-p["total"], p["name"]))


def transfers_for_home(transfers: list) -> list:
    return [{k: v for k, v in t.items() if k != "rows_detail"} for t in transfers]


def race_donations(ctx) -> list:
    by = {}
    for r in candidate_rows(ctx):
        p = by.setdefault(r["party_name"], {"name": r["party_name"], "key": r["party"], "registered": r["registered"], "total": 0.0, "rows": 0, "by_year": defaultdict(float)})
        p["total"] = F.money(p["total"] + r["declared"])
        p["rows"] += 1
        p["by_year"][str(r["year"])] += r["declared"]
    for p in by.values():
        p["by_year"] = {y: F.money(v) for y, v in sorted(p["by_year"].items())}
    return sorted(by.values(), key=lambda p: (-p["total"], p["name"]))


def race_spend(ctx) -> list:
    by = {}
    counts = defaultdict(int)
    for name, races in ctx.contests().items():
        for r in races:
            if r.get("kind") == "general":
                for c in r["candidates"]:
                    counts[c.get("party") or c.get("party_filed") or "no party listed"] += 1
    for r in candidate_rows(ctx):
        p = by.setdefault(r["party_name"], {"party": r["party_name"], "key": r["party"], "registered": r["registered"], "spend": 0.0, "by_year": defaultdict(float), "with_figure": 0})
        p["spend"] = F.money(p["spend"] + r["expenses"])
        p["by_year"][str(r["year"])] += r["expenses"]
        p["with_figure"] += 1
    for name, p in by.items():
        p["by_year"] = {y: F.money(v) for y, v in sorted(p["by_year"].items())}
        p["candidates"] = counts.get(name, 0)
    return sorted(by.values(), key=lambda p: (-p["spend"], p["party"]))


def party_funding(ctx, race_don: list) -> list:
    cand = {p["key"]: p for p in race_don if p["key"]}
    out = []
    for key, S in ctx.series.items():
        name = ctx.idx.name(key)
        if not name:
            continue
        w = S.window()
        by_year = defaultdict(float)
        parts = {"party": 0.0, "candidates": 0.0, "public": 0.0}
        for d in w["series"]:
            if d["total"] is not None:
                by_year[str(d["year"])] += d["total"]
                parts["party"] += d["total"]
        for y, v in cand.get(key, {}).get("by_year", {}).items():
            by_year[y] += v
            parts["candidates"] += v
        for y, v in S.allocated_by_year.items():
            by_year[str(y)] += v
            parts["public"] += v
        total = F.money(sum(parts.values()))
        if total:
            out.append({"party": name, "key": key, "total": total, "by_year": {y: F.money(v) for y, v in sorted(by_year.items())},
                        "parts": {k: F.money(v) for k, v in parts.items()}})
    return sorted(out, key=lambda p: (-p["total"], p["party"]))


def donor_categories(ctx) -> dict:
    cats = {"named": 0.0, "sub_threshold": 0.0, "anonymous": 0.0, "overseas": 0.0, "protected": 0.0}
    party_years, years = 0, set()
    for S in ctx.series.values():
        for y, held in S.returns_by_year.items():
            if len(held) != 1:
                continue
            r = held[0]
            party_years += 1
            years.add(y)
            for part, cat in (("part_a", "named"), ("part_g", "sub_threshold"), ("part_c", "anonymous"), ("part_d", "overseas"), ("part_f", "protected")):
                cats[cat] += float(r.get(part) or 0)
    return {**{k: F.money(v) for k, v in cats.items()}, "party_years": party_years, "years": sorted(years),
            "basis": "the parts of every party return held singly for a year in the window: Part A named, Part G under the itemisation threshold, "
                     "Parts C, D and F anonymous, overseas and protected; a year with two returns held and none replaced is left out"}


def party_spend(ctx) -> dict:
    by_year = {}
    for e in ctx.tables.get("pub.party_expenses"):
        k = ctx.idx.key(e.get("party"))
        y = e.get("year")
        if not k or y not in ctx.years:
            continue
        b = by_year.setdefault(str(y), {"returns": 0, "with_figure": 0, "spend": 0.0, "broadcast": 0.0, "unreconciled": 0, "unreconciled_by": 0.0})
        b["returns"] += 1
        if e.get("total_expenses") is not None:
            b["with_figure"] += 1
            b["spend"] = F.money(b["spend"] + float(e["total_expenses"]))
        b["broadcast"] = F.money(b["broadcast"] + float(e.get("allocation") or 0))
        if e.get("agrees") is False:
            b["unreconciled"] += 1
            b["unreconciled_by"] = F.money(b["unreconciled_by"] + abs(float(e.get("total_expenses") or 0) - float(e.get("return_total") or 0)))
    return {"by_year": dict(sorted(by_year.items())), "total": F.money(sum(b["spend"] for b in by_year.values())),
            "broadcast": F.money(sum(b["broadcast"] for b in by_year.values())), "returns": sum(b["returns"] for b in by_year.values()),
            "parties_with_figure": sum(b["with_figure"] for b in by_year.values()), "unreconciled": sum(b["unreconciled"] for b in by_year.values()),
            "unreconciled_by": F.money(sum(b["unreconciled_by"] for b in by_year.values())),
            "basis": "party election expense returns as the Commission tabulates them (pub.party_expenses), election years in the window; "
                     "unreconciled counts a return whose own total the lane read differently from the Commission's figure"}


def race_public(ctx) -> list:
    out = []
    for key, S in ctx.series.items():
        if not S.allocated_by_year:
            continue
        out.append({"name": ctx.idx.name(key), "key": key, "total": F.money(sum(S.allocated_by_year.values())), "spent": F.money(sum(S.spent_by_year.values())),
                    "by_year": {str(y): F.money(v) for y, v in sorted(S.allocated_by_year.items())}, "named_as_filed": False})
    return sorted(out, key=lambda p: (-p["total"], p["name"]))


def public_money(ctx) -> dict:
    by_year, parties = {}, set()
    for b in ctx.tables.get("pub.broadcasting_allocations"):
        k = ctx.idx.key(b.get("party"))
        if not k or not b.get("final") or b.get("year") not in ctx.years:
            continue
        y = by_year.setdefault(str(b["year"]), {"allocated": 0.0, "spent": 0.0, "parties": 0, "allocated_nothing": 0})
        amt = float(b.get("amount") or 0)
        if b.get("eligible") and amt > 0:
            y["allocated"] = F.money(y["allocated"] + amt)
            y["parties"] += 1
            parties.add(k)
            y["spent"] = F.money(y["spent"] + float(ctx.series[k].spent_by_year.get(b["year"], 0) if k in ctx.series else 0))
        else:
            y["allocated_nothing"] += 1
    return {"allocated": F.money(sum(v["allocated"] for v in by_year.values())), "spent": F.money(sum(v["spent"] for v in by_year.values())),
            "parties": len(parties), "party_years": sum(v["parties"] for v in by_year.values()), "allocated_nothing": sum(v["allocated_nothing"] for v in by_year.values()),
            "by_year": dict(sorted(by_year.items())),
            "basis": "the Commission's final broadcasting allocation decision for each election year in the window; spent is the party's expense return's figure"}


def promoter_spend(ctx) -> dict:
    people = defaultdict(list)
    for p in ctx.tables.get("pub.promoter_people"):
        people[(p.get("year"), CM.fold(p.get("promoter")))].append({"role": p.get("role"), "name": p.get("name")})
    by_year, named = {}, []
    for e in ctx.tables.get("pub.promoter_expenses"):
        y = e.get("year")
        if y not in ctx.years:
            continue
        b = by_year.setdefault(str(y), {"returns": 0, "spend": 0.0, "referendum": 0.0, "read_from_the_return": 0, "agree": 0})
        b["returns"] += 1
        spend = float(e.get("election_expenses") or 0)
        ref = float(e.get("cannabis_referendum_expenses") or 0) + float(e.get("end_of_life_referendum_expenses") or 0)
        b["spend"] = F.money(b["spend"] + spend)
        b["referendum"] = F.money(b["referendum"] + ref)
        b["read_from_the_return"] += 1 if e.get("election_return") is not None else 0
        b["agree"] += 1 if e.get("election_agrees") else 0
        named.append({"year": y, "name": e.get("promoter"), "spend": F.money(spend),
                      "cannabis": F.money(e["cannabis_referendum_expenses"]) if e.get("cannabis_referendum_expenses") is not None else None,
                      "eol": F.money(e["end_of_life_referendum_expenses"]) if e.get("end_of_life_referendum_expenses") is not None else None,
                      "document_held": bool(e.get("return_document")), "read_from_return": e.get("election_return") is not None, "agrees": e.get("election_agrees"),
                      "people": people.get((y, CM.fold(e.get("promoter"))), []), "ref": f"party_finance:{e['key']}",
                      "cite": ctx.cite(e.get("document"), e.get("page"), e.get("place"))})
    named.sort(key=lambda n: (-n["spend"], n["name"] or ""))
    cannabis = F.money(sum(n["cannabis"] or 0 for n in named if n["year"] == 2020))
    eol = F.money(sum(n["eol"] or 0 for n in named if n["year"] == 2020))
    promoters = {(p.get("year"), CM.fold(p.get("promoter"))) for p in ctx.tables.get("pub.promoters") if p.get("year") in ctx.years}
    return {"by_year": dict(sorted(by_year.items())), "total": F.money(sum(b["spend"] for b in by_year.values())),
            "returns": sum(b["returns"] for b in by_year.values()), "referendum_2020": F.money(cannabis + eol), "cannabis_2020": cannabis, "eol_2020": eol,
            "promoters": len(promoters), "people": sum(len(v) for k, v in people.items() if k[0] in ctx.years),
            "read_from_the_return": sum(b["read_from_the_return"] for b in by_year.values()), "agree": sum(b["agree"] for b in by_year.values()),
            "named": named, "nil_returns": sum(1 for n in named if n["spend"] == 0 and not (n["cannabis"] or n["eol"])),
            "basis": "registered promoters' expense returns as the Commission tabulates them (pub.promoter_expenses), with the people named on the register; "
                     "read_from_the_return counts returns whose document the lane read, agree those whose figure equals the Commission's"}


def donors_sighted(ctx) -> dict:
    n, total = 0, 0.0
    for d in ctx.donors.values():
        t = F.donor_totals(d)
        if t["total"] == 0 and t["disclosures_sighted"] > 0:
            n += 1
            total += t["disclosures_sighted"]
    return {"n": n, "total": F.money(total), "basis": "donors known from a large-donation declaration alone in a year a return covers: sighted, never summed or ranked"}


# ── the parties page's three counts ──────────────────────────────────────────

def unaffiliated_sitting(ctx) -> int:
    return sum(1 for m in ctx.tables.get("pub.members") if not (m.get("to_by") or m.get("ended_on")) and not ctx.idx.key(m.get("party_registered") or m.get("party")))


def junk_labels(ctx) -> dict:
    rows = [r for r in F.current(ctx.tables.get("pub.party_return_donors")) if r["year"] in ctx.years and not ctx.idx.key(r.get("party_key") or r.get("party"))]
    return {"rows": len(rows), "total": F.money(sum(float(r.get("amount") or 0) for r in rows)),
            "basis": "Part A rows in the window whose return's party label the parties lane could not join to a registration; counted here, never to a party"}


def unmatched_disclosures(ctx) -> dict:
    rows = [d for d in F.live_disclosures(ctx.tables.get("pub.disclosures")) if F.disclosure_year(d) in ctx.years and not ctx.idx.key(d.get("party"))]
    return {"rows": len(rows), "total": F.money(sum(float(d.get("amount") or 0) for d in rows)),
            "labels": sorted({d.get("party_label") or "(unreadable)" for d in rows}),
            "basis": "the Commission's declarations in the window whose party the parties lane could not join to a registration; counted here, never to a party"}


# ── the party page ───────────────────────────────────────────────────────────

def top_donors(ctx, key: str, years=None, n: int = 10) -> list:
    """The party's largest folded donors by counted money in the window (or in the given years): named rows plus disclosures in open years."""
    out = []
    for d in ctx.donors.values():
        rows = [r for r in d.rows if r.get("party") == key and r["counts"] and r["source"] in ("return", "disclosure") and (years is None or r["year"] in years)]
        if not rows:
            continue
        total = F.money(sum(r["amount"] for r in rows))
        if total <= 0:
            continue
        out.append({"name": d.name, "name_key": d.name_key, "kind": d.kind, "total": total, "n": len(rows),
                    "first_year": min(r["year"] for r in rows), "last_year": max(r["year"] for r in rows),
                    "returns": F.money(sum(r["amount"] for r in rows if r["source"] == "return")),
                    "open_year_disclosures": F.money(sum(r["amount"] for r in rows if r["source"] == "disclosure")),
                    "page": paths.path("donor", d.name)})
    out.sort(key=lambda x: (-x["total"], x["name"]))
    return out[:n]
