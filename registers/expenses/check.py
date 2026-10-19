"""The lane's checks, and its one figure against the outside world.

Each release prints its own arithmetic twice, and both are read:

  a member's row     its categories add to its own total ("Grand Total",
                     "Sub Total Internal Costs"). The reading's own check:
                     a row that fails it is set aside, never published.
  the printed totals each party's total and the release's grand total,
                     against the sum of the member rows they cover. This
                     is the outside check (contract: the lane): the
                     publisher's own figure for the period against the sum
                     of the lane's rows. A difference is reported with the
                     columns it falls in; it is the publisher's arithmetic
                     or ours, and the report says which rows to look at.

Rounding: a quarter printed in whole dollars rounds each cell, so a sum of
n whole-dollar cells may differ from its rounded total by up to n halves.
A cell carrying cents is held to a cent.

    row_check(line, table)       (check, categories_sum, total)
    total_scopes(table, k)       {scope: [member lines]} for the total line at index k
    totals(table)                [per total line: {line, scope, columns: [(heading, printed, rows_sum, equal)]}]
    outside(table)               the release's grand total against its rows: equal | differ | no-total
    python -m registers.expenses.check [--schema expenses] [--database querynz_v4] [--shared]
"""
import sys

CENT = 0.011
PUBLISHED_CHECKS = ("adds", "rounding", "nothing-to-add")


def _whole(v) -> bool:
    return v is not None and abs(v - round(v)) < 1e-6


def tolerance(values) -> float:
    vals = [v for v in values if v is not None]
    return CENT + sum(0.5 if _whole(v) else 0.0001 for v in vals)


def row_check(line, table) -> tuple:
    """'adds' (to the cent), 'rounding' (within the halves of its whole-dollar cells), 'differs',
    'nothing-to-add' (no category and no total: a row carrying only money outside the total), or
    'no-total' (categories and no total figure)."""
    tc = table.total_col
    cats = [c.col for c in table.columns if c.role == "category"]
    vals = [line.figures[c][0] for c in cats if c in line.figures and line.figures[c][0] is not None]
    total = line.figures.get(tc, (None,))[0] if tc else None
    s = round(sum(vals), 2)
    if total is None:
        return ("nothing-to-add" if not vals else "no-total"), (s if vals else None), None
    diff = abs(sum(vals) - total)
    if diff <= CENT:
        return "adds", s, total
    if diff <= tolerance(vals + [total]):
        return "rounding", s, total
    return "differs", s, total


def _label_party(label: str) -> str:
    words = [w for w in label.replace(":", " ").split() if w.lower() not in ("total", "totals", "party")]
    return " ".join(words).lower()


def total_scopes(table, k: int, before: list = ()) -> dict:
    """The member rows a printed total at line index `k` may cover, narrowest first: the party it
    names, the rows since the last total, the whole table, and (for a total printed after the
    last table's notes) every table before it on the sheet (`before`)."""
    ln = table.lines[k]
    members = [x for x in table.lines[:k] if x.kind == "member"]
    prev = max((i for i in range(k) if table.lines[i].kind == "total"), default=-1)
    named = _label_party(ln.name)
    out = {}
    if named:
        party = [x for x in members if x.party and _label_party(x.party) == named]
        if party:
            out["party"] = party
    out["since"] = [x for x in table.lines[prev + 1:k] if x.kind == "member"]
    out["table"] = members
    if before:
        out["sheet"] = list(before) + members
    return {s: rows for s, rows in out.items() if rows}


def _compare(ln, rows, table) -> list:
    cols = []
    for c in table.columns:
        printed = ln.figures.get(c.col, (None,))[0]
        if printed is None:
            continue
        vals = [x.figures[c.col][0] for x in rows if c.col in x.figures and x.figures[c.col][0] is not None]
        s = round(sum(vals), 2)
        cols.append((c.heading, printed, s, abs(sum(vals) - printed) <= tolerance(vals + [printed])))
    return cols


def totals(table, before: list = ()) -> list:
    out = []
    for k, ln in enumerate(table.lines):
        if ln.kind != "total":
            continue
        scopes = total_scopes(table, k, before)
        best = None
        for scope, rows in scopes.items():
            cols = _compare(ln, rows, table)
            if cols and all(e for *_, e in cols):
                best = (scope, cols)
                break
            if best is None:
                best = (scope, cols)
        if best is None:
            out.append({"line": ln, "scope": None, "columns": []})
        else:
            out.append({"line": ln, "scope": best[0], "columns": best[1]})
    return out


def outside(table, before: list = ()) -> dict:
    """The release table's widest printed total (the last total covering the whole table or sheet)
    against the sum of its member rows, in the total column and every other column."""
    ts = [t for t in totals(table, before) if t["scope"] in ("table", "sheet")]
    if not ts:
        return {"result": "no-total", "line": None, "columns": []}
    t = ts[-1]
    bad = [c for c in t["columns"] if not c[3]]
    return {"result": "equal" if not bad else "differ", "line": t["line"], "columns": t["columns"], "differ": bad}


def rows(conn, schema: str, shared: bool = False) -> list:
    pre = "expenses_" if shared else ""
    cur = conn.execute(f"SELECT r.publisher, r.period_start, r.period_end, r.document, t.release, t.scope, t.heading, "
                       f"t.printed, t.rows_sum, t.equal, t.total_role FROM {schema}.{pre}totals t "
                       f"JOIN {schema}.{pre}releases r ON r.key = t.release WHERE t.widest ORDER BY 1, 2, 5, 7")
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur]


def summarise(found: list) -> dict:
    """Per release: equal in the total column or not; every other column that differs is listed."""
    out = {}
    for r in found:
        k = r["release"]
        o = out.setdefault(k, {"publisher": r["publisher"], "period": (r["period_start"], r["period_end"]),
                               "document": r["document"], "total_equal": None, "differ": []})
        if r["total_role"] == "total":
            o["total_equal"] = r["equal"]
        if not r["equal"]:
            o["differ"].append((r["heading"], float(r["printed"]), float(r["rows_sum"])))
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "expenses"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        s = summarise(rows(conn, schema, "--shared" in argv))
    for pub in ("parliamentary-service", "internal-affairs"):
        mine = [v for v in s.values() if v["publisher"] == pub]
        eq = sum(1 for v in mine if v["total_equal"])
        print(f"{pub}: {len(mine)} release tables; grand total equal to the rows in {eq}; "
              f"some column differs in {sum(1 for v in mine if v['differ'])}")
        for v in sorted(mine, key=lambda v: v["period"]):
            for h, p, rs in v["differ"]:
                print(f"  {v['period'][0]}..{v['period'][1]} {h}: printed {p:.2f}, rows {rs:.2f} ({v['document'][:12]})")
    return 1 if any(v["total_equal"] is False for v in s.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
