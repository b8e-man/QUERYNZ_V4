"""A handed-over lane's walk answered from the MCP's copies (9 November 2026), and the estate-* record shape."""
import pytest

from support import mcpsource as M
from support.mcpsource import replay

A, B = "a" * 64, "b" * 64


class Files:
    """mcpsource.files as the replay asks it: rows (corpus, seq, url, sha, state)."""

    def __init__(self, rows):
        self.rows, self.asked = rows, []

    def execute(self, sql, params):
        url, corpora = params
        self.asked.append(sql)
        hits = sorted((r for r in self.rows if r[2] == url and r[0] in corpora and r[4] in ("landed", "held")),
                      key=lambda r: -r[1])

        class R:
            def fetchone(s):
                return (hits[0][3],) if hits else None
        return R()


def test_the_newest_copy_of_an_address_answers_and_an_absent_one_is_a_failed_read():
    conn = Files([("estate-fma", 3, "https://x/p", A, "landed"), ("estate-fma", 9, "https://x/p", B, "held"),
                  ("estate-fma", 12, "https://x/p", "c" * 64, "waiting"), ("estate-other", 20, "https://x/p", "d" * 64, "landed")])
    store = {A: b"old", B: b"new"}
    open_url = replay.opener(conn, ["estate-fma"], read_bytes=lambda sha: store[sha])
    f = open_url("https://x/p", 60)
    assert (f.status, f.body, f.final_url, f.blocked) == (200, b"new", "https://x/p", "")
    with pytest.raises(replay.NotHeld):
        open_url("https://x/q", 60)
    assert isinstance(replay.NotHeld("x"), OSError)          # a lane's walk counts it as a failed read


def test_bytes_not_yet_in_the_store_are_not_held():
    def missing(sha):
        raise FileNotFoundError(sha)
    open_url = replay.opener(Files([("estate-fma", 1, "https://x/p", A, "landed")]), ["estate-fma"], read_bytes=missing)
    with pytest.raises(replay.NotHeld):
        open_url("https://x/p")


def test_an_estate_record_s_address_is_its_first_url_and_it_points_at_its_file():
    rec = {"id": A, "sha256": A, "content_type": "text/html", "size": 10,
           "urls": [{"url": "https://www.fma.govt.nz/a/", "via": ["fma.capture"]}, {"url": "https://www.fma.govt.nz/b/"}],
           "capture": {"fetched_at": "2026-11-08 07:05:52+00:00", "sha256": A}}
    assert M.record_url(rec) == "https://www.fma.govt.nz/a/"
    assert M.file_pointer(rec) == ("https://www.fma.govt.nz/a/", "text/html", A, None)
    assert M.record_url({"url": "https://own/", "urls": [{"url": "https://other/"}]}) == "https://own/"
    assert M.record_url({"urls": [{"url": "qnz-raw://x"}]}) is None
