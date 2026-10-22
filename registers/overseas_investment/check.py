"""The lane's one figure against the outside world (contract: the lane).

The source's own count is the office's listing, year by year from 2017: its
pager states the last page on the first page of every pass, and the rows it
shows (60 a page, then the last page's) are the office's count of decision
rows for that year. Exit 1 on any of:

  1. a year from 2017 to this year with no finished pass
  2. a finished pass whose distinct rows differ from the rows its pages
     showed, or whose pages differ from the pager's statement (a row moved
     between pages while the pass ran, or the walk missed a page)
  3. a row it listed is not read: not captured yet, or set aside
  4. the reading does not reconcile (a listed row with no ledger line, a
     decision with no ledger line, a party with no decision, a private row
     with no decision, more private rows than decisions), or a view shows a withheld name or its origins,
     carries an address column, or a text value shaped like a street
     address (reported by key, never by value)

Every line printed is a count. Run bare it connects with the session reader,
which has no grant on `overseas_investment_private` (by design): the private
figures come from `read_statements`, the count the load writes beside its
ledger. The load and the gate's staging step run `reading` under the owner,
which also holds that count to the private table itself.

    python -m registers.overseas_investment.check [--database querynz_v4]
"""
import argparse
import json
import re
import sys

from registers.overseas_investment import capture, read

SCHEMA = "overseas_investment"
ADDRESSISH = ("address", "street", "postal", "residential", "home", "email", "phone", "suburb", "postcode")
VIEWS = ("overseas_investment_decisions", "overseas_investment_parties")
#: columns read for a house number before a street: the land's statement and the rationale (never a party's name,
#: where "VP 568 Limited" is a company)
HOUSE_COLUMNS = ("investment", "rationale")
SKIP = ("key", "decision_key", "document", "reader", "profile", "place", "url", "attribution")
_NUM = r"\d{1,4}[A-Za-z]?(?:\s*[-/]\s*\d{1,4}[A-Za-z]?)?"
_STREET = (r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Way|Parade|Highway|Hwy|"
           r"Grove|Close|Court|Ct|Rise|Quay|Square|Boulevard|Esplanade|Mews|Heights|Glade|Row|Promenade|Strand|Mall)")
_NOT_A_HOUSE = "".join(f"(?<!{re.escape(w)} )" for w in ("Highway", "Hwy", "SH", "No", "No.", "Act", "Regulations",
                                                         "Section", "Schedule", "Part", "Clause", "s", "ss", "RD"))
STREET = re.compile(rf"(?<![\w/.-]){_NOT_A_HOUSE}{_NUM},?\s+(?:[A-Z][\w'’.-]*\s+){{1,4}}{_STREET}\b"
                    rf"(?!\s+(?:Limited|Ltd|Incorporated|Inc)\b)")


def reading(conn, schema: str = SCHEMA, private: bool = True) -> list:
    """Problems in the reading under `schema`. `private=False` names no private table (the session reader's run)."""
    T = lambda t: capture.table(schema, t)
    out = []
    n = conn.execute(f"SELECT count(*) FROM {T('decisions')} d WHERE NOT EXISTS (SELECT 1 FROM {T('read_items')} r "
                     "WHERE r.slug = d.slug AND r.document = d.document AND r.state = 'read')").fetchone()[0]
    if n:
        out.append(f"{n} decision rows with no ledger line")
    read_n = conn.execute(f"SELECT count(DISTINCT slug) FROM {T('read_items')} WHERE state = 'read'").fetchone()[0]
    decisions = conn.execute(f"SELECT count(*) FROM {T('decisions')}").fetchone()[0]
    if read_n != decisions:
        out.append(f"{decisions} decision rows against {read_n} summary pages read in the ledger")
    said = conn.execute(f"SELECT coalesce(sum(parties), 0) FROM {T('read_items')}").fetchone()[0]
    parties = conn.execute(f"SELECT count(*) FROM {T('parties')}").fetchone()[0]
    if said != parties:
        out.append(f"{parties} party rows against {said} in the ledger")
    orphans = conn.execute(f"SELECT count(*) FROM {T('parties')} p WHERE NOT EXISTS (SELECT 1 FROM {T('decisions')} d "
                           "WHERE d.key = p.decision_key)").fetchone()[0]
    if orphans:
        out.append(f"{orphans} parties with no decision")
    there = conn.execute("SELECT to_regclass(%s)", (T("read_statements"),)).fetchone()[0] is not None
    counted = conn.execute(f"SELECT statements, stray FROM {T('read_statements')}").fetchall() if there else []
    if not there:
        out.append("the private statements' count is missing (no load since read_statements was added)")
    elif len(counted) != 1:
        out.append(f"{len(counted)} rows in the private statements' count (one expected)")
    else:
        statements, stray = counted[0]
        if stray:
            out.append(f"{stray} private statements with no decision")
        if statements > decisions:
            out.append(f"{statements} private statements against {decisions} decision rows")
        if private:
            held = conn.execute(f"SELECT count(*), count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM {T('decisions')} d "
                                f"WHERE d.key = i.key)) FROM {T('investments')} i").fetchone()
            if tuple(held) != (statements, stray):
                out.append(f"the private statements' count says {statements} ({stray} stray); the private table holds "
                           f"{held[0]} ({held[1]} stray)")
    leaked = conn.execute(f"SELECT count(*) FROM {T('parties')} WHERE withheld AND (name IS NOT NULL OR origins IS NOT NULL "
                          "OR trust IS NOT NULL OR status IS NOT NULL)").fetchone()[0]
    if leaked:
        out.append(f"{leaked} withheld parties keep a name or its origins in the table")
    return out


