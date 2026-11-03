"""The LINZ lane on fakes (step 8.3): the URL never carries the key and never asks for a geometry or an address; the
profile recognises a WFS page of its source and nothing else; an owner's name is read as LINZ prints it; a pull pages
through, lands each page once, resumes where it stopped and stops at a failed read; the check holds rows to the stated
count; the night takes the due sources small first."""
import datetime as dt
import json
import os

import pytest

from registers.linz import capture as C, check, read as R
from support.lane import check_folder

KEY = "SECRETKEY123"


def page(source, rows):
    return json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "geometry": None, "properties": r} for r in rows]}).encode()


def owner(i, **kw):
    r = {"id": i, "tte_id": 10 + i, "title_no": f"T{i}", "status": "LIVE", "land_district": "Otago", "estate_share": "1/1",
         "owner_type": "Individual", "prime_surname": "DOE", "prime_other_names": "Jane Mary", "name_suffix": None,
         "corporate_name": None}
    r.update(kw)
    return r


# ── the URL and the columns ───────────────────────────────────────────────────

def test_a_url_never_carries_the_key_nor_a_geometry_and_the_key_goes_in_a_header():
    for s in C.SOURCES:
        u = C.wfs_url(s, 20_000, C.PAGE)
        assert KEY not in u and "key=" not in u and "services;key" not in u
        assert "startIndex=20000" in u and "count=10000" in u
        if s in C.ASKED_WHOLE:
            assert "propertyName" not in u, "a source read whole is asked for every column"
        else:
            assert "propertyName=" in u and "geom" not in u.split("propertyName=")[1].lower()
        assert "resultType=hits" in C.wfs_url(s, hits=True)
    assert C.headers(KEY) == {"Authorization": f"key {KEY}", "Accept": "application/json"}


@pytest.mark.parametrize("col", ["owner_address", "street_name", "road_name_suffix", "postal_box", "geometry", "shape_area"])
def test_a_column_that_may_carry_an_address_or_a_geometry_is_never_read(monkeypatch, col):
    o = C.SOURCES["owners"]
    monkeypatch.setitem(C.SOURCES, "owners", o[:2] + (o[2] + (col,),) + o[3:])
    with pytest.raises(ValueError):
        C.columns("owners")


def test_a_public_source_never_asks_for_an_address_or_a_geometry_and_only_a_private_one_is_read_whole():
    for s in C.SOURCES:
        if s in C.ASKED_WHOLE:
            assert s in C.PRIVATE_SOURCES and C.columns(s) == ()
            continue
        asked = C.wfs_url(s).split("propertyName=")[1].split("&")[0].lower()
        assert "geom" not in asked and "shape" not in asked
        assert ("address" in asked) == (s == "property_addresses"), s
    assert C.SPINE == {"property_titles", "property_addresses", "addresses"} and C.SPINE <= C.PRIVATE_SOURCES
    assert {"owners", "titles", "place_names"}.isdisjoint(C.PRIVATE_SOURCES)
    assert C.SOURCES["addresses"][0] == "layer-123113" and "addresses" in C.ASKED_WHOLE, "each address with its point"
    assert C.SOURCES["property_titles"][0] == "table-113970" and C.SOURCES["property_addresses"][0] == "table-115638"


def test_a_public_source_is_never_read_whole(monkeypatch):
    monkeypatch.setattr(C, "ASKED_WHOLE", C.ASKED_WHOLE | {"owners"})
    with pytest.raises(ValueError):
        C.columns("owners")


@pytest.mark.parametrize("col", ["shape", "geometry", "the_geom"])
def test_a_typed_private_source_never_lists_a_geometry_either(monkeypatch, col):
    a = C.SOURCES["property_titles"]
    monkeypatch.setitem(C.SOURCES, "property_titles", a[:2] + (a[2] + (col,),) + a[3:])
    with pytest.raises(ValueError):
        C.columns("property_titles")


