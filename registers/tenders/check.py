"""The lane's checks: against the source's own files and lists. Prints counts
only and exits 1 when any check fails.

1. **The source's own count.** Each listed file's records, counted here
   afresh from its bytes by a reader that knows nothing of the profiles
   (`count_records`), equal the records the reading's ledger took in; and
   every record is a row or a catch-log line with its reason: notices
   equal the notices files' typed records, suppliers the supplier files'.
2. **The old estate's figure.** The old estate held 29,874 award notices
   from the files of 14 August 2026 (the plan's reference note, step 6.2):
   7,314 historic and 22,560 current. The pinned files must read to exactly
   those; a later current release must hold at least as many notices as
   the one it follows, and the historic file never changes.
3. **One release per era.** The four files of an era read share one
   report date, so no reading mixes two quarters.
4. **The catalogue's own list.** Every CSV the government data catalogue
   lists for the package, in its newest landed description, is held for
   its set, or the capture's catch log says why it is not.
5. **Nothing finer than a name.** No published view has a column for an
   address, a website, an email or a phone.

Beside the checks it reports the current release's age: the ministry
refreshes the file quarterly, and a release older than `STALE_DAYS` is
printed as stale (the refresh job's own record carries the alarm).

    python -m registers.tenders.check [--schema tenders] [--database querynz_v4]
"""
import argparse
import csv
import datetime as dt
import io
import json
import sys

from registers.tenders import capture, load, read

OLD_ESTATE = {"historic": 7314, "current": 22560, "total": 29874,
              "source": "docs/plan/step-6.md 6.2 (29,874 award notices to 14 August 2026); the old estate's audit "
                        "of 16 August 2026 gives 7,314 historic and 22,560 current"}
PINNED = {"historic": capture.OLD_RAWS["gets-award-notices-historic.csv"],
          "current": capture.OLD_RAWS["gets-award-notices.csv"]}
STALE_DAYS = 120
FORBIDDEN = ("address", "website", "email", "phone", "street", "postal", "residential")


def count_records(data: bytes) -> int:
    """The records of a CSV after its header, counted from the bytes alone
    (Latin-1 maps every byte, so no decoding choice can change the count)."""
    return max(0, sum(1 for _ in csv.reader(io.StringIO(data.decode("latin-1"), newline=""))) - 1)


def _q(conn, sql, args=()):
    return conn.execute(sql, args).fetchall()


def reading(conn, schema: str, listed: dict, shared: bool = False, read_bytes=None) -> list:
    """Problems with a built reading, as plain lines; empty when it holds."""
    from support.docstore.landing import read_bytes as rb
    read_bytes = read_bytes or rb
    T = lambda t: load.table(schema, t, shared)
    out = []
    ledger = {r[0]: {"set_name": r[1], "era": r[2], "records": r[3], "typed": r[4], "set_aside": r[5],
                     "skipped": r[6], "report_date": r[7]}
              for r in _q(conn, f"SELECT document, set_name, era, records, typed, set_aside, skipped, report_date "
                                f"FROM {T('read_files')}")}
    # 1. the source's own count
    for (s, era), sha in sorted(listed.items()):
        led = ledger.get(sha)
        if led is None:
            out.append(f"{s} {era}: the listed file {sha[:12]} was not read")
            continue
        n = count_records(read_bytes(sha))
        if led["records"] != n:
            out.append(f"{s} {era}: the file holds {n} records, the reading took in {led['records']}")
        if led["typed"] + led["set_aside"] + led["skipped"] != led["records"]:
            out.append(f"{s} {era}: records in {led['records']} ≠ typed {led['typed']} + set aside "
                       f"{led['set_aside']} + skipped {led['skipped']}")
        if led["skipped"]:
            out.append(f"{s} {era}: {led['skipped']} records skipped in a full reading")
    extra = set(ledger) - set(listed.values())
    if extra:
        out.append(f"{len(extra)} file(s) read that the listing does not name")
    asides = dict(((r[0], r[1]), r[2]) for r in
                  _q(conn, f"SELECT document, stage, count(*) FROM {T('read_set_aside')} "
                           f"WHERE place <> 'whole file' GROUP BY 1, 2"))
    for sha, led in ledger.items():
        held = sum(v for (d, _), v in asides.items() if d == sha)
        if held != led["set_aside"]:
            out.append(f"{led['set_name']} {led['era']}: the ledger says {led['set_aside']} set aside, the catch log "
                       f"holds {held}")
    for t, s in (("notices", "notices"), ("suppliers", "suppliers")):
        rows = {r[0]: r[1] for r in _q(conn, f"SELECT era, count(*) FROM {T(t)} GROUP BY 1")}
        for era in read.ERAS:
            typed = sum(l["typed"] for l in ledger.values() if l["set_name"] == s and l["era"] == era)
            if rows.get(era, 0) != typed:
                out.append(f"{t} {era}: {rows.get(era, 0)} rows, the ledger typed {typed}")
    # 2. the old estate's figure
    notices = {l["era"]: l["typed"] for sha, l in ledger.items() if l["set_name"] == "notices"}
    for era in read.ERAS:
        sha = listed.get(("notices", era))
        if sha is None:
            out.append(f"no {era} notices file is listed")
        elif sha == PINNED[era] and notices.get(era) != OLD_ESTATE[era]:
            out.append(f"the pinned {era} file reads to {notices.get(era)} notices; the old estate held {OLD_ESTATE[era]}")
        elif sha != PINNED[era] and era == "historic":
            out.append("the historic file is not the pinned one: it is fixed since 2019")
        elif sha != PINNED[era] and (notices.get(era) or 0) < OLD_ESTATE[era]:
            out.append(f"the current release holds {notices.get(era)} notices, fewer than the {OLD_ESTATE[era]} "
                       "of 15 July 2026")
    if listed.get(("notices", "current")) == PINNED["current"] and sum(notices.values()) != OLD_ESTATE["total"]:
        out.append(f"{sum(notices.values())} notices from the pinned files; the old estate held {OLD_ESTATE['total']}")
    # 3. one release per era
    for era in read.ERAS:
        dates = {l["report_date"] for l in ledger.values() if l["era"] == era}
        if len(dates) > 1:
            out.append(f"the {era} files read carry {len(dates)} report dates: two releases mixed")
    return out


