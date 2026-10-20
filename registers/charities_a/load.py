"""Loading (plan 1b.7; the lane contract). `load(conn, schema)` builds this
build's tables under `schema` from the capture lane's listing (the newest
finished full pass of each set and the changes passes after it, through
`registers.charities.read.pages`) and the pages in the document store;
`publish(conn, staging)` is the gate's second step and, for this build,
publishes nothing: of the two builds of the charities reading one is kept
and moves to `registers/charities` with the `charities` schema (plan 4.1).
`fill` in sample.py and the tests use `build` with pages named outright.

Idempotent per pass: a load records the ordered hashes of the pages it read
(`runs.signature`); run again over the same listing it reloads nothing and
says so, unless forced. A load wipes and refills the tables inside one
transaction. Every printed line is a count: no name or address is printed.

    python -m registers.charities_a.load [--schema scratch_charities_a] [--database querynz_v4_sample] [--force]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.charities import read as capture_read
from registers.charities_a import read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "charities_a"
JOB = "qv4-charities-load"
TABLES = ("charities", "charity_officers", "charity_returns", "charity_groups", "codes", "files", "set_aside", "runs")
_CITE = ("lists_document", "document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "charities": ("key", "charity_number", "organisation_id", "nzbn", "nzbn_filed", "companies_office_number", "name",
                  "other_names", "status", "registered_on", "deregistered_on", "deregistration_reason", "deregistration_note",
                  "legal_structure", "legal_structure_other", "entity_structure", "main_activity_id", "main_activity",
                  "main_sector_id", "main_sector", "main_beneficiary_id", "main_beneficiary", "activities", "sectors",
                  "beneficiaries", "areas_of_operation", "sources_of_funds", "charitable_purpose", "address_for_service",
                  "postal_address", "year_end_day", "year_end_month", "annual_return_due_on", "group_id", "group_key",
                  "group_name", "group_type", "incorporated", "percent_spent_overseas", "modified_at") + _CITE,
    "charity_officers": ("key", "officer_id", "charity_key", "charity_number", "organisation_id", "contact_id", "first_name",
                         "middle_names", "last_name", "full_name", "body_corporate", "body_corporate_name", "name_note", "role", "status",
                         "started_on", "ended_on", "ended_on_stated", "disqualified", "disqualification", "appointed_officer",
                         "suppressed", "modified_at") + _CITE[1:],
    "charity_returns": ("key", "annual_return_id", "charity_key", "charity_number", "organisation_id", "group_key", "group_id",
                        "period_ended_on", "as_at_on", "covers_months", "status_code", "tier_id", "tier", "currency", "audited",
                        "audit_opinion_modified", "audit_opinion", "accounting_method_flag", "withheld", "first_time_reporting",
                        "gst_inclusive") + tuple(read.NAMED_FIGURES.values()) + ("figures", "modified_at") + _CITE[1:],
    "charity_groups": ("key", "group_id", "registration_number", "name", "other_names", "group_type", "status", "registered_on",
                       "deregistered_on", "deregistration_note", "main_activity", "main_sector", "main_beneficiary",
                       "address_for_service", "postal_address", "modified_at") + _CITE[1:],
}
#: the sets read, in the order the load walks them
CODE_SETS = tuple(read.CODE_LISTS)
ROW_SETS = ("Groups", "Organisations", "vOrganisations", "Officers", "AnnualReturn")
SETS = CODE_SETS + ROW_SETS


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the tables carry this lane's name."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(row)
            n += 1
    return n


def _flat(cols: tuple, rows):
    for row in rows:
        flat = {**row, **row.get("filed", {})}
        yield tuple(flat.get(c) for c in cols)


def listing(conn) -> dict:
    """set → [(sha256, url)] from the capture lane's listing, in reading order."""
    return {s: capture_read.pages(conn, s) for s in SETS}


def signature(pages: dict) -> str:
    h = hashlib.sha256()
    for s in SETS:
        for sha, _ in pages.get(s, []):
            h.update(f"{s} {sha}\n".encode())
    return h.hexdigest()


def has_listing(conn) -> bool:
    return conn.execute("SELECT to_regclass('charities.capture_pages') IS NOT NULL").fetchone()[0]


class _Files:
    def __init__(self):
        self.rows, self.ordinal = [], 0

    def add(self, sha, entity_set, url, res):
        self.ordinal += 1
        c = res.counts
        self.rows.append((sha, entity_set, url, res.rows_in, c.get("typed", 0), c.get("set_aside", 0), c.get("filtered", 0),
                          res.stated, self.ordinal))
        return self.ordinal


