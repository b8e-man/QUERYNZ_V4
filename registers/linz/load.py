"""Loading (step 8.3): `build(conn, schema)` reads each source's newest finished pull, page by page, into the reading's
tables under `schema`; `publish(conn, staging)` moves them into `linz` and makes the views, in one transaction. A source
with no finished pull yet is not loaded, and its view stays as it was published (or empty).

Rebuilt whole every load (regenerable). Rows landed equal rows read plus set aside; the check holds it.

The private sources (capture.PRIVATE_SOURCES) are read into the lane's private schema (`linz_private`; a staging
schema's is `<staging>_private`), and once all three have a finished pull each title's street address is joined there,
title → unit of property → address id → address (`title_addresses`, `JOINED_BY`): a join on ids, no geometry. Nothing
private is published; `publish.sql` makes no view of it.

    python -m registers.linz.load [--schema staging_…|scratch_…]
    python -m registers.linz.load --job

Every catalogue source read whole (capture.WHOLE, Arthur, 4 November 2026, ruling 142: "we want everything") has its own
table in the private schema (`whole_sql`: every attribute as JSON, the geometry as GeoJSON text and its box). They are
many and some are tens of millions of rows, so one is staged only when its newest finished pull is not the one
published (`--full` stages them all), published by moving the staged table into `linz_private` whole, and not staged
while the database's disk has under `DB_FLOOR_BYTES` free. Then, for the titles the spine gives no address, each
title's address by geometry (`geometry_join`): the title's parcels (table 51569) → the parcel's polygon (layer 51571) →
the address points strictly inside it (registers.linz.geo, pure Python, no PostGIS), into `title_address_points`; a
sample of titles the spine does give an address is joined the same way and the two compared, counts only.

Every line printed is a count.
"""
import argparse
import json
import os
import shutil
import sys
import time

from support import jobrun
from support.docstore.landing import read_bytes
from registers.linz import capture, geo, read

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = "linz"
PRIVATE = "linz_private"
JOB = "qv4-linz-load"
STAGING = "staging_linz_load"
READING = ("titles", "owners", "place_names", "read_set_aside", "loaded_pulls")
PRIVATE_READING = ("property_titles", "property_addresses", "addresses", "title_addresses", "title_address_points")
#: the typed sources, rebuilt whole every load; then every catalogue source read whole (capture.WHOLE)
TYPED = ("titles", "owners", "place_names", "property_titles", "property_addresses", "addresses")
WHOLE = tuple(s for s in capture.DUE_ORDER if s in capture.WHOLE)
SOURCES = TYPED + WHOLE
_CITE = ("document", "page", "place", "read_from", "reader", "profile", "profile_version")
#: a whole source's table: its row's id, every attribute as JSON, the geometry and its box (read.WHOLE_FIELDS)
WHOLE_COLUMNS = ("key",) + read.WHOLE_FIELDS + _CITE
COLUMNS = {
    "titles": ("key",) + read.KEEP["titles"][1] + _CITE,
    "owners": ("key", "title_key", "kind", "name") + read.KEEP["owners"][1] + _CITE,
    "place_names": ("key",) + read.KEEP["place_names"][1] + _CITE,
    "property_titles": ("key",) + read.KEEP["property_titles"][1] + _CITE,
    "property_addresses": ("key",) + read.KEEP["property_addresses"][1] + _CITE,
    "addresses": ("key",) + read.KEEP["addresses"][1] + read.WHOLE_FIELDS[1:] + _CITE,
    **{w: WHOLE_COLUMNS for w in WHOLE},
}
#: a whole source is not staged while the database's disk has less free than this (the cluster's data is on `/`)
DB_VOLUME = "/"
DB_FLOOR_BYTES = 150 * 1000 ** 3
TITLE_ADDRESS_COLUMNS = ("title_no", "address_id", "full_address", "address_lifecycle", "unit_of_property_id", "joined_by",
                         "titles_on_property", "addresses_on_property", "property_title_key", "property_address_key",
                         "address_key", "property_title_document", "property_address_document", "address_document")