def test_a_public_source_still_never_reads_an_address_column(monkeypatch):
    t = C.SOURCES["titles"]
    monkeypatch.setitem(C.SOURCES, "titles", t[:2] + (t[2] + ("full_address",),) + t[3:])
    with pytest.raises(ValueError):
        C.columns("titles")


def test_the_stated_count_and_the_projection():
    assert C.number_matched(b'<wfs:FeatureCollection numberMatched="5745217" numberReturned="0">') == 5745217
    assert C.number_matched(b"<ExceptionReport/>") is None
    assert C.projected_bytes(31_155, 100, 5_745_217) == 1_789_922_356


# ── the profile and the reading ───────────────────────────────────────────────

def test_the_profile_recognises_a_page_of_its_source_and_nothing_else():
    assert R.recognises(page("owners", [owner(1)]), "owners")
    assert R.recognises(page("owners", []), "owners"), "an empty last page is still a page"
    assert not R.recognises(page("owners", [{"name": "Dunedin", "name_id": 1}]), "owners"), "a place-names page"
    assert not R.recognises(b"<ows:ExceptionReport>bad key</ows:ExceptionReport>", "owners")
    assert not R.recognises(json.dumps({"type": "Feature"}).encode(), "titles")
    assert R.recognises(page("place_names", [{"name": "Dunedin", "name_id": 1}]), "place_names")


def test_an_owner_is_read_as_linz_prints_it_and_a_row_without_its_title_is_set_aside():
    rows, aside = R.read_page(page("owners", [owner(1), owner(2, owner_type="Corporate", corporate_name="ACME LIMITED",
                                                        prime_surname=None, prime_other_names=None),
                                              owner(3, title_no=None)]), "owners", "a" * 64, 1, start_index=20_000)
    assert [(r["name"], r["kind"], r["key"], r["title_key"]) for r in rows] == [
        ("Jane Mary DOE", "individual", "linz/owners/1", "linz/titles/T1"),
        ("ACME LIMITED", "corporate", "linz/owners/2", "linz/titles/T2")]
    assert rows[0]["place"] == "row 20001" and rows[0]["profile"] == R.PROFILE and rows[0]["document"] == "a" * 64
    assert aside == [{"document": "a" * 64, "place": "row 20003", "stage": "read", "reason": "no title_no"}]
    assert not any("address" in k for r in rows for k in r)


def test_a_page_not_of_the_shape_is_set_aside_whole():
    rows, aside = R.read_page(b"<html>maintenance</html>", "titles", "b" * 64, 1, 0)
    assert rows == [] and aside[0]["stage"] == "recognise"


def test_a_title_is_keyed_by_its_number():
    rows, _ = R.read_page(page("titles", [{"id": 9, "title_no": "OT12A/34", "status": "LIVE", "type": "Freehold"}]),
                          "titles", "c" * 64, 1)
    assert rows[0]["key"] == "linz/titles/OT12A/34"


# ── the pull, on a fake service and a fake database ──────────────────────────

class Fetched:
    def __init__(self, status, body, blocked=""):
        self.status, self.body, self.blocked = status, body, blocked


class FakeService:
    """`total` rows of a source; fails at the request numbered `fail_at`."""

    def __init__(self, total, fail_at=None):
        self.total, self.fail_at, self.asked, self.headers = total, fail_at, [], []

    def __call__(self, url, timeout=300, headers=None, pacer=None):
        self.asked.append(url)
        self.headers.append(headers)
        if self.fail_at is not None and len(self.asked) == self.fail_at:
            return Fetched(429, b"", "HTTP 429: a block or a challenge")
        if "resultType=hits" in url:
            return Fetched(200, f'<x numberMatched="{self.total}"/>'.encode())
        q = dict(p.split("=", 1) for p in url.split("?", 1)[1].split("&"))
        start, count = int(q["startIndex"]), int(q["count"])
        return Fetched(200, page("owners", [owner(i) for i in range(start, min(start + count, self.total))]))


class Ref:
    def __init__(self, sha):
        self.sha256 = sha


