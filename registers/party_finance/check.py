"""The lane's one check against the outside world (contract: the lane): the
Commission's own figure for each party's election expenses (its table,
`expense_listing`) against the total the party's return itself states
(`expense_returns`, the current return only: the amendment where the
Commission lists one).

The Commission is a second opinion, not an authority (facts and traps: it
printed Part A alone as two parties' 2020 totals). So a difference is
explained, not hidden, in one measured case only: the return's own parts
reconcile with its total and the Commission's figure is that return's Part
A to the cent. Every other difference fails the check, and a party whose
return was not read is listed as unread, never as agreeing.

    compare(listing, returns)   {"equal", "part_a_only", "differ", "unread"}
    compare_years(figures)      {"equal", "differ"}: a statement's prior-year column against the year before's figure
    compare_promoters(listing, returns)   {"equal", "differ", "unread"}: each promoter's column against its return's part,
                                          the Commission's referendum columns never added to its election one
    issue_rows(conn, schema)              {table: rows carrying ruling 66's `issue`}: a sum admitted below $100
                                          off its printed total, counted, never failed
    python -m registers.party_finance.check [--schema party_finance] [--database querynz_v4] [--shared]
"""
import sys

TOLERANCE = 0.011


def _eq(a, b) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) <= TOLERANCE


def compare(listing: list, returns: list) -> dict:
    """listing: dicts with key, year, party_label, total_expenses; returns:
    dicts with listing_row, current, total, total_check, part_a, document."""
    current = {r["listing_row"]: r for r in returns if r["current"]}
    out = {"equal": [], "part_a_only": [], "differ": [], "unread": []}
    for row in sorted(listing, key=lambda r: (r["year"], r["party_label"])):
        ec = row["total_expenses"]
        r = current.get(row["key"])
        item = {"year": row["year"], "party": row["party_label"], "commission": None if ec is None else float(ec)}
        if r is None:
            out["unread"].append(item)
            continue
        item.update(ours=float(r["total"]), document=r["document"], check=r["total_check"])
        if _eq(r["total"], ec):
            out["equal"].append(item)
        elif r["total_check"] == "parts-sum" and _eq(r["part_a"], ec):
            out["part_a_only"].append(item)
        else:
            out["differ"].append(item)
    return out


SPENDING = ("election_expenses", "cannabis_referendum_expenses", "end_of_life_referendum_expenses")


def compare_promoters(listing: list, returns: list) -> dict:
    """listing: promoter_listing dicts (key, year, promoter and the three columns); returns: promoter_returns
    dicts (listing_row, spending, figure, document). A column the Commission leaves empty is not compared."""
    by = {(r["listing_row"], r["spending"]): r for r in returns}
    out = {"equal": [], "differ": [], "unread": []}
    for row in sorted(listing, key=lambda r: (r["year"], r["promoter"])):
        for col in SPENDING:
            ec = row.get(col)
            if ec is None:
                continue
            r = by.get((row["key"], col))
            item = {"year": row["year"], "promoter": row["promoter"], "spending": col, "commission": float(ec)}
            if r is None:
                out["unread"].append(item)
                continue
            item.update(ours=float(r["figure"]), document=r["document"])
            out["equal" if _eq(r["figure"], ec) else "differ"].append(item)
    return out


def compare_years(figures: list) -> dict:
    """Each current statement's prior-year column against the year before's own figure, party by party:
    {"equal", "differ"} (a restated year differs; it is reported, not refused)."""
    cur = [f for f in figures if f["current"] and f["party"]]
    by = {(f["party"], f["filed_year"], f["figure"]): f for f in cur}
    out = {"equal": [], "differ": []}
    for f in sorted(cur, key=lambda f: (f["party"], f["filed_year"], f["figure"])):
        before = by.get((f["party"], f["filed_year"] - 1, f["figure"]))
        if before is None or f["prior_amount"] is None:
            continue
        item = {"party": f["party_label"], "year": f["filed_year"], "figure": f["figure"],
                "prior_column": float(f["prior_amount"]), "year_before": float(before["amount"])}
        tol = max(TOLERANCE, float(f["scale"] or 1), float(before["scale"] or 1))
        out["equal" if abs(item["prior_column"] - item["year_before"]) <= tol else "differ"].append(item)
    return out


def rows(conn, schema: str, shared: bool = False) -> tuple:
    pre = "party_finance_" if shared else ""

    def q(sql):
        cur = conn.execute(sql)
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
    return (q(f"SELECT key, year, party_label, total_expenses FROM {schema}.{pre}expense_listing"),
            q(f"SELECT listing_row, current, total, total_check, part_a, document FROM {schema}.{pre}expense_returns"),
            q(f"SELECT key, year, promoter, {', '.join(SPENDING)} FROM {schema}.{pre}promoter_listing"),
            q(f"SELECT listing_row, spending, figure, document FROM {schema}.{pre}promoter_returns"),
            q(f"SELECT party, party_label, filed_year, figure, amount, prior_amount, scale, current "
              f"FROM {schema}.{pre}statement_figures"))


#: the tables whose rows a sum against a printed total admits (ruling 66)
ISSUE_TABLES = ("expense_returns", "promoter_returns", "allocations", "allocation_totals", "statement_figures")


def issue_rows(conn, schema: str, shared: bool = False) -> dict:
    pre = "party_finance_" if shared else ""
    return {t: conn.execute(f"SELECT count(*) FROM {schema}.{pre}{t} WHERE issue IS NOT NULL").fetchone()[0]
            for t in ISSUE_TABLES}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "party_finance"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        listing, returns, p_listing, p_returns, figures = rows(conn, schema, "--shared" in argv)
        issues = issue_rows(conn, schema, "--shared" in argv)
    out, pro = compare(listing, returns), compare_promoters(p_listing, p_returns)
    for k in ("equal", "part_a_only", "differ", "unread"):
        print(f"{k}: {len(out[k])}")
    for d in out["part_a_only"]:
        print(f"  the Commission printed Part A alone: {d['party']} {d['year']}: ours {d['ours']:.2f}, "
              f"Commission {d['commission']:.2f}, document {d['document']}")
    for d in out["differ"]:
        print(f"  DIFFERS {d['party']} {d['year']}: ours {d['ours']:.2f}, Commission {d['commission']}, document {d['document']}")
    for d in out["unread"]:
        print(f"  unread: {d['party']} {d['year']} (Commission {d['commission']})")
    print("promoters, each column against its return's part:")
    for k in ("equal", "differ", "unread"):
        print(f"{k}: {len(pro[k])}")
    for d in pro["differ"]:
        print(f"  DIFFERS {d['promoter']} {d['year']} {d['spending']}: ours {d['ours']:.2f}, Commission "
              f"{d['commission']:.2f}, document {d['document']}")
    for d in pro["unread"]:
        print(f"  unread: {d['promoter']} {d['year']} {d['spending']} (Commission {d['commission']:.2f})")
    years = compare_years(figures)
    print(f"statements: {len(figures)} figures; the prior-year column against the year before: "
          f"{len(years['equal'])} equal, {len(years['differ'])} differ (a restatement, reported)")
    for d in years["differ"]:
        print(f"  {d['party']} {d['year']} {d['figure']}: prior column {d['prior_column']:,.2f}, "
              f"the year before's statement {d['year_before']:,.2f}")
    print(f"rows reconciled with an issue (ruling 66, below $100): {sum(issues.values())} "
          f"({', '.join(f'{t} {n}' for t, n in issues.items())})")
    return 1 if out["differ"] or pro["differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
