"""The lane's one check against the outside world (contract: the lane): each
edition's own introduction lists its categories by number and heading, in
the statutory wording. The lane files every declaration by the heading its
member's return prints, never by the number; this check asks whether, for
every number a return files under, that heading's category is the one the
edition's own introduction gives the same number. It is the test of the
rule "key on the heading": the register renumbered its categories in 2018,
so a number-keyed reading would agree in one era and fail in the other.

No edition prints a count of members or declarations, so the edition's own
list of categories is the figure held against.

    compare(numbering)    {"agree": [...], "differ": [...], "unlisted": [...]} by edition and number
    python -m registers.mp_interests.check [--schema mp_interests] [--database querynz_v4] [--shared]
"""
import sys


def compare(numbering: list) -> dict:
    """numbering: dicts with as_at, number, intro_heading, intro_category, body_headings, body_category, agrees."""
    out = {"agree": [], "differ": [], "unlisted": []}
    for r in sorted(numbering, key=lambda r: (str(r["as_at"]), r["number"])):
        if not r["body_headings"]:
            continue
        if r["intro_heading"] is None:
            out["unlisted"].append(r)
        elif r["agrees"]:
            out["agree"].append(r)
        else:
            out["differ"].append(r)
    return out


def rows(conn, schema: str, shared: bool = False) -> list:
    pre = "mp_interests_" if shared else ""
    cur = conn.execute(f"SELECT e.as_at, n.number, n.intro_heading, n.intro_category, n.body_headings, n.body_category, "
                       f"n.agrees FROM {schema}.{pre}numbering n JOIN {schema}.{pre}editions e ON e.key = n.edition")
    return [dict(zip([d[0] for d in cur.description], r)) for r in cur]


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "mp_interests"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        out = compare(rows(conn, schema, "--shared" in argv))
    editions = {str(r["as_at"]) for k in out for r in out[k]}
    print(f"{len(editions)} editions; numbers filed under: {len(out['agree'])} agree with the edition's own list, "
          f"{len(out['differ'])} differ, {len(out['unlisted'])} not in its list")
    for r in out["differ"] + out["unlisted"]:
        print(f"  {r['as_at']} {r['number']}: the introduction says {r['intro_heading']!r} ({r['intro_category']}); "
              f"the returns print {r['body_headings']!r} ({r['body_category']})")
    return 1 if out["differ"] or out["unlisted"] else 0


if __name__ == "__main__":
    sys.exit(main())
