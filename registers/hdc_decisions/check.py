"""The lane's one figure against the outside world (contract: the lane).

The source's own count is the Commissioner's listing: each year's decisions
(`?filter-year=Y`) state "Page 1 of N", twelve to a page, so a year holds
12 × (N − 1) plus the tiles of page N; the case studies are one page. Exit 1
on any of:

  1. a listing from 2017 to this year, or the case studies, has no finished pass
  2. a finished pass walked fewer or more pages than its first page stated, or
     a page before the last carried fewer than twelve tiles (the count would
     be short)
  3. an entry it listed (dated from 2017) is not read: not captured yet, or
     set aside
  4. the reading does not reconcile (a ledger line with no row, a row with no
     ledger line, a provider with no decision), or a view carries an address
     column, a heading or title column, a value that describes a consumer
     (`read.consumer_detail`), a provider or a role shaped like a person's
     name, or a case study's own address (reported by key and field, never by
     value)

Every line printed is a count. Held: red while nothing is published (a lane
fed by nothing is not green).

    python -m registers.hdc_decisions.check [--database querynz_v4]
"""
import argparse
import datetime as dt
import json
import sys

from registers.hdc_decisions import capture, read

SCHEMA = "hdc_decisions"
ADDRESSISH = ("address", "street", "postal", "residential", "home", "email", "phone", "suburb", "postcode")
NO_SUCH_COLUMN = ("title", "heading", "summary", "consumer", "complainant", "age", "condition")
VIEWS = ("hdc_decisions", "hdc_decision_providers")
#: columns whose values are the page's own identifiers or our citation, not text read from the page
NOT_TEXT = ("key", "decision_key", "document", "reader", "profile", "place", "url", "web_id", "case_number",
            "case_numbers", "kind_of_page", "found_by", "company_number", "charity_number")
#: columns that may carry a provider's own name (a place in it is the provider), or the Commissioner's own classification
#: ("Disability Services Provider"): held to the narrower guard (no letter label, age or relation)
NAMES = ("name", "abbreviation", "also_called", "recommended_to", "findings", "provider_kinds", "occupations")


def reading(conn, schema: str = SCHEMA) -> list:
    T = lambda t: capture.table(schema, t)
    out = []
    n = conn.execute(f"SELECT count(*) FROM {T('decisions')} d WHERE NOT EXISTS (SELECT 1 FROM {T('read_items')} r "
                     "WHERE r.document = d.document AND r.state = 'read')").fetchone()[0]
    if n:
        out.append(f"{n} decision rows with no ledger line")
    read_n = conn.execute(f"SELECT count(*) FROM {T('read_items')} WHERE state = 'read'").fetchone()[0]
    rows = conn.execute(f"SELECT count(*) FROM {T('decisions')}").fetchone()[0]
    if read_n != rows:
        out.append(f"{rows} decision rows against {read_n} pages read in the ledger")
    said = conn.execute(f"SELECT coalesce(sum(providers), 0) FROM {T('read_items')}").fetchone()[0]
    providers = conn.execute(f"SELECT count(*) FROM {T('providers')}").fetchone()[0]
    if said != providers:
        out.append(f"{providers} provider rows against {said} in the ledger")
    orphans = conn.execute(f"SELECT count(*) FROM {T('providers')} p WHERE NOT EXISTS (SELECT 1 FROM {T('decisions')} d "
                           "WHERE d.key = p.decision_key)").fetchone()[0]
    if orphans:
        out.append(f"{orphans} providers with no decision")
    old = conn.execute(f"SELECT count(*) FROM {T('decisions')} WHERE decided_on < %s", (read.SINCE,)).fetchone()[0]
    if old:
        out.append(f"{old} decisions dated before 2017 (ruling 71)")
    return out


