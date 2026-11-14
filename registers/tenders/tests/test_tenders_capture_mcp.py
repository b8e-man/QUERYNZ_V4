"""The refresh from the ingest MCP's copy (`--from-mcp`, estate-tenders): every file opened through
support.mcpsource.replay over a fake `mcpsource.files`, never the web; a file whose bytes differ from what the lane
holds is landed in a run that lists every file the copy holds, so the load's newest release is the copy's; a copy
the same as what is held makes no run; a file the copy lacks leaves its era's release as it was; a challenge page
in the copy is set aside, never landed. No network, no database."""
import pytest

import support.fetchgate as fg
from support.docstore import describe, sha256_bytes
from support.mcpsource import replay
from registers.tenders import capture, load, read
from registers.tenders.tests import fixtures

FIX = fixtures.files()
NAME = {("notices", "current"): "gets-award-notices.csv", ("suppliers", "current"): "gets-supplier-data.csv",
        ("regions", "current"): "gets-region-by-tender.csv", ("categories", "current"): "gets-product-categories.csv",
        ("notices", "historic"): "gets-award-notices-historic.csv",
        ("suppliers", "historic"): "gets-supplier-data-historic.csv",
        ("regions", "historic"): "gets-region-by-tender-historic.csv",
        ("categories", "historic"): "gets-product-categories-historic.csv"}
WORKBOOK = b"PK\x03\x04 an invented workbook"


class Store:
    """The document store and `mcpsource.files`: url → [bytes, oldest first] (the highest seq the newest)."""

    def __init__(self, copies):
        self.blobs, self.rows = {}, []
        for url, bodies in copies.items():
            for body in bodies:
                self.blobs[sha256_bytes(body)] = body
                self.rows.append((len(self.rows), url, sha256_bytes(body)))

    def read_bytes(self, sha):
        return self.blobs[sha]

    def execute(self, sql, params):
        url, corpora = params
        assert corpora == list(capture.MCP_CORPORA)
        rows = sorted((r for r in self.rows if r[1] == url), reverse=True)
        return _Rows([(rows[0][2],)] if rows else [])


class _Rows:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class Lane:
    """The capture's tables: every listed file with its run, and the `capture_files` query load.releases makes."""

    def __init__(self, held=()):
        self.files, self.asides, self.runs = [], [], 0
        if held:
            run = self.begin("copy")
            for (s, era), body in held:
                self.files.append((run, s, era, sha256_bytes(body), NAME[(s, era)], len(self.files)))

    def begin(self, mode):
        self.runs += 1
        return self.runs

    def finish(self, run_id, counts, stopped=""):
        pass

    def held(self, name):
        got = [f for f in self.files if f[4] == name]
        return got[-1][3] if got else None

    def add_file(self, run_id, name, url, ref, new, how, held_from, acquired_at):
        role, s, era = capture.classify(url)
        assert how == "fetched" and held_from.startswith("estate-tenders: ")
        if role == "data":
            self.files.append((run_id, s, era, ref.sha256, name, len(self.files)))

    def set_aside(self, run_id, item, stage, reason):
        self.asides.append((item, stage, reason))

    def execute(self, sql, params=None):       # load.releases' one query
        return _Rows([(r, s, e, sha, fid) for r, s, e, sha, _, fid in self.files])


def land_fn(data, *, name, name_kind, fetched_at=None, content_type=""):
    return describe(data, name, content_type, "tenders"), True


@pytest.fixture(autouse=True)
def no_web(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("the --from-mcp path asked the web")
    monkeypatch.setattr(fg, "open_url", refuse)


def run(lane, copies):
    store = Store(copies)
    opener = replay.opener(store, capture.MCP_CORPORA, read_bytes=store.read_bytes)
    asked = []

    def counted(url, timeout=None, **k):
        asked.append(url)
        return opener(url, timeout)
    return capture.from_mcp(lane, land_fn=land_fn, opener=counted), asked


def copy_of(files, **changed):
    out = {capture.FILES_URL + NAME[k]: [body] for k, (_, body) in files.items()}
    out[capture.FILES_URL + "schema-and-documentation.xlsx"] = [WORKBOOK]
    for url, bodies in changed.items():
        out[capture.FILES_URL + url].extend(bodies)
    return out


def held_from(files):
    return [(k, body) for k, (_, body) in files.items()]


def test_a_newer_file_in_the_copy_becomes_the_release_the_load_reads():
    newer = FIX[("suppliers", "current")][1] + b"30000003,,Newer Limited,,New Zealand,,20261015\r\n"
    lane = Lane(held_from(FIX))
    out, asked = run(lane, copy_of(FIX, **{"gets-supplier-data.csv": [newer]}))
    assert all(u.startswith(capture.FILES_URL) for u in asked) and len(asked) == len(capture.MCP_FILES)
    assert out["landed"] == len(capture.MCP_FILES) and out["stopped"] == ""
    rel = load.listings(lane)
    assert rel[("suppliers", "current")] == sha256_bytes(newer)            # the newest copy, not the one held
    assert rel[("notices", "current")] == sha256_bytes(FIX[("notices", "current")][1])
    assert set(rel) == {(s, e) for s in read.SETS for e in read.ERAS}


def test_a_copy_the_same_as_what_is_held_makes_no_run():
    lane = Lane(held_from(FIX))
    lane.files.append((1, None, None, sha256_bytes(WORKBOOK), "schema-and-documentation.xlsx", 99))
    before = list(lane.files)
    out, _ = run(lane, copy_of(FIX))
    assert out["stopped"].startswith("unchanged") and lane.files == before and lane.runs == 1


def test_a_file_the_copy_lacks_leaves_its_era_as_it_was():
    lane = Lane(held_from(FIX))
    copies = copy_of(FIX, **{"gets-supplier-data.csv": [FIX[("suppliers", "current")][1] + b"\r\n"]})
    del copies[capture.FILES_URL + "gets-product-categories-historic.csv"]
    out, _ = run(lane, copies)
    assert out["not_held"] == 1
    rel = load.releases(lane)
    assert rel["current"][0] == 2 and rel["historic"][0] == 1   # current from the copy's run, historic as held


def test_a_challenge_page_in_the_copy_is_set_aside_not_landed():
    lane = Lane(held_from(FIX))
    out, _ = run(lane, copy_of(FIX, **{"gets-award-notices.csv": [fixtures.CHALLENGE]}))
    assert out["set_aside"] == 1 and lane.asides[0][0].endswith("gets-award-notices.csv")
    assert load.listings(lane)[("notices", "current")] == sha256_bytes(FIX[("notices", "current")][1])
