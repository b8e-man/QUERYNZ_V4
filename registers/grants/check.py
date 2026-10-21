"""The lane's figures against the outside world (contract: the lane).

Neither publisher states a count of its grants beside them, so the outside
figures are the documents' own: exit 1 on any of

  1. nothing read: no national file, or no record of grants
  2. the national file's records counted afresh from its bytes (lines that
     open a record, by a reader that is not the lane's) differ from the
     records read; every record is a grant or a catch-log line
  3. a society on the Department's own list (granted.govt.nz, 21 October
     2026: 31 societies) has no grant in the Department's own file
  4. a record of grants that prints a total whose rows do not sum to it
  5. the reading does not reconcile (a grant with no ledger line, a recipient
     whose grants do not count up, a grantor with no publisher row), or a
     view carries an address column, a text value shaped like a street
     address (reported by key, never by value), or a row with no licence or
     attribution
  6. the national file's newest decision is more than 15 months old (the
     Department updates it once a year)

Every line printed is a count.

    python -m registers.grants.check [--database querynz_v4]
"""
import argparse
import datetime as dt
import json
import re
import sys

from registers.grants import capture, read

SCHEMA = "grants"
ADDRESSISH = ("address", "street", "postal", "residential", "home", "email", "phone", "suburb", "postcode")
VIEWS = ("grants", "grant_recipients", "grant_publishers")
STALE_MONTHS = 15
_NUM = r"\d{1,4}[A-Za-z]?(?:\s*[-/]\s*\d{1,4}[A-Za-z]?)?"
_STREET = (r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Way|Parade|Highway|Hwy|"
           r"Grove|Close|Court|Ct|Rise|Quay|Square|Boulevard|Esplanade|Mews|Heights|Glade|Row|Promenade|Strand|Mall)")
_NOT_A_HOUSE = "".join(f"(?<!{re.escape(w)} )" for w in ("Highway", "Hwy", "SH", "No", "No.", "Act", "Section", "s"))
STREET = re.compile(rf"(?<![\w/.-]){_NOT_A_HOUSE}{_NUM},?\s+(?:[A-Z][\w'’.-]*\s+){{1,4}}{_STREET}\b"
                    rf"(?!\s+(?:Limited|Ltd|Incorporated|Inc|Trust|Club|School|Kindergarten|Church|Hall)\b)")


def records_in_bytes(data: bytes) -> int:
    """The CSV's records, counted without the lane's reader: newlines outside quotes, less the header."""
    n, quoted = 0, False
    for b in data:
        if b == 0x22:
            quoted = not quoted
        elif b == 0x0A and not quoted:
            n += 1
    if data and not data.endswith(b"\n"):
        n += 1
    return n - 1


def total_of(stated: str):
    m = re.search(r"\$?\s*([\d,]+(?:\.\d{2})?)", stated or "")
    return float(m.group(1).replace(",", "")) if m else None


def reading(conn, schema: str = SCHEMA) -> list:
    T = lambda t: capture.table(schema, t)
    out = []
    one = lambda q: conn.execute(q).fetchone()[0]
    said = one(f"SELECT coalesce(sum(grants), 0) FROM {T('read_documents')}")
    rows = one(f"SELECT count(*) FROM {T('grants')}")
    if said != rows:
        out.append(f"{rows} grant rows against {said} in the ledger")
    n = one(f"SELECT count(*) FROM {T('read_documents')} WHERE records <> grants + set_aside")
    if n:
        out.append(f"{n} documents whose records are not grants plus set aside")
    n = one(f"SELECT count(*) FROM {T('grants')} g WHERE NOT EXISTS (SELECT 1 FROM {T('read_documents')} d "
            "WHERE d.document = g.document)")
    if n:
        out.append(f"{n} grants with no ledger line")
    n = one(f"SELECT coalesce(sum(grants), 0) FROM {T('recipients')}")
    if n != rows:
        out.append(f"recipients count {n} grants against {rows} grant rows")
    n = one(f"SELECT count(*) FROM {T('grants')} g WHERE NOT EXISTS (SELECT 1 FROM {T('recipients')} r "
            "WHERE r.key = g.recipient_key)")
    if n:
        out.append(f"{n} grants with no recipient row")
    n = one(f"SELECT count(*) FROM {T('grants')} g WHERE NOT EXISTS (SELECT 1 FROM {T('publishers')} p "
            "WHERE p.key = g.grantor_key) OR NOT EXISTS (SELECT 1 FROM {0} p WHERE p.key = g.publisher_key)"
            .format(T('publishers')))
    if n:
        out.append(f"{n} grants whose grantor or publisher has no publisher row")
    n = one(f"SELECT count(*) FROM {T('grants')} WHERE amount_nzd IS NOT NULL AND status <> 'Accepted'")
    if n:
        out.append(f"{n} grants not accepted carry an amount granted")
    n = one(f"SELECT count(*) FROM {T('grants')} WHERE period < '{read.WINDOW_FROM}'")
    if n:
        out.append(f"{n} grants before {read.WINDOW_FROM} (ruling 71)")
    return out


