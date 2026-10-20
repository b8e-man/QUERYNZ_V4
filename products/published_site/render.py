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

from products.published_site import candidate_money as CM
from products.published_site import figures as F
from products.published_site import money_sections as M
from products.published_site import paths
from products.published_site import site_template as ftm


class Context:
    def __init__(self, template, tables, listing, years: list, idx: F.PartyIndex, series: dict, donors: dict,
                 doc_names: dict, generated_at: str, cm=None):
        self.template, self.tables, self.listing, self.years = template, tables, listing, years
        self.s = template.settings
        self.idx, self.series, self.donors = idx, series, donors
        self.doc_names = doc_names
        self.generated_at = generated_at
        self.races = ftm.races(self.s)
        self.statements = F.statements(tables, idx, years)
        self.elections = F.elections_in_window(tables, years)
        self.cm = cm if cm is not None else CM.candidate_money(tables, idx, self.elections, years)
        self._contests = None
        self._transfers = None
        self._people_money = None
        self.interests = F.interests(tables, years)
        self.cm_last_year = max([x["return"]["year"] for x in self.cm.by_candidate.values()] + [y for (y, _e) in self.cm.unjoined] + [0])

    @property
    def transfers(self) -> list:
        if self._transfers is None:
            self._transfers = M.party_transfers(self)
        return self._transfers

    @property
    def people_money(self) -> dict:
        """{name_key: [candidacy money dicts]} for every candidate in the window's races."""
        if self._people_money is None:
            out = defaultdict(list)
            for races in self.contests().values():
                for r in races:
                    for c in r["candidates"]:
                        out[c.get("name_key") or ""].append(c)
            self._people_money = dict(out)
        return self._people_money

    def contests(self) -> dict:
        """{electorate name: [race]} computed once: every race in the window with its candidates and money."""
        if self._contests is None:
            self._contests = contests(self)
        return self._contests

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
    electorates = electorate_summary(ctx)
    transfers, race_don, race_sp = M.transfers_for_home(ctx.transfers), M.race_donations(ctx), M.race_spend(ctx)
    p_spend, pub_money, prom = M.party_spend(ctx), M.public_money(ctx), M.promoter_spend(ctx)
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
                       "electorate_spend": F.money(sum(e["spend"] for e in electorates)), "electorate_declared": F.money(sum(e["declared"] for e in electorates)),
                       "electorates": len(electorates), "candidates": sum(e["candidates"] for e in electorates),
                       "candidates_with_figure": sum(e["with_figure"] for e in electorates), "candidates_declaring": sum(e["declaring"] for e in electorates),
                       "candidate_returns_not_joined": sum(e["returns_not_joined"] for e in electorates),
                       "party_spend_returns": p_spend["returns"], "public_allocated": pub_money["allocated"],
                       "promoter_spend": prom["total"], "promoter_returns": prom["returns"], "promoters_registered": prom["promoters"], "promoter_people": prom["people"]},
            "donors": donors, "donors_basis": "the largest folded donors in the window by money that counts: Part A rows plus disclosures in years no return covers",
            "recent_disclosures": {"year": open_year, "rows": recent, "n": len(recent), "total": F.money(sum(r["amount"] for r in recent)),
                                   "basis": "donations over the threshold declared to the Commission within 10 working days (Electoral Act 1993 s 210C); "
                                            "no annual return is held for the open year, so these are the only money known for it"},
            "party_transfers": transfers, "race_donations": race_don, "race_spend": race_sp, "race_spend_total": F.money(sum(p["spend"] for p in race_sp)),
            "party_funding": M.party_funding(ctx, race_don), "donor_categories": M.donor_categories(ctx), "party_spend": p_spend,
            "race_public": M.race_public(ctx), "public_money": pub_money, "promoter_spend": prom, "donors_sighted": M.donors_sighted(ctx),
            "basis": {"parties": "one figure per calendar year from the window's start: the return's own declared total; the second figure is the Part A rows "
                                 f"above ${s['line']:,.0f}; disclosures are sighted beside the return and never added; the races follow ruling 361, 2017 is no race (366)",
                      "window": f"calendar {s['window_from']} onward (ruling 364); earlier rows are kept in the registers and never published here",
                      "electorates": "one row per electorate with a contest in the window: candidate election expenses (spend) and declared donations from the "
                                     "candidate-returns lane, the Commission's table as the headline, summed over the window's races; a return the results list no "
                                     "candidate for is counted apart on the electorate page and not here",
                      "sections": {
                "party_transfers": "candidate-return donor lines whose filed name is a party (its registered name, first name, abbreviation or a name the parties lane "
                                   "published) or a committee, branch or club naming one party and a committee word; the row keeps its filed name on every page (ruling 253) "
                                   "and is counted here as the party's own money reaching its candidates",
                "race_donations": "candidates' declared donations (the Commission's table as the headline) by the party the results give the candidate, by election year",
                "race_spend": "candidates' election expenses by the same party and year; candidates counts every candidate in the results, with_figure those with a return held",
                "party_funding": "one figure per party and year: the party's own declared total, its candidates' declared donations and its broadcasting allocation; "
                                 "the three parts are named and the disclosures are never added",
                "donor_categories": "the parts of the party returns held singly per year", "party_spend": "party expense returns as the Commission tabulates them",
                "race_public": "broadcasting allocation per party, final decision", "public_money": "broadcasting allocation per election year",
                "promoter_spend": "promoter expense returns with the people on the register", "donors_sighted": "declaration-only donors in covered years"}},
            "electorates": electorates,
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
            "unaffiliated_sitting": M.unaffiliated_sitting(ctx), "junk_labels": M.junk_labels(ctx), "unmatched_disclosures": M.unmatched_disclosures(ctx),

            "historic": {"count": len(historic), "total": F.money(sum(c["total_window"] or 0 for c in historic)),
                         "parties": sorted(c["party"] for c in historic),
                         "basis": "parties off the register today with a return in the window: the sum of their returns' own declared totals inside the window, "
                                  "never all time; each party's page carries its years"},
            "unresolved_returns": {"returns": len(unresolved_rows), "declared": F.money(sum(float(r["declared_total"] or 0) for r in unresolved_rows)),
                                   "labels": sorted({r.get("party_label") or "(unreadable)" for r in unresolved_rows}),
                                   "basis": "returns whose filed party label the parties lane could not join to a registration; counted here, never to a party"},
            "basis": {"page": "the parties on the register today, each with the window's figures; a party off the register keeps its figures under historic",
                      "unaffiliated_sitting": "members sitting now whose party the house lane gives resolves to no registration"}}


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


