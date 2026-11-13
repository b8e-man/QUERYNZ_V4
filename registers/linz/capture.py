"""How this lane's documents arrive (step 8.3; Arthur, 2 November 2026): the LINZ Data Service's WFS, through the fetch
gate and the landing wrapper only, under `docs/legal/positions/linz-data-service.md`.

Three sources, each read whole and landed page by page, by its sha256:

  owners       table 51564, "NZ Property Titles Owners List" (aspatial): one row per owner of a title, owner_type
               corporate or individual, the corporate name or the prime surname and other names, the title number, the
               land district, the estate share, the status. Under the LINZ Licence for Personal Data.
  titles       layer 50804, "NZ Property Titles", read WITHOUT its geometry (`PROPERTYNAME` names the attribute columns
               only): title number, status, type, land district, issue date, guarantee status, estate description,
               number of owners. CC BY 4.0.
  place_names  layer 51681, "NZ Place Names (NZGB)", without geometry: the gazetteer's name, its feature type, status,
               district. CC BY 4.0.

And three private sources, the property spine that gives each title its street address (Arthur, 3 November 2026: "why
no address on land ownership?"; "gather everything"), read into `linz_private` and never published (hard limit 15 binds
a product's surface, ruling 102):

  property_titles     table 113970, "NZ Properties: Property-Title Reference": a unit of property
                      (a rating unit) and a title number on it. CC BY 4.0.
  property_addresses  table 115638, "NZ Properties: Property-Address Reference": a unit of property and an address id
                      on it. CC BY 4.0.
  addresses           layer 123113, "NZ Addresses" (AIMS), without its geometry: an address id and the address as LINZ
                      gives it. CC BY 4.0.

A title's address is then a join on the two ids, no geometry (registers.linz.load).

And everything else (Arthur, 4 November 2026, ruling 142: "Get LINZ and all available information and put it all in
the database. Always do this. we want everything"): every layer and table of the service's catalogue that bears on land
(`registers.linz.catalogue`, docs/research/linz-everything-2026-11-04.md), each read WHOLE (`WHOLE`): no `propertyName`,
so every attribute and the geometry, into `linz_private` only. The addresses (layer 123113) are read whole too, so each
address carries its point; the other five keep their typed columns. A geometry is now wanted (the rule "never read a
geometry" is gone); a public source still never asks for an address or a geometry column (`NEVER`).

The key is ours (`~/.querynz/linz.env`, `LINZ_API_KEY`), read at the call and sent as an `Authorization: key …` header,
never in a URL, a log, a landed document's name or a printed line.

A pull, in order: `--survey` (a handful of requests, any hour: each source's record count, from WFS `resultType=hits`, and
a 100-row sample page's bytes, so the whole pull's size is projected before anything large is asked for); then `--pull
SOURCE` pages the source `PAGE` rows at a time, oldest key first (`sortBy` on the source's id), off-peak only unless
`--anytime`, one request at a time at the gate's floor or the stated crawl delay, each page landed once by hash and
recorded in `linz.pages`; a source projected over `MAX_PULL_BYTES` is refused until `--allow-large` is given.

Politeness (hard limit 7): one request at a time, the gate's floor, off-peak, nothing fetched twice within a pull (a page
landed is never asked again for that pull). A 401, 403, 429, a 5xx or a challenge page is a failed read (hard limit 6):
logged, and the pull stops; the next run resumes from the last page landed.

    python -m registers.linz.capture --survey
    python -m registers.linz.capture --pull owners|titles|place_names|property_titles|property_addresses|addresses|<a
                                     WHOLE source> [--anytime] [--budget-s N] [--allow-large]
    python -m registers.linz.capture --due      the night: every due source, the five typed first, then the catalogue by
                                                tranche and size; a source not yet surveyed is surveyed first
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.parse
from zoneinfo import ZoneInfo

import support.fetchgate as fg
from registers.linz import catalogue as K

SOURCE = SCHEMA = "linz"
JOB = "qv4-linz-capture"
HOST = "data.linz.govt.nz"
WFS = f"https://{HOST}/services/wfs"
KEY_FILE = "linz.env"
KEY_NAME = "LINZ_API_KEY"
NZ = ZoneInfo("Pacific/Auckland")
PAGE = 10_000
OFF_PEAK = (22, 6)
#: a source projected over this is refused until --allow-large (the step's brief: report a layer over 5 GB first)
MAX_PULL_BYTES = 5 * 1000 ** 3
SAMPLE_ROWS = 100
DEFAULT_BUDGET_S = 6 * 3600
#: a pull stops when the document store's disk has less free than this (everything is a billion rows; the store is shared)
STORE_FLOOR_BYTES = 200 * 1000 ** 3
LICENCE_CC = "CC BY 4.0: sourced from the LINZ Data Service and licensed for reuse under CC BY 4.0"
LICENCE_PERSONAL = ("LINZ Licence for Personal Data (CC BY 4.0 + personal-data terms): never indexed by a public search "
                    "engine; supplied onward only under the licence; refreshed regularly; amended or deleted within five "
                    "business days of LINZ's request")

#: source → (typeName, id column to sort on, the attribute columns read: never a geometry; an address only in a
#: private source; licence)
SOURCES = {
    "owners": ("table-51564", "id",
               ("id", "title_no", "status", "land_district", "estate_share", "owner_type", "prime_surname",
                "prime_other_names", "corporate_name", "name_suffix"),
               LICENCE_PERSONAL),
    "titles": ("layer-50804", "id",
               ("id", "title_no", "status", "type", "land_district", "issue_date", "guarantee_status",
                "estate_description", "number_owners", "spatial_extents_shared"),
               LICENCE_CC),
    "place_names": ("layer-51681", "name_id",
                    ("name_id", "feat_id", "name", "status", "feat_type", "maori_name", "land_district",
                     "territorial_authority", "region", "crd_latitude", "crd_longitude", "info_origin", "info_description",
                     "treaty_legislation", "nzgb_ref"),
               LICENCE_CC),
    "property_titles": ("table-113970", "id", ("id", "title_no", "unit_of_property_id"), LICENCE_CC),
    "property_addresses": ("table-115638", "id", ("id", "unit_of_property_id", "address_id"), LICENCE_CC),
    # asked whole since 4 November 2026 (ASKED_WHOLE): every column and the address's point
    "addresses": ("layer-123113", "address_id", (), LICENCE_CC),
}
#: every other taken entry of the catalogue, read whole (every attribute and the geometry) into `linz_private`:
#: name → (typeName, the columns its pages are sorted on, licence, its geometry column or None, its tranche)
WHOLE = {e[1]: (e[0], e[6], LICENCE_PERSONAL if e[3] == "personal" else LICENCE_CC, e[5], e[7])
         for e in K.ENTRIES if e[7] and e[1] not in SOURCES}
for _name, (_type, _sort, _licence, _geom, _tranche) in WHOLE.items():
    SOURCES[_name] = (_type, ",".join(_sort), (), _licence)
#: the sources asked for every column the service has, the geometry with it (no propertyName)
ASKED_WHOLE = frozenset(WHOLE) | {"addresses"}
#: the property spine: a title → its unit of property → an address id → the address (load.join_sql)
SPINE = frozenset({"property_titles", "property_addresses", "addresses"})
#: the sources read into `linz_private` only, never into a published table: the only ones an address or a geometry is
#: read from
PRIVATE_SOURCES = SPINE | frozenset(WHOLE)
#: a typed private source's list never names a geometry (it is asked whole, or not at all)
NEVER_GEOMETRY = re.compile(r"geom|shape", re.I)
#: a column that would carry an address is never asked for of a public source (hard limit 15)
NEVER = re.compile(r"address|street|road_name|postal|geom|shape", re.I)


# ── pure pieces ───────────────────────────────────────────────────────────────

def columns(source: str) -> tuple:
    """The columns asked of a source: () for a source asked whole (every column and its geometry)."""
    if source in ASKED_WHOLE:
        if source not in PRIVATE_SOURCES:
            raise ValueError(f"{source}: only a private source is read whole")
        return ()
    cols = SOURCES[source][2]
    never = NEVER_GEOMETRY if source in PRIVATE_SOURCES else NEVER
    bad = [c for c in cols if never.search(c)]
    if bad:
        what = "a geometry" if source in PRIVATE_SOURCES else "an address or a geometry"
        raise ValueError(f"{source}: a column that may carry {what} is never read: {bad}")
    return cols


def wfs_url(source: str, start: int = 0, count: int = PAGE, hits: bool = False, cols: tuple = None) -> str:
    """The WFS GetFeature URL for one page of a source (or its count with `hits`); never carries the key."""
    type_name, sort_col, _, _ = SOURCES[source]
    q = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": type_name}
    if hits:
        q["resultType"] = "hits"
    else:
        q.update({"outputFormat": "json", "startIndex": str(start), "count": str(count), "sortBy": sort_col})
        cols = columns(source) if cols is None else cols
        if cols:
            q["propertyName"] = ",".join(cols)
    return WFS + "?" + urllib.parse.urlencode(q)


_MATCHED = re.compile(rb'numberMatched="(\d+)"')


def number_matched(body: bytes):
    m = _MATCHED.search(body or b"")
    return int(m.group(1)) if m else None


def rows_of(body: bytes) -> list:
    """The attribute rows of a GeoJSON page: [properties], geometry never kept."""
    doc = json.loads(body)
    return [f.get("properties") or {} for f in doc.get("features") or []]


def projected_bytes(sample_bytes: int, sample_rows: int, total: int) -> int:
    return int(sample_bytes / sample_rows * total) if sample_rows else 0


def off_peak(now_local: dt.datetime) -> bool:
    start, end = OFF_PEAK
    return now_local.hour >= start or now_local.hour < end


def api_key() -> str:
    """Our LINZ key, read now from the credential folder. Never print it."""
    from support import db
    path = os.path.join(db.CRED_DIR, KEY_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(KEY_NAME + "="):
                    return line.split("=", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    raise RuntimeError(f"no {KEY_NAME} in the credential folder's {KEY_FILE}: Arthur registers it himself")


def headers(key: str) -> dict:
    return {"Authorization": f"key {key}", "Accept": "application/json"}


# ── the database side ─────────────────────────────────────────────────────────

def capture_sql(schema: str = SCHEMA) -> str:
    return f"""
