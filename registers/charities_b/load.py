"""Loading (plan 1b.7): `load(conn, schema)` builds this build's tables under
`schema` from the pages the capture lists, and `publish(conn, staging)` would
move them into place. `fill` in sample.py uses the same `build`.

Idempotent per pass: the tables are dropped and made again and every row is
read again from the same pages inside one transaction, so a second load of
the same listing gives the same rows under the same keys (only `loaded_at`
moves). Items in equal items out plus items set aside, page by page, in the
`pages` ledger; check.py holds the lane to it.

Two builds of this reading exist (plan step 4.1) and one is kept, so this one
publishes nothing until it is the one kept: `KEPT` is the setting the
integrator turns on, with the move into `charities`.

    python -m registers.charities_b.load [--schema scratch_charities_b_full] [--database querynz_v4_sample]

reads the listing and the pages from querynz_v4 with the read-only login and
writes into `schema` of `database` with the owner's. Every line printed is a count.
"""
import argparse
import collections
import decimal
import json
import os
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.charities_b import capture, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "charities_b"
JOB = "qv4-charities-b-load"
KEPT = False            # the integrator sets this when this build is the one kept (plan 4.1)
SCRATCH = "scratch_charities_b_full"
TABLES = ("pages", "codes", "groups", "charities", "officers", "returns", "set_aside", "notes")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
COLUMNS = {
    "pages": ("document", "entity_set", "rows", "typed", "set_aside", "skipped"),
    "codes": ("code_list", "entity", "code", "name", "document"),
    "groups": ("key", "number", "group_id", "name", "status", "registered_on", "deregistered_on",
               "source_modified_at") + _CITE,
    "charities": ("key", "number", "organisation_id", "name", "other_names", "status", "registered_on",
                  "deregistered_on", "deregistration_reason", "legal_structure", "legal_structure_other",
                  "charitable_purpose", "main_sector_id", "main_sector", "main_activity_id", "main_activity",
                  "main_beneficiary_id", "main_beneficiary", "address_for_service", "group_key", "group_number",
                  "group_name", "group_type", "nzbn", "incorporation_number", "year_end_month", "year_end_day",
                  "annual_return_due_on", "source_modified_at") + _CITE,
    "officers": ("key", "officer_id", "charity_key", "organisation_id", "kind", "full_name", "first_name",
                 "middle_name", "last_name", "role", "started_on", "ended_on", "ended_on_stated", "status",
                 "disqualified", "declared_not_disqualified", "source_modified_at") + _CITE,
    "returns": ("key", "return_id", "charity_key", "group_key", "organisation_id", "group_id", "period_end",
                "months_covered", "began_on", "tier_id", "tier", "currency", "audited", "modified_opinion", "opinion",
                "status_code") + tuple(read.HEADLINE) + ("figures", "material_expenses", "source_modified_at") + _CITE,
    "set_aside": ("entity_set", "document", "place", "stage", "reason"),
    "notes": ("note", "count"),
}
JSON_COLUMNS = ("figures", "material_expenses")


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    build's tables carry its name: `schema.charities_b_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    return text.replace(f"{SCHEMA}.", f"{schema}.{SCHEMA}_" if shared else f"{schema}.")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _json(v):
    if v is None:
        return None
    return json.dumps(v, ensure_ascii=False, sort_keys=True,
                      default=lambda d: float(d) if isinstance(d, decimal.Decimal) else str(d))


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(_json(row.get(c)) if c in JSON_COLUMNS else row.get(c) for c in cols))
            n += 1
    return n


class Ledger:
    """Rows in, typed and set aside, page by page."""

    def __init__(self):
        self.pages = {}

    def open(self, entity_set: str):
        def on_page(sha, n):
            self.pages[sha] = {"document": sha, "entity_set": entity_set, "rows": n, "typed": 0, "set_aside": 0,
                               "skipped": 0}
        return on_page

    def typed(self, sha):
        self.pages[sha]["typed"] += 1

    def aside(self, sha):
        self.pages[sha]["set_aside"] += 1

    def close(self):
        for p in self.pages.values():
            p["skipped"] = p["rows"] - p["typed"] - p["set_aside"]
        return list(self.pages.values())


