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


def pickers(ctx: Context) -> dict:
    s = ctx.s
    running = {}
    for c in ctx.tables.get("pub.candidates"):
        if c.get("election") == "ge-2026" and c.get("name_key"):
            running.setdefault(c["name_key"], []).append(c)
    mps = []
    for m in ctx.tables.get("pub.members"):
        if m.get("to_by") or m.get("ended_on"):
            continue
        k = ctx.idx.key(m.get("party_registered") or m.get("party"))
        runs = running.get(m.get("name_key") or "", [])
        nm = m.get("display_name") or m.get("name") or ""
        mps.append({"name": nm or "(unreadable)", "name_key": m.get("name_key"), "party": ctx.idx.name(k) or m.get("party"),
                    "party_key": k, "seat": {"election": m.get("election"), "electorate": m.get("electorate"), "route": m.get("route"),
                                             "from": m.get("from_on"), "basis": m.get("from_basis")},
                    "running": {"year": 2026, "electorate": runs[0].get("electorate"), "list_place": runs[0].get("list_place"),
                                "party": ctx.idx.name(ctx.idx.key(runs[0].get("party_registered"))) or runs[0].get("party"),
                                "namesakes": len(runs) - 1, "basis": "the Commission's 2026 candidate list, joined on the shared reading of the name"}
                    if runs else None,
                    "page": paths.path("subject", "person", nm) if nm else None,
                    "cite": ctx.cite(m.get("document"), m.get("page"), m.get("place"))})
    mps.sort(key=lambda x: (x["name_key"] or "", x["name"]))
    ranked = sorted(((F.donor_totals(d), d) for d in ctx.donors.values()), key=lambda td: (-td[0]["total"], td[1].name))
    ranked = [(t, d) for t, d in ranked if t["total"] > 0]
    cut = int(s.get("donor_list_cut") or 1500)
    donors = [{"name": d.name, "name_key": d.name_key, "kind": d.kind, "total": t["total"], "returns": t["returns"],
               "open_year_disclosures": t["open_year_disclosures"], "spellings": sorted(d.spellings),
               "parties": sorted(t["by_receiver"]), "page": paths.path("donor", d.name)} for t, d in ranked[:cut]]
    return {"generated_at": ctx.generated_at, "mps": mps, "mps_basis": "members sitting now from the house lane (no end date); former members are on the search index",
            "donors": donors, "donors_listed": len(donors), "donor_population": len(ranked), "donors_not_shown": max(0, len(ranked) - cut),
            "donors_cut_at": cut, "donors_cut_basis": "the list is cut after folding, so a donor past the line keeps its page and is found by search; only its row here is absent",
            "donor_total_basis": f"money that counts since {s['window_from']}: Part A rows plus disclosures in years no return covers"}