CREATE SCHEMA IF NOT EXISTS {schema};
-- one row per pull of a source: when it began, the count the service stated, how far it got
CREATE TABLE IF NOT EXISTS {schema}.pulls (
    pull_id      text PRIMARY KEY,                      -- <source>-<UTC stamp>
    source       text NOT NULL,
    stated       integer,                               -- the service's numberMatched at the pull's start
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz,                           -- set when the last page (fewer rows than asked) is landed
    licence      text NOT NULL
);
-- one row per page landed: its place in the pull and its hash
CREATE TABLE IF NOT EXISTS {schema}.pages (
    pull_id      text NOT NULL REFERENCES {schema}.pulls (pull_id),
    start_index  integer NOT NULL,
    rows         integer NOT NULL,
    document     text NOT NULL CHECK (document ~ '^[0-9a-f]{{64}}$'),
    landed_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (pull_id, start_index)
);
-- one row per survey of a source
CREATE TABLE IF NOT EXISTS {schema}.surveys (
    source       text NOT NULL,
    stated       integer,
    sample_rows  integer,
    sample_bytes integer,
    projected    bigint,
    surveyed_at  timestamptz NOT NULL DEFAULT now()
);
"""


class Blocked(Exception):
    pass


class Transient(Exception):
    """The server's own error (HTTP 5xx): the pull stops where it is and resumes on the next run."""