#: how a title's address is joined: through the property spine, on ids, no geometry
JOINED_BY = ("property spine: table 113970 title_no → unit_of_property_id → table 115638 address_id → layer 123113 "
             "full_address")
#: and by geometry, for the titles the spine gives none
GEOMETRY_JOINED_BY = ("geometry: table 51569 title_no → par_id → layer 51571 parcel polygon → layer 123113 address points "
                      "strictly inside it (registers.linz.geo, ray casting, holes honoured; a point on a boundary may fall "
                      "either side)")
GEOMETRY_COLUMNS = ("title_no", "address_id", "full_address", "address_lifecycle", "par_id", "joined_by",
                    "titles_on_parcel", "addresses_in_parcel", "association_key", "parcel_key", "address_key",
                    "association_document", "parcel_document", "address_document")
#: the sources the geometry join reads
ASSOCIATION, PARCELS = "title_parcel_association_list", "parcels"
#: titles the spine does give an address, joined by geometry too and compared (counts only)
AGREEMENT_SAMPLE = 20_000


def private_of(schema: str) -> str:
    return PRIVATE if schema == SCHEMA else f"{schema}_private"


def table_of(schema: str, source: str) -> str:
    """Where a source's rows go: a private source's into the schema's private twin."""
    return f"{private_of(schema)}.{source}" if source in capture.PRIVATE_SOURCES else f"{schema}.{source}"


def join_sql(private: str) -> str:
    """Each title's street address, one row per title and address id, from the three private sources in `private`."""
    cols = ", ".join(TITLE_ADDRESS_COLUMNS)
    return f"""
INSERT INTO {private}.title_addresses ({cols})
SELECT DISTINCT ON (pt.title_no, a.address_id)
       pt.title_no, a.address_id, a.full_address, a.address_lifecycle, pt.unit_of_property_id, %s,
       tc.n, ac.n, pt.key, pa.key, a.key, pt.document, pa.document, a.document
FROM {private}.property_titles pt
JOIN {private}.property_addresses pa ON pa.unit_of_property_id = pt.unit_of_property_id
JOIN {private}.addresses a ON a.address_id = pa.address_id
JOIN (SELECT unit_of_property_id, count(DISTINCT title_no)::int AS n FROM {private}.property_titles GROUP BY 1) tc
  ON tc.unit_of_property_id = pt.unit_of_property_id
JOIN (SELECT unit_of_property_id, count(DISTINCT address_id)::int AS n FROM {private}.property_addresses GROUP BY 1) ac
  ON ac.unit_of_property_id = pt.unit_of_property_id
ORDER BY pt.title_no, a.address_id, pt.unit_of_property_id, pt.key, pa.key"""


def profile_version() -> int:
    from support import profiles
    v = profiles.reading_version(read.PROFILE)
    if v is not None:
        return int(v)
    with open(os.path.join(HERE, "profile-proposed.jsonl"), encoding="utf-8") as f:
        return max(json.loads(l)["version"] for l in f if l.strip() and json.loads(l)["slug"] == read.PROFILE)


def create_tables(conn, schema: str) -> None:
    private = private_of(schema)
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {private}")
    for t in READING:
        conn.execute(f"DROP TABLE IF EXISTS {schema}.{t} CASCADE")
    for t in PRIVATE_READING:
        conn.execute(f"DROP TABLE IF EXISTS {private}.{t} CASCADE")
    conn.execute(tables_sql(schema))


_GEOMETRY_DDL = "CREATE TABLE linz_private.title_address_points"


def tables_sql(schema: str, part: str = "reading") -> str:
    """tables.sql for `schema`: the reading (every table but title_address_points, which only the geometry join makes,
    so a load that could not join leaves the published one alone), or the geometry join's own table."""
    with open(os.path.join(HERE, "tables.sql"), encoding="utf-8") as f:
        sql = f.read()
    i = sql.index(_GEOMETRY_DDL)
    sql = sql[:i] if part == "reading" else sql[i:]
    return (sql.replace("CREATE TABLE linz_private.", f"CREATE TABLE {private_of(schema)}.")
            .replace("CREATE TABLE linz.", f"CREATE TABLE {schema}."))


