"""The figures every kind of published file shares, computed once per build
from the template's views and never twice (design: "No second copy of
logic"; a kind that needs a figure takes it from here).

  PartyIndex    the registered parties by key, and any party value a view
                carries (a key, a registered name, a filed label resolved by
                the lane) back to its key
  party_series  one figure per party-year, basis named: the return's declared
                total, the Part A named rows, the rows over the line, loans,
                the Commission's disclosures (sighted, never added), the
                races (ruling 361; 363 for the 2020 race's named donors;
                366: 2017 is no race), public money, seats
  donors        every filed donor folded under the estate's one reading of
                its name (pub.names.name_key), with its history and totals

Every figure keeps the document it came from; nothing here reads a lane's
inside, and nothing here reads an address.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import Counter, defaultdict

_DATE = re.compile(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})")


def parse_dates(text) -> list:
    """Dates as a Part A row prints them (d/m/yy, d/m/yyyy, several)."""
    out = []
    for d, m, y in _DATE.findall(text or ""):
        y = int(y)
        y = y + 2000 if y < 100 else y
        try:
            out.append(dt.date(y, int(m), int(d)))
        except ValueError:
            continue
    return out


def year_of(iso) -> int | None:
    return int(str(iso)[:4]) if iso else None


def money(x) -> float:
    return round(float(x or 0), 2)


class PartyIndex:
    def __init__(self, parties: list, party_names: list):
        self.by_key = {p["key"]: p for p in parties}
        self.key_of_name = {}
        for p in parties:
            self.key_of_name[p["name"]] = p["key"]
            if p.get("first_name"):
                self.key_of_name.setdefault(p["first_name"], p["key"])
        for n in party_names:
            if n.get("party") and n.get("name"):
                self.key_of_name.setdefault(n["name"], n["party"])
                if n.get("name_key"):
                    self.key_of_name.setdefault("key:" + n["name_key"], n["party"])

    def key(self, value) -> str | None:
        """A key stays a key; a registered name (any era) becomes its key; anything else is None."""
        if not value:
            return None
        if value in self.by_key:
            return value
        return self.key_of_name.get(value)

    def name(self, key) -> str:
        p = self.by_key.get(key)
        return p["name"] if p else ""

    def registered(self) -> list:
        return sorted((p for p in self.by_key.values() if p.get("on_register")), key=lambda p: p["name"])


def current(rows: list) -> list:
    return [r for r in rows if not r.get("replaced_by")]


def disclosure_year(d: dict) -> int | None:
    return year_of(d.get("received_on") or d.get("given_on"))


def live_disclosures(rows: list) -> list:
    """The Commission's declarations that stand: not withdrawn, not an amendment the Commission withdrew."""
    return [d for d in rows if not d.get("withdrawn_on") and d.get("amendment") != "amendment withdrawn"]


