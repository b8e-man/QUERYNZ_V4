"""The keyword search the board's papers past tab calls (search.py), on a tiny store and tantivy index built in a tmp
folder (never the archive's own): words join by AND, OR and phrases as asked, each hit read back through the catalogue
with its window of text, pages by offset, an id the catalogue lacks is said, and one article reads back whole."""
import datetime as dt

import pytest

from registers.papers_past import index, search, store

pytest.importorskip("tantivy")

TEXTS = {
    "OW18620801.2.5": (1001, "OW", "The Gold Escort", "The gold escort left Dunedin for the Otago diggings this morning."),
    "OW18620802.2.7": (1002, "OW", "Shipping", "A gold mine at Gabriel's Gully yields well; kauri gum from the north."),
    "TC19170911.2.1": (1003, "TC", "Te Whiti", "Te Whiti spoke at Parihaka to a large gathering."),
}
EXTRA = [(2000 + i, f"EP19040730.2.{i}", "the gold standard, word " * 3) for i in range(30)]


class Cursor:
    def __init__(self, names, rows):
        self.description = [(n,) for n in names]
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def __iter__(self):
        return iter(self._rows)


class Conn:
    """The two tables the search reads, as a session reader would answer them."""
    COLS = ("upstream_id", "key", "paper", "published_on", "title", "chars", "url", "path", "frame_at", "frame_bytes", "at",
            "bytes", "sha256")

    def __init__(self, sdir, items):
        self.sdir, self.items, self.sql = sdir, items, []

    def execute(self, sql, params=()):
        self.sql.append(sql)
        if "FROM papers_past.batches" in sql:
            return Cursor(["store"], [(self.sdir,)])
        if "upstream_id = ANY" in sql:
            rows = [r for r in self.items if r[0] in params[0]]
            return Cursor(self.COLS, rows)
        if "i.key = %s" in sql:
            rows = [r[1:] for r in self.items if r[1] == params[0]]
            return Cursor(self.COLS[1:], rows)
        raise AssertionError(sql)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    sdir = str(tmp_path_factory.mktemp("pp") / "db.s")
    w = store.Writer(sdir, frame=300)
    docs = []
    for key, (uid, paper, title, text) in TEXTS.items():
        w.add(key, paper, key[len(paper):len(paper) + 4], text)
        docs.append((uid, title, text))
    for uid, key, text in EXTRA:
        w.add(key, "EP", 1904, text)
        docs.append((uid, "Advertisements", text))
    places = w.close()
    index.tantivy_index(iter(docs), search.index_path(sdir), threads=1, heap=50_000_000)
    items = []
    for key, p in places.items():
        uid, paper, title, text = TEXTS.get(key) or next((u, "EP", "Advertisements", t) for u, k, t in EXTRA if k == key)
        items.append((uid, key, paper, dt.date(int(key[len(paper):len(paper) + 4]), 1, 1), title, len(text),
                      f"https://paperspast.natlib.govt.nz/newspapers/{key}", p.file, p.frame_at, p.frame_bytes, p.at,
                      p.bytes, p.sha256))
    return sdir, items


def test_words_join_by_and_unless_the_query_says_or(built):
    conn = Conn(*built)
    got = search.search(conn, "gold escort")
    assert got["count"] == 1 and [h["key"] for h in got["hits"]] == ["OW18620801.2.5"]
    assert search.search(conn, "escort OR kauri")["count"] == 2
    assert search.search(conn, '"gold mine"')["count"] == 1
    assert search.search(conn, "gold -escort")["count"] == 31


def test_a_hit_carries_its_catalogue_row_and_a_window_of_its_text(built):
    h = search.search(Conn(*built), "Parihaka")["hits"][0]
    assert h["key"] == "TC19170911.2.1" and h["paper"] == "TC" and h["title"] == "Te Whiti"
    assert h["url"] == "https://paperspast.natlib.govt.nz/newspapers/TC19170911.2.1"
    assert "Parihaka" in h["snippet"] and h["chars"] == len(TEXTS["TC19170911.2.1"][3])


def test_pages_by_offset_and_counts_the_whole(built):
    conn = Conn(*built)
    first, second = search.search(conn, "standard", limit=20), search.search(conn, "standard", limit=20, offset=20)
    assert first["count"] == second["count"] == 30
    assert len(first["hits"]) == 20 and len(second["hits"]) == 10
    assert not {h["key"] for h in first["hits"]} & {h["key"] for h in second["hits"]}
    assert first["seconds"] >= first["index seconds"] >= 0


def test_an_id_the_catalogue_lacks_is_said_and_never_hidden(built):
    sdir, items = built
    got = search.search(Conn(sdir, [r for r in items if r[0] != 1003]), "Parihaka")
    assert got["count"] == 1 and got["hits"][0]["key"] is None and got["hits"][0]["upstream_id"] == 1003


def test_one_article_reads_back_whole_and_an_unknown_key_is_none(built):
    conn = Conn(*built)
    a = search.article(conn, "OW18620802.2.7")
    assert a["text"] == TEXTS["OW18620802.2.7"][3] and a["title"] == "Shipping"
    assert search.article(conn, "XX18000101.2.1") is None


def test_an_empty_query_asks_nothing_and_a_bad_one_is_read_as_far_as_it_can(built):
    conn = Conn(*built)
    assert search.search(conn, "  ")["hits"] == [] and conn.sql == []
    got = search.search(conn, 'escort title:(')
    assert got["count"] >= 0 and "seconds" in got


def test_the_snippet_starts_near_the_first_word_asked():
    text = "x " * 400 + "the Parihaka meeting" + " y" * 400
    s = search.snippet(text, ["parihaka"])
    assert "Parihaka" in s and s.startswith("… ") and s.endswith(" …") and len(s) < search.SNIPPET + 10
    assert search.words('"Te Whiti" AND title:parihaka OR NOT x') == ["te", "whiti", "parihaka", "x"]