def whole_sql(table: str, if_not_exists: bool = False) -> str:
    """A whole source's table: the row's id, every attribute as JSON, its geometry and box, the citation stamp."""
    ine = "IF NOT EXISTS " if if_not_exists else ""
    return f"""CREATE TABLE {ine}{table} (
    key text NOT NULL, fid text NOT NULL, props jsonb NOT NULL, geom_type text, geom text,
    west double precision, south double precision, east double precision, north double precision,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now())"""


def ensure_private(conn) -> None:
    """Every whole source's table and the geometry join's exist in `linz_private`, empty until a load publishes one,
    so the check finds every column a profile's field lands in before the first pull of each."""
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {PRIVATE}")
    for w in WHOLE:
        conn.execute(whole_sql(f"{PRIVATE}.{w}", if_not_exists=True))
    conn.execute(tables_sql(SCHEMA, "geometry").replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1))


def published_pull(conn, source: str):
    if not conn.execute("SELECT to_regclass('linz.loaded_pulls') IS NOT NULL").fetchone()[0]:
        return None
    r = conn.execute(f"SELECT pull_id FROM {SCHEMA}.loaded_pulls WHERE source = %s", (source,)).fetchone()
    return r[0] if r else None


def db_free() -> int:
    return shutil.disk_usage(DB_VOLUME).free


def _copy(conn, name: str, cols: tuple, rows) -> int:
    n = 0
    with conn.cursor().copy(f"COPY {name} ({', '.join(cols)}) FROM STDIN") as cp:
        for row in rows:
            cp.write_row(tuple(row.get(c) for c in cols))
            n += 1
    return n


def build(conn, schema: str, read_bytes=read_bytes, version: int = None, sources=SOURCES, log=print, full: bool = False,
          free_fn=None) -> dict:
    t0 = time.monotonic()
    version = version or profile_version()
    free_fn = free_fn or db_free
    create_tables(conn, schema)
    ensure_private(conn)
    counts, read_pages = {"seconds": 0}, []
    for source in sources:
        pages = capture.latest_pages(conn, source)
        if not pages:
            counts[f"{source}.pull"] = "none finished"
            continue
        pull_id = pages[0][3]
        if source in capture.WHOLE:
            if not full and published_pull(conn, source) == pull_id:
                counts[f"{source}.pull"] = "published"
                continue
            if free_fn() < DB_FLOOR_BYTES:
                counts[f"{source}.pull"] = f"held: the database's disk has under {DB_FLOOR_BYTES / 1e9:.0f} GB free"
                log(f"{SCHEMA}: {source}: {counts[f'{source}.pull']}")
                continue
            conn.execute(f"DROP TABLE IF EXISTS {table_of(schema, source)}")
            conn.execute(whole_sql(table_of(schema, source)))
        stated = conn.execute(f"SELECT stated FROM {capture.SCHEMA}.pulls WHERE pull_id = %s", (pull_id,)).fetchone()[0]
        landed = read_n = aside_n = 0
        for document, start_index, n_rows, _ in pages:
            rows, aside = read.read_page(read_bytes(document), source, document, version, start_index)
            landed += n_rows
            if rows or not aside:
                read_pages.append((document, source))
            read_n += _copy(conn, table_of(schema, source), COLUMNS[source], rows)
            aside_n += _copy(conn, f"{schema}.read_set_aside", ("source", "document", "place", "stage", "reason"),
                             [dict(a, source=source) for a in aside])
        conn.execute(f"INSERT INTO {schema}.loaded_pulls VALUES (%s, %s, %s, %s, %s, %s)",
                     (source, pull_id, stated, landed, read_n, aside_n))
        if source in capture.WHOLE:
            conn.execute(f"CREATE INDEX ON {table_of(schema, source)} (fid)")
        counts.update({f"{source}.pull": pull_id, f"{source}.stated": stated, f"{source}.landed": landed,
                       f"{source}.read": read_n, f"{source}.set_aside": aside_n})
        log(f"{SCHEMA}: {source}: {read_n:,} read, {aside_n} set aside of {landed:,} landed ({pull_id})")
    if all(f"{s}.read" in counts for s in capture.SPINE):
        counts.update(join_addresses(conn, private_of(schema)))
        log(f"{SCHEMA}: title_addresses: {counts['title_addresses.rows']:,} rows, "
            f"{counts['title_addresses.titles']:,} titles with an address")
    staged = {s for s in sources if f"{s}.read" in counts}
    counts.update(geometry_join(conn, schema, staged, log=log))
    # what each page has had extracted, by field (docs.extractions, a ledger: never wiped)
    from support.docstore import extraction
    from registers.linz import extracts
    ledger = extraction.record_many(conn, extracts.extracted(read_pages))
    counts.update({"extractions": ledger["rows"], "extractions written": ledger["written"],
                   "extractions not held": ledger["not held"]})
    counts["seconds"] = round(time.monotonic() - t0, 1)
    return counts


