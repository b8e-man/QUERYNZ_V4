"""The ten kinds of published file, rendered from the shared figures. Each
function takes the build context and returns {relative path: object}. A
kind the estate cannot yet fill writes its "not held" plainly (design:
"a blank says whether it means none found or not held").

The shapes follow the frozen site's files where the estate holds the data,
so the comparison in checks/ (plan 4.5) can read the two sides key by key;
where the frozen key rested on a register this estate does not hold, the
key is present with "not held" and its basis.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from products.published_site import figures as F
from products.published_site import paths
from products.templates import ftm


class Context:
    def __init__(self, template, tables, listing, years: list, idx: F.PartyIndex, series: dict, donors: dict,
                 doc_names: dict, generated_at: str):
        self.template, self.tables, self.listing, self.years = template, tables, listing, years
        self.s = template.settings
        self.idx, self.series, self.donors = idx, series, donors
        self.doc_names = doc_names
        self.generated_at = generated_at
        self.races = ftm.races(self.s)

    def cite(self, document, page=None, place=None, href=None) -> dict:
        names = self.doc_names.get(document) or []
        return {"document": document, "page": page, "place": place, "source_file": names[0] if names else None,
                "source_url": href, "pinned": self.listing.holds(document) if self.listing else None}

    def party_card(self, key: str) -> dict:
        p = self.idx.by_key.get(key, {})
        S = self.series.get(key) or F.Series(key, self.years, self.s)
        w = S.window()
        return {"party": p.get("name") or key, "key": key, "abbreviation": p.get("abbreviation"), "website": p.get("website"),
                "on_register": bool(p.get("on_register")), "registered_on": p.get("registered_on"), "cancelled_on": p.get("cancelled_on"),
                "headline": key in self.s["headline_parties"],
                "window": w, "total_window": w["total"], "named_window": w["named"], "over_line_window": w["over_line"],
                "races": {str(r): S.race(r, ys) for r, ys in self.races.items()},
                "declared_by_year": {str(d["year"]): d["total"] for d in w["series"]},
                "named_by_year": {str(n["year"]): n["total"] for n in w["named_series"]},
                "disclosed_by_year": {str(d["year"]): d["total"] for d in w["disclosed_series"] if d["n"]},
                "disclosed_open_years": w["disclosed_open_years"], "disclosed_sighted": w["disclosed_sighted"],
                "public_money": S.public_money(), "seats": S.seats,
                "register_cite": self.cite(p.get("document"), p.get("page"), p.get("place")) if p.get("document") else None,
                "rows": len(S.named_rows), "returns_held": sum(len(v) for v in S.returns_by_year.values())}


def not_held(what: str, why: str) -> dict:
    return {"held": False, "not_held": what, "basis": why}


def home(ctx: Context) -> dict:
    s = ctx.s
    parties = [ctx.party_card(p["key"]) for p in ctx.idx.registered()]
    with_money = {k for k, S in ctx.series.items() if S.window()["total"] or S.named_rows or S.disclosures}
    for k in sorted(with_money - {p["key"] for p in parties}):
        parties.append(ctx.party_card(k))
    parties.sort(key=lambda c: (not c["headline"], -(c["total_window"] or 0), c["party"]))
    totals_by_year = defaultdict(float)
    for S in ctx.series.values():
        for d in S.window()["series"]:
            if d["total"] is not None:
                totals_by_year[str(d["year"])] += d["total"]
    open_year = max(ctx.years)
    recent = []
    for S in ctx.series.values():
        for d in S.disclosures:
            if F.disclosure_year(d) == open_year:
                recent.append({"party": ctx.idx.name(S.key), "party_key": S.key, "donor": d.get("donor_name"), "amount": F.money(d["amount"]),
                               "received_on": d.get("received_on"), "amendment": d.get("amendment"), "ref": f"disclosures:{d['key']}",
                               "cite": ctx.cite(d["document"], d.get("page"), d.get("place"), d.get("href"))})
    recent.sort(key=lambda r: (r["received_on"] or "", r["donor"] or ""), reverse=True)
    top = sorted(ctx.donors.values(), key=lambda d: -F.donor_totals(d)["total"])
    donors = []
    for d in top[:40]:
        t = F.donor_totals(d)
        if t["total"] <= 0:
            break
        donors.append({"name": d.name, "name_key": d.name_key, "kind": d.kind, "total": t["total"], "returns": t["returns"],
                       "open_year_disclosures": t["open_year_disclosures"], "spellings": sorted(d.spellings), "rows": len(d.rows),
                       "page": paths.path("donor", d.name)})
    pm = {"allocated": F.money(sum(sum(S.allocated_by_year.values()) for S in ctx.series.values())),
          "spent": F.money(sum(sum(S.spent_by_year.values()) for S in ctx.series.values())),
          "expenses": F.money(sum(sum(S.expenses_by_year.values()) for S in ctx.series.values()))}
    return {"generated_at": ctx.generated_at, "template": ctx.template.name, "template_version": ctx.template.version,
            "window_from": s["window_from"], "totals_from": s["window_from"], "named_from": s["named_from"],
            "cycles": sorted(ctx.races), "map_cycles": s.get("map_races", []), "cycle_years": {str(r): [str(y) for y in ys] for r, ys in ctx.races.items()},
            "parties": parties, "headline_parties": [c["key"] for c in parties if c["headline"]],
            "totals": {"declared_by_year": {y: F.money(v) for y, v in sorted(totals_by_year.items())},
                       "declared_window": F.money(sum(totals_by_year.values())),
                       "party_spend": pm["expenses"], "broadcast_allocation": pm["allocated"], "public_spent": pm["spent"],
                       "electorate_spend": not_held("candidate expense returns", "no lane publishes candidate returns yet (step 4.1, candidate-returns)"),
                       "electorate_declared": not_held("candidate donation returns", "no lane publishes candidate returns yet")},
            "donors": donors, "donors_basis": "the largest folded donors in the window by money that counts: Part A rows plus disclosures in years no return covers",
            "recent_disclosures": {"year": open_year, "rows": recent, "n": len(recent), "total": F.money(sum(r["amount"] for r in recent)),
                                   "basis": "donations over the threshold declared to the Commission within 10 working days (Electoral Act 1993 s 210C); "
                                            "no annual return is held for the open year, so these are the only money known for it"},
            "electorates": not_held("electorate money", "candidate returns are not published yet; candidates and results are on the electorate pages"),
            "basis": {"parties": "one figure per calendar year from the window's start: the return's own declared total; the second figure is the Part A rows "
                                 f"above ${s['line']:,.0f}; disclosures are sighted beside the return and never added; the races follow ruling 361, 2017 is no race (366)",
                      "window": f"calendar {s['window_from']} onward (ruling 364); earlier rows are kept in the registers and never published here"},
            "known_limits": ctx.template.known_limits}


def parties(ctx: Context) -> dict:
    reg = []
    for p in ctx.idx.registered():
        c = ctx.party_card(p["key"])
        c["secretary"] = p.get("secretary")
        reg.append(c)
    reg.sort(key=lambda c: (-(c["total_window"] or 0), c["party"]))
    historic = [ctx.party_card(k) for k in ctx.series if not ctx.idx.by_key.get(k, {}).get("on_register")]
    unresolved_rows = [r for r in F.current(ctx.tables.get("pub.party_return_totals"))
                       if r["year"] in ctx.years and not ctx.idx.key(r.get("party_key") or r.get("party"))]
    return {"generated_at": ctx.generated_at, "registered": reg, "registered_n": len(reg),
            "historic": {"count": len(historic), "total": F.money(sum(c["total_window"] or 0 for c in historic)),
                         "parties": sorted(c["party"] for c in historic)},
            "unresolved_returns": {"returns": len(unresolved_rows), "declared": F.money(sum(float(r["declared_total"] or 0) for r in unresolved_rows)),
                                   "labels": sorted({r.get("party_label") or "(unreadable)" for r in unresolved_rows}),
                                   "basis": "returns whose filed party label the parties lane could not join to a registration; counted here, never to a party"},
            "basis": "the parties on the register today, each with the window's figures; a party off the register keeps its figures under historic"}


def search_index(ctx: Context) -> dict:
    entries = []
    for c in home(ctx)["parties"]:
        aliases = {c["party"].lower()}
        if c.get("abbreviation"):
            aliases.add(c["abbreviation"].lower())
        entries.append({"n": c["party"], "k": "party", "f": c["total_window"] or 0, "a": sorted(aliases), "p": paths.path("subject", "party", c["party"])})
    for d in ctx.donors.values():
        t = F.donor_totals(d)
        entries.append({"n": d.name, "k": "donor", "f": t["total"], "a": sorted(x.lower() for x in d.spellings), "p": paths.path("donor", d.name)})
    return {"entries": entries, "generated_at": ctx.generated_at}


def subject_parties(ctx: Context) -> dict:
    out = {}
    keys = {p["key"] for p in ctx.idx.registered()} | set(ctx.series)
    for k in keys:
        name = ctx.idx.name(k)
        if not name:
            continue
        S = ctx.series.get(k) or F.Series(k, ctx.years, ctx.s)
        card = ctx.party_card(k)
        received = []
        for r in sorted(S.counted_named_rows(), key=lambda r: (-r["year"], -float(r["amount"] or 0), r.get("donor") or "")):
            received.append({"ref": f"party_returns:{r['key']}", "year": r["year"], "donor": r.get("donor"), "amount": F.money(r["amount"]),
                             "dates": r.get("dates"), "read_from": r.get("read_from"),
                             "cite": ctx.cite(r["document"], r.get("page"), r.get("ordinal"))})
        disclosed = []
        for d in sorted(S.disclosures, key=lambda d: (d.get("received_on") or "", d.get("donor_name") or ""), reverse=True):
            disclosed.append({"ref": f"disclosures:{d['key']}", "year": F.disclosure_year(d), "donor": d.get("donor_name"), "amount": F.money(d["amount"]),
                              "received_on": d.get("received_on"), "amendment": d.get("amendment"), "regime": d.get("regime"),
                              "covered_by_return": bool(S.returns_by_year.get(F.disclosure_year(d))),
                              "cite": ctx.cite(d["document"], d.get("page"), d.get("place"), d.get("href"))})
        loans = [{"ref": f"party_returns:{r['key']}", "year": r["year"], "lender": r.get("lender"), "amount": F.money(r["amount"]),
                  "cite": ctx.cite(r["document"], r.get("page"), r.get("ordinal"))}
                 for y in sorted(S.loans_by_year) for r in S.loans_by_year[y]]
        by_race = {}
        for race, ys in ctx.races.items():
            rows_ = [x for x in received if x["year"] in ys]
            by_race[str(race)] = {"race": race, "named": F.money(sum(x["amount"] for x in rows_)), "rows": len(rows_)}
        out[paths.path("subject", "party", name)] = {
            "subject": name, "kind": "party", "key": k, "generated_at": ctx.generated_at, "card": card,
            "donations_received": received, "donations_received_total": F.money(sum(x["amount"] for x in received)),
            "donations_received_by_race": by_race,
            "disclosures": disclosed, "disclosures_sighted_total": F.money(sum(x["amount"] for x in disclosed if x["covered_by_return"])),
            "disclosures_open_total": F.money(sum(x["amount"] for x in disclosed if not x["covered_by_return"])),
            "loans": loans, "loans_total": F.money(sum(x["amount"] for x in loans)),
            "board": not_held("party board members", "no lane publishes party boards; the frozen site read them from party websites"),
            "mps": {"seats": S.seats, "basis": "members sitting now, from the house lane; the roster of names is on the pickers"},
            "financials": not_held("financial statement figures", "pub.party_statement_figures is read but not yet rendered (tranche 3)"),
            "received_note": "Part A rows as filed, the current return only; a year whose rows are set aside shows its declared total and no rows",
            "basis": card["window"]["basis"]}
    return out


def donor_pages(ctx: Context) -> dict:
    out = {}
    for d in ctx.donors.values():
        t = F.donor_totals(d)
        hist = []
        for r in sorted(d.rows, key=lambda r: (-r["year"], r["party_name"], -r["amount"])):
            row = dict(r)
            row["cite"] = ctx.cite(r["document"], r.get("page"), r.get("ordinal"), r.get("href"))
            hist.append(row)
        rel = paths.path("donor", d.name)
        if rel in out:   # two folded donors whose display names collide: keep both apart by key
            rel = paths.path("donor", f"{d.name} ({d.name_key})")
        out[rel] = {"generated_at": ctx.generated_at, "name": d.name, "name_key": d.name_key,
                    "identity": {"kind": d.kind, "spellings": sorted(d.spellings), "rows_folded": len(d.refs),
                                 "basis": "folded under the estate's one reading of the filed name (links, pub.names); a person is never joined to a company role here"},
                    "history": hist, "history_total_rows": len(hist),
                    "totals": t, "ownership": {"notes": ["ownership is a note and never adds to an owner's total (ruling 253)"], "companies": not_held("owned companies", "the links' groups are not yet read into donor pages")},
                    "basis": "returns plus disclosures in years no return covers"}
    return out