class FakeDB:
    def __init__(self):
        self.pulls, self.pages, self.surveys, self.commits = {}, {}, [], 0

    def commit(self):
        self.commits += 1

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        res = []
        if s.startswith("SELECT pull_id, stated FROM linz.pulls WHERE source"):
            res = [(k, v["stated"]) for k, v in self.pulls.items() if v["source"] == params[0] and not v["finished"]]
        elif s.startswith("SELECT coalesce(max(start_index + rows), 0)"):
            res = [(max([st + n for (pid, st), (n, _) in self.pages.items() if pid == params[0]] or [0]),)]
        elif s.startswith("INSERT INTO linz.pulls"):
            self.pulls[params[0]] = {"source": params[1], "stated": params[2], "finished": False}
        elif s.startswith("INSERT INTO linz.pages"):
            self.pages.setdefault((params[0], params[1]), (params[2], params[3]))
        elif s.startswith("UPDATE linz.pulls SET finished_at"):
            self.pulls[params[0]]["finished"] = True
        elif s.startswith("INSERT INTO linz.surveys"):
            self.surveys.append(params)
        else:
            raise AssertionError(s)
        return Rows(res)


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


def puller(db, svc, landed):
    def land(data, *, name, source, conn, name_kind, content_type):
        assert KEY not in name
        sha = f"{len(landed):064x}"
        landed.append((name, len(data)))
        return Ref(sha), True
    return C.Puller(db, key=KEY, opener=svc, land_fn=land, now=lambda: dt.datetime(2026, 11, 2, 23, 0, tzinfo=C.NZ),
                    log=lambda *a: None)


def test_a_pull_pages_through_lands_each_page_once_and_finishes_on_a_short_page(monkeypatch):
    monkeypatch.setattr(C, "PAGE", 4)
    db, svc, landed = FakeDB(), FakeService(10), []
    out = puller(db, svc, landed).pull("owners")
    assert out["finished"] and out["pages"] == 3 and out["rows"] == 10 and out["stated"] == 10
    assert sorted(st for (_, st) in db.pages) == [0, 4, 8]
    assert all(h == C.headers(KEY) for h in svc.headers), "the key goes in a header on every request"
    assert not any(KEY in u for u in svc.asked)


def test_a_failed_read_stops_the_pull_and_the_next_run_resumes_from_the_last_page(monkeypatch):
    monkeypatch.setattr(C, "PAGE", 4)
    db, landed = FakeDB(), []
    with pytest.raises(C.Blocked):
        puller(db, FakeService(10, fail_at=3), landed).pull("owners")   # hits, page 0, then a 429
    assert [st for (_, st) in db.pages] == [0]
    svc = FakeService(10)
    out = puller(db, svc, landed).pull("owners")
    assert out["finished"] and out["rows"] == 6, "resumed at row 4"
    assert "resultType=hits" not in svc.asked[0] and "startIndex=4" in svc.asked[0], "nothing landed is asked again"


def test_off_peak_holds_a_pull_unless_anytime(monkeypatch):
    db, landed = FakeDB(), []
    p = puller(db, FakeService(3), landed)
    p.now = lambda: dt.datetime(2026, 11, 2, 12, 0, tzinfo=C.NZ)
    assert p.pull("owners")["stopped"] == "off-peak ended" and not landed
    assert p.pull("owners", anytime=True)["finished"]


# ── the check and the night's order ──────────────────────────────────────────

