"""Loading (plan 1b.7). The merge gate's staging step calls `load` to build
this lane's tables under a staging schema of the real database, and
`publish` to move the rows into the lane's own tables in one transaction
and refresh the published views. `fill` in sample.py uses the same pieces.

Land the four export parts (never run the export: capture.py was run once),
and lay the latest monthly package held whole over them (monthly.py: the
zip, landed once by `capture.py --land-package`), read each, copy the rows in. Items in equal items out plus items set aside
(read.py says how). About 5.6 million rows: the entities first, so a role
whose company the package does not name is counted.
"""
import os

from support import jobrun
from support.docstore.landing import read_bytes
from registers.companies import capture, monthly, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "companies"
PRIVATE = "companies_private"
TABLES = ("entities", "entity_states", "directors", "shareholders", "registered_offices", "insolvencies", "villages",
          "files", "set_aside")
PRIVATE_TABLES = ("residential_addresses", "package_addresses")
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version", "loaded_at")
COLUMNS = {
    "entities": ("key", "register", "nzbn", "number", "name", "entity_type", "status", "registered_on", "removed_on",
                 "in_latest", "first_file", "last_file", "extra", "old_id", "source_note") + _CITE,
    "entity_states": ("key", "entity_key", "file", "name", "entity_type", "status", "registered_on",
                      "removed_on") + _CITE,
    "directors": ("key", "entity_key", "nzbn", "company_number", "first_name", "middle_names", "last_name",
                  "full_name", "role_type", "appointed_on", "ended_on", "in_latest", "first_file", "last_file",
                  "suppressed", "old_id", "source_note") + _CITE,
    "shareholders": ("key", "entity_key", "nzbn", "company_number", "shareholder_type", "name", "holder_nzbn",
                     "shares", "allocation_status", "in_latest", "first_file", "last_file", "suppressed", "old_id",
                     "source_note") + _CITE,
    "registered_offices": ("key", "entity_key", "register", "started_on", "care_of", "line_1", "line_2", "line_3",
                           "line_4", "postcode", "country", "in_latest", "last_file", "source_note") + _CITE,
    # the package-only files (monthly.py, 2 November 2026)
    "insolvencies": ("key", "entity_key", "nzbn", "entity_name", "insolvency_type", "started_on", "appointment_type",
                     "appointee_first_name", "appointee_middle_names", "appointee_last_name", "appointee", "organisation",
                     "appointed_on", "vacated_on", "resolution_of_solvency", "last_file", "source_note") + _CITE,
    "villages": ("key", "entity_key", "number", "name", "status", "operator_name", "operator_number", "supervisor_name",
                 "supervisor_appointed_on", "last_file", "source_note") + _CITE,
}


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table(schema: str, t: str, shared: bool = False) -> str:
    """`schema.t`; in a schema every module shares (the sample's), the
    lane's tables carry its name: `schema.companies_t`."""
    return f"{schema}.{SCHEMA}_{t}" if shared else f"{schema}.{t}"


def sql(name: str, schema: str = SCHEMA, shared: bool = False) -> str:
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        text = f.read()
    pre = f"{SCHEMA}_" if shared else ""
    return text.replace(f"{PRIVATE}.", f"{private_of(schema)}.{pre}").replace(f"{SCHEMA}.", f"{schema}.{pre}")