def build(conn, schema: str, pages: dict, read_bytes=read_bytes, only: dict = None, shared: bool = False) -> dict:
    """Read every listed page into the tables under `schema`. `pages`: feed
    set → [sha256], oldest first. `only`: feed set → the ids to read (the
    sample's); None for all. Returns the counts."""
    t0 = time.monotonic()
    create_tables(conn, schema, shared)
    T = lambda t: table(schema, t, shared)
    ledger, notes, asides, counts = Ledger(), collections.Counter(), [], collections.Counter()
    pick = lambda s: None if only is None or s not in only else set(only[s])   # a set with no key line: whole

    codes = read.Codes()
    for lst in read.CODE_LISTS:
        for sha in pages.get(lst, ()):
            _, rows = read.parse_page(read_bytes(sha))
            n = codes.add_page(lst, rows, sha)
            ledger.pages[sha] = {"document": sha, "entity_set": lst, "rows": len(rows), "typed": n,
                                 "set_aside": len(rows) - n, "skipped": 0}
            for r in rows:
                if read.text(r.get("Name")) is None:
                    asides.append(read.aside(lst, sha, r.get(read._CODE_ID.get(lst, "Id")), "read", "a code with no name"))
    missing = codes.missing()
    if missing:
        raise LookupError(f"charities_b: no page of the code list(s) {', '.join(missing)} is listed; nothing is read")
    counts["codes"] = _copy(conn, T("codes"), COLUMNS["codes"],
                            (dict(zip(COLUMNS["codes"], e)) for e in codes.entries))

    def take(entity_set, reader, sink, on_aside=None):
        """Every row of a set's pages to `sink` (typed) or the catch log."""
        for sha, row, line in read.newest_first(pages.get(entity_set, []), entity_set, read_bytes,
                                                pick(entity_set), ledger.open(entity_set)):
            if line is not None:
                asides.append(line)
                ledger.aside(sha)
                continue
            out, why = reader(row, sha)
            if out is None:
                asides.append(read.aside(entity_set, sha, row[read.SETS[entity_set]], read.stage_of(why), why))
                ledger.aside(sha)
                if on_aside:
                    on_aside(row, why)
                continue
            sink(out)
            ledger.typed(sha)

    groups = []
    take("Groups", read.read_group, groups.append)
    by_gid = {g["group_id"]: g for g in groups}
    orgs, charities = [], {}
    take("Organisations", lambda r, sha: read.read_organisation(r, sha, codes, by_gid, notes), orgs.append,
         lambda r, why: charities.__setitem__(r["OrganisationId"], (None, why)))
    held = collections.Counter(o["number"] for o in orgs)
    kept = []
    for o in orgs:
        if held[o["number"]] > 1:
            why = f"the register's number is held by {held[o['number']]} organisations"
            asides.append(read.aside("Organisations", o["document"], o["organisation_id"], "key", why))
            ledger.pages[o["document"]]["typed"] -= 1
            ledger.aside(o["document"])
            charities[o["organisation_id"]] = (None, why)
        else:
            kept.append(o)
            charities[o["organisation_id"]] = (o["key"], None)
    counts["groups"] = _copy(conn, T("groups"), COLUMNS["groups"], groups)
    counts["charities"] = _copy(conn, T("charities"), COLUMNS["charities"], kept)
    del orgs, kept

    for entity_set, t, reader in (
            ("Officers", "officers", lambda r, sha: read.read_officer(r, sha, codes, charities, notes)),
            ("AnnualReturn", "returns", lambda r, sha: read.read_return(r, sha, codes, charities, by_gid, notes))):
        batch = []

        def sink(out, t=t, batch=batch):
            batch.append(out)
            if len(batch) >= 5000:
                counts[t] += _copy(conn, T(t), COLUMNS[t], batch)
                batch.clear()

        take(entity_set, reader, sink)
        counts[t] += _copy(conn, T(t), COLUMNS[t], batch)

    ledger_rows = ledger.close()
    if only is None:
        bad = [p for p in ledger_rows if p["skipped"]]
        if bad:
            raise AssertionError(f"charities_b: {len(bad)} page(s) do not reconcile (rows in ≠ typed + set aside)")
    _copy(conn, T("pages"), COLUMNS["pages"], ledger_rows)
    counts["set_aside"] = _copy(conn, T("set_aside"), COLUMNS["set_aside"], asides)
    _copy(conn, T("notes"), COLUMNS["notes"], ({"note": k, "count": v} for k, v in sorted(notes.items())))
    counts["pages"] = len(ledger_rows)
    counts["rows_in"] = sum(p["rows"] - p["skipped"] for p in ledger_rows)
    counts["seconds"] = round(time.monotonic() - t0, 1)
    for a in asides:
        counts[f"aside: {a['entity_set']}: {a['reason'] if a['stage'] != 'supersede' else 'read again on a later page'}"] += 1
    return dict(counts)


def listings(conn) -> dict:
    """Feed set → [sha256] oldest first, for every set this build reads."""
    return {s: [sha for sha, _, _ in capture.listing(conn, s)] for s in tuple(read.SETS) + read.CODE_LISTS}


def load(conn, schema: str, log=print) -> int:
    """Every listed page, read, under `schema` of the connection's database
    (the merge gate's staging step). Returns the rows typed."""
    started = jobrun.now()
    counts = build(conn, schema, listings(conn))
    rows = counts["charities"] + counts["officers"] + counts["returns"] + counts["groups"]
    detail = ", ".join(f"{k} {v}" for k, v in counts.items() if not k.startswith("aside")) + f", into {schema}"
    log("charities_b: " + detail)
    jobrun.record(JOB, True, detail, started, {k: v for k, v in counts.items() if not k.startswith("aside")})
    return rows


def publish(conn, staging: str, log=print) -> None:
    """Nothing, until this build is the one kept (plan 4.1): two builds of
    one reading must not both publish `pub.charities`. When kept, the tables
    move into the lane's schema and publish.sql makes the views, in one
    transaction (contract: the lane)."""
    if not KEPT:
        log("charities_b: not the build kept (plan 4.1); nothing published")
        return
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        conn.execute(sql("publish.sql"))


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.charities_b.load")
    ap.add_argument("--schema", default=SCRATCH)
    ap.add_argument("--database", default="querynz_v4_sample")
    a = ap.parse_args(argv)
    if not a.schema.startswith(("scratch_", "staging_")):
        print("charities_b: a session loads only a scratch or staging schema")
        return 2
    started = jobrun.now()
    with db.connect(db.READ_KEY, "querynz_v4") as src:
        src.execute("SET statement_timeout = '60s'")
        pages = listings(src)
    with db.connect(db.OWNER_KEY, a.database) as conn:
        with conn.transaction():
            counts = build(conn, a.schema, pages)
    for k, v in counts.items():
        print(f"charities_b: {k}: {v}")
    jobrun.record(JOB, True, f"{counts['charities']} charities, {counts['officers']} officers, {counts['returns']} "
                  f"returns into {a.database}.{a.schema}", started,
                  {k: v for k, v in counts.items() if not k.startswith("aside")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