class CheckConn:
    """The check's queries on a fake catalog: `pub_cols` the published linz views' columns, `seen` whether the reader
    login can see the private schema, `titles`/`with_address`/`address_orphans` the private join's counts, and the
    catalog holding every lands column unless `missing` names one."""

    def __init__(self, loaded, dup=0, owners=0, orphans=0, cols=("title_no",), pub_cols=(("linz_titles", "title_no"),),
                 seen=False, titles=0, with_address=0, address_orphans=0, missing=(), geometry=None, dup_fids=0):
        self.loaded, self.dup, self.owners, self.orphans, self.cols = loaded, dup, owners, orphans, cols
        self.pub_cols, self.seen, self.titles, self.with_address = pub_cols, seen, titles, with_address
        self.address_orphans, self.missing = address_orphans, missing
        #: (titles reached, of them not among the titles, of them already on the spine), or None: no geometry join
        self.geometry, self.dup_fids = geometry, dup_fids

    def execute(self, sql, params=()):
        from registers.linz import extracts
        s = " ".join(sql.split())
        if "FROM s.loaded_pulls" in s:
            return All(self.loaded)
        if "table_schema = 'pub'" in s:
            return All(list(self.pub_cols))
        if s.startswith("SELECT to_regclass(%s) IS NOT NULL"):
            return All([(params[0].endswith("title_address_points") and self.geometry is not None,)])
        if self.geometry is not None and "FROM s_private.title_address_points" in s:
            return All([({"reached": self.geometry[0], "orphans": self.geometry[1], "both": self.geometry[2]}[
                "orphans" if "NOT EXISTS" in s else "both" if "EXISTS" in s else "reached"],)])
        if s.startswith("SELECT to_regclass('s.titles')") or s.startswith("SELECT to_regclass('s_private.title_addresses')"):
            return All([(True,)])
        if "GROUP BY fid HAVING" in s:
            return All([(self.dup_fids,)])
        if "has_schema_privilege" in s:
            assert params[1] == "s_private"
            return All([(self.seen,)])
        if "FROM pg_attribute" in s:
            schema, table = params
            assert schema in ("s", "s_private", "linz_private"), schema
            lane_t = table if schema == "s" else f"linz_private.{table}"
            return All([(c,) for c in extracts.TABLES.get(lane_t, ()) if f"{lane_t}.{c}" not in self.missing])
        if s.startswith("SELECT count(*) FROM s_private.title_addresses"):
            return All([(self.with_address * 2,)])
        if s.startswith("SELECT count(DISTINCT title_no) FROM s_private.title_addresses"):
            return All([(self.with_address,)])
        if s.startswith("SELECT count(DISTINCT a.title_no) FROM s_private.title_addresses a WHERE NOT EXISTS"):
            return All([(self.address_orphans,)])
        if s.startswith("SELECT count(*) FROM s.titles"):
            return All([(self.titles,)])
        if "HAVING count(*) > 1" in s:
            return All([(self.dup,)])
        if s.startswith("SELECT count(*) FROM s.owners o WHERE NOT EXISTS"):
            return All([(self.orphans,)])
        if s.startswith("SELECT count(*) FROM s.owners"):
            return All([(self.owners,)])
        if "information_schema.columns" in s:
            return All([(c,) for c in self.cols])
        raise AssertionError(s)


class All:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0]

    def __iter__(self):
        return iter(self.rows)


def test_the_check_holds_rows_to_the_stated_count_and_refuses_an_address_column():
    ok = CheckConn([("titles", "p1", 1_000_000, 1_000_000, 999_990, 10), ("owners", "p2", 2_000_000, 2_000_000, 2_000_000, 0)],
                   owners=2_000_000, orphans=100)
    assert check.reading(ok, "s") == []
    short = CheckConn([("titles", "p1", 1_000_000, 990_000, 990_000, 0)])
    assert any("against 1,000,000" in p for p in check.reading(short, "s"))
    lost = CheckConn([("titles", "p1", 100, 100, 90, 0)])
    assert any("90 read and 0 set aside" in p for p in check.reading(lost, "s"))
    assert any("address" in p for p in check.reading(CheckConn([], cols=("owner_address",)), "s"))
    assert any("more than once" in p for p in check.reading(CheckConn([("titles", "p", 5, 5, 5, 0)], dup=2), "s"))


def test_an_address_column_in_a_published_linz_view_is_red():
    assert check.reading(CheckConn([]), "s") == []
    for col in ("full_address", "street_name", "shape", "geom"):
        bad = check.reading(CheckConn([], pub_cols=(("linz_titles", "title_no"), ("linz_titles", col))), "s")
        assert any(f"pub.linz_titles.{col}" in p for p in bad), col