def join_addresses(conn, private: str) -> dict:
    """Join each title's street address in `private`; counts only."""
    for q in (f"CREATE INDEX ON {private}.property_titles (unit_of_property_id)",
              f"CREATE INDEX ON {private}.property_addresses (unit_of_property_id)",
              f"CREATE INDEX ON {private}.addresses (address_id)"):
        conn.execute(q)
    rows = conn.execute(join_sql(private), (JOINED_BY,)).rowcount
    titles = conn.execute(f"SELECT count(DISTINCT title_no) FROM {private}.title_addresses").fetchone()[0]
    return {"title_addresses.rows": rows, "title_addresses.titles": titles}


def _exists_with_rows(conn, table: str, where: str = "") -> bool:
    if not conn.execute("SELECT to_regclass(%s) IS NOT NULL", (table,)).fetchone()[0]:
        return False
    return conn.execute(f"SELECT EXISTS (SELECT 1 FROM {table} {where})").fetchone()[0]


def geometry_inputs(schema: str, staged: set) -> dict:
    """Where the geometry join reads each input: the staging copy of a source staged now, else the published one."""
    priv = private_of(schema)
    at = lambda s: f"{priv}.{s}" if s in staged else f"{PRIVATE}.{s}"  # noqa: E731
    return {"titles": f"{schema}.titles" if "titles" in staged else f"{SCHEMA}.titles",
            "spine": f"{priv}.title_addresses" if capture.SPINE <= staged else f"{PRIVATE}.title_addresses",
            "association": at(ASSOCIATION), "parcels": at(PARCELS), "addresses": at("addresses")}


def match_parcels(rows, grid) -> dict:
    """par_id → the address ids strictly inside its polygon, each parcel tested once: `rows` are (par_id, geom text)."""
    out = {}
    for par_id, geom in rows:
        if par_id in out:
            continue
        g = json.loads(geom) if geom else None
        out[par_id] = grid.within(g) if g else []
    return out