def party_keys_by_name(ctx: Context, keys) -> list:
    """[(key, name, path)]: one page per registration key. Two registrations
    with one name (New Zealand Loyal, 2023 and 2026) would share a path, so
    the key with the most to show in the window keeps the plain path (ties:
    the one on the register) and the other is keyed by its registration."""
    def weight(k):
        S = ctx.series.get(k)
        return (len(S.named_rows) + len(S.disclosures) + sum(len(v) for v in S.returns_by_year.values()) if S else 0) + len(ctx.statements.get(k, []))
    named = sorted(((k, ctx.idx.name(k)) for k in keys if ctx.idx.name(k)),
                   key=lambda kn: (kn[1], -weight(kn[0]), not ctx.idx.by_key.get(kn[0], {}).get("on_register"), kn[0]))
    out, taken = [], set()
    for k, name in named:
        rel = paths.path("subject", "party", name)
        if rel in taken:
            rel = paths.path("subject", "party", f"{name} ({k})")
        taken.add(rel)
        out.append((k, name, rel))
    return out


def subject_parties(ctx: Context) -> dict:
    out = {}
    keys = {p["key"] for p in ctx.idx.registered()} | set(ctx.series) | set(ctx.statements)
    pages = party_keys_by_name(ctx, keys)
    namesakes = defaultdict(list)
    for k, name, rel in pages:
        namesakes[name].append((k, rel))
    for k, name, rel in pages:
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
        made = [dict(r, cite=ctx.cite(r["document"], r.get("page"), r.get("ordinal"))) for t in ctx.transfers if t["key"] == k for r in t["rows_detail"]]
        made.sort(key=lambda r: (-r["year"], -r["amount"], r["receiver"]))
        sitting = []
        for m in ctx.tables.get("pub.members"):
            if (m.get("to_by") or m.get("ended_on")) or ctx.idx.key(m.get("party_registered") or m.get("party")) != k:
                continue
            nm = m.get("display_name") or m.get("name") or ""
            receipts = F.money(sum(c["declared"] for cs in ctx.people_money.get(m.get("name_key") or "", []) for c in [cs] if c["return_held"]))
            sitting.append({"name": nm, "name_key": m.get("name_key"), "seat": m.get("electorate"), "route": m.get("route"), "election": m.get("election"),
                            "receipts": receipts, "elections_with_return": sum(1 for c in ctx.people_money.get(m.get("name_key") or "", []) if c["return_held"]),
                            "page": paths.path("subject", "person", nm) if nm else None, "cite": ctx.cite(m.get("document"), m.get("page"), m.get("place"))})
        sitting.sort(key=lambda x: (-x["receipts"], x["name"]))
        card["other_registrations_of_this_name"] = [{"key": k2, "page": r2, "on_register": bool(ctx.idx.by_key.get(k2, {}).get("on_register"))}
                                                    for k2, r2 in namesakes[name] if k2 != k]
        out[rel] = {
            "subject": name, "kind": "party", "key": k, "generated_at": ctx.generated_at, "card": card,
            "donations_received": received, "donations_received_total": F.money(sum(x["amount"] for x in received)),
            "donations_received_by_race": by_race,
            "disclosures": disclosed, "disclosures_sighted_total": F.money(sum(x["amount"] for x in disclosed if x["covered_by_return"])),
            "disclosures_open_total": F.money(sum(x["amount"] for x in disclosed if not x["covered_by_return"])),
            "loans": loans, "loans_total": F.money(sum(x["amount"] for x in loans)),
            "board": not_held("party board members", "no lane publishes party boards; the frozen site read them from party websites"),
            "party_window": {
                "leaders": not_held("party leaders", "no lane publishes party leaders; the frozen site read them from party websites"),
                "rules": not_held("party rules", "no lane publishes party rules yet (party-finance's card: party-rules-are-not-in-this-lane-s-folders)"),
                "top_donors": M.top_donors(ctx, k), "top_donors_by_race": {str(r): M.top_donors(ctx, k, ys) for r, ys in ctx.races.items()},
                "top_donors_note": "the ten largest folded donors by money that counts: Part A rows of the party's returns plus declarations in years no return covers; "
                                   "folded under the links' shared reading of the filed name; each donor's page lists every row",
                "basis": "the frozen page's party_window block: leaders, rules and top donors live here on both sides"},
            "mps": {"seats": S.seats, "members": sitting, "basis": "members sitting now from the house lane, each with the declared donations of their candidacies in the window "
                                                                  "(the Commission's table as the headline) summed across elections; 'no return held' counts nothing"},
            "donations_made": made, "donations_made_not_shown": 0, "donations_made_total": F.money(sum(r["amount"] for r in made)),
            "donations_made_basis": "the party's own money reaching its candidates: candidate-return donor lines filed under the party's name or a committee, branch or club of it; "
                                    "each line keeps its filed name and cites the candidate's return",
            "industries": not_held("industry exposure", "needs the links to read donors against the companies register; the queue asks whether it belongs in this template"),
            "exposure": not_held("industry exposure", "as industries"),
            "exposure_cascade": not_held("industry exposure by division and donor", "as industries"),
            "coverage": _coverage(ctx, k, S, made),
            "financials": [dict(st, cite=ctx.cite(st["documents"][0] if st["documents"] else st["listing_document"], st.get("page"), st.get("place")),
                                 figures={f: dict(v, cite=ctx.cite(v["document"], v.get("page"), v.get("place"))) for f, v in st["figures"].items()})
                           for st in ctx.statements.get(k, [])],
            "financials_basis": "annual financial statements filed with the Commission under the Electoral Act 1993 s 210K, from the filed year the window starts; "
                                "one row per statement the Commission lists, newest first; the six headline figures are read from the statement document, each cited; "
                                "a statement listed with no document held shows its row and no figure; an empty list means none listed in the window",
            "received_note": "Part A rows as filed, the current return only; a year whose rows are set aside shows its declared total and no rows",
            "basis": card["window"]["basis"]}
    return out