SPINE = [("titles", "p1", 100, 100, 100, 0)] + [(s, f"p{s}", 10, 10, 10, 0) for s in
                                                 ("property_titles", "property_addresses", "addresses")]


def test_the_private_join_is_held_to_the_titles_and_the_private_schema_to_the_reader():
    assert check.reading(CheckConn(SPINE, titles=100, with_address=95), "s") == []
    assert any("the reader login can see" in p for p in check.reading(CheckConn([], seen=True), "s"))
    assert check.reading(CheckConn(SPINE, titles=100, with_address=92), "s") == [], "the first build's 92.4%"
    assert any("84 of 100" in p for p in check.reading(CheckConn(SPINE, titles=100, with_address=84), "s")), \
        "the floor is 85%: under the measured share by a week's drift, far over a broken join"
    low = check.reading(CheckConn(SPINE, titles=100, with_address=50), "s")
    assert any("50 of 100 titles have a street address" in p for p in low)
    stray = check.reading(CheckConn(SPINE, titles=100, with_address=95, address_orphans=5), "s")
    assert any("5 of 95 titles with an address are not among the titles" in p for p in stray)


def test_the_lane_is_held_to_its_profile_and_its_lands_columns_to_the_catalog(monkeypatch):
    from registers.linz import extracts
    assert extracts.problems() == [], "the lane's code and linz-wfs-page's extract list agree"
    gone = check.reading(CheckConn([], missing=("linz_private.title_addresses.full_address",)), "s")
    assert any("s_private.title_addresses has no column full_address" in p for p in gone)
    monkeypatch.setitem(extracts.LANE.produces, extracts.SLUG, {**extracts.produces(), "owner_address": ("rules", None)})
    assert any("owner_address" in p for p in check.reading(CheckConn([]), "s"))


def test_the_night_takes_unfinished_and_stale_sources_small_first():
    now = dt.datetime(2026, 11, 20, tzinfo=dt.timezone.utc)

    class DueConn:
        def execute(self, sql, params=()):
            s = params[0]
            if "finished_at IS NULL" in sql:
                return Rows([(1,)] if s == "owners" else [])
            return Rows([({"place_names": now - dt.timedelta(days=2), "titles": now - dt.timedelta(days=9)}.get(s),)])
    due = C.due_sources(DueConn(), now)
    assert due[:5] == ["property_titles", "addresses", "titles", "property_addresses", "owners"], \
        "a source never pulled is due; the private sources take their place by size"
    assert due[5:] == [s for s in C.DUE_ORDER if s in C.WHOLE], "then every catalogue source, never pulled"
    assert due[5:7] == ["title_parcel_association_list", "parcels"], "the geometry join's two first"


def test_the_lane_folder_has_the_shape():
    assert check_folder(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) == []


# ── the private sources and each title's street address ──────────────────────

def test_a_private_source_is_read_with_its_join_keys_and_a_row_without_one_is_set_aside():
    body = page("property_titles", [{"id": 1, "title_no": "T1", "unit_of_property_id": "u-1"},
                                    {"id": 2, "title_no": "T2", "unit_of_property_id": None}])
    rows, aside = R.read_page(body, "property_titles", "d" * 64, 2)
    assert [r["key"] for r in rows] == ["linz/property_titles/1"] and aside[0]["reason"] == "no unit_of_property_id"
    a, _ = R.read_page(page("addresses", [{"address_id": 7, "full_address": "1 Invented Lane, Nowhere",
                                           "address_lifecycle": "Current"}]), "addresses", "e" * 64, 2)
    assert a[0]["key"] == "linz/addresses/7" and a[0]["full_address"] == "1 Invented Lane, Nowhere"
    assert not R.recognises(page("addresses", [{"address_id": 7}]), "addresses"), "an address page without its address"


