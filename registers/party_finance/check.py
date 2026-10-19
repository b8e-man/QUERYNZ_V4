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


def rows(conn, schema: str, shared: bool = False) -> tuple:
    pre = "party_finance_" if shared else ""

    def q(sql):
        cur = conn.execute(sql)
        return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
    return (q(f"SELECT key, year, party_label, total_expenses FROM {schema}.{pre}expense_listing"),
            q(f"SELECT listing_row, current, total, total_check, part_a, document FROM {schema}.{pre}expense_returns"))


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "party_finance"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        out = compare(*rows(conn, schema, "--shared" in argv))
    for k in ("equal", "part_a_only", "differ", "unread"):
        print(f"{k}: {len(out[k])}")
    for d in out["part_a_only"]:
        print(f"  the Commission printed Part A alone: {d['party']} {d['year']}: ours {d['ours']:.2f}, "
              f"Commission {d['commission']:.2f}, document {d['document']}")
    for d in out["differ"]:
        print(f"  DIFFERS {d['party']} {d['year']}: ours {d['ours']:.2f}, Commission {d['commission']}, document {d['document']}")
    for d in out["unread"]:
        print(f"  unread: {d['party']} {d['year']} (Commission {d['commission']})")
    return 1 if out["differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