class Series:
    """One party's figures across the window. Dict-shaped on purpose: the
    kinds write it into JSON as it is."""

    def __init__(self, key: str, years: list, settings: dict):
        self.key = key
        self.years = years
        self.s = settings
        self.returns_by_year = defaultdict(list)       # year -> [current return rows]
        self.named_rows = []                           # current Part A rows in the window
        self.loans_by_year = defaultdict(list)
        self.disclosures = []                          # live disclosure rows in the window
        self.allocated_by_year, self.spent_by_year, self.expenses_by_year = {}, {}, {}
        self.seats = {"total": 0, "electorate": 0, "list": 0}

    # one figure per party-year, basis named
    def declared(self, year: int) -> dict:
        held = self.returns_by_year.get(year, [])
        if not held:
            return {"year": year, "total": None, "basis": "no return held", "documents": []}
        docs = [{"document": r["document"], "page": r.get("page"), "read_from": r.get("read_from"), "total_check": r.get("total_check")} for r in held]
        if len(held) > 1:
            return {"year": year, "total": None, "basis": f"{len(held)} returns held and none replaced; none chosen (queued for Arthur)", "documents": docs,
                    "held": [money(r["declared_total"]) for r in held]}
        r = held[0]
        how = "read from the text layer" if r.get("read_from") == "text" else "read from pixels: weaker evidence"
        return {"year": year, "total": money(r["declared_total"]), "basis": f"the return's own declared total ({r.get('declared_parts') or 'as printed'}), {how}",
                "documents": docs, "part_a": money(r["part_a"]) if r.get("part_a") is not None else None,
                "loans": money(r["loans_total"]) if r.get("loans_total") is not None else None}

    def ambiguous_years(self) -> set:
        """Years with more than one current return held: nothing of theirs is summed."""
        return {y for y, held in self.returns_by_year.items() if len(held) > 1}

    def counted_named_rows(self) -> list:
        amb = self.ambiguous_years()
        return [r for r in self.named_rows if r["year"] not in amb]

    def named(self, year: int) -> dict:
        rows_ = [r for r in self.named_rows if r["year"] == year]
        held = self.returns_by_year.get(year, [])
        if not held:
            return {"year": year, "total": None, "rows": 0, "over_line": None, "basis": "no return held"}
        if len(held) > 1:
            return {"year": year, "total": None, "rows": len(rows_), "over_line": None,
                    "basis": f"{len(held)} returns held and none replaced; the rows of neither are counted"}
        if not rows_:
            nil = any((r.get("part_a") or 0) == 0 for r in held)
            return {"year": year, "total": 0.0 if nil else None, "rows": 0, "over_line": 0.0 if nil else None,
                    "basis": "Part A declared nil" if nil else "named rows not read (set aside by the lane)"}
        line = float(self.s["line"])
        return {"year": year, "total": money(sum(float(r["amount"] or 0) for r in rows_)), "rows": len(rows_),
                "over_line": money(sum(float(r["amount"] or 0) for r in rows_ if float(r["amount"] or 0) > line)),
                "basis": f"Part A rows as filed; over the line is rows above ${line:,.0f}"}

    def disclosed(self, year: int) -> dict:
        rows_ = [d for d in self.disclosures if disclosure_year(d) == year]
        covered = bool(self.returns_by_year.get(year))
        return {"year": year, "total": money(sum(float(d["amount"] or 0) for d in rows_)), "n": len(rows_),
                "covered_by_return": covered,
                "basis": "sighted beside the return, never added" if covered else "open year: no return held, the disclosures are the only money known"}

    def window(self) -> dict:
        decl = [self.declared(y) for y in self.years]
        held = [d for d in decl if d["total"] is not None]
        left_out = [d["year"] for d in decl if d["total"] is None and d["documents"]]
        named = [self.named(y) for y in self.years]
        disc = [self.disclosed(y) for y in self.years]
        return {"from": self.years[0], "to": self.years[-1], "total": money(sum(d["total"] for d in held)),
                "years_held": [d["year"] for d in held], "years_left_out": left_out,
                "named": money(sum(n["total"] for n in named if n["total"] is not None)),
                "named_rows": sum(n["rows"] for n in named),
                "over_line": money(sum(n["over_line"] for n in named if n["over_line"] is not None)),
                "line": self.s["line"],
                "disclosed_open_years": money(sum(d["total"] for d in disc if not d["covered_by_return"])),
                "disclosed_sighted": money(sum(d["total"] for d in disc if d["covered_by_return"])),
                "series": decl, "named_series": named, "disclosed_series": disc,
                "basis": "one figure per calendar year: the return's own declared total where one return is held; a year with two returns held and "
                         "none replaced is left out and named; named donors are the Part A rows as filed and come second; disclosures are never added"}

    def race(self, race: int, years: list) -> dict:
        decl = [self.declared(y) for y in years]
        held = [d for d in decl if d["total"] is not None]
        named_from = dt.date.fromisoformat(self.s["named_from"])
        named_rows = []
        undated_2017 = 0
        for r in self.counted_named_rows():
            if r["year"] in years:
                named_rows.append(r)
            elif race == 2020 and r["year"] == 2017:
                dates = parse_dates(r.get("dates"))
                if dates and max(dates) >= named_from:
                    named_rows.append(r)
                elif not dates:
                    undated_2017 += 1
        line = float(self.s["line"])
        return {"race": race, "years": years, "years_held": [d["year"] for d in held],
                "total": money(sum(d["total"] for d in held)),
                "named": money(sum(float(r["amount"] or 0) for r in named_rows)), "named_rows": len(named_rows),
                "over_line": money(sum(float(r["amount"] or 0) for r in named_rows if float(r["amount"] or 0) > line)),
                "undated_2017_rows_left_out": undated_2017 if race == 2020 else 0,
                "basis": "every calendar year after the election before it up to its own (ruling 361)"
                         + ("; the 2020 race's named rows run from 24 September 2017 by each row's own date (ruling 363)" if race == 2020 else "")}

    def public_money(self) -> dict:
        return {"allocated": money(sum(self.allocated_by_year.values())), "spent": money(sum(self.spent_by_year.values())),
                "by_year": {str(y): money(v) for y, v in sorted(self.allocated_by_year.items())},
                "spent_by_year": {str(y): money(v) for y, v in sorted(self.spent_by_year.items())},
                "expenses_by_year": {str(y): money(v) for y, v in sorted(self.expenses_by_year.items())},
                "basis": "broadcasting allocation: the Commission's final decision for the election year; spent and expenses: the party's expense return as the Commission tabulates it"}