def store_free() -> int:
    import shutil
    from support.docstore import landing
    return shutil.disk_usage(landing.ROOT).free


class Puller:
    def __init__(self, conn, *, key: str = None, opener=None, land_fn=None, pacer=None, now=None, log=print, free_fn=None):
        from support.docstore.landing import land
        self.conn, self.key = conn, key
        self.free_fn = free_fn or store_free
        self.opener = opener or fg.open_url
        self.land_fn = land_fn or land
        self.pacer = pacer or fg.Pacer()
        self.now = now or (lambda: dt.datetime.now(NZ))
        self.log = log

    def get(self, url: str):
        f = self.opener(url, timeout=300, headers=headers(self.key or api_key()), pacer=self.pacer)
        if not f.blocked and 500 <= f.status < 600:
            raise Transient(f"HTTP {f.status} at {url}")
        if f.blocked or f.status != 200:
            raise Blocked(f"a failed read at {url}: {f.blocked or f'HTTP {f.status}'}")
        return f

    def survey(self, source: str) -> dict:
        stated = number_matched(self.get(wfs_url(source, hits=True)).body)
        # the source's own column names first (one row, every attribute), so the columns read are the ones it has
        one = rows_of(self.get(wfs_url(source, 0, 1, cols=())).body)
        have = sorted(one[0]) if one else []
        want = tuple(c for c in columns(source) if c in have)
        page = self.get(wfs_url(source, 0, SAMPLE_ROWS, cols=want))
        n = len(rows_of(page.body))
        out = {"source": source, "stated": stated, "sample_rows": n, "sample_bytes": len(page.body),
               "projected": projected_bytes(len(page.body), n, stated or 0),
               "has": have, "missing": [c for c in columns(source) if c not in have]}
        self.conn.execute(f"INSERT INTO {SCHEMA}.surveys (source, stated, sample_rows, sample_bytes, projected) "
                          f"VALUES (%(source)s, %(stated)s, %(sample_rows)s, %(sample_bytes)s, %(projected)s)", out)
        return out

    def open_pull(self, source: str) -> tuple:
        """The unfinished pull of the source to resume, or a new one: (pull_id, next start index, stated)."""
        r = self.conn.execute(f"SELECT pull_id, stated FROM {SCHEMA}.pulls WHERE source = %s AND finished_at IS NULL "
                              f"ORDER BY started_at DESC LIMIT 1", (source,)).fetchone()
        if r:
            nxt = self.conn.execute(f"SELECT coalesce(max(start_index + rows), 0) FROM {SCHEMA}.pages WHERE pull_id = %s",
                                    (r[0],)).fetchone()[0]
            return r[0], nxt, r[1]
        stated = number_matched(self.get(wfs_url(source, hits=True)).body)
        pull_id = f"{source}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
        self.conn.execute(f"INSERT INTO {SCHEMA}.pulls (pull_id, source, stated, licence) VALUES (%s, %s, %s, %s)",
                          (pull_id, source, stated, SOURCES[source][3]))
        self.conn.commit()
        return pull_id, 0, stated

    def pull(self, source: str, *, budget_s: float = DEFAULT_BUDGET_S, anytime: bool = False) -> dict:
        t0 = time.monotonic()
        pull_id, start, stated = self.open_pull(source)
        counts = {"pull": pull_id, "stated": stated, "pages": 0, "rows": 0, "finished": False, "stopped": ""}
        while True:
            if not anytime and not off_peak(self.now()):
                counts["stopped"] = "off-peak ended"
                break
            if time.monotonic() - t0 >= budget_s:
                counts["stopped"] = "budget spent"
                break
            if self.free_fn() < STORE_FLOOR_BYTES:
                counts["stopped"] = f"the document store has under {STORE_FLOOR_BYTES / 1e9:.0f} GB free"
                break
            url = wfs_url(source, start, PAGE)
            try:
                f = self.get(url)
            except (Transient, OSError) as exc:   # 13 Nov an HTTP 502, 14 Nov "no route to host", hours into a pull
                self.conn.commit()
                counts["stopped"] = f"a failed read in transport at row {start:,} ({str(exc)[:160]}); resumes next run"
                break
            rows = rows_of(f.body)
            ref, _ = self.land_fn(f.body, name=url, source=SOURCE, conn=self.conn, name_kind="url",
                                  content_type="application/json")
            self.conn.execute(f"INSERT INTO {SCHEMA}.pages (pull_id, start_index, rows, document) VALUES (%s, %s, %s, %s) "
                              f"ON CONFLICT DO NOTHING", (pull_id, start, len(rows), ref.sha256))
            counts["pages"] += 1
            counts["rows"] += len(rows)
            start += len(rows)
            if len(rows) < PAGE:
                self.conn.execute(f"UPDATE {SCHEMA}.pulls SET finished_at = now() WHERE pull_id = %s", (pull_id,))
                self.conn.commit()
                counts["finished"] = True
                break
            self.conn.commit()
        return counts