def test_the_private_sources_and_the_join_land_in_the_private_schema_only():
    from registers.linz import load as L
    assert L.table_of("staging_x", "addresses") == "staging_x_private.addresses"
    assert L.table_of("linz", "property_titles") == "linz_private.property_titles"
    assert L.table_of("staging_x", "titles") == "staging_x.titles"
    sql = L.join_sql("staging_x_private")
    assert "INSERT INTO staging_x_private.title_addresses" in sql and " staging_x." not in sql
    with open(os.path.join(os.path.dirname(L.__file__), "publish.sql"), encoding="utf-8") as f:
        pub = f.read().lower()
    assert "linz_private" not in pub and "full_address" not in pub and "address_id" not in pub
    with open(os.path.join(os.path.dirname(L.__file__), "tables.sql"), encoding="utf-8") as f:
        tables = f.read()
    public_part = tables[:tables.index("CREATE TABLE linz_private.")]
    assert "address" not in " ".join(l.split("--")[0] for l in public_part.splitlines()).lower()


def test_each_page_records_the_fields_its_source_yields():
    from registers.linz import extracts
    rows = extracts.extracted([("a" * 64, "addresses"), ("a" * 64, "addresses"), ("b" * 64, "titles")])
    by = {}
    for sha, slug, f, it, reader, model in rows:
        assert slug == "linz-wfs-page" and reader == R.READER and model is None
        by.setdefault(sha, {})[f] = it
    assert by["a" * 64] == {"address_id": 3, "full_address": 4,   # 4: judgment-address-title@1 named (ruling 142)
                             "address_lifecycle": 3, "props": 3, "geom_type": 3,
                            "geom": 3, "xmin": 4, "ymin": 4, "xmax": 4, "ymax": 4}
    assert "title_no" in by["b" * 64] and "full_address" not in by["b" * 64]


# ── everything the service gives (ruling 142, 4 November 2026): the catalogue, read whole, and the geometry ──────────

def test_the_catalogue_takes_every_land_layer_and_says_why_it_leaves_one():
    from registers.linz import catalogue as K
    names = [e[1] for e in K.ENTRIES]
    assert len(names) == len(set(names)), "one name a source"
    for type_name, name, title, licence, rows, geom, sort, tranche, why, cadence in K.ENTRIES:
        assert type_name.startswith(("layer-", "table-")) and licence in ("cc", "personal") and rows >= 0
        assert (tranche is None) == bool(why), name
        assert tranche is None or tranche in K.REFRESH_DAYS
        if tranche:
            assert name in C.SOURCES and C.SOURCES[name][0] == type_name, name
    taken = {e[0] for e in K.ENTRIES if e[7]}
    for t in ("table-51569", "layer-51571", "table-51695", "table-114085", "table-52067", "layer-113968"):
        assert t in taken, t
    assert {"titles", "owners", "place_names", "property_titles", "property_addresses", "addresses"} <= set(names)


def test_a_whole_source_is_asked_for_everything_sorted_on_its_key_and_lands_private():
    u = C.wfs_url("parcels", 0, C.PAGE)
    assert "typeNames=layer-51571" in u and "propertyName" not in u and "sortBy=id" in u
    u = C.wfs_url("lol_title_memorial_text", 0, C.PAGE)
    assert "sortBy=audit_id" in u, "a table with no id is paged on a column that is one a row"
    assert "parcels" in C.PRIVATE_SOURCES and C.WHOLE["parcels"][3] == "shape"
    assert C.refresh_days("parcels") == 7 and C.refresh_days("lol_setup") == 90 and C.refresh_days("owners") == 7
    assert C.reported("lol_setup") and not C.reported("owners")


def test_the_addresses_asked_whole_are_due_again_once_though_pulled_this_week():
    now = dt.datetime(2026, 11, 5, tzinfo=dt.timezone.utc)

    class DueConn:
        def execute(self, sql, params=()):
            if "finished_at IS NULL" in sql:
                return Rows([])
            return Rows([(now - dt.timedelta(days=1, hours=12),)])     # every source finished a day and a half ago
    assert C.due_sources(DueConn(), now) == ["addresses"], "pulled before it was widened"