def views(conn, prefix: str = "pub.") -> list:
    out = []
    schema, _, stem = prefix.rstrip(".").partition(".")
    schema = schema or "pub"
    for v in VIEWS:
        name = (stem + v) if stem else v
        cols = [r for r in conn.execute("SELECT column_name, data_type FROM information_schema.columns "
                                        "WHERE table_schema = %s AND table_name = %s", (schema, name))]
        if not cols:
            out.append(f"{v} is not there")
            continue
        extra = [c for c, _ in cols if any(w in c for w in ADDRESSISH) or c in NO_SUCH_COLUMN]
        if extra:
            out.append(f"{v} carries {', '.join(extra)}")
        for c, typ in cols:
            if typ not in ("text", "ARRAY") or c in NOT_TEXT:
                continue
            field = "name" if c in NAMES else c
            hits = []
            for key, value in conn.execute(f"SELECT key, {c} FROM {schema}.{name}"):
                for x in (value or []) if typ == "ARRAY" else [value]:
                    if x and read.consumer_detail(str(x), field):
                        hits.append(key)
                        break
                    if x and c in ("name", "named_roles", "abbreviation") and read.PERSON.match(str(x)):
                        hits.append(key)
                        break
            if hits:
                out.append(f"{v}.{c}: {len(hits)} values describe a consumer or name a person (first key {hits[0]})")
    n = conn.execute(f"SELECT count(*) FROM {schema}.{stem}hdc_decisions WHERE kind_of_page = 'case study' "
                     "AND url IS NOT NULL").fetchone()[0]
    if n:
        out.append(f"{n} case studies show their own address (it is their summary)")
    return out


def outside(conn, schema: str = SCHEMA, today: dt.date = None) -> dict:
    T = lambda t: capture.table(schema, t)
    per, ok, missing = {}, True, []
    for lst in capture.all_lists(today):
        r = conn.execute(f"SELECT pass_id, stated, pages, items FROM {T('capture_passes')} WHERE list = %s AND "
                         "finished_at IS NOT NULL ORDER BY finished_at DESC LIMIT 1", (lst.name,)).fetchone()
        if r is None:
            missing.append(lst.name)
            ok = False
            continue
        pass_id, stated, pages, items = r
        short = conn.execute(f"SELECT count(*) FROM {T('capture_pages')} WHERE pass_id = %s AND page_no < %s AND items < %s",
                             (pass_id, stated or 1, read.PER_PAGE)).fetchone()[0] if lst.kind == "decision" else 0
        states = dict(conn.execute(f"SELECT state, count(*) FROM {T('read_items')} WHERE pass_id = %s GROUP BY state",
                                   (pass_id,)).fetchall())
        windowed = conn.execute(f"SELECT count(*) FROM {T('capture_listed')} WHERE pass_id = %s AND "
                                "(listed_on IS NULL OR listed_on >= %s)", (pass_id, read.SINCE)).fetchone()[0]
        good = (stated is not None and pages == stated and not short and states.get("read", 0) == windowed)
        ok = ok and good
        per[lst.name] = {"pages_stated": stated, "pages": pages, "listed": items, "from_2017": windowed,
                         "read": states.get("read", 0), "set_aside": states.get("set aside", 0),
                         "not_captured": states.get("not captured", 0), "short_pages": short, "ok": good}
    total = sum(x["from_2017"] for x in per.values())
    return {"ok": ok and not missing, "missing": missing, "listed_from_2017": total,
            "read": sum(x["read"] for x in per.values()), "lists": per}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.hdc_decisions.check")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('hdc_decisions.read_items')").fetchone()[0] is None:
            why = "held: nothing published (the Commissioner's written permission is not on file)" \
                if not capture.authorisation() else "nothing published yet (no load has run)"
            print(f"{SCHEMA}: check: {why}")
            return 1
        out = outside(conn)
        out["problems"] = reading(conn) + views(conn)
    print(f"{SCHEMA}: check: " + json.dumps(out, default=str))
    return 0 if out["ok"] and not out["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