def window_years(settings: dict, today: dt.date = None) -> list:
    today = today or dt.date.today()
    return list(range(int(settings["window_from"]), today.year + 1))


def party_series(tables, settings: dict, idx: PartyIndex, years: list) -> dict:
    out = {}

    def S(key):
        if key not in out:
            out[key] = Series(key, years, settings)
        return out[key]

    for r in current(tables.get("pub.party_return_totals")):
        k = idx.key(r.get("party_key") or r.get("party"))
        if k and r["year"] in years:
            S(k).returns_by_year[r["year"]].append(r)
    for r in current(tables.get("pub.party_return_donors")):
        k = idx.key(r.get("party_key") or r.get("party"))
        if k and r["year"] in years:
            S(k).named_rows.append(r)
    for r in current(tables.get("pub.party_return_loans")):
        k = idx.key(r.get("party_key") or r.get("party"))
        if k and r["year"] in years:
            S(k).loans_by_year[r["year"]].append(r)
    for d in live_disclosures(tables.get("pub.disclosures")):
        k = idx.key(d.get("party"))
        y = disclosure_year(d)
        if k and y in years:
            S(k).disclosures.append(d)
    for b in tables.get("pub.broadcasting_allocations"):
        k = idx.key(b.get("party"))
        if k and b.get("final") and b.get("eligible") and b["year"] in years:
            S(k).allocated_by_year[b["year"]] = float(b["amount"] or 0)
    for e in tables.get("pub.party_expenses"):
        k = idx.key(e.get("party"))
        if k and e["year"] in years:
            if e.get("allocation_spent") is not None:
                S(k).spent_by_year[e["year"]] = float(e["allocation_spent"])
            if e.get("total_expenses") is not None:
                S(k).expenses_by_year[e["year"]] = float(e["total_expenses"])
    for m in tables.get("pub.members"):
        if m.get("to_by") or m.get("ended_on"):
            continue
        k = idx.key(m.get("party_registered") or m.get("party"))
        if k:
            s = S(k).seats
            s["total"] += 1
            s["list" if m.get("route") == "list" else "electorate"] += 1
    return out


class Donor:
    def __init__(self, name_key: str, kind: str):
        self.name_key, self.kind = name_key, kind
        self.spellings = Counter()
        self.rows = []          # history rows, each with its document
        self.refs = []          # the pub.names refs folded here

    @property
    def name(self) -> str:
        best = sorted(self.spellings.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))
        return best[0][0] if best else "(unreadable)"


def donors(tables, settings: dict, idx: PartyIndex, series: dict, years: list) -> dict:
    """{name_key: Donor} over the current Part A rows and the live disclosures
    in the window, folded by the shared reading. A disclosure in a year the
    party's return covers is a sighting, never money."""
    reading = {}
    for n in tables.get("pub.names"):
        reading[n["ref"]] = n
    out = {}

    def D(ref, filed):
        n = reading.get(ref)
        nk = n["name_key"] if n and n.get("name_key") else ("filed:" + (filed or "").strip().lower())
        kind = n["kind"] if n else "unreadable"
        if nk not in out:
            out[nk] = Donor(nk, kind)
        d = out[nk]
        d.spellings[(filed or "").strip() or "(unreadable)"] += 1
        d.refs.append(ref)
        return d

    for r in current(tables.get("pub.party_return_donors")):
        k = idx.key(r.get("party_key") or r.get("party"))
        if not k or r["year"] not in years:
            continue
        d = D(f"party_returns:{r['key']}", r.get("donor"))
        ambiguous = bool(series.get(k)) and r["year"] in series[k].ambiguous_years()
        d.rows.append({"ref": f"party_returns:{r['key']}", "source": "return", "year": r["year"], "party": k, "party_name": idx.name(k),
                       "party_filed": r.get("party_label"), "donor_filed": r.get("donor"), "amount": money(r["amount"]),
                       "dates": r.get("dates"), "document": r["document"], "page": r.get("page"), "read_from": r.get("read_from"),
                       "counts": not ambiguous,
                       "basis": "two returns held for this year and none replaced; the row is shown and not counted" if ambiguous else "Part A of the party's return"})
    for x in live_disclosures(tables.get("pub.disclosures")):
        k = idx.key(x.get("party"))
        y = disclosure_year(x)
        if not k or y not in years:
            continue
        covered = bool(series.get(k) and series[k].returns_by_year.get(y))
        d = D(f"disclosures:{x['key']}", x.get("donor_name"))
        d.rows.append({"ref": f"disclosures:{x['key']}", "source": "disclosure", "year": y, "party": k, "party_name": idx.name(k),
                       "party_filed": x.get("party_label"), "donor_filed": x.get("donor_name"), "amount": money(x["amount"]),
                       "received_on": x.get("received_on"), "document": x["document"], "page": x.get("page"),
                       "declaration_document": x.get("declaration_document"), "href": x.get("href"), "regime": x.get("regime"),
                       "counts": not covered,
                       "basis": "sighted: the return for this year is the record" if covered else "open year: no return held"})
    return out