def test_a_pull_stops_when_the_store_runs_low(monkeypatch):
    monkeypatch.setattr(C, "PAGE", 4)
    db, landed = FakeDB(), []
    p = puller(db, FakeService(10), landed)
    p.free_fn = lambda: C.STORE_FLOOR_BYTES - 1
    out = p.pull("owners")
    assert not landed and "free" in out["stopped"] and not out["finished"]


def feature(fid, props, geometry=None):
    return {"type": "Feature", "id": fid, "geometry": geometry, "properties": props}


SQUARE = {"type": "Polygon", "coordinates": [[[170.0, -45.0], [170.1, -45.0], [170.1, -44.9], [170.0, -44.9], [170.0, -45.0]],
                                             [[170.04, -44.96], [170.06, -44.96], [170.06, -44.94], [170.04, -44.94],
                                              [170.04, -44.96]]]}


def test_a_page_read_whole_keeps_every_attribute_and_the_geometry_with_its_box():
    body = json.dumps({"type": "FeatureCollection", "features": [
        feature("layer-51571.7", {"id": 7, "appellation": "Lot 1 DP 1", "titles": "T1, T2"}, SQUARE),
        feature("layer-51571.8", {"id": 8, "appellation": "Lot 2 DP 1"}),
        {"type": "Feature", "geometry": None, "properties": {"appellation": "no id at all"}}]}).encode()
    rows, aside = R.read_page(body, "parcels", "f" * 64, 3, start_index=10)
    assert [r["key"] for r in rows] == ["linz/parcels/7", "linz/parcels/8"]
    r = rows[0]
    assert json.loads(r["props"]) == {"id": 7, "appellation": "Lot 1 DP 1", "titles": "T1, T2"}, "nothing stripped"
    assert r["geom_type"] == "Polygon" and json.loads(r["geom"]) == SQUARE
    assert (r["west"], r["south"], r["east"], r["north"]) == (170.0, -45.0, 170.1, -44.9)
    assert rows[1]["geom"] is None and rows[1]["west"] is None
    assert aside == [{"document": "f" * 64, "place": "row 13", "stage": "read", "reason": "no id"}]
    rows, _ = R.read_page(json.dumps({"type": "FeatureCollection", "features": [
        feature("table-52007.99", {"ttm_id": 5, "sequence_no": 1, "std_text": "x"})]}).encode(),
        "lol_title_memorial_text", "f" * 64, 3)
    assert rows[0]["fid"] == "99", "a table sorted on a column that is not one a row is keyed by the service's own id"
    assert R.read_page(b"<ows:ExceptionReport/>", "parcels", "f" * 64, 3)[1][0]["stage"] == "recognise"


def test_an_address_read_whole_carries_its_point():
    body = page("addresses", [{"address_id": 7, "full_address": "1 Invented Lane, Nowhere", "address_lifecycle": "Current",
                               "suburb_locality": "Nowhere"}])
    doc = json.loads(body)
    doc["features"][0]["geometry"] = {"type": "Point", "coordinates": [170.05, -44.99]}
    rows, _ = R.read_page(json.dumps(doc).encode(), "addresses", "e" * 64, 3)
    assert rows[0]["full_address"] == "1 Invented Lane, Nowhere" and rows[0]["west"] == 170.05 and rows[0]["north"] == -44.99
    assert json.loads(rows[0]["props"])["suburb_locality"] == "Nowhere"


