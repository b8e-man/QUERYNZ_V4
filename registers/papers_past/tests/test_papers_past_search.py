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


UNDATED = (3000, "UNDATED.2.1", "the gold standard of an undated sheet")


def _build(sdir, with_fields=True):
    """The store and an index over it; `with_fields` False builds the index as it was built before day, paper and
    chars (3 November 2026): id, title, text alone."""
    import tantivy
    w = store.Writer(sdir, frame=300)
    rows = [(uid, key, paper, int(key[len(paper):len(paper) + 4]), title, text) for key, (uid, paper, title, text) in TEXTS.items()]
    rows += [(uid, key, "EP", 1904, "Advertisements", text) for uid, key, text in EXTRA]
    rows.append((UNDATED[0], UNDATED[1], "UN", None, "Undated", UNDATED[2]))
    for uid, key, paper, year, title, text in rows:
        w.add(key, paper, year, text)
    places = w.close()
    items, docs = [], []
    for n, (uid, key, paper, year, title, text) in enumerate(rows):
        day = dt.date(year, 1 + n % 12, 1 + n % 28) if year else None
        p = places[key]
        items.append((uid, key, paper, day, title, len(text), f"https://paperspast.natlib.govt.nz/newspapers/{key}",
                      p.file, p.frame_at, p.frame_bytes, p.at, p.bytes, p.sha256))
        docs.append((uid, title, text, paper, index.day_of(day), len(text)))
    if with_fields:
        index.tantivy_index(iter(docs), search.index_path(sdir), threads=1, heap=50_000_000)
    else:
        sb = tantivy.SchemaBuilder()
        sb.add_integer_field("id", stored=True, indexed=True, fast=True)
        sb.add_text_field("title", stored=False, tokenizer_name="default", index_option="position")
        sb.add_text_field("text", stored=False, tokenizer_name="default", index_option="position")
        import os
        os.makedirs(search.index_path(sdir))
        ix = tantivy.Index(sb.build(), path=search.index_path(sdir))
        iw = ix.writer(heap_size=50_000_000, num_threads=1)
        for uid, title, text, *_ in docs:
            iw.add_document(tantivy.Document(id=uid, title=title, text=text))
        iw.commit()
        iw.wait_merging_threads()
    return sdir, items


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    return _build(str(tmp_path_factory.mktemp("pp") / "db.s"))


@pytest.fixture(scope="module")
def built_before(tmp_path_factory):
    return _build(str(tmp_path_factory.mktemp("pp0") / "db.s"), with_fields=False)


def test_words_join_by_and_unless_the_query_says_or(built):
    conn = Conn(*built)
    got = search.search(conn, "gold escort")
    assert got["count"] == 1 and [h["key"] for h in got["hits"]] == ["OW18620801.2.5"]
    assert search.search(conn, "escort OR kauri")["count"] == 2
    assert search.search(conn, '"gold mine"')["count"] == 1
    assert search.search(conn, "gold -escort")["count"] == 32


def test_a_hit_carries_its_catalogue_row_and_a_window_of_its_text(built):
    h = search.search(Conn(*built), "Parihaka")["hits"][0]
    assert h["key"] == "TC19170911.2.1" and h["paper"] == "TC" and h["title"] == "Te Whiti"
    assert h["url"] == "https://paperspast.natlib.govt.nz/newspapers/TC19170911.2.1"
    assert "Parihaka" in h["snippet"] and h["chars"] == len(TEXTS["TC19170911.2.1"][3])
    assert h["published_on"].year == 1917


def test_pages_by_offset_and_counts_the_whole(built):
    conn = Conn(*built)
    first, second = search.search(conn, "standard", limit=20), search.search(conn, "standard", limit=20, offset=20)
    assert first["count"] == second["count"] == 31
    assert len(first["hits"]) == 20 and len(second["hits"]) == 11
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


def _days(got):
    return [h["published_on"] for h in got["hits"]]


def test_oldest_and_newest_order_by_issue_date_and_an_undated_article_comes_last_both_ways(built):
    conn = Conn(*built)
    for sort, rev in (("oldest", False), ("newest", True)):
        got = search.search(conn, "gold", limit=100, sort=sort)
        days = _days(got)
        assert got["sort"] == sort and got["unavailable"] == [] and got["count"] == 33
        assert days[-1] is None and None not in days[:-1], "the undated article is last"
        assert days[:-1] == sorted(days[:-1], reverse=rev)
    first = search.search(conn, "gold", limit=10, sort="oldest")
    second = search.search(conn, "gold", limit=10, offset=10, sort="oldest")
    assert max(_days(first)) <= min(_days(second)), "a page goes on where the last ended"
    assert _days(search.search(conn, "gold", limit=1, sort="oldest"))[0].year == 1862


def test_a_paper_a_year_range_and_a_least_length_narrow_the_hits(built):
    conn = Conn(*built)
    assert {h["paper"] for h in search.search(conn, "gold", limit=100, paper="OW")["hits"]} == {"OW"}
    assert search.search(conn, "gold", paper="OW")["count"] == 2
    assert search.search(conn, "gold", paper="ZZ")["count"] == 0
    got = search.search(conn, "gold", limit=100, year_from=1900, year_to=1910)
    assert got["count"] == 30 and {h["published_on"].year for h in got["hits"]} == {1904}
    assert search.search(conn, "gold", year_to=1870)["count"] == 2
    assert search.search(conn, "gold", year_from=1900)["count"] == 30, "a year range never matches the undated"
    texts = [t[3] for t in TEXTS.values()] + [t for _, _, t in EXTRA] + [UNDATED[2]]
    golds = sorted(len(t) for t in texts if "gold" in t.lower())
    cut = golds[-1]
    assert 0 < search.search(conn, "gold", min_chars=cut)["count"] == sum(1 for n in golds if n >= cut) < len(golds)
    assert search.search(conn, "gold", min_chars=golds[-1] + 1)["count"] == 0
    assert dict(search.search(conn, "gold")["papers"]) == {"EP": 30, "OW": 2, "UN": 1}


def test_the_index_built_before_the_fields_answers_by_relevance_and_says_what_waits(built_before):
    conn = Conn(*built_before)
    plain = search.search(conn, "gold", limit=100)
    got = search.search(conn, "gold", limit=100, sort="newest", paper="OW", year_from=1900, min_chars=60)
    assert got["sort"] == "relevance" and got["count"] == plain["count"] == 33
    assert [h["key"] for h in got["hits"]] == [h["key"] for h in plain["hits"]]
    assert set(got["unavailable"]) == {"newest first", "the paper filter", "the year range", "the minimum length"}
    assert plain["unavailable"] == [] and plain["papers"] is None
