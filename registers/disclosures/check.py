"""The lane's checks against the world outside it (contract: the lane).

1. The frozen site. Its current release's `data/home.json` carries, for
   every party, the large donations it shows by year (`disclosed_by_year`,
   bucketed by the day the party received the gift) and their count
   (`disclosed_n`). Every party-year the frozen site shows is compared with
   the declarations this lane holds from the Commission's table for the
   same party and year; a difference is a card, never a silent fix. The
   frozen site reads only the 2023 regime, so the earlier regimes are
   counted apart, not compared.
2. The form's own total (tranche 2): the Commission prints the amount
   twice, in its table and on the scanned declaration; where a reading of
   the scan is held, the two are compared.

    frozen()                       ({(party, year): total}, {party: count})
    compare(rows, frozen_by_year, frozen_n)
    python -m registers.disclosures.check [--schema disclosures] [--database querynz_v4]

Read-only.
"""
import json
import os
import sys

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
HOME_JSON = os.path.join(OLD_LIVE, "var", "pi-snapshot", "current", "data", "home.json")
COMPARED = "over-20000-from-2023"
TOLERANCE = 0.005


def frozen(path: str = None) -> tuple:
    with open(path or HOME_JSON, encoding="utf-8") as f:
        home = json.load(f)
    by_year, n = {}, {}
    for p in home.get("parties", []):
        for y, v in (p.get("disclosed_by_year") or {}).items():
            by_year[(p["party"], int(y))] = float(v)
        if p.get("disclosed_n"):
            n[p["party"]] = int(p["disclosed_n"])
    return by_year, n


def compare(rows: list, frozen_by_year: dict, frozen_n: dict) -> dict:
    """rows: dicts with party, party_label, regime, amount, given_on."""
    ours, count, earlier, unresolved = {}, {}, 0, {}
    for r in rows:
        if r["regime"] != COMPARED:
            earlier += 1
            continue
        if not r.get("party"):
            unresolved[r["party_label"]] = unresolved.get(r["party_label"], 0) + 1
            continue
        k = (r["party"], int(str(r["given_on"])[:4]))
        ours[k] = round(ours.get(k, 0.0) + float(r["amount"]), 2)
        count[r["party"]] = count.get(r["party"], 0) + 1
    equal, differ = [], []
    for k in sorted(set(ours) | set(frozen_by_year)):
        a, b = ours.get(k, 0.0), frozen_by_year.get(k, 0.0)
        (equal if abs(a - b) <= TOLERANCE else differ).append({"party": k[0], "year": k[1], "ours": a, "frozen": b})
    counts = [{"party": p, "ours": count.get(p, 0), "frozen": frozen_n.get(p, 0)}
              for p in sorted(set(count) | set(frozen_n)) if count.get(p, 0) != frozen_n.get(p, 0)]
    return {"equal": equal, "differ": differ, "count_differs": counts, "earlier_regimes": earlier,
            "unresolved_parties": unresolved}


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "disclosures"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        cur = conn.execute(f"SELECT party, party_label, regime, amount, given_on FROM {schema}.declarations")
        rows = [dict(zip([d[0] for d in cur.description], r)) for r in cur]
    out = compare(rows, *frozen())
    print(f"equal: {len(out['equal'])} party-years; differ: {len(out['differ'])}; "
          f"earlier regimes held, not on the frozen site: {out['earlier_regimes']}")
    for d in out["differ"]:
        print(f"  DIFFERS {d['party']} {d['year']}: ours {d['ours']:.2f}, frozen {d['frozen']:.2f}")
    for c in out["count_differs"]:
        print(f"  count {c['party']}: ours {c['ours']}, frozen {c['frozen']}")
    for label, n in sorted(out["unresolved_parties"].items()):
        print(f"  not a registered party in keys.parties: {label!r} ({n})")
    return 1 if out["differ"] else 0


if __name__ == "__main__":
    sys.exit(main())