def create_tables(conn, schema: str, shared: bool = False) -> None:
    """The lane's tables as tables.sql has them now, made again on every
    build: every row is rebuilt from documents."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private_of(schema)}")
    for t in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(schema, t, shared)} CASCADE")
    for t in PRIVATE_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table(private_of(schema), t, shared)} CASCADE")
    conn.execute(sql("tables.sql", schema, shared))


def _copy(conn, name: str, cols: tuple, rows) -> None:
    with conn.cursor().copy(f"COPY {name} ({', '.join(chr(34) + c + chr(34) for c in cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(row)


def _flat(cols: tuple, rows: list):
    for row in rows:
        flat = {**row, **row.get("filed", {})}
        yield tuple(flat.get(c) for c in cols)


PACKAGE_ADDRESS_COLUMNS = ("document", "place", "nzbn", "number", "kind", "address", "file")


def build(conn, schema: str, exports: list, aside: list, only=None, shared: bool = False, package=None) -> dict:
    """exports: [(part, sha256, name)]; aside: [(item, why)] from capture;
    only: the NZBNs and register numbers to read (the sample's), None for
    all; package: (label, sha256) of the monthly package laid over the
    export, None for none. Wipes and fills `schema`; returns the counts."""
    pkg = (package[0], read_bytes(package[1]), package[1]) if package else None
    create_tables(conn, schema, shared)
    _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason", "count"),
          [(i, "capture", w, 1) for i, w in aside])
    counts, entities = {"not_held": len(aside)}, None
    for part, sha, name in sorted(exports, key=lambda e: capture.PARTS.index(e[0])):
        res = read.read(part, read_bytes(sha), sha, only=only, entities=entities, package=pkg)
        if part == "entities":
            entities = {r["key"] for r in res.rows["entities"]}
        for t in read.TABLE_OF[part]:
            _copy(conn, table(schema, t, shared), COLUMNS[t], _flat(COLUMNS[t], res.rows[t]))
        _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason", "count"), res.set_aside)
        conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, %s, 'read')", (sha, name, part))
        if pkg:
            conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, %s, 'read')",
                         (pkg[2], f"{monthly.PACKAGES[pkg[0]][0]} ({part})", part))
        counts.update({f"{part}.{k}" if k in ("lines", "set_aside", "set_aside_lines", "no_entity") else k: v
                       for k, v in res.counts.items()})
        del res
    if pkg:
        # the files only the package carries: a company's insolvency appointments, a village's operator and supervisor
        res = read.read_package(pkg, only=only, entities=entities)
        for t in ("insolvencies", "villages"):
            _copy(conn, table(schema, t, shared), COLUMNS[t], _flat(COLUMNS[t], res.rows[t]))
        _copy(conn, table(schema, "set_aside", shared), ("item", "stage", "reason", "count"), res.set_aside)
        for part in read.PACKAGE_PARTS:
            conn.execute(f"INSERT INTO {table(schema, 'files', shared)} VALUES (%s, %s, %s, 'read')",
                         (pkg[2], f"{monthly.PACKAGES[pkg[0]][0]} ({part})", part))
        # a village's operator joined to its company row by the company number, where exactly one company carries it
        conn.execute(f"UPDATE {table(schema, 'villages', shared)} v SET operator_key = o.key, operator_nzbn = o.nzbn "
                     f"FROM (SELECT number, min(key) AS key, min(nzbn) AS nzbn FROM {table(schema, 'entities', shared)} "
                     f"WHERE register = 'companies' AND number IN (SELECT operator_number FROM "
                     f"{table(schema, 'villages', shared)}) GROUP BY number HAVING count(*) = 1) o "
                     f"WHERE o.number = v.operator_number")
        counts.update(res.counts)
        # every other address block the package carries, into the private twin (ruling 142)
        counts["package_addresses"] = _copy(
            conn, table(private_of(schema), "package_addresses", shared), PACKAGE_ADDRESS_COLUMNS,
            (tuple(a[c] for c in PACKAGE_ADDRESS_COLUMNS)
             for a in monthly.package_addresses(pkg[1], pkg[0], pkg[2], only=only)))
        counts["villages.operator_joined"] = conn.execute(
            f"SELECT count(*) FROM {table(schema, 'villages', shared)} WHERE operator_key IS NOT NULL").fetchone()[0]
    return counts


def load(conn, schema: str, log=print) -> int:
    """The four parts landed and read, under `schema`. Returns the entity count."""
    started = jobrun.now()
    landed, aside = capture.copy_all(conn)
    package = capture.latest_package()
    counts = build(conn, schema, [(part, ref.sha256, name) for part, ref, name, at in landed], aside, package=package)
    detail = ", ".join(f"{k} {v}" for k, v in counts.items()) + f", into {schema}"
    log("companies: " + detail)
    jobrun.record("qv4-companies-load", True, detail, started, counts)
    return counts["entities"]


def publish(conn, staging: str) -> None:
    """The lane's own tables wiped and refilled from the staged ones, and
    the views refreshed, in one transaction (contract: the lane)."""
    with conn.transaction():
        create_tables(conn, SCHEMA)
        for t in TABLES:
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for t in PRIVATE_TABLES:
            conn.execute(f"INSERT INTO {PRIVATE}.{t} SELECT * FROM {private_of(staging)}.{t}")
        conn.execute(sql("publish.sql"))
