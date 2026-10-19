"""The lane's check against the world outside it (contract: the lane).

The register's own figure: the NZBN API's search for registered
incorporated societies by a name term, as it answered on 20 October 2026
(07:31 to 07:32 NZDT), landed by hash below. The search caps its total at
10,000, so it cannot count all 22,787 registered societies; it counts the
societies a term finds, by their current or a previous name. For each term:

  register        the register's own count of registered societies the term finds
  equal           of those, the lane's rows that are registered under the same NZBN
  other status    in the lane under another status (restored or changed since the file)
  after the file  not in the lane and registered after the file's cut: the file cannot hold them
  missing         not in the lane and registered before the cut: a lane fault
  unfound         the lane's registered societies whose current name has the term as a
                  word that the register's search did not return

The check fails when, for any term, `equal` is under AGREE of the register's
count less the societies registered after the cut, or `unfound` is over
UNFOUND of the lane's own count for the term. On 20 October 2026, against
the August file: party 18 of 18; hockey 189 of 189 (one registered in
September); tennis 430 of 431 (one restored since), 1 of 415 unfound.

    figures(conn, table)     the comparison, from the lane's rows and the landed answers
    failed(f)                the reasons the check fails, empty when it passes
    python -m registers.societies.check [--schema societies | scratch_<session>] [--database querynz_v4]

Read-only.
"""
import json
import re
import sys

from support.docstore.landing import read_bytes

AGREE = 0.99
UNFOUND = 0.01
#: term → the sha256 of each page of the register's answer
SEARCHES = {
    "party": ("e0d08b6ddc0fed895f6f752b650cd198a7915e638783a57ae7565a078e93b202",),
    "hockey": ("7a2d702ab9cc930dc54963cc81d85adf65e66b84d176565967de9288f0ee9983",),
    "tennis": ("e32306e94d6a7507a076d2915e078f7a99ba3d64c30fc29ae18ddc1c0529328c",
               "8c18461b4184ee5ebb12c34725c421a29e6eb1d0ca8afef900a5c3281958ad21",
               "919477c84cdaaa8e70c746b82c62d873b3a905b5f37a223ed16206734172d481"),
}


def register_items(term: str, read=read_bytes) -> tuple:
    """(the register's stated total, {nzbn: registration date})."""
    items, total = {}, None
    for sha in SEARCHES[term]:
        b = json.loads(read(sha))
        total = b["totalItems"]
        for it in b["items"]:
            items[it["nzbn"]] = (it.get("registrationDate") or "")[:10]
    if len(items) != total:
        raise AssertionError(f"societies check: the {term} answer states {total} and lists {len(items)}")
    return total, items


def compare(term: str, total: int, items: dict, lane: dict, cut: str) -> dict:
    """`lane`: nzbn → (name, status) for every society the lane holds in the latest file."""
    word = re.compile(rf"\b{re.escape(term)}\b", re.I)
    f = {"term": term, "register": total, "equal": 0, "other_status": 0, "after_the_file": 0, "missing": 0}
    for nzbn, registered in items.items():
        held = lane.get(nzbn)
        if held is None:
            f["after_the_file" if registered > cut else "missing"] += 1
        elif held[1] == "registered":
            f["equal"] += 1
        else:
            f["other_status"] += 1
    named = [n for n, (name, status) in lane.items() if status == "registered" and word.search(name)]
    f["lane_named"] = len(named)
    f["unfound"] = sum(1 for n in named if n not in items)
    return f


def figures(conn, table: str = "societies.societies", read=read_bytes) -> dict:
    lane = {r[0]: (r[1], r[2]) for r in conn.execute(
        f"SELECT nzbn, name, status FROM {table} WHERE in_latest AND nzbn IS NOT NULL")}
    cut = str(conn.execute(f"SELECT max(registered_on) FROM {table} WHERE in_latest").fetchone()[0])
    terms = []
    for term in SEARCHES:
        total, items = register_items(term, read)
        terms.append(compare(term, total, items, lane, cut))
    return {"cut": cut, "terms": terms}


def failed(f: dict) -> list:
    out = []
    for t in f["terms"]:
        base = t["register"] - t["after_the_file"]
        if base and t["equal"] < AGREE * base:
            out.append(f"{t['term']}: {t['equal']} of the register's {base} registered societies are registered "
                       f"in the lane, under {AGREE:.0%}")
        if t["missing"]:
            out.append(f"{t['term']}: {t['missing']} registered before the file's cut are not in the lane")
        if t["lane_named"] and t["unfound"] > UNFOUND * t["lane_named"]:
            out.append(f"{t['term']}: {t['unfound']} of the lane's {t['lane_named']} are not on the register's list")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "societies"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    shared = schema.startswith("scratch_")
    table = f"{schema}.societies_societies" if shared else f"{schema}.societies"
    with db.connect(db.READ_KEY, database) as conn:
        conn.execute("SET statement_timeout = '30s'")
        f = figures(conn, table)
    for t in f["terms"]:
        print(f"{t['term']}: register {t['register']}, equal {t['equal']}, other status {t['other_status']}, "
              f"after the file {t['after_the_file']}, missing {t['missing']}; lane {t['lane_named']}, "
              f"unfound {t['unfound']}")
    bad = failed(f)
    for b in bad:
        print("FAIL " + b)
    print(f"societies check (cut {f['cut']}): " + ("green" if not bad else "red"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