def geometry_join(conn, schema: str, staged: set, log=print) -> dict:
    """Each title the spine gives no address, its address by geometry (GEOMETRY_JOINED_BY), into
    `<private>.title_address_points`; and a sample of AGREEMENT_SAMPLE titles the spine does give an address, joined the
    same way and compared with the spine. Skipped, and the published table kept, until every input holds rows and the
    addresses carry their points. Counts only."""
    t0 = time.monotonic()
    src = geometry_inputs(schema, staged)
    priv = private_of(schema)
    lacking = [k for k, t in src.items() if not _exists_with_rows(conn, t)]
    if not lacking and not _exists_with_rows(conn, src["addresses"], "WHERE geom_type = 'Point'"):
        lacking = ["address points"]
    if lacking:
        log(f"{SCHEMA}: title_address_points: not joined, no rows yet in {', '.join(lacking)}")
        return {"title_address_points": f"not joined: {', '.join(lacking)} empty"}
    # every address point, in a grid of 0.002° cells
    grid = geo.Grid()
    with conn.cursor(name="linz_points") as cur:
        cur.itersize = 50_000
        cur.execute(f"SELECT address_id, west, south FROM {src['addresses']} WHERE geom_type = 'Point'")
        for address_id, x, y in cur:
            grid.add(address_id, x, y)
    conn.execute("CREATE TEMP TABLE linz_geo_titles (title_no text PRIMARY KEY, gap boolean NOT NULL) ON COMMIT DROP")
    conn.execute(f"INSERT INTO linz_geo_titles SELECT t.title_no, true FROM {src['titles']} t WHERE NOT EXISTS "
                 f"(SELECT 1 FROM {src['spine']} s WHERE s.title_no = t.title_no) ON CONFLICT DO NOTHING")
    conn.execute(f"INSERT INTO linz_geo_titles SELECT title_no, false FROM (SELECT DISTINCT title_no FROM {src['spine']}) d "
                 f"ORDER BY md5(title_no) LIMIT {AGREEMENT_SAMPLE} ON CONFLICT DO NOTHING")
    gap = conn.execute("SELECT count(*) FROM linz_geo_titles WHERE gap").fetchone()[0]
    # each title's parcels with their polygons; a parcel several titles share is tested once
    pairs, matched = [], {}
    with conn.cursor(name="linz_parcels") as cur:
        cur.itersize = 5_000
        cur.execute(f"""SELECT g.title_no, g.gap, a.props->>'par_id', a.key, a.document, p.key, p.document, p.geom
FROM linz_geo_titles g JOIN {src['association']} a ON a.props->>'title_no' = g.title_no
JOIN {src['parcels']} p ON p.fid = a.props->>'par_id' AND p.geom_type IN ('Polygon', 'MultiPolygon')""")
        for title_no, is_gap, par_id, a_key, a_doc, p_key, p_doc, geom in cur:
            if par_id not in matched:
                matched.update(match_parcels([(par_id, geom)], grid))
            pairs.append((title_no, is_gap, par_id, a_key, a_doc, p_key, p_doc))
    conn.execute("CREATE TEMP TABLE linz_geo_pairs (title_no text, gap boolean, par_id text, address_id bigint, "
                 "association_key text, parcel_key text, association_document text, parcel_document text) ON COMMIT DROP")
    with conn.cursor().copy("COPY linz_geo_pairs FROM STDIN") as cp:
        for title_no, is_gap, par_id, a_key, a_doc, p_key, p_doc in pairs:
            for address_id in matched.get(par_id, ()):
                cp.write_row((title_no, is_gap, par_id, address_id, a_key, p_key, a_doc, p_doc))
    titles_with_parcel = {(t, g) for t, g, *_ in pairs}
    conn.execute(f"DROP TABLE IF EXISTS {priv}.title_address_points")
    conn.execute(tables_sql(schema, "geometry"))
    cols = ", ".join(GEOMETRY_COLUMNS)
    rows = conn.execute(f"""INSERT INTO {priv}.title_address_points ({cols})
SELECT DISTINCT ON (x.title_no, x.address_id)
       x.title_no, x.address_id, ad.full_address, ad.address_lifecycle, x.par_id, %s, tc.n, ac.n,
       x.association_key, x.parcel_key, ad.key, x.association_document, x.parcel_document, ad.document
FROM linz_geo_pairs x
JOIN {src['addresses']} ad ON ad.address_id = x.address_id
JOIN (SELECT props->>'par_id' AS par_id, count(DISTINCT props->>'title_no')::int AS n FROM {src['association']}
      GROUP BY 1) tc ON tc.par_id = x.par_id
JOIN (SELECT par_id, count(DISTINCT address_id)::int AS n FROM linz_geo_pairs GROUP BY 1) ac ON ac.par_id = x.par_id
WHERE x.gap
ORDER BY x.title_no, x.address_id, x.par_id""", (GEOMETRY_JOINED_BY,)).rowcount
    one = lambda q: conn.execute(q).fetchone()[0]  # noqa: E731
    reached = one(f"SELECT count(DISTINCT title_no) FROM {priv}.title_address_points")
    # the sample: does the geometry give a title one of the addresses the spine gives it?
    sample = one("SELECT count(*) FROM linz_geo_titles WHERE NOT gap")
    s_polygon = sum(1 for _, g in titles_with_parcel if not g)
    s_found = one("SELECT count(DISTINCT title_no) FROM linz_geo_pairs WHERE NOT gap")
    s_agree = one(f"SELECT count(DISTINCT x.title_no) FROM linz_geo_pairs x JOIN {src['spine']} s "
                  f"ON s.title_no = x.title_no AND s.address_id = x.address_id WHERE NOT x.gap")
    out = {"title_address_points.rows": rows, "title_address_points.titles": reached, "geometry.gap_titles": gap,
           "geometry.gap_titles_with_a_polygon": sum(1 for _, g in titles_with_parcel if g),
           "geometry.parcels_tested": len(matched), "geometry.address_points": grid.n,
           "geometry.sample_titles": sample, "geometry.sample_with_a_polygon": s_polygon,
           "geometry.sample_with_an_address": s_found, "geometry.sample_agreeing": s_agree,
           "geometry.seconds": round(time.monotonic() - t0, 1)}
    log(f"{SCHEMA}: title_address_points: {reached:,} of {gap:,} titles without a spine address reached by geometry "
        f"({rows:,} rows); sample: {s_agree:,} of {s_found:,} titles with a geometry address agree with the spine "
        f"({sample:,} sampled, {s_polygon:,} with a polygon)")
    return out