def test_a_point_is_inside_a_polygon_not_in_its_hole_and_the_grid_finds_it():
    from registers.linz import geo
    assert geo.contains(SQUARE, 170.01, -44.99) and not geo.contains(SQUARE, 170.05, -44.95), "the hole"
    assert not geo.contains(SQUARE, 170.2, -44.95)
    multi = {"type": "MultiPolygon", "coordinates": [SQUARE["coordinates"][:1],
                                                     [[[171, -45], [171.1, -45], [171.1, -44.9], [171, -45]]]]}
    assert geo.contains(multi, 171.08, -44.95) and geo.bbox(multi) == (170.0, -45.0, 171.1, -44.9)
    assert not geo.contains({"type": "Point", "coordinates": [170.01, -44.99]}, 170.01, -44.99)
    g = geo.Grid()
    for k, x, y in ((1, 170.01, -44.99), (2, 170.05, -44.95), (3, 170.5, -44.5), (4, 171.08, -44.95)):
        g.add(k, x, y)
    assert sorted(g.within(SQUARE)) == [1] and sorted(g.within(multi)) == [1, 2, 4], "the multi's first has no hole"
    huge = {"type": "Polygon", "coordinates": [[[160, -50], [180, -50], [180, -30], [160, -30], [160, -50]]]}
    assert sorted(g.within(huge)) == [1, 2, 3, 4], "a box wider than the points walks the filled cells"


def test_each_parcel_is_tested_once_and_a_parcel_without_a_polygon_reaches_nothing():
    from registers.linz import geo, load as L
    g = geo.Grid()
    g.add(1, 170.01, -44.99)
    got = L.match_parcels([("p1", json.dumps(SQUARE)), ("p1", json.dumps(SQUARE)), ("p2", None)], g)
    assert got == {"p1": [1], "p2": []}


def test_publishing_moves_a_private_table_whole_and_keeps_the_geometry_join_unless_it_ran():
    from registers.linz import load as L
    plan = L.publish_plan({"titles", "parcels", "property_titles", "property_addresses", "addresses"}, geometry=False)
    assert ("copy", "titles") in plan and ("move", "parcels") in plan and ("move", "addresses") in plan
    assert ("move", "title_addresses") in plan and ("move", "title_address_points") not in plan
    assert ("move", "title_address_points") in L.publish_plan({"parcels"}, geometry=True)
    assert ("move", "title_addresses") not in L.publish_plan({"parcels"}, geometry=False), "the spine not restaged"
    assert L.geometry_inputs("staging_x", {"titles", "parcels"}) == {
        "titles": "staging_x.titles", "spine": "linz_private.title_addresses",
        "association": "linz_private.title_parcel_association_list", "parcels": "staging_x_private.parcels",
        "addresses": "linz_private.addresses"}, "an input not staged now is read as published"
    assert "CREATE TABLE linz_private.title_address_points" not in L.tables_sql("s"), \
        "only the geometry join makes its table, so a load that could not join leaves the published one"
    assert "CREATE TABLE s_private.title_address_points" in L.tables_sql("s", "geometry")


def test_the_geometry_join_is_held_to_the_titles_and_the_spine():
    assert check.reading(CheckConn([], geometry=(100, 0, 0)), "s") == []
    assert any("reached no title" in p for p in check.reading(CheckConn([], geometry=(0, 0, 0)), "s"))
    assert any("5 of 100 titles reached by geometry are not among" in p
               for p in check.reading(CheckConn([], geometry=(100, 5, 0)), "s"))
    assert any("already have a spine address" in p for p in check.reading(CheckConn([], geometry=(100, 0, 3)), "s"))
    dup = check.reading(CheckConn([("parcels", "p", 10, 10, 10, 0)], dup_fids=2), "s")
    assert any("parcels: 2 row ids carried more than once" in p for p in dup)


def test_no_lane_column_is_a_system_column_of_the_database():
    """A column named xmin, xmax, cmin, cmax, ctid or tableoid cannot be made (4 November 2026: the box was xmin … ymax,
    and the first real load refused its table)."""
    from registers.linz import extracts, load as L
    system = {"tableoid", "xmin", "cmin", "xmax", "cmax", "ctid", "oid"}
    for t, cols in extracts.TABLES.items():
        assert not system & set(cols), t
    for sql in (L.tables_sql("s"), L.tables_sql("s", "geometry"), L.whole_sql("s_private.parcels")):
        for line in sql.splitlines():
            for c in system:
                assert not line.strip().startswith(c + " ") and f", {c} " not in line, line
