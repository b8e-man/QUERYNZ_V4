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

The liquidations are checked against the Companies Office register (the
companies lane's `pub.companies`, joined at load by register.py): a share
of the company rows the register holds, and of the printed company numbers
whose register name agrees, below its floor fails, and so does a load that
did not join the register at all. The rows the register does not hold are
catch-log lines and are counted here, never failed one by one: the
register's own gaps (a company renamed after its liquidation, a name it
never held) are not the reading's.

The old lane's gate recorded a failure and still exited 0. This one exits 1.

    figures(rows, acted, marked, joined)  the counts from [(notice, title, format)],
                        [(notice, supersedes)], the notices whose rows say what superseded them,
                        and {register_match: rows} over the liquidation rows
    failed(f)           the reasons the check fails, empty when it passes
    python -m registers.gazette.check [--schema gazette | scratch_<session>] [--database querynz_v4]

Read-only.
"""
import re
import sys
from collections import defaultdict

from registers.gazette import notices
from registers.gazette import register as R

CELEBRANT = "gazette-celebrant-list"
PROHIBITION = "gazette-director-prohibition"
LIQUIDATION = "gazette-liquidator-appointment"
PROHIBITION_TITLE = re.compile(r"^\s*Notice\s+Prohibiting\s+(?:a\s+)?Persons?\b", re.I)
SERIES = re.compile(r"^\s*(Marriage|Civil Union) Celebrants? for (\d{4})\s+Notice No\.?\s*(\d+)", re.I)
CLOSED_FROM, CLOSED_TO = 2000, 2025
#: measured 20 October 2026 on every row: 98.1% joined, 98.8% of held printed numbers agreeing by name
JOINED_FLOOR, NUMBER_FLOOR = 0.97, 0.98
#: the company-notice profiles: the Gazette's section, the profile every notice in it must be taken by, and the
#: floor of its company rows the register must hold (measured 20 October 2026: removals 96.7%, applications 96.0%,
#: receiverships 90.9%: a company sold out of receivership is often renamed, and the register holds the latest name)
COMPANY = {"removal": ("ds", "gazette-removal-notice", 0.95),
           "winding-up application": ("aw", "gazette-winding-up-application", 0.95),
           "receivership": ("ar", "gazette-receivership", 0.88)}
#: every notice in section ba is taken by one of these
BANKRUPTCY = ("gazette-bankruptcy-list", "gazette-no-asset-procedure-list", "gazette-bankruptcy-notice")


def _register(joined: dict) -> dict:
    total = sum(joined.values())
    numbered = joined.get(R.NUMBER, 0) + joined.get(R.NUMBER_NAME_DIFFERS, 0)
    return {"rows": total, "by": dict(joined), "not_joined": joined.get(None, 0),
            "joined": sum(v for k, v in joined.items() if k and k not in R.UNMATCHED),
            "numbered": numbered, "number_agrees": joined.get(R.NUMBER, 0)}


def _register_fails(what: str, r: dict, floor: float, number_floor: float = None) -> list:
    if r["not_joined"] or not r["rows"]:
        return [f"{r['not_joined']:,} {what} rows were never joined to the companies register (not in the database at load)"]
    why = []
    if r["joined"] < floor * r["rows"]:
        why.append(f"the companies register holds {r['joined']:,} of {r['rows']:,} {what} companies, below {floor:.0%}")
    if number_floor and r["numbered"] and r["number_agrees"] < number_floor * r["numbered"]:
        why.append(f"{r['number_agrees']:,} of {r['numbered']:,} printed company numbers carry the register's name, below {number_floor:.0%}")
    return why


def figures(rows, acted=(), marked=(), joined=None, company_joined=None, annulled_shown=0) -> dict:
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
    if joined is not None:
        liq["register"] = _register(joined)
    company = {}
    for kind, (code, profile, floor) in COMPANY.items():
        filed = [(n, f) for n, t, f in rows if (notices.number(n) or (0, ""))[1] == code]
        company[kind] = {"code": code, "filed": len(filed), "not_read": sorted(n for n, f in filed if f != profile)}
        if company_joined is not None:
            company[kind]["register"] = _register(company_joined.get(kind, {}))
    ba = [(n, f) for n, t, f in rows if (notices.number(n) or (0, ""))[1] == "ba"]
    bank = {"filed": len(ba), "by": {p: sum(1 for n, f in ba if f == p) for p in BANKRUPTCY},
            "not_read": sorted(n for n, f in ba if f not in BANKRUPTCY), "annulled_shown": annulled_shown}
    return {"numbering": numbering, "celebrants": cel, "prohibitions": pro, "liquidations": liq, "company": company,
            "bankruptcies": bank}


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
        if q.get("register") is not None:
            why += _register_fails("liquidation", q["register"], JOINED_FLOOR, NUMBER_FLOOR)
    for kind, c in f.get("company", {}).items():
        if not c["filed"]:
            why.append(f"no notice under section {c['code']} is published")
        for n in c["not_read"][:20]:
            why.append(f"{n}: filed by the Gazette under {c['code']} and not taken by the {kind} profile")
        if c.get("register") is not None:
            why += _register_fails(kind, c["register"], COMPANY[kind][2])
    b = f.get("bankruptcies")
    if b is not None:
        if not b["filed"]:
            why.append("no notice under section ba is published")
        for n in b["not_read"][:20]:
            why.append(f"{n}: filed by the Gazette under ba and not taken by a bankruptcy profile")
        if b["annulled_shown"]:
            why.append(f"{b['annulled_shown']} people an annulment names are published by name")
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
        joined = dict(conn.execute(f"SELECT register_match, count(*) FROM {table(schema, 'liquidations', shared)} GROUP BY 1").fetchall())
        company_joined = defaultdict(dict)
        for kind, match, n in conn.execute(
                f"SELECT kind, register_match, count(*) FROM {table(schema, 'company_notices', shared)} GROUP BY 1, 2"):
            company_joined[kind][match] = n
        annulled_shown = conn.execute(f"SELECT count(*) FROM {table(schema, 'bankruptcies', shared)} "
                                      f"WHERE kind = 'annulment' AND withheld_by IS NULL").fetchone()[0]
    f = figures(rows, acted, marked, joined, company_joined, annulled_shown)
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
    for what, c in [("liquidation", q)] + list(f["company"].items()):
        if what != "liquidation":
            print(f"{what.capitalize()}s: {c['filed']:,} notices the Gazette files under {c['code']}, "
                  f"{c['filed'] - len(c['not_read']):,} taken by its profile (read, or set aside with a reason)")
        r = c.get("register")
        if r and r["rows"]:
            print(f"  against the companies register: {r['joined']:,} of {r['rows']:,} company rows joined "
                  f"({100 * r['joined'] / r['rows']:.1f}%); {r['number_agrees']:,} of {r['numbered']:,} held printed numbers agree by name")
            for k, v in sorted(r["by"].items(), key=lambda kv: -kv[1]):
                print(f"    {k or 'not joined'}: {v:,}")
    b = f["bankruptcies"]
    print(f"Bankruptcies: {b['filed']:,} notices the Gazette files under ba, "
          f"{b['filed'] - len(b['not_read']):,} taken by a profile ("
          + ", ".join(f"{p.split('gazette-')[1]} {v:,}" for p, v in b["by"].items()) + ")")
    why = failed(f)
    for w in why:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
