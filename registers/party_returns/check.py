"""The lane's one check against the outside world (contract: the lane).

Until the Commission's own listing is fetched by a lane of its own, the
outside figure is the one the frozen site shows for each party and year:
the current release's `data/home.json` in the live old folder, where every
front-page party carries a series with `basis: declared` and the total it
read. Plan 1.11's test is this comparison: for every return this lane
read, the declared total equals the frozen site's figure for that party
and year, or the difference has a card.

    frozen_series()            (registered party, year) → (total, source file)
    compare(rows, frozen)      {"equal": [...], "differ": [...], "unmatched": [...], "other_returns": [...]}
    python -m registers.party_returns.check [--schema party_returns] [--database querynz_v4]

Read-only. The frozen site chose one return per party-year, so where this
lane holds several (an original and its amendment) a party-year is equal
when one of them carries the figure, and the others are listed as
`other_returns`, not as differences.
"""
import json
import os
import sys

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
HOME_JSON = os.path.join(OLD_LIVE, "var", "pi-snapshot", "current", "data", "home.json")
TOLERANCE = 0.011


def frozen_series(path: str = None) -> dict:
    path = path or HOME_JSON
    with open(path, encoding="utf-8") as f:
        home = json.load(f)
    out = {}
    for p in home.get("parties", []):
        for s in p.get("window", {}).get("series", []):
            if s.get("basis") == "declared" and s.get("total") is not None:
                out[(p["party"], int(s["year"]))] = (float(s["total"]), s.get("source_file"))
    return out


def compare(rows: list, frozen: dict) -> dict:
    """rows: dicts with party, party_label, year, declared_total, document."""
    by_py = {}
    for r in rows:
        by_py.setdefault((r.get("party"), int(r["year"])), []).append(r)
    equal, differ, unmatched, other = [], [], [], []
    for (party, year), ours in sorted(by_py.items(), key=lambda kv: (kv[0][0] or "", kv[0][1])):
        if party is None or (party, year) not in frozen:
            unmatched += [{"party": party, "party_label": r.get("party_label"), "year": year,
                           "ours": float(r["declared_total"]), "document": r["document"]} for r in ours]
            continue
        total, source = frozen[(party, year)]
        hits = [r for r in ours if abs(float(r["declared_total"]) - total) <= TOLERANCE]
        rest = [r for r in ours if r not in hits]
        if hits:
            equal.append({"party": party, "year": year, "total": total, "document": hits[0]["document"], "frozen_file": source})
            other += [{"party": party, "year": year, "ours": float(r["declared_total"]), "frozen": total,
                       "document": r["document"]} for r in rest]
        else:
            differ += [{"party": party, "year": year, "ours": float(r["declared_total"]), "frozen": total,
                        "document": r["document"], "frozen_file": source} for r in ours]
    return {"equal": equal, "differ": differ, "unmatched": unmatched, "other_returns": other}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "party_returns"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        cur = conn.execute(f"SELECT party, party_label, year, declared_total, document FROM {schema}.returns")
        rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
    out = compare(rows, frozen_series())
    for k in ("equal", "differ", "unmatched", "other_returns"):
        print(f"{k}: {len(out[k])}")
    for d in out["differ"]:
        print(f"  DIFFERS {d['party']} {d['year']}: ours {d['ours']:.2f}, frozen {d['frozen']:.2f}, document {d['document']}")
    for u in out["unmatched"]:
        print(f"  not on the frozen site: {u['party'] or u['party_label']!r} {u['year']} {u['ours']:.2f} {u['document'][:12]}")
    return 1 if out["differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