def views(conn, prefix: str = "pub.") -> list:
    out = []
    schema, _, stem = prefix.rstrip(".").partition(".")
    schema = schema or "pub"
    for v in VIEWS:
        name = (stem + v) if stem else v
        cols = list(conn.execute("SELECT column_name, data_type FROM information_schema.columns "
                                 "WHERE table_schema = %s AND table_name = %s", (schema, name)))
        if not cols:
            out.append(f"{v} is not there")
            continue
        extra = [c for c, _ in cols if any(w in c for w in ADDRESSISH)]
        if extra:
            out.append(f"{v} carries {', '.join(extra)}")
        if not {"licence", "attribution"} <= {c for c, _ in cols}:
            out.append(f"{v} carries no licence or attribution")
        else:
            n = conn.execute(f"SELECT count(*) FROM {schema}.{name} WHERE coalesce(licence, '') = '' OR coalesce(attribution, '') = ''"
                             ).fetchone()[0]
            if n:
                out.append(f"{v}: {n} rows with no licence or attribution")
        for c, typ in cols:
            if typ != "text" or c in ("key", "document", "reader", "profile", "place", "website", "attribution",
                                      "recipient_key", "role"):
                continue
            keys = [r[0] for r in conn.execute(f"SELECT key, {c} FROM {schema}.{name} WHERE {c} ~ '[0-9]'")
                    if r[1] and STREET.search(r[1])]
            if keys:
                out.append(f"{v}.{c}: {len(keys)} values shaped like a street address (first key {keys[0]})")
    return out


def outside(conn, schema: str = SCHEMA, read_bytes=None, today: dt.date = None) -> dict:
    from support.docstore.landing import read_bytes as rb
    read_bytes = read_bytes or rb
    T = lambda t: capture.table(schema, t)
    problems = []
    docs = conn.execute(f"SELECT document, list, url, profile, records, grants, set_aside, stated "
                        f"FROM {T('read_documents')}").fetchall()
    files = [d for d in docs if d[3] == read.DIA_CSV]
    pages = [d for d in docs if d[3] == read.LOTTERY_PAGE]
    unread = [d for d in docs if d[3] is None]
    if not files:
        problems.append("no national file of class 4 grants read")
    if not pages:
        problems.append("no Lottery record of grants read")
    if unread:
        problems.append(f"{len(unread)} listed documents no profile recognises")
    for d in files:
        n = records_in_bytes(read_bytes(d[0]))
        if n != d[4]:
            problems.append(f"the national file {d[0][:12]}…: {n} records in its bytes, {d[4]} read")
    for d in pages:
        stated = d[7] if isinstance(d[7], dict) else json.loads(d[7] or "{}")
        if stated.get("total"):
            want = total_of(stated["total"])
            got = conn.execute(f"SELECT coalesce(sum(amount_nzd), 0) FROM {T('grants')} WHERE document = %s",
                               (d[0],)).fetchone()[0]
            if want is None or abs(float(got) - want) > 0.5:
                problems.append(f"the record {d[0][:12]}… prints a total of {stated['total']}; its rows sum to {got}")
    listed = [k for k, (_, _, on) in read.SOCIETIES.items() if on]
    with_grants = {r[0] for r in conn.execute(f"SELECT DISTINCT grantor_key FROM {T('grants')} "
                                              "WHERE publisher_key = 'dia' AND grantor_key <> 'lottery-grants-board'")}
    missing = sorted(set(listed) - with_grants) if files else []
    if missing:
        problems.append(f"{len(missing)} societies on the Department's list have no grant in its file: "
                        + ", ".join(missing))
    newest = conn.execute(f"SELECT max(decided_on) FROM {T('grants')} WHERE profile = %s", (read.DIA_CSV,)).fetchone()[0]
    today = today or dt.date.today()
    if newest and (today.year - newest.year) * 12 + today.month - newest.month > STALE_MONTHS:
        problems.append(f"the national file's newest decision is {newest}: stale")
    per_year = dict(conn.execute(f"SELECT period, count(*) FROM {T('grants')} WHERE profile = %s GROUP BY period "
                                 "ORDER BY period", (read.DIA_CSV,)).fetchall())
    return {"ok": not problems, "problems": problems, "files": len(files), "records_of_grants": len(pages),
            "file_records": sum(d[4] for d in files), "grants_by_year": per_year, "newest_decision": newest,
            "societies_listed": len(listed), "societies_with_grants": len(with_grants)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.grants.check")
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        if conn.execute("SELECT to_regclass('grants.read_documents')").fetchone()[0] is None:
            print(f"{SCHEMA}: check: nothing published yet (no load has run)")
            return 1
        out = outside(conn)
        out["problems"] += reading(conn) + views(conn)
    print(f"{SCHEMA}: check: " + json.dumps(out, default=str))
    return 0 if not out["problems"] else 1


if __name__ == "__main__":
    sys.exit(main())
