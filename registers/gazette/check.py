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

The prohibitions are checked on the Gazette's own words twice: every held
notice the Gazette titles "Notice Prohibiting Person…" must be read as a
prohibition, and every notice a revocation, substitution or variation names
by its number must be held and read as one (its rows then carry what
superseded them).

The old lane's gate recorded a failure and still exited 0. This one exits 1.

    figures(rows, acted, marked)  the counts from [(notice, title, format)],
                        [(notice, supersedes)] and the notices whose rows say what superseded them
    failed(f)           the reasons the check fails, empty when it passes
    python -m registers.gazette.check [--schema gazette | scratch_<session>] [--database querynz_v4]

Read-only.
"""
import re
import sys
from collections import defaultdict

from registers.gazette import notices

CELEBRANT = "gazette-celebrant-list"
PROHIBITION = "gazette-director-prohibition"
LIQUIDATION = "gazette-liquidator-appointment"
PROHIBITION_TITLE = re.compile(r"^\s*Notice\s+Prohibiting\s+(?:a\s+)?Persons?\b", re.I)
SERIES = re.compile(r"^\s*(Marriage|Civil Union) Celebrants? for (\d{4})\s+Notice No\.?\s*(\d+)", re.I)
CLOSED_FROM, CLOSED_TO = 2000, 2025


def figures(rows, acted=(), marked=()) -> dict:
    """rows: [(notice, title, format)] from the lane's published notices;
    acted: [(notice, supersedes)] for the notices that act on others; marked:
    the notices whose prohibition rows carry what superseded them."""
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
    fmt = {n: f for n, t, f in rows}
    titled = sorted(n for n, t, f in rows if PROHIBITION_TITLE.match(t or ""))
    named = {}
    for n, supersedes in acted:
        for t in (supersedes or "").split(", "):
            if t:
                named[t] = (n, fmt.get(t))
    pro = {"titled": len(titled), "titled_not_read": [n for n in titled if fmt[n] != PROHIBITION],
           "read": sum(1 for f in fmt.values() if f == PROHIBITION), "named": named,
           "named_not_held_or_read": sorted(t for t, (n, f) in named.items() if f != PROHIBITION),
           "named_not_marked": sorted(t for t in named if t not in set(marked))}
    al = [(n, f) for n, t, f in rows if (notices.number(n) or (0, ""))[1] == "al"]
    liq = {"filed": len(al), "not_read": sorted(n for n, f in al if f != LIQUIDATION)}
    return {"numbering": numbering, "celebrants": cel, "prohibitions": pro, "liquidations": liq}


def failed(f: dict) -> list:
    why = []
    if not f["celebrants"]:
        why.append("no numbered celebrant notice is published: the lane read nothing it can be checked on")
    for (s, y), c in f["celebrants"].items():
        for n in c["not_recognised"]:
            why.append(f"{s} celebrants {y}: notice {n} is held and the lane did not read it as a celebrant list")
    p = f.get("prohibitions")
    if p is not None:
        if not p["read"]:
            why.append("no prohibition notice is read")
        for n in p["titled_not_read"]:
            why.append(f"{n}: titled a prohibition by the Gazette and not read as one")
        for t in p["named_not_held_or_read"]:
            why.append(f"{t}: named by {p['named'][t][0]} as the notice it acts on, and not held or not read")
        for t in p["named_not_marked"]:
            why.append(f"{t}: acted on by {p['named'][t][0]}, and its rows do not say so")
    q = f.get("liquidations")
    if q is not None:
        if not q["filed"]:
            why.append("no notice under section al is published")
        for n in q["not_read"][:20]:
            why.append(f"{n}: filed by the Gazette under al and not read as a liquidator's appointment")
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
        acted = conn.execute(f"SELECT notice, supersedes FROM {table(schema, 'notices', shared)} WHERE supersedes IS NOT NULL").fetchall()
        marked = [n for (n,) in conn.execute(
            f"SELECT DISTINCT notice FROM {table(schema, 'prohibitions', shared)} WHERE superseded_by IS NOT NULL")]
    f = figures(rows, acted, marked)
    print(f"{len(rows)} notices published. The Gazette's own numbering, closed years "
          f"({CLOSED_FROM}-{CLOSED_TO}): highest number against numbers held")
    for y, (top, held) in f["numbering"].items():
        if CLOSED_FROM <= y <= CLOSED_TO:
            print(f"  {y}: {held:,} of {top:,} ({100 * held / top:.1f}%)")
    print("Celebrant notices, the Gazette's own 'Notice No.' against held and read as celebrant lists:")
    for (s, y), c in f["celebrants"].items():
        print(f"  {s} {y}: printed to No. {c['printed']}, held {c['held']}, read {c['recognised']}"
              + (f", {c['printed'] - c['held']} never captured" if c["printed"] > c["held"] else ""))
    p = f["prohibitions"]
    print(f"Prohibitions: {p['titled']:,} notices the Gazette titles 'Notice Prohibiting Person', "
          f"{p['titled'] - len(p['titled_not_read']):,} read as such; {p['read']:,} read in all; "
          f"{len(p['named'])} named by number by a later notice, "
          f"{len(p['named']) - len(p['named_not_held_or_read'])} held and read")
    q = f["liquidations"]
    print(f"Liquidator's appointments: {q['filed']:,} notices the Gazette files under al, "
          f"{q['filed'] - len(q['not_read']):,} taken by its profile (read, or set aside with a reason)")
    why = failed(f)
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