def views(conn, prefix: str = "pub.") -> list:
    out = []
    n = conn.execute(f"SELECT count(*) FROM {prefix}overseas_investment_parties WHERE withheld AND "
                     "(name <> 'name withheld' OR origins IS NOT NULL OR trust IS NOT NULL)").fetchone()[0]
    if n:
        out.append(f"{n} withheld parties show a name or its origins on the view")
    n = conn.execute(f"SELECT count(*) FROM {prefix}overseas_investment_decisions d WHERE d.applicant_listed IS NOT NULL "
                     f"AND EXISTS (SELECT 1 FROM {prefix}overseas_investment_parties p WHERE p.decision_key = d.key "
                     "AND p.role = 'applicant' AND p.withheld)").fetchone()[0]
    if n:
        out.append(f"{n} decisions show the listed applicant where the office withholds the name")
    schema, _, stem = prefix.rstrip(".").partition(".")
    schema = schema or "pub"
    for v in VIEWS:
        name = (stem + v) if stem else v
        cols = [r for r in conn.execute("SELECT column_name, data_type FROM information_schema.columns "
                                        "WHERE table_schema = %s AND table_name = %s", (schema, name))]
        if not cols:
            out.append(f"{v} is not there")
            continue
        extra = [c for c, _ in cols if any(w in c for w in ADDRESSISH) and c != "addresses_withheld"]
        if extra:
            out.append(f"{v} carries {', '.join(extra)}")
        for c, typ in cols:
            if typ not in ("text", "ARRAY") or c in SKIP:
                continue
            expr = f"array_to_string({c}, ' ; ')" if typ == "ARRAY" else c
            keys = []
            for k, val in conn.execute(f"SELECT key, {expr} FROM {schema}.{name}"):
                if not val:
                    continue
                if STREET.search(val) or (c in HOUSE_COLUMNS and (read.STREET.search(val) or read.LEGAL.search(val))):
                    keys.append(k)
            if keys:
                out.append(f"{v}.{c}: {len(keys)} values shaped like a street address (first key {keys[0]})")
    return out


def outside(conn, schema: str = SCHEMA) -> dict:
    T = lambda t: capture.table(schema, t)
    years, ok = {}, True
    for lst in capture.lists():
        r = conn.execute(f"SELECT pass_id, stated_pages, stated, pages, items FROM {T('capture_passes')} "
                         "WHERE list = %s AND finished_at IS NOT NULL ORDER BY pass_id DESC LIMIT 1", (lst.name,)).fetchone()
        if r is None:
            years[lst.year] = {"ok": False, "detail": "no finished pass"}
            ok = False
            continue
        pass_id, stated_pages, stated, pages, items = r
        states = dict(conn.execute(f"SELECT state, count(*) FROM {T('read_items')} WHERE pass_id = %s GROUP BY state",
                                   (pass_id,)).fetchall())
        y_ok = stated is not None and items == stated and pages == stated_pages and states.get("read", 0) == items
        ok = ok and y_ok
        years[lst.year] = {"ok": y_ok, "stated": stated, "listed": items, "pages": pages, "stated_pages": stated_pages,
                           "read": states.get("read", 0), "set_aside": states.get("set aside", 0),
                           "not_captured": states.get("not captured", 0)}
    total = sum(y.get("stated") or 0 for y in years.values())
    read_n = sum(y.get("read") or 0 for y in years.values())
    return {"ok": ok, "stated": total, "read": read_n, "years": years}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.overseas_investment.check")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('overseas_investment.read_items')").fetchone()[0] is None:
            print(f"{SCHEMA}: check: nothing published yet (no load has run)")
            return 1
        out = outside(conn)
        out["problems"] = reading(conn, private=False) + views(conn)
    print(f"{SCHEMA}: check: " + json.dumps(out, default=str))
    return 0 if out["ok"] and not out["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