def _coverage(ctx: Context, k: str, S, made: list) -> dict:
    """What the template holds for this party and what it knows it lacks, the frozen page's coverage block in the new estate's words."""
    years = sorted(S.returns_by_year)
    part_a_years = sorted({r["year"] for r in S.named_rows})
    gaps = []
    for y in years:
        held = S.returns_by_year[y]
        if len(held) == 1 and y not in part_a_years and (held[0].get("part_a") or 0) != 0:
            gaps.append({"what": f"Part A rows of the {y} return not read", "why": "the party-returns lane has read the return's totals page and set its donor pages aside",
                         "status": "open", "card": "part-a-rows-not-read"})
        if len(held) > 1:
            gaps.append({"what": f"{len(held)} current returns held for {y}", "why": "none replaced, none chosen; nothing of the year is summed", "status": "open"})
    with_return = sum(1 for cs in ctx.people_money.values() for c in cs if c["return_held"] and ctx.idx.key(c.get("party")) == k)
    return {"party_years": f"{years[0]}–{years[-1]} ({len(years)} years with a return)" if years else "no return in the window",
            "party_return_files": len({r["document"] for ys in S.returns_by_year.values() for r in ys}),
            "part_a_years": part_a_years, "financial_statements": len(ctx.statements.get(k, [])), "disclosures": f"{len(S.disclosures)} rows",
            "candidate_returns_of_its_candidates": with_return, "candidate_donation_rows_from_the_party": len(made), "gaps": gaps,
            "basis": "counts of what the template's reads hold for this party in the window, and the gaps the lanes have named; nothing here is a figure of money"}


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
    for k, name, rel in party_keys_by_name(ctx, [k for k, S in ctx.series.items() if any(S.returns_by_year.values())]):
        S = ctx.series[k]
        rel = rel.replace("/subject/party/", "/size-bands/", 1)
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
        out[rel] = {
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
    for ckey, x in ctx.cm.rows():
        r = x["return"]
        who = CM.display(ctx.cm.candidate_of(ckey) if ckey else None, r)
        put(f"candidate_returns:{r['key']}", r["document"], r.get("page"), r.get("place"), "EC candidate return (declaration)", read_from=r.get("read_from"),
            text=f"{who}, {r.get('electorate')} {r.get('year')}: donations ${float(r.get('donations') or 0):,.2f}, expenses ${float(r.get('expenses') or 0):,.2f}")
        for d in x["donors"]:
            put(f"candidate_returns:{d['key']}", d["document"], d.get("page"), d.get("ordinal"), "EC candidate return (Part A)", read_from=d.get("read_from"),
                text=f"{d.get('donor')}: ${float(d.get('amount') or 0):,.2f} to {who} ({r.get('electorate')} {r.get('year')})")
    return out


MORE_KINDS = [("pickers", lambda ctx: {paths.path("pickers"): pickers(ctx)}), ("size-bands", size_bands), ("cite", cites)]


# ── electorates, electorate pages, people, board members ─────────────────────

def _elections(ctx: Context) -> dict:
    return ctx.elections


NO_RETURN = ("no return held by the candidate-returns lane: the candidate filed nothing the Commission lists, the return's scan is queued for reading, "
             "or the Commission's table row alone is not published (the lane's card); not a nil")


def _money_of(ctx: Context, c: dict) -> dict:
    """A candidate's money from the joined return; with no return joined the three figures are 'not held' (the
    estate cannot tell a candidate who filed nothing from one whose return it has not read), never a zero."""
    x = ctx.cm.of(c["key"])
    if not x:
        return {"declared": not_held("candidate donations", NO_RETURN), "expenses": not_held("candidate expenses", NO_RETURN),
                "loans": not_held("candidate loans", NO_RETURN), "return_held": False, "declared_basis": NO_RETURN, "expenses_basis": NO_RETURN,
                "loans_basis": NO_RETURN, "nil": None, "itemised_n": 0, "itemised_total": 0.0, "weaker": False, "return_cite": None, "return_ref": None}
    r, f = x["return"], x["figures"]
    out = dict(f)
    out.update({"return_held": True, "return_ref": f"candidate_returns:{r['key']}", "return_status": r.get("status"),
                "itemised_n": len(x["donors"]), "itemised_total": F.money(sum(F.money(d.get("amount")) for d in x["donors"])),
                "commission_file": r.get("commission_file"), "return_cite": ctx.cite(r["document"], r.get("page"), r.get("place"))})
    return out


def _candidate_row(ctx: Context, c: dict, sitting: set) -> dict:
    k = ctx.idx.key(c.get("party_registered"))
    row = {"candidate": c.get("name"), "display": c.get("display_name") or c.get("name"), "name_key": c.get("name_key"),
           "party": ctx.idx.name(k) or None, "party_filed": c.get("party"), "party_registered": bool(k),
           "list_place": c.get("list_place"), "votes": c.get("votes"), "poll_cancelled": bool(c.get("poll_cancelled")),
           "elected": None, "sitting_mp": (c.get("name_key") or "") in sitting,
           "page": paths.path("subject", "person", c.get("display_name") or c.get("name")) if (c.get("display_name") or c.get("name")) else None,
           "cite": ctx.cite(c.get("document"), c.get("page"), c.get("place")), "tier": "register-asserted"}
    row.update(_money_of(ctx, c))
    return row


def _unjoined_row(ctx: Context, x: dict) -> dict:
    r, f = x["return"], x["figures"]
    return {"candidate_as_filed": CM.display(None, r), "surname": r.get("surname"), "given_names": r.get("given_names"), "party_filed": r.get("party"), "year": int(r["year"]),
            "declared": f["declared"], "declared_basis": f["declared_basis"], "expenses": f["expenses"], "expenses_basis": f["expenses_basis"],
            "loans": f["loans"], "nil": f["nil"], "weaker": f["weaker"], "itemised_n": len(x["donors"]),
            "why": x.get("why"), "return_ref": f"candidate_returns:{r['key']}", "return_cite": ctx.cite(r["document"], r.get("page"), r.get("place"))}


def race_money(cands: list, unjoined: list) -> dict:
    """The race's money over the candidates' joined returns, the unjoined returns counted apart and never added."""
    held = [c for c in cands if c["return_held"]]
    return {"declared_total": F.money(sum(c["declared"] or 0 for c in held)), "expenses_total": F.money(sum(c["expenses"] or 0 for c in held)),
            "loans_total": F.money(sum(c["loans"] or 0 for c in held)),
            "returns_held": len(held), "declaring": sum(1 for c in held if (c["declared"] or 0) > 0), "nil_returns": sum(1 for c in held if c["nil"]),
            "no_return": len(cands) - len(held), "weaker": sum(1 for c in held if c["weaker"]),
            "itemised_n": sum(c["itemised_n"] for c in held), "itemised_total": F.money(sum(c["itemised_total"] for c in held)),
            "returns_not_joined": {"n": len(unjoined), "declared": F.money(sum(u["declared"] or 0 for u in unjoined)),
                                   "expenses": F.money(sum(u["expenses"] or 0 for u in unjoined)), "rows": unjoined},
            "money_basis": "candidate donations and expenses from the candidate-returns lane, joined to the results by year, electorate and surname; "
                           "the Commission's own table is the headline where it has a figure and the return as read stands beside it; "
                           "a return the results list no candidate for is counted apart under returns_not_joined and never added"}


def contests(ctx: Context) -> dict:
    """{electorate name: [race dict]} in polling-day order; the one computation the electorate pages, the year files and the home page share."""
    elections = ctx.elections
    sitting = {m.get("name_key") for m in ctx.tables.get("pub.members") if not (m.get("to_by") or m.get("ended_on"))}
    winners = {}
    for m in ctx.tables.get("pub.members"):
        if m.get("route") in ("electorate", "by-election") and m.get("electorate") and m.get("candidate"):
            winners[m["candidate"]] = m
    by_seat = defaultdict(list)
    for c in ctx.tables.get("pub.candidates"):
        if c.get("election") in elections and c.get("electorate"):
            by_seat[c["electorate"]].append(c)
    rows = {e["key"]: e for e in ctx.tables.get("pub.electorates") if e.get("election") in elections}
    names = defaultdict(dict)
    for key, e in rows.items():
        names[e["name"]][e["election"]] = e
    out = {}
    for name in sorted(names):
        races = []
        for ek, e in sorted(names[name].items(), key=lambda kv: elections[kv[0]].get("polled_on") or "9999"):
            el = elections[ek]
            cands = [_candidate_row(ctx, c, sitting) for c in by_seat.get(e["key"], [])]
            for c, raw in zip(cands, by_seat.get(e["key"], [])):
                w = winners.get(raw["key"])
                c["elected"] = True if w else (False if e.get("result_held") else None)
            cands.sort(key=lambda c: (-(c["votes"] or 0), c["display"] or ""))
            parties = defaultdict(lambda: {"candidates": 0, "votes": 0, "declared": 0.0, "expenses": 0.0, "declaring": 0})
            for c in cands:
                p = parties[c["party"] or c["party_filed"] or "no party listed"]
                p["candidates"] += 1
                p["votes"] += c["votes"] or 0
                if c["return_held"]:
                    p["declared"] = F.money(p["declared"] + (c["declared"] or 0))
                    p["expenses"] = F.money(p["expenses"] + (c["expenses"] or 0))
                    p["declaring"] += 1 if (c["declared"] or 0) > 0 else 0
                    p["returns_held"] = p.get("returns_held", 0) + 1
            year = F.year_of(el.get("polled_on")) or 2026
            unjoined = [_unjoined_row(ctx, x) for x in ctx.cm.unjoined_for(year, name)] if el.get("kind") == "general" else []
            entries = [(ctx.cm.candidate_of(k), ctx.cm.of(k)) for k in (c["key"] for c in by_seat.get(e["key"], [])) if ctx.cm.of(k)]
            entries += [(None, x) for x in ctx.cm.unjoined_for(year, name)] if el.get("kind") == "general" else []
            donors = CM.donor_lines(entries, CM.display)
            top = max((c for c in cands if c["return_held"]), key=lambda c: (c["declared"] or 0, c["display"]), default=None)
            race = {"year": year, "election": ek, "election_name": el.get("name"), "kind": el.get("kind"), "polled_on": el.get("polled_on"),
                    "result_held": bool(e.get("result_held")), "poll_cancelled": bool(e.get("poll_cancelled")),
                    "votes_counted": e.get("votes_counted"), "candidate_total": e.get("candidate_total"), "party_total": e.get("party_total"),
                    "candidates": cands, "candidates_n": len(cands),
                    "elected": next((c["display"] for c in cands if c["elected"]), None),
                    "parties": [{"party": p, **v} for p, v in sorted(parties.items(), key=lambda kv: -kv[1]["votes"])],
                    "top": {"display": top["display"], "party": top["party"] or top["party_filed"], "declared": top["declared"], "elected": top["elected"]} if top and (top["declared"] or 0) > 0 else None,
                    "donors": donors, "donors_n": len(donors),
                    "donors_basis": "per-donor lines from the candidates' own returns as the lane read them, names as filed and never folded; each line cites its return; "
                                    "a candidate whose Part A the lane set aside, or who declared below the itemising threshold, has no lines here",
                    "cite": ctx.cite(e.get("document"), e.get("page"), e.get("place")),
                    "statsnz": {"code": e.get("statsnz_code"), "name": e.get("statsnz_name"), "layer": e.get("layer"), "join": e.get("join_basis")}}
            race.update(race_money(cands, unjoined))
            races.append(race)
        out[name] = races
    return out


def electorate_summary(ctx: Context) -> list:
    """One row per electorate across the window's races, for the home page: the frozen site's `electorates` list."""
    out = []
    for name, races in ctx.contests().items():
        row = {"electorate": name, "key": paths.slug(name), "page": paths.path("electorate", name),
               "spend": F.money(sum(r["expenses_total"] for r in races)), "spend_by_year": {str(r["year"]): r["expenses_total"] for r in races},
               "declared": F.money(sum(r["declared_total"] for r in races)), "declared_by_year": {str(r["year"]): r["declared_total"] for r in races},
               "candidates": sum(r["candidates_n"] for r in races), "candidates_by_year": {str(r["year"]): r["candidates_n"] for r in races},
               "with_figure": sum(r["returns_held"] for r in races), "with_figure_by_year": {str(r["year"]): r["returns_held"] for r in races},
               "declaring": sum(r["declaring"] for r in races), "declaring_by_year": {str(r["year"]): r["declaring"] for r in races},
               "returns_not_joined": sum(r["returns_not_joined"]["n"] for r in races),
               "winner": None, "elections": [r["year"] for r in races]}
        last = next((r for r in reversed(races) if r["elected"]), None)
        if last:
            c = next(c for c in last["candidates"] if c["elected"])
            row["winner"] = {"name": c["display"], "party": c["party"], "party_filed": c["party_filed"], "year": last["year"]}
        out.append(row)
    return out


def electorates_and_pages(ctx: Context) -> dict:
    names = ctx.contests()
    files = {}
    per_year = defaultdict(list)
    for name, races in names.items():
        for race in races:
            per_year[race["year"]].append({"electorate": name, "key": paths.slug(name), "page": paths.path("electorate", name), "candidates": race["candidates_n"],
                                           "result_held": race["result_held"], "elected": race["elected"], "votes_counted": race["votes_counted"],
                                           "declared_total": race["declared_total"], "expenses_total": race["expenses_total"],
                                           "returns_held": race["returns_held"], "declaring": race["declaring"], "returns_not_joined": race["returns_not_joined"]["n"]})
        apart = [_unjoined_row(ctx, x) for y in sorted(ctx.cm.years_of(name)) if y not in {r["year"] for r in races} for x in ctx.cm.unjoined_for(y, name)]
        files[paths.path("electorate", name)] = {
            "electorate": name, "key": paths.slug(name), "found": True, "generated_at": ctx.generated_at, "elections": [r["year"] for r in races],
            "races": races,
            **({"returns_for_contests_not_held": {"n": len(apart), "declared": F.money(sum(u["declared"] or 0 for u in apart)), "rows": apart,
                                                  "years": sorted({u["year"] for u in apart}),
                                                  "basis": "returns the lane holds for a contest in this electorate that the house lane's results do not hold (a by-election); "
                                                           "counted apart, never added to a race"}} if apart else {}),
            "money": {"declared_total": F.money(sum(r["declared_total"] for r in races)), "expenses_total": F.money(sum(r["expenses_total"] for r in races)),
                      "by_year": {str(r["year"]): {"declared": r["declared_total"], "expenses": r["expenses_total"], "returns_held": r["returns_held"]} for r in races},
                      "returns_not_joined": sum(r["returns_not_joined"]["n"] for r in races),
                      "basis": "the window's races summed; each race says what it holds"},
            "basis": {"page": "one electorate, every election in the window: the candidates as the Commission's results and lists print them, the winner from the house "
                              "lane's seats; money from the candidate-returns lane, the Commission's own table as the headline",
                      "candidates": "every candidate in the Commission's official result for the race (the house lane), not only those who filed a return; "
                                    "a candidate with no return shows 'no return held'",
                      "contests_not_held": "a return the lane holds for a contest the results do not hold (a by-election) is listed under returns_for_contests_not_held, "
                                           "present only when there is one"}}
    for year in sorted(per_year):
        rows_ = sorted(per_year[year], key=lambda r: r["electorate"])
        files[paths.path("electorates", str(year))] = {
            "year": year, "generated_at": ctx.generated_at, "electorates": rows_,
            "contests": len(rows_), "with_result": sum(1 for r in rows_ if r["result_held"]),
            "candidates": sum(r["candidates"] for r in rows_),
            "money": {"declared_total": F.money(sum(r["declared_total"] for r in rows_)), "expenses_total": F.money(sum(r["expenses_total"] for r in rows_)),
                      "returns_held": sum(r["returns_held"] for r in rows_), "declaring": sum(r["declaring"] for r in rows_),
                      "returns_not_joined": sum(r["returns_not_joined"] for r in rows_),
                      "basis": "the year's contests summed: candidate donations and expenses from the candidate-returns lane, the Commission's table as the headline; "
                               "each electorate's row carries its own"},
            "basis": "every electorate contested in the year's elections, from the house lane"}
    files[paths.path("electorates", "all")] = {
        "generated_at": ctx.generated_at, "years": sorted(per_year), "electorates": [
            {"electorate": name, "key": paths.slug(name), "elections": [r["year"] for r in races], "page": paths.path("electorate", name),
             "declared_total": F.money(sum(r["declared_total"] for r in races)), "expenses_total": F.money(sum(r["expenses_total"] for r in races))}
            for name, races in names.items()],
        "n": len(names),
        "money": {"declared_total": F.money(sum(r["declared_total"] for rs in names.values() for r in rs)),
                  "expenses_total": F.money(sum(r["expenses_total"] for rs in names.values() for r in rs)),
                  "by_year": {str(y): {"declared": F.money(sum(r["declared_total"] for r in per_year[y])), "expenses": F.money(sum(r["expenses_total"] for r in per_year[y]))} for y in sorted(per_year)},
                  "basis": "every race in the window summed"},
        "basis": "every electorate with a contest in the window; the per-year files list each year's contests"}
    return files


def subject_people(ctx: Context) -> dict:
    elections = _elections(ctx)
    e_names = {e["key"]: e.get("name") for e in ctx.tables.get("pub.electorates")}
    people = {}

    def P(name_key, display):
        if not name_key or not display:
            return None
        if name_key not in people:
            people[name_key] = {"subject": display, "kind": "person", "name_key": name_key, "generated_at": ctx.generated_at,
                                "name_forms": set(), "seats": [], "candidacies": [], "donations_received": [],
                                "party_boards": not_held("party board roles", "no lane publishes party boards; the frozen site read them from party websites"),
                                "donations_made": [], "donations_made_total": 0.0,
                                "donations_made_basis": "a person is joined to a donor row only by a group the links' two confirming rules built (pub.groups); today no group "
                                                        "joins a house row to a party-return, candidate-return or declaration row: rule 1 needs a full name with a middle name on "
                                                        "both rows and rule 2 a shared office, which a candidate or member row never carries; namesakes are never joined by name alone",
                                "interests": not_held("declared interests", "no return in the Register of Pecuniary Interests reads as this name (the shared reading, pub.names); "
                                                                            "members only, from the register's editions in the window"),
                                "positions": [], "properties": [], "interests_extra": [],
                                "interests_tree": not_held("declared positions anchored to the companies register",
                                                           "anchoring a declared directorship or business interest to a company needs the links to read the interests register "
                                                           "against the companies register, which they do not yet; the queue asks whether it belongs in this template"),
                                "exposure": not_held("industry exposure", "as interests_tree"),
                                "industry_exposure": not_held("industry exposure", "as interests_tree"),
                                "donations_received_not_shown": 0, "disclosures_sighted_total": 0.0,
                                "public_expenses": not_held("MPs' and ministers' expenses", "the links have not read the expenses registers' names (pub.names has no "
                                                                                              "mp_expenses or minister_expenses rows), so no expense row can be attached under the "
                                                                                              "shared reading; carded for links; the queue asks whether it belongs in this template"),
                                "basis": {"page": "a person as the house lane holds them: seats and candidacies under the shared reading of the name, the candidate's own "
                                                  "returns, and the member's own returns in the Register of Pecuniary Interests under the same reading; nothing else is joined here",
                                          "donations_received_not_shown": "every donor line of every joined return is shown; nothing is cut",
                                          "disclosures_sighted_total": "declarations to the Commission naming this person as the donor: none, since no group joins a house row "
                                                                       "to a declaration row (donations_made_basis)"}}
        people[name_key]["name_forms"].add(display)
        return people[name_key]

    for m in ctx.tables.get("pub.members"):
        p = P(m.get("name_key"), m.get("display_name") or m.get("name"))
        if not p:
            continue
        k = ctx.idx.key(m.get("party_registered") or m.get("party"))
        p["seats"].append({"election": m.get("election"), "route": m.get("route"), "electorate": m.get("electorate"), "party": ctx.idx.name(k) or m.get("party"),
                           "from": m.get("from_on"), "to_by": m.get("to_by"), "ended_on": m.get("ended_on"), "sitting": not (m.get("to_by") or m.get("ended_on")),
                           "cite": ctx.cite(m.get("document"), m.get("page"), m.get("place"))})
    for m in ctx.tables.get("pub.members"):
        if m.get("route") != "list" or m.get("election") not in elections:
            continue
        p = P(m.get("name_key"), m.get("display_name") or m.get("name"))
        if not p:
            continue
        k = ctx.idx.key(m.get("party_registered") or m.get("party"))
        p["candidacies"].append({"election": m.get("election"), "year": F.year_of(elections[m["election"]].get("polled_on")) or 2026,
                                 "electorate": None, "electorate_name": None, "party": ctx.idx.name(k) or m.get("party"), "party_filed": m.get("party"),
                                 "list_place": None, "votes": None, "route": "list", "elected": True,
                                 "elected_basis": "a list seat in the official result (the house lane's seats); the party list itself is not held for this election "
                                                  "(house card: the-2020-and-2023-party-lists-are-not-held), so the place on it is not shown",
                                 "declared": not_held("candidate donations", "a list-only candidacy files no electorate return"),
                                 "expenses": not_held("candidate expenses", "a list-only candidacy files no electorate return"),
                                 "declared_basis": "none: list only", "expenses_basis": "none: list only", "loans": None, "return_held": False, "return_ref": None,
                                 "return_cite": None, "itemised_n": 0, "itemised_total": 0.0, "weaker": False,
                                 "cite": ctx.cite(m.get("document"), m.get("page"), m.get("place"))})
    for c in ctx.tables.get("pub.candidates"):
        if c.get("election") not in elections:
            continue
        p = P(c.get("name_key"), c.get("display_name") or c.get("name"))
        if not p:
            continue
        k = ctx.idx.key(c.get("party_registered"))
        if not c.get("electorate"):
            p["candidacies"].append({"election": c.get("election"), "year": F.year_of(elections[c["election"]].get("polled_on")) or 2026,
                                     "electorate": None, "electorate_name": None, "party": ctx.idx.name(k) or c.get("party"), "party_filed": c.get("party"),
                                     "list_place": c.get("list_place"), "votes": None, "route": "list", "elected": None,
                                     "elected_basis": "on the party list as the Commission published it; no result yet",
                                     "declared": not_held("candidate donations", "a list-only candidacy files no electorate return"),
                                     "expenses": not_held("candidate expenses", "a list-only candidacy files no electorate return"),
                                     "declared_basis": "none: list only", "expenses_basis": "none: list only", "loans": None, "return_held": False, "return_ref": None,
                                     "return_cite": None, "itemised_n": 0, "itemised_total": 0.0, "weaker": False,
                                     "cite": ctx.cite(c.get("list_document") or c.get("document"), c.get("page"), c.get("list_place_cite") or c.get("place"))})
            continue
        money = _money_of(ctx, c)
        p["candidacies"].append({"election": c.get("election"), "year": F.year_of(elections[c["election"]].get("polled_on")) or 2026,
                                 "electorate": c.get("electorate"), "electorate_name": e_names.get(c.get("electorate")), "party": ctx.idx.name(k) or c.get("party"),
                                 "party_filed": c.get("party"), "list_place": c.get("list_place"), "votes": c.get("votes"), "route": "electorate",
                                 "declared": money["declared"], "declared_basis": money["declared_basis"], "expenses": money["expenses"], "expenses_basis": money["expenses_basis"],
                                 "loans": money["loans"], "return_held": money["return_held"], "return_ref": money["return_ref"], "return_cite": money["return_cite"],
                                 "itemised_n": money["itemised_n"], "itemised_total": money["itemised_total"], "weaker": money["weaker"],
                                 "cite": ctx.cite(c.get("document"), c.get("page"), c.get("place"))})
        x = ctx.cm.of(c["key"])
        if x:
            for d in x["donors"]:
                p["donations_received"].append({"ref": f"candidate_returns:{d['key']}", "year": int(x["return"]["year"]), "electorate": x["return"].get("electorate"),
                                                "party_filed": x["return"].get("party"), "donor": (d.get("donor") or "").strip() or "(unreadable)",
                                                "amount": F.money(d.get("amount")), "dates": d.get("dates"), "contributions": d.get("contributions"),
                                                "read_from": d.get("read_from"), "cite": ctx.cite(d["document"], d.get("page"), d.get("ordinal"))})
    out = {}
    for nk, p in people.items():
        p["name_forms"] = sorted(p["name_forms"])
        p["sitting_mp"] = any(s["sitting"] for s in p["seats"])
        p["candidacies"].sort(key=lambda c: (-c["year"], c.get("electorate_name") or ""))
        reg = ctx.interests.get(nk)
        if reg:
            def item(i):
                return {"ref": i["ref"], "category": i["category"], "heading": i["heading"], "text": i["text"] if not i["withheld"] else None, "withheld": i["withheld"],
                        "first_seen": i["first_seen"], "last_seen": i["last_seen"], "editions": i["editions"], "tier": "register-asserted",
                        "cite": ctx.cite(i["document"], i["page"], i["place"])}
            p["interests"] = {"returns": [dict(r, cite=ctx.cite(r["document"], r["page"], r["place"])) for r in reg["returns"]],
                              "editions": [r["as_at"] for r in reg["returns"]], "latest": reg["returns"][0]["as_at"] if reg["returns"] else None,
                              "categories": {cat: len(v) for cat, v in sorted(reg["items"].items())},
                              "basis": "the member's own returns in the Register of Pecuniary and Other Specified Interests, every edition in the window, under the shared "
                                       "reading of the printed name; a declaration repeated across editions is one line with first and last seen"}
            p["positions"] = [item(i) for cat in F.POSITION_CATEGORIES for i in reg["items"].get(cat, [])]
            p["properties"] = [item(i) for i in reg["items"].get(F.PROPERTY_CATEGORY, [])]
            p["interests_extra"] = [{"category": cat, "heading": v[0]["heading"], "n": len(v), "rows": [item(i) for i in v]}
                                    for cat, v in sorted(reg["items"].items()) if cat not in F.POSITION_CATEGORIES and cat != F.PROPERTY_CATEGORY]
            p["basis"]["positions"] = "declared company directorships and controlling interests, other business interests, trusts and employment, as declared and unanchored"
            p["basis"]["properties"] = ("real-property declarations: the count and the editions, the text withheld (queue: may-the-interests-register-s-real-property-"
                                        "declarations-be-shown, default no; hard limit 15)")
        elif not p["seats"]:
            del p["interests"]                      # never a member in the window: no return to hold, so nothing is 'not held'
        gap = [c for c in p["candidacies"] if c.get("route") == "electorate" and not c["return_held"] and c["year"] <= ctx.cm_last_year]
        if gap:
            p["basis"]["candidate_rows_gap"] = (f"no candidate return held for {len(gap)} of this person's electorate candidacies ({', '.join(str(c['year']) for c in gap)}): "
                                       "the figures are not held, not nil (candidate-returns card: candidate-returns-not-held)")
        p["donations_received"].sort(key=lambda r: (-r["year"], -r["amount"], r["donor"]))
        p["donations_received_total"] = F.money(sum(r["amount"] for r in p["donations_received"]))
        p["donations_received_by_year"] = [{"year": c["year"], "electorate": c.get("electorate_name"), "party_filed": c["party_filed"], "total": c["declared"],
                                            "declared_basis": c["declared_basis"], "itemised_total": c["itemised_total"], "itemised_n": c["itemised_n"],
                                            "return_cite": c["return_cite"]} for c in p["candidacies"] if c["return_held"]]
        p["received_note"] = ("the candidate's own returns: the year's declared total (the Commission's table as the headline) and the per-donor lines "
                              "the lane read from Part A, names as filed; a year with a total and no lines had its Part A set aside or declared under the threshold")
        p["namesakes_note"] = "one page per shared reading of the name; two people with one name would share it, so every row cites its own document"
        rel = paths.path("subject", "person", p["subject"])
        out[rel] = p
    return out


def board_members(ctx: Context) -> dict:
    """No lane publishes party boards: no file is written and the manifest says why (kinds_not_held)."""
    return {}


MORE_KINDS += [("electorates", electorates_and_pages), ("subject-person", subject_people), ("board-member", board_members)]
NOT_HELD_KINDS = {"board-member": "no lane publishes party boards; the frozen site read them from party websites (not captured here)"}