#: a source is pulled again when its newest finished pull is older than this (the personal-data licence's regular refresh);
#: a catalogue source by its tranche's (catalogue.REFRESH_DAYS)
REFRESH_DAYS = 7
#: the order a night takes the due sources in: the five typed sources small first, so a night cut short still finishes
#: something, then the catalogue's by tranche and, within one, by size
TYPED_ORDER = ("place_names", "property_titles", "addresses", "titles", "property_addresses", "owners")
_ROWS = {e[1]: e[4] for e in K.ENTRIES}
DUE_ORDER = TYPED_ORDER + tuple(sorted(WHOLE, key=lambda n: (WHOLE[n][4], _ROWS[n], n)))
#: a source whose asking changed: a pull finished before this is due at once (the addresses, asked whole from 4 November)
WIDENED = {"addresses": dt.datetime(2026, 11, 4, tzinfo=dt.timezone.utc)}


def refresh_days(source: str) -> int:
    return K.REFRESH_DAYS[WHOLE[source][4]] if source in WHOLE else REFRESH_DAYS


def due_sources(conn, now: dt.datetime = None) -> list:
    """The sources a night should pull, in DUE_ORDER: one with an unfinished pull (to resume), none finished within its
    refresh, or none finished since it was widened."""
    now = now or dt.datetime.now(dt.timezone.utc)
    out = []
    for s in DUE_ORDER:
        open_ = conn.execute(f"SELECT 1 FROM {SCHEMA}.pulls WHERE source = %s AND finished_at IS NULL LIMIT 1", (s,)).fetchone()
        last = conn.execute(f"SELECT max(finished_at) FROM {SCHEMA}.pulls WHERE source = %s", (s,)).fetchone()[0]
        if open_ or last is None or (now - last).days >= refresh_days(s) or (s in WIDENED and last < WIDENED[s]):
            out.append(s)
    return out


