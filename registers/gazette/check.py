"""The lane's check against the world outside it (contract: the lane).

The Gazette counts its own notices twice, and both counts are printed in the
notices themselves:

  numbering   every notice number is <year>-<section><n>, one sequence a year
              across every section, so the highest number held for a closed
              year is the Gazette's own count of notices that year (a floor:
              a number never captured cannot raise it)
  celebrants  the Registrar-General's lists are titled "Marriage Celebrants
              for <year> Notice No. <n>" and "Civil Union Celebrants for
              <year> Notice No. <n>": the highest <n> is the Gazette's own
              count of celebrant notices in that series and year

Against the second, the lane's rows: every numbered celebrant notice held
must be recognised as a celebrant list (format `gazette-celebrant-list`).
A held notice the lane did not recognise fails the check, and so does a
lane with no celebrant lists, or a year whose notices the lane holds and
does not publish. The gaps (numbers the Gazette printed and the old estate
never captured) are reported, never failed: they are the capture's limit,
not the reading's.

The old lane's gate recorded a failure and still exited 0. This one exits 1.

    figures(rows)       the two counts from [(notice, title, format)]
    failed(f)           the reasons the check fails, empty when it passes
    python -m registers.gazette.check [--schema gazette | scratch_<session>] [--database querynz_v4]

Read-only.
"""
import re
import sys
from collections import defaultdict

from registers.gazette import notices

CELEBRANT = "gazette-celebrant-list"
SERIES = re.compile(r"^\s*(Marriage|Civil Union) Celebrants? for (\d{4})\s+Notice No\.?\s*(\d+)", re.I)
CLOSED_FROM, CLOSED_TO = 2000, 2025


def figures(rows) -> dict:
    """rows: [(notice, title, format)] from the lane's published notices."""
    by_year = defaultdict(set)
    series = defaultdict(dict)                      # (series, year) → {printed number: (notice, format)}
    for notice, title, fmt in rows:
        num = notices.number(notice)
        if num:
            by_year[num[0]].add(num[2])
        m = SERIES.match(title or "")
        if m:
            series[(m.group(1).title(), int(m.group(2)))][int(m.group(3))] = (notice, fmt)
    numbering = {y: (max(ns), len(ns)) for y, ns in sorted(by_year.items())}
    cel = {}
    for k, held in sorted(series.items()):
        cel[k] = {"printed": max(held), "held": len(held),
                  "recognised": sum(1 for n, f in held.values() if f == CELEBRANT),
                  "not_recognised": sorted(n for n, f in held.values() if f != CELEBRANT)}
    return {"numbering": numbering, "celebrants": cel}


def failed(f: dict) -> list:
    why = []
    if not f["celebrants"]:
        why.append("no numbered celebrant notice is published: the lane read nothing it can be checked on")
    for (s, y), c in f["celebrants"].items():
        for n in c["not_recognised"]:
            why.append(f"{s} celebrants {y}: notice {n} is held and the lane did not read it as a celebrant list")
    years = set(f["numbering"])
    for y in range(CLOSED_FROM, CLOSED_TO + 1):
        if y not in years:
            why.append(f"{y}: the lane publishes no notice for a closed year")
    return why


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "gazette"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    from registers.gazette.load import table
    with db.connect(db.READ_KEY if database == "querynz_v4" else db.OWNER_KEY, database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        # the sample's shared schema names the lane's tables `gazette_…`; a lane or staging schema does not
        shared = conn.execute("SELECT to_regclass(%s) IS NOT NULL", (table(schema, "notices", True),)).fetchone()[0]
        rows = conn.execute(f"SELECT notice, title, format FROM {table(schema, 'notices', shared)}").fetchall()
    f = figures(rows)
    print(f"{len(rows)} notices published. The Gazette's own numbering, closed years "
          f"({CLOSED_FROM}-{CLOSED_TO}): highest number against numbers held")
    for y, (top, held) in f["numbering"].items():
        if CLOSED_FROM <= y <= CLOSED_TO:
            print(f"  {y}: {held:,} of {top:,} ({100 * held / top:.1f}%)")
    print("Celebrant notices, the Gazette's own 'Notice No.' against held and read as celebrant lists:")
    for (s, y), c in f["celebrants"].items():
        print(f"  {s} {y}: printed to No. {c['printed']}, held {c['held']}, read {c['recognised']}"
              + (f", {c['printed'] - c['held']} never captured" if c["printed"] > c["held"] else ""))
    why = failed(f)
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