def load(conn, schema: str, log=print) -> int:
    """The merge gate's staging step (support/staging)."""
    from registers.linz import check
    conn.execute(capture.capture_sql())
    counts = build(conn, schema, log=log)
    problems = check.reading(conn, schema)
    log(f"{SCHEMA}: into {schema}; " + ("; ".join(problems) or "reconciles"))
    return sum(v for k, v in counts.items() if k.endswith(".read"))


INDEXES = (
    "CREATE INDEX IF NOT EXISTS linz_titles_title_no ON linz.titles (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_owners_title_no ON linz.owners (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_owners_name ON linz.owners (lower(name))",
    "CREATE INDEX IF NOT EXISTS linz_place_names_name ON linz.place_names (lower(name))",
    "CREATE INDEX IF NOT EXISTS linz_title_addresses_title_no ON linz_private.title_addresses (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_title_addresses_address ON linz_private.title_addresses (address_id)",
    "CREATE INDEX IF NOT EXISTS linz_title_address_points_title_no ON linz_private.title_address_points (title_no)",
    "CREATE INDEX IF NOT EXISTS linz_title_address_points_address ON linz_private.title_address_points (address_id)",
)


def private_views(conn) -> list:
    """The lane's own private views (its private-view file beside this one, which the links lane alone reads), made
    again after a private table is moved in: each under its own savepoint, a view whose table is not there yet waits."""
    from support import db
    path = db.private_view_files().get("linz")
    if not path:
        return []
    conn.execute(f"CREATE SCHEMA IF NOT EXISTS {db.PRIVATE_VIEWS}")
    made = []
    with open(path, encoding="utf-8") as f:
        for s in db.private_view_statements(f.read()):
            try:
                with conn.transaction():
                    conn.execute(s)
                made.append(s.split()[4])
            except Exception:     # the lane's table not there yet: the view waits for its load
                pass
    return made


def publish_plan(staged: set, geometry: bool) -> list:
    """What publishing a staging does, in order: ("copy", table) for a public table (its views stand on it), ("move",
    table) for a private one (the staged table replaces the published one whole: a whole source may be tens of millions
    of rows, and a typed private table's columns may have grown)."""
    joined = capture.SPINE <= staged
    out = []
    for source in sorted(staged):
        out.append(("move" if source in capture.PRIVATE_SOURCES else "copy", source))
    if joined:
        out.append(("move", "title_addresses"))
    if geometry:
        out.append(("move", "title_address_points"))
    return out