def reported(source: str) -> bool:
    """A source the inventory reported, its rows counted (docs/research/linz-everything-2026-11-04.md): a pull over
    MAX_PULL_BYTES is not refused for it (the brief: report a layer over 5 GB first; the inventory is that report)."""
    return source in WHOLE


def latest_pages(conn, source: str) -> list:
    """The pages of the newest finished pull of a source, in order: [(document, start_index, rows, pull_id)]."""
    r = conn.execute(f"SELECT pull_id FROM {SCHEMA}.pulls WHERE source = %s AND finished_at IS NOT NULL "
                     f"ORDER BY finished_at DESC LIMIT 1", (source,)).fetchone()
    if not r:
        return []
    return [tuple(x) + (r[0],) for x in conn.execute(
        f"SELECT document, start_index, rows FROM {SCHEMA}.pages WHERE pull_id = %s ORDER BY start_index", (r[0],))]


def main(argv=None) -> int:
    from support import db, jobrun
    ap = argparse.ArgumentParser(prog="python -m registers.linz.capture")
    ap.add_argument("--survey", nargs="?", const="all", choices=["all"] + sorted(SOURCES))
    ap.add_argument("--pull", choices=sorted(SOURCES))
    ap.add_argument("--due", action="store_true", help="the night's job: every due source, small first, within the budget")
    ap.add_argument("--anytime", action="store_true")
    ap.add_argument("--allow-large", action="store_true")
    ap.add_argument("--budget-s", type=float, default=DEFAULT_BUDGET_S)
    a = ap.parse_args(argv)
    started = jobrun.now()
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = '120s'")
        conn.execute(capture_sql())
        conn.commit()
        p = Puller(conn)
        try:
            if a.survey:
                for s in (SOURCES if a.survey == "all" else (a.survey,)):
                    out = p.survey(s)
                    conn.commit()
                    print(f"linz: {s}: stated {out['stated']:,} rows; {out['sample_rows']} sample rows "
                          f"{out['sample_bytes']:,} bytes; projected {out['projected'] / 1e9:.2f} GB; columns it has: "
                          f"{', '.join(out['has'])}; asked for and missing: {', '.join(out['missing']) or 'none'}")
                return 0
            if a.due:
                t0, lines, ok = time.monotonic(), [], True
                for s in due_sources(conn):
                    left = a.budget_s - (time.monotonic() - t0)
                    if left <= 0:
                        lines.append(f"{s}: budget spent")
                        break
                    last = conn.execute(f"SELECT projected FROM {SCHEMA}.surveys WHERE source = %s ORDER BY surveyed_at "
                                        f"DESC LIMIT 1", (s,)).fetchone()
                    try:
                        if not last and (a.anytime or off_peak(p.now())):
                            # a catalogue source not yet surveyed: its count and a sample page first, then the pull
                            last = (p.survey(s)["projected"],)
                            conn.commit()
                        if not last or (last[0] > MAX_PULL_BYTES and not reported(s)):
                            lines.append(f"{s}: not surveyed or projected over {MAX_PULL_BYTES / 1e9:.0f} GB; not pulled")
                            continue
                        out = p.pull(s, budget_s=left, anytime=a.anytime)
                    except Blocked as e:
                        conn.commit()
                        lines.append(f"{s}: stopped: {e}")
                        ok = False
                        break
                    lines.append(f"{s}: {out['pages']} pages, {out['rows']:,} rows of {out['stated'] or 0:,} stated"
                                 + ("; finished" if out["finished"] else f"; stopped: {out['stopped']}"))
                    if not out["finished"]:
                        break
                detail = "; ".join(lines) or "nothing due"
                print("linz: " + detail)
                jobrun.record(JOB, ok, detail, started, {})
                return 0 if ok else 1
            if a.pull:
                last = conn.execute(f"SELECT projected FROM {SCHEMA}.surveys WHERE source = %s ORDER BY surveyed_at DESC "
                                    f"LIMIT 1", (a.pull,)).fetchone()
                if not last:
                    print(f"linz: {a.pull}: survey it first (--survey)")
                    return 2
                if last[0] > MAX_PULL_BYTES and not (a.allow_large or reported(a.pull)):
                    print(f"linz: {a.pull}: projected {last[0] / 1e9:.1f} GB, over {MAX_PULL_BYTES / 1e9:.0f} GB: "
                          f"refused without --allow-large")
                    return 2
                out = p.pull(a.pull, budget_s=a.budget_s, anytime=a.anytime)
                detail = (f"{a.pull}: {out['pages']} pages, {out['rows']:,} rows of {out['stated'] or 0:,} stated"
                          + ("; finished" if out["finished"] else f"; stopped: {out['stopped']}"))
                print("linz: " + detail)
                jobrun.record(JOB, True, detail, started, {k: v for k, v in out.items() if isinstance(v, int)})
                return 0
        except Blocked as e:
            conn.commit()
            print(f"linz: stopped: {e}")
            if a.pull:
                jobrun.record(JOB, False, f"{a.pull}: stopped: {e}", started, {})
            return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
