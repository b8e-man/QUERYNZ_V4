"""The lane's one figure against the outside world (plan 4.1): the
Commission's own spreadsheet of candidate totals for an election, against
the lane's rows, joined on year, electorate and surname (`join.py`), to the
cent.

A candidate is `equal` when the current return (status `current` or
`unlisted`: no amendment the Commission publishes replaces it) declares the
spreadsheet's donations and expenses to the cent, and, where the
spreadsheet states total loans and the return was read on the 2023 form,
its loans. "NIL" is 0.00. Otherwise it `differs` (named, with both
figures), or its return is `set aside` (not read), or `not held` (a
spreadsheet row no held return answers; "Return not received" counted
apart). A replaced return is never compared: its figures are a fact about
an earlier filing.

    compare(files, returns, commission) -> {"equal": [...], "differs": [...], "set_aside": [...], "not_held": [...],
                                            "not_received": [...], "no_spreadsheet": [...]}
    python -m registers.candidate_returns.check [--schema candidate_returns] [--database querynz_v4]

Read-only.
"""
import sys

CENT = 0.005


def _eq(a, b) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) < CENT


def compare(files: list, returns: list, commission: list) -> dict:
    """Plain dicts: `files` and `returns` as the lane's tables, `commission` its spreadsheet rows."""
    out = {k: [] for k in ("equal", "differs", "set_aside", "not_held", "not_received", "no_spreadsheet")}
    by_doc = {r["document"]: r for r in returns}
    sheet = {c["key"]: c for c in commission if c["source"] == "spreadsheet"}
    answered = set()
    for f in files:
        if f["status"] not in ("current", "unlisted"):
            continue
        c = sheet.get(f["sheet_key"]) if f["sheet_key"] else None
        if c is None:
            out["no_spreadsheet"].append((f["document"], f["year"], f["surname"], f["electorate"]))
            continue
        answered.add(c["key"])
        r = by_doc.get(f["document"])
        tag = (f["document"], f["year"], f["surname"], f["electorate"])
        if r is None:
            out["set_aside"].append(tag)
            continue
        diffs = []
        for k in ("donations", "expenses"):
            if not _eq(r[k], c[k]):
                diffs.append((k, r[k], c[k]))
        if c.get("loans") is not None and r.get("loans_check"):
            if not _eq(r["loans"], c["loans"]):
                diffs.append(("loans", r["loans"], c["loans"]))
        (out["differs"] if diffs else out["equal"]).append(tag + (tuple(diffs),) if diffs else tag)
    for c in sheet.values():
        if c["key"] in answered:
            continue
        (out["not_received"] if not c["received"] else out["not_held"]).append((c["year"], c["surname"], c["electorate"]))
    return out


def summary(result: dict) -> str:
    return ", ".join(f"{k.replace('_', ' ')} {len(v)}" for k, v in result.items())


def _rows(conn, sql: str) -> list:
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "candidate_returns"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY, database) as conn:
        res = compare(_rows(conn, f"SELECT * FROM {schema}.files"), _rows(conn, f"SELECT * FROM {schema}.returns"),
                      _rows(conn, f"SELECT * FROM {schema}.commission"))
    print(summary(res))
    for d in res["differs"]:
        print(f"  {d[0][:12]} {d[1]} {d[2]}, {d[3]}: " + "; ".join(f"{k} {a} against {b}" for k, a, b in d[4]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