def publish(conn, staging: str, log=print) -> None:
    """The staged sources replace the lane's; a source the staging did not load keeps what is published, and so does
    the geometry join's table when this load could not join."""
    staged = {r[0] for r in conn.execute(f"SELECT source FROM {staging}.loaded_pulls")}
    geometry = conn.execute("SELECT to_regclass(%s) IS NOT NULL",
                            (f"{private_of(staging)}.title_address_points",)).fetchone()[0]
    plan = publish_plan(staged, geometry)
    with conn.transaction():
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {PRIVATE}")
        exists = conn.execute("SELECT to_regclass('linz.loaded_pulls') IS NOT NULL").fetchone()[0]
        if not exists:
            create_tables(conn, SCHEMA)
        ensure_private(conn)
        for t in ("read_set_aside", "loaded_pulls"):
            conn.execute(f"DELETE FROM {SCHEMA}.{t} WHERE source = ANY(%s)", (sorted(staged),))
            conn.execute(f"INSERT INTO {SCHEMA}.{t} SELECT * FROM {staging}.{t}")
        for how, table in plan:
            if how == "copy":
                conn.execute(f"TRUNCATE {SCHEMA}.{table}")
                conn.execute(f"INSERT INTO {SCHEMA}.{table} SELECT * FROM {staging}.{table}")
            else:
                # CASCADE takes the lane's own pub_private views with it (the links lane's reading of it); they are
                # made again below, in the same transaction
                conn.execute(f"DROP TABLE IF EXISTS {PRIVATE}.{table} CASCADE")
                conn.execute(f"ALTER TABLE {private_of(staging)}.{table} SET SCHEMA {PRIVATE}")
        for q in INDEXES:
            conn.execute(q)
        private_views(conn)
        with open(os.path.join(HERE, "publish.sql"), encoding="utf-8") as f:
            conn.execute(f.read())
    log(f"{SCHEMA}: published {', '.join(sorted(staged)) or 'nothing'} from {staging}"
        + ("; title_addresses joined, kept private" if capture.SPINE <= staged else "")
        + ("; title_address_points joined by geometry, kept private" if geometry else ""))


def job(log=print) -> int:
    """qv4-linz-load: build in staging, hold it to the checks, publish only then."""
    from support import db
    from registers.linz import check
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '1800s'")
        conn.execute(capture.capture_sql())
        with conn.transaction():
            counts = build(conn, STAGING, log=log)
        problems = check.reading(conn, STAGING)
        detail = ", ".join(f"{k} {v:,}" if isinstance(v, int) else f"{k} {v}" for k, v in counts.items()
                           if k.endswith((".read", ".set_aside", ".stated")) or v == "none finished")
        detail += "; " + ("; ".join(problems) or "reconciles")
        if problems:
            log(f"{SCHEMA}: RED, nothing published: " + detail)
            jobrun.record(JOB, False, "nothing published: " + detail, started, {})
            return 1
        publish(conn, STAGING, log)
    jobrun.record(JOB, True, "published: " + detail, started, {k: v for k, v in counts.items() if isinstance(v, int)})
    log(f"{SCHEMA}: published: " + detail)
    return 0


def main(argv=None) -> int:
    from support import db
    ap = argparse.ArgumentParser(prog="python -m registers.linz.load")
    ap.add_argument("--schema", default="staging_linz_session")
    ap.add_argument("--job", action="store_true")
    ap.add_argument("--full", action="store_true", help="stage every whole source, published or not")
    ap.add_argument("--only", nargs="*", help="the sources to stage (the geometry join reads the rest as published)")
    a = ap.parse_args(argv)
    if a.job:
        return job()
    if not a.schema.startswith(("scratch_", "staging_")):
        print(f"{SCHEMA}: a session loads only a scratch or staging schema")
        return 2
    from registers.linz import check
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '1800s'")
        conn.execute(capture.capture_sql())
        with conn.transaction():
            counts = build(conn, a.schema, full=a.full, sources=tuple(a.only) if a.only else SOURCES)
        problems = check.reading(conn, a.schema)
    for k, v in counts.items():
        print(f"{SCHEMA}: {k}: {v}")
    print(f"{SCHEMA}: check: " + ("; ".join(problems) or "reconciles"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