def build(conn, schema: str, pages: dict, only=None, shared: bool = False, log=print, read_fn=read_bytes,
          loaded_at: str = None) -> dict:
    """pages: set → [(sha256, url)] in reading order; only: the charity
    numbers a sample keeps, None for all. Returns the counts. Items in equal
    items out plus items set aside, page by page (`files`)."""
    t0 = time.monotonic()
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    version = read.profile_version()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    files, aside, counts = _Files(), [], {}
    codes = read.Codes()
    # the code lists
    code_rows = []
    for s in CODE_SETS:
        for sha, url in pages.get(s, []):
            lists, rows = read.read_codes(s, read_fn(sha))
            codes.lists.setdefault(s, {}).update(lists)
            code_rows += [r + (sha,) for r in rows]
            res = read.Result(entity_set=s, rows_in=len(rows), counts={"typed": len(rows)})
            files.add(sha, s, url, res)
    counts["codes"] = _copy(conn, T("codes"), ("list", "id", "name", "entity_name", "attribute", "document"), code_rows)
    # the groups, then the organisations with their lists: held whole (small), a later page replacing an earlier key
    groups = {}
    for sha, url in pages.get("Groups", []):
        res = read.read_page("Groups", read_fn(sha), sha, codes, loaded_at=loaded_at, version=version)
        for r in res.rows["charity_groups"]:
            if r["key"] in groups:
                counts["replaced"] = counts.get("replaced", 0) + 1
            groups[r["key"]] = r
        aside += res.set_aside
        files.add(sha, "Groups", url, res)
    group_keys = {g["filed"]["group_id"]: g["key"] for g in groups.values()}
    charities, aliases = {}, {}      # aliases: the OrganisationId of a row not kept → the key of the row kept for its number
    for sha, url in pages.get("Organisations", []):
        res = read.read_page("Organisations", read_fn(sha), sha, codes, only=only, loaded_at=loaded_at, version=version)
        for r in res.rows["charities"]:
            old = charities.get(r["key"])
            if old is not None and old["filed"]["organisation_id"] != r["filed"]["organisation_id"]:
                keep, drop = (r, old) if (r["filed"]["modified_at"] or "") >= (old["filed"]["modified_at"] or "") else (old, r)
                aside.append((f"{drop['document']}/{drop['place']}", "Organisations",
                              "charity number held by two organisation rows; the later modified one kept, "
                              "the other's officers and returns attached to it", 1))
                counts["number_held_twice"] = counts.get("number_held_twice", 0) + 1
                aliases[drop["filed"]["organisation_id"]] = keep["key"]
                r = keep
            elif old is not None:
                counts["replaced"] = counts.get("replaced", 0) + 1
            charities[r["key"]] = r
        aside += res.set_aside
        files.add(sha, "Organisations", url, res)
    for sha, url in pages.get("vOrganisations", []):
        res = read.read_page("vOrganisations", read_fn(sha), sha, codes, only=only, loaded_at=loaded_at, version=version)
        for r in res.rows["charity_lists"]:
            c = charities.get(r["key"])
            if c is None:
                aside.append((f"{sha}/{r['place']}", "vOrganisations", "lists for an organisation the copy does not hold", 1))
                res.counts["typed"] -= 1
                res.counts["set_aside"] = res.counts.get("set_aside", 0) + 1
                continue
            if c["filed"]["organisation_id"] != r["filed"]["organisation_id"]:
                aside.append((f"{sha}/{r['place']}", "vOrganisations", "lists for the organisation row not kept", 1))
                res.counts["typed"] -= 1
                res.counts["set_aside"] = res.counts.get("set_aside", 0) + 1
                continue
            for f in ("activities", "sectors", "beneficiaries", "areas_of_operation", "sources_of_funds", "group_name",
                      "deregistration_reason"):
                c["filed"][f] = r["filed"][f]
            c["lists_document"] = sha
        aside += res.set_aside
        files.add(sha, "vOrganisations", url, res)
    for c in charities.values():
        c.setdefault("lists_document", None)
        for f in ("activities", "sectors", "beneficiaries", "areas_of_operation", "sources_of_funds", "group_name",
                  "deregistration_reason"):
            c["filed"].setdefault(f, None)
    counts["charity_groups"] = _copy(conn, T("charity_groups"), COLUMNS["charity_groups"],
                                     _flat(COLUMNS["charity_groups"], sorted(groups.values(), key=lambda r: r["key"])))
    counts["charities"] = _copy(conn, T("charities"), COLUMNS["charities"],
                                _flat(COLUMNS["charities"], sorted(charities.values(), key=lambda r: r["key"])))
    held = {c["filed"]["organisation_id"]: c["key"] for c in charities.values()}
    held.update({oid: key for oid, key in aliases.items() if key in charities})
    # the officers and the returns: streamed page by page through a holding table; the latest reading of a key wins
    for s, t in (("Officers", "charity_officers"), ("AnnualReturn", "charity_returns")):
        cols = COLUMNS[t]
        hold = f"hold_{t}"
        conn.execute(f"CREATE TEMP TABLE {hold} (LIKE {T(t)} INCLUDING DEFAULTS) ON COMMIT DROP")
        conn.execute(f"ALTER TABLE {hold} ADD COLUMN ordinal integer")
        copied = 0
        for sha, url in pages.get(s, []):
            res = read.read_page(s, read_fn(sha), sha, codes, held=held, only=only, loaded_at=loaded_at, version=version,
                                 groups=group_keys)
            n = files.add(sha, s, url, res)
            copied += _copy(conn, hold, cols + ("ordinal",), (row + (n,) for row in _flat(cols, res.rows[t])))
            aside += res.set_aside
        col_list = ", ".join(chr(34) + c + chr(34) for c in cols)
        conn.execute(f"INSERT INTO {T(t)} ({col_list}) SELECT DISTINCT ON (key) {col_list} FROM {hold} "
                     "ORDER BY key, ordinal DESC")
        counts[t] = conn.execute(f"SELECT count(*) FROM {T(t)}").fetchone()[0]
        counts["replaced"] = counts.get("replaced", 0) + (copied - counts[t])
    for s, n in codes.unresolved.items():
        counts[f"unresolved.{s}"] = n
    _copy(conn, T("files"), ("document", "entity_set", "url", "rows", "typed", "set_aside", "filtered", "stated", "ordinal"),
          files.rows)
    counts["set_aside"] = _copy(conn, T("set_aside"), ("item", "stage", "reason", "count"), aside)
    counts["pages"] = len(files.rows)
    counts["rows_in"] = sum(r[3] for r in files.rows)
    counts["seconds"] = round(time.monotonic() - t0, 1)
    conn.execute(f"INSERT INTO {T('runs')} (signature, passes, counts, seconds, loaded_at) VALUES (%s, %s, %s, %s, %s)",
                 (signature(pages), json.dumps({s: len(v) for s, v in pages.items()}), json.dumps(counts),
                  counts["seconds"], loaded_at))
    return counts