def size_bands(ctx: Context) -> dict:
    s = ctx.s
    line = float(s["line"])
    th = s.get("itemisation_threshold", {"to_2022": 15000, "from_2023": 5000})
    out = {}
    for k, S in ctx.series.items():
        name = ctx.idx.name(k)
        if not name or not any(S.returns_by_year.values()):
            continue
        over, under, unknown = [], [], []
        g_by_year, aside_by_year = {}, {"anonymous": {}, "overseas": {}, "protected": {}}
        years = []
        for y in ctx.years:
            held = S.returns_by_year.get(y, [])
            if len(held) != 1:
                continue
            r = held[0]
            g = float(r.get("part_g") or 0)
            g_by_year[str(y)] = F.money(g)
            for part, key in (("part_c", "anonymous"), ("part_d", "overseas"), ("part_f", "protected")):
                if r.get(part) is not None and float(r[part]) != 0:
                    aside_by_year[key][str(y)] = F.money(r[part])
            rows_ = [x for x in S.counted_named_rows() if x["year"] == y]
            named = sum(float(x["amount"] or 0) for x in rows_)
            placed = named + g + sum(float(r.get(p) or 0) for p in ("part_c", "part_d", "part_f"))
            years.append({"year": y, "threshold": th["from_2023"] if y >= 2023 else th["to_2022"], "line": s["line"],
                          "declared_total": F.money(r["declared_total"]), "part_a": F.money(r.get("part_a")), "part_g": F.money(g),
                          "named_rows": len(rows_), "named": F.money(named), "placed": F.money(placed),
                          "reconciles": abs(placed - float(r["declared_total"] or 0)) < 0.01 if rows_ or (r.get("part_a") or 0) == 0 else None,
                          "basis": "the declaration's own parts; named rows are Part A as read" + ("" if rows_ else "; Part A rows not read, so nothing is placed from them")})
            for x in rows_:
                row = {"ref": f"party_returns:{x['key']}", "year": y, "donor": x.get("donor"), "amount": F.money(x["amount"]),
                       "cite": ctx.cite(x["document"], x.get("page"), x.get("ordinal"))}
                (over if float(x["amount"] or 0) > line else under).append(row)
        bands = [{"key": "over_15k", "label": f"more than ${line:,.0f}: named in the return, every year", "rows": over, "n": len(over),
                  "total": F.money(sum(x["amount"] for x in over)), "basis": "named rows (Part A), each cited"},
                 {"key": "under_15k", "label": f"${line:,.0f} or less", "rows": under, "n": len(under),
                  "named": F.money(sum(x["amount"] for x in under)), "part_g": F.money(sum(g_by_year.values())), "part_g_by_year": g_by_year,
                  "total": F.money(sum(x["amount"] for x in under) + sum(g_by_year.values())),
                  "basis": "named rows at or under the line plus Part G, the return's one total for everything under its itemisation threshold, which carries no names"},
                 {"key": "unknown", "label": "size unknown: filed as a sum with no amounts", "rows": unknown, "n": 0,
                  "total": F.money(sum(sum(v.values()) for v in aside_by_year.values())),
                  "by_kind": {kk: F.money(sum(v.values())) for kk, v in aside_by_year.items()}, "by_year": aside_by_year,
                  "basis": "anonymous, overseas and protected money (Parts C, D, F): a size we do not have, not a size of zero"}]
        out[paths.path("size-bands", name)] = {
            "party": name, "key": k, "generated_at": ctx.generated_at, "window": [ctx.years[0], ctx.years[-1]], "line": s["line"],
            "bands": bands, "years": years, "years_covered": [y["year"] for y in years],
            "declared_total": F.money(sum(y["declared_total"] for y in years)),
            "statute": {"pre_2023": {"threshold": th["to_2022"], "disclosure_cut": 30000}, "from_2023": {"threshold": th["from_2023"], "disclosure_cut": 20000},
                        "why_line": f"to 2022 the return names a donation of more than ${th['to_2022']:,}; from 2023 more than ${th['from_2023']:,}; "
                                    f"so more than ${line:,.0f} is named in every year and is the one cut that means the same thing across the window"},
            "basis": "three bands split at the line that holds in every year; disclosures are not here (the same money appears in the return)"}
    return out


def cites(ctx: Context) -> dict:
    out = {}

    def put(ref, document, page, place, register, href=None, read_from=None, text=""):
        if not document:
            return
        c = ctx.cite(document, page, place, href)
        c.update({"ref": ref, "register": register, "read_from": read_from, "evidence_text": text,
                  "tier": "register-asserted", "source_url_how": "the Commission's link as the lane read it" if href else "none held"})
        out[paths.path("cite", ref)] = c

    for S in ctx.series.values():
        pn = ctx.idx.name(S.key)
        for y, held in S.returns_by_year.items():
            for r in held:
                put(f"party_returns:{r['key']}", r["document"], r.get("page"), r.get("place"), "EC party donation return (declaration)",
                    read_from=r.get("read_from"), text=f"{pn} {y}: declared total ${float(r['declared_total'] or 0):,.2f}")
        for r in S.named_rows:
            put(f"party_returns:{r['key']}", r["document"], r.get("page"), r.get("ordinal"), "EC party donation return (Part A)",
                read_from=r.get("read_from"), text=f"{r.get('donor')}: ${float(r['amount'] or 0):,.2f} to {pn} ({r['year']})")
        for d in S.disclosures:
            put(f"disclosures:{d['key']}", d["document"], d.get("page"), d.get("place"), "EC large-donation disclosures (the Commission's table)",
                href=d.get("href"), read_from=d.get("read_from"),
                text=f"{d.get('donor_name')}: ${float(d['amount'] or 0):,.2f} to {pn} ({F.disclosure_year(d)})")
    return out


MORE_KINDS = [("pickers", lambda ctx: {paths.path("pickers"): pickers(ctx)}), ("size-bands", size_bands), ("cite", cites)]