def catalogue(conn, schema: str = capture.SCHEMA, read_bytes=None) -> list:
    """Check 4: every CSV the newest landed catalogue description lists is
    held for its set and era, or the capture's catch log says why not."""
    from support.docstore.landing import read_bytes as rb
    read_bytes = read_bytes or rb
    r = conn.execute(f"SELECT sha256 FROM {schema}.capture_files WHERE role = 'catalogue' "
                     "ORDER BY landed_at DESC LIMIT 1").fetchone()
    if r is None:
        return ["no description of the package from the catalogue is held"]
    held = {(s, e) for s, e in _q(conn, f"SELECT DISTINCT set_name, era FROM {schema}.capture_files WHERE role = 'data'")}
    why = {row[0] for row in _q(conn, f"SELECT item FROM {schema}.capture_set_aside")}
    out = []
    for name, url in capture.listed_files(read_bytes(r[0])):
        role, s, era = capture.classify(url)
        if role != "data":
            if url not in why:
                out.append(f"the catalogue lists {name!r}, a file this lane does not know, and no catch-log line says so")
        elif (s, era) not in held and url not in why and capture.lower_name(url) not in why:
            out.append(f"the catalogue lists {name!r} ({s}, {era}): not held and no catch-log line")
    return out


def columns_problems(conn, schema: str = "pub", prefix: str = "") -> list:
    out = []
    for view in (prefix + "award_notices", prefix + "award_suppliers"):
        cols = [r[0] for r in _q(conn, "SELECT column_name FROM information_schema.columns WHERE table_schema = %s "
                                       "AND table_name = %s", (schema, view))]
        if not cols:
            out.append(f"{schema}.{view} does not exist")
        out += [f"{schema}.{view} has a column `{c}`" for c in cols if any(w in c for w in FORBIDDEN)]
        for c in ("licence", "attribution", "document", "place", "profile", "profile_version"):
            if cols and c not in cols:
                out.append(f"{schema}.{view} has no `{c}`")
    return out


def age(conn, schema: str) -> dict:
    r = conn.execute(f"SELECT max(report_date) FROM {schema}.read_files WHERE era = 'current'").fetchone()
    if not r or r[0] is None:
        return {"report_date": None, "days": None, "stale": True}
    days = (dt.date.today() - r[0]).days
    return {"report_date": r[0].isoformat(), "days": days, "stale": days > STALE_DAYS}


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.tenders.check")
    ap.add_argument("--schema", default=load.SCHEMA)
    ap.add_argument("--database", default="querynz_v4")
    a = ap.parse_args(argv)
    key = db.READ_KEY if a.schema == load.SCHEMA else db.OWNER_KEY     # a scratch schema is the owner's alone
    with db.connect(db.READ_KEY, "querynz_v4") as src, db.connect(key, a.database) as conn:
        for c in (src, conn):
            c.execute("SET statement_timeout = '120s'")
        listed = load.listings(src)
        problems = reading(conn, a.schema, listed)
        problems += catalogue(src)
        problems += (columns_problems(conn) if a.schema == load.SCHEMA else columns_problems(conn, a.schema, "pub_"))
        fresh = age(conn, a.schema)
    print("tenders: check: " + json.dumps({"files": len(listed), "problems": len(problems), **fresh}))
    for p in problems:
        print(f"tenders: RED: {p}")
    if fresh["stale"]:
        print(f"tenders: the current release is {fresh['days']} days old: STALE (the refresh is blocked; card "
              "the-ministry-s-files-answer-403)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