def last_signature(conn, schema: str, shared: bool = False):
    try:
        r = conn.execute(f"SELECT signature FROM {table(schema, 'runs', shared)} ORDER BY run_id DESC LIMIT 1").fetchone()
    except Exception:  # noqa: BLE001 — no table yet is a first load
        conn.rollback()
        return None
    return r[0] if r else None


def load(conn, schema: str, log=print, force: bool = False, shared: bool = False, listing_conn=None) -> int:
    """Every page the capture lane lists, read, under `schema`. The listing
    is read from `conn`'s database when it holds one (the gate's staging
    load), else from the real database through the read-only login. Returns
    the charities count; -1 when nothing new was there to load."""
    started = jobrun.now()
    close = None
    if listing_conn is None:
        if has_listing(conn):
            listing_conn = conn
        else:
            from support import db
            listing_conn = close = db.connect(db.READ_KEY, "querynz_v4")
            listing_conn.execute("SET statement_timeout = '60s'")
    try:
        pages = listing(listing_conn)
    finally:
        if close is not None:
            close.close()
    sig = signature(pages)
    if not force and last_signature(conn, schema, shared) == sig:
        log(f"{SCHEMA}: the same {sum(len(v) for v in pages.values())} pages as the last load; nothing reloaded")
        return -1
    counts = build(conn, schema, pages, shared=shared, log=log)
    if not conn.autocommit:
        conn.commit()
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log(f"{SCHEMA}: " + detail)
    jobrun.record(JOB, True, detail, started, counts)
    return counts["charities"]


def publish(conn, staging: str) -> None:
    """The gate's second step. This build publishes nothing: one of the two
    builds of the charities reading is kept and moves to `registers/charities`
    with the `charities` schema (plan 4.1); its tables are published there."""
    print(f"{SCHEMA}: staged in {staging}; published nothing (plan 4.1: the build kept moves to registers/charities)")


def main(argv=None) -> int:
    from support import db, sample
    ap = argparse.ArgumentParser(prog="registers.charities_a.load")
    ap.add_argument("--schema", default=sample.scratch_name("charities-a"))
    ap.add_argument("--database", default="querynz_v4_sample")
    ap.add_argument("--force", action="store_true", help="reload even when the listing has not changed")
    a = ap.parse_args(argv)
    if a.database == "querynz_v4" and not a.schema.startswith("staging_"):
        print(f"{SCHEMA}: a load into the real database goes through the merge gate's staging step, not this command")
        return 2
    shared = a.schema.startswith(db.SCRATCH_PREFIX)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '600s'")
        n = load(conn, a.schema, shared=shared, force=a.force)
    return 0 if n >= 0 else 0


if __name__ == "__main__":
    sys.exit(main())