def donor_totals(d: Donor) -> dict:
    by_year, by_receiver = defaultdict(float), defaultdict(float)
    returns = sum(r["amount"] for r in d.rows if r["source"] == "return" and r["counts"])
    uncounted = sum(r["amount"] for r in d.rows if r["source"] == "return" and not r["counts"])
    open_disc = sum(r["amount"] for r in d.rows if r["source"] == "disclosure" and r["counts"])
    sighted = sum(r["amount"] for r in d.rows if r["source"] == "disclosure" and not r["counts"])
    for r in d.rows:
        if r["counts"]:
            by_year[str(r["year"])] += r["amount"]
            by_receiver[r["party_name"]] += r["amount"]
    return {"returns": money(returns), "returns_not_counted": money(uncounted), "open_year_disclosures": money(open_disc), "disclosures_sighted": money(sighted),
            "total": money(returns + open_disc),
            "by_year": {k: money(v) for k, v in sorted(by_year.items())},
            "by_receiver": {k: money(v) for k, v in sorted(by_receiver.items())},
            "basis": "returns plus disclosures in years no return covers; a disclosure the return covers is sighted and never added; "
                     "ownership is a note and never adds to an owner's total"}


# ── party financial statements (party-finance lane; plan 4.4 tranche 2) ───────

STATEMENT_FIGURES = ("income", "expenditure", "surplus", "assets", "liabilities", "net_assets")


def statements(tables, idx: PartyIndex, years: list) -> dict:
    """{party key: [statement]} from pub.party_financial_statements, newest
    filed year first, each with the headline figures the lane read from the
    statement document (pub.party_statement_figures, current rows only).
    A statement listed by the Commission with no document held keeps its
    row and says so. Filed years inside the window only."""
    figs = defaultdict(dict)
    for f in tables.get("pub.party_statement_figures"):
        if not f.get("current") or f.get("figure") not in STATEMENT_FIGURES:
            continue
        figs[f.get("roster_row") or ""][f["figure"]] = {
            "amount": money(f["amount"]) if f.get("amount") is not None else None,
            "prior": money(f["prior_amount"]) if f.get("prior_amount") is not None else None,
            "scale": f.get("scale"), "check": f.get("figure_check"), "printed": f.get("printed"),
            "document": f.get("document"), "page": f.get("page"), "place": f.get("place"), "read_from": f.get("read_from")}
    out = defaultdict(list)
    for s in tables.get("pub.party_financial_statements"):
        k = idx.key(s.get("party"))
        if not k or s.get("filed_year") is None or int(s["filed_year"]) not in years:
            continue
        docs = [d for d in (s.get("statements") or []) if d]
        out[k].append({"ref": f"party_finance:{s['key']}", "filed_year": int(s["filed_year"]), "balance_date": s.get("balance_date"),
                       "deadline": s.get("deadline"), "date_filed": s.get("date_filed"),
                       "audit_requirement": s.get("audit_requirement"), "party_filed": s.get("party_label"), "party_basis": s.get("party_basis"),
                       "note": s.get("note"), "mark": s.get("mark"), "documents": docs, "document_held": bool(docs),
                       "figures": figs.get(s["key"], {}), "figures_read": sorted(figs.get(s["key"], {})),
                       "read_from": s.get("read_from"), "listing_document": s.get("document"), "page": s.get("page"), "place": s.get("place"),
                       "basis": "the Commission's list of statements filed under s 210K; the figures are read from the statement document itself"
                                + ("" if docs else "; no statement document is held, so no figure is read")})
    for k in out:
        out[k].sort(key=lambda s: (-s["filed_year"], s["ref"]))
    return dict(out)
