"""How fresh the ingest MCP's copies are (ruling 159, 10 November 2026).

The boxes read several sources only through the MCP's copies (`--from-mcp`),
so a register is only as fresh as its copy. The MCP's `corpora` answer says,
per corpus, its record count, `ingest_cursor`, `arrivals_last_24h` and
`newest_arrival`; its `pipeline` answer names the provider's gathering lanes
and the corpus each fills. Every time the pull reads `corpora` (every six
hours, and the weekly re-walk), one row per corpus goes into
`mcpsource.freshness`, never wiped, so a corpus that stops growing shows in
its own history even when nothing else changes. `pipeline` is asked once
beside it, without retries: when it does not answer, the rows say so
(`pipeline_read` false) and the lane is not guessed.

    record(conn, schema, corpora, pipeline, at)   one row per corpus of the listing
    latest(conn, schema)                          corpus -> its newest row
    parse_time(s)                                 the MCP's four spellings of a time

The lights (checks/source_lights.py) judge each corpus by the provider's
`newest_arrival`, never by our pull, against its source's cadence
(checks/mcp_cadence.toml)."""
import datetime as dt


def parse_time(value):
    """A time the MCP serves, as an aware datetime, or None. It spells them
    four ways on 10 November 2026: `…T…+00:00`, `…T…Z`, `… …+00:00` and
    `… …+13:00` (estate-courts); a time with no zone is taken as UTC."""
    if not value or not isinstance(value, str):
        return None
    try:
        t = dt.datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def _int(v):
    return int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def pipeline_lanes(pipeline) -> dict:
    """corpus -> (lane name, status) from a `pipeline` answer; {} when there is none."""
    out = {}
    if not isinstance(pipeline, dict):
        return out
    for lane in pipeline.get("lanes") or []:
        if isinstance(lane, dict) and lane.get("corpus") and lane.get("name"):
            out.setdefault(str(lane["corpus"]), (str(lane["name"]), str(lane.get("status") or "")))
    return out


def rows_of(corpora: list, pipeline, at: dt.datetime) -> list:
    """The freshness rows for one reading of `corpora` (and `pipeline`, or None when it did not answer)."""
    lanes, read = pipeline_lanes(pipeline), isinstance(pipeline, dict)
    out = []
    for c in corpora or []:
        if not (isinstance(c, dict) and c.get("name")):
            continue
        lane = lanes.get(c["name"])
        out.append((at, c["name"], _int(c.get("records")), _int(c.get("ingest_cursor")),
                    parse_time(c.get("newest_arrival")), _int(c.get("arrivals_last_24h")),
                    str(c["date_to"]) if c.get("date_to") else None,
                    lane[0] if lane else None, lane[1] if lane else None, read))
    return out


COLUMNS = ("at", "corpus", "records", "ingest_cursor", "newest_arrival", "arrivals_last_24h", "date_to",
           "pipeline_lane", "pipeline_status", "pipeline_read")


def record(conn, schema: str, corpora: list, pipeline=None, at: dt.datetime = None) -> int:
    """One row per corpus of the listing, at `at` (now); the rows written."""
    at = at or dt.datetime.now(dt.timezone.utc)
    rows = rows_of(corpora, pipeline, at)
    if rows:
        with conn.cursor() as cur:
            cur.executemany(f"INSERT INTO {schema}.freshness ({', '.join(COLUMNS)}) VALUES "
                            f"({', '.join(['%s'] * len(COLUMNS))}) ON CONFLICT (corpus, at) DO NOTHING", rows)
    return len(rows)


def latest(conn, schema: str = "mcpsource") -> dict:
    """corpus -> its newest row as a dict, plus `grew_at`: when its record count last rose in our history
    (None when it never has inside what we hold). {} before the first pull has made the table: the lights then say
    "no freshness measure yet"."""
    if conn.execute("SELECT to_regclass(%s)", (f"{schema}.freshness",)).fetchone()[0] is None:
        return {}
    rows = conn.execute(
        f"SELECT DISTINCT ON (corpus) {', '.join(COLUMNS)} FROM {schema}.freshness ORDER BY corpus, at DESC").fetchall()
    out = {r[1]: dict(zip(COLUMNS, r)) for r in rows}
    for corpus, grew in conn.execute(
            f"SELECT corpus, max(at) FROM (SELECT corpus, at, records, lag(records) OVER (PARTITION BY corpus ORDER BY at) "
            f"AS before FROM {schema}.freshness) x WHERE records > before GROUP BY corpus").fetchall():
        if corpus in out:
            out[corpus]["grew_at"] = grew
    for v in out.values():
        v.setdefault("grew_at", None)
    return out


def poll_pipeline(client, log=None):
    """The `pipeline` answer, asked once (it is telemetry: no retries, no wait); None when it does not answer."""
    from support.mcpsource.client import McpError
    try:
        got = client.call("pipeline", {})
    except McpError as e:
        if log:
            log(f"mcpsource: `pipeline` did not answer ({e.why[:200]}); freshness rows carry no lane")
        return None
    return got if isinstance(got, dict) else None
