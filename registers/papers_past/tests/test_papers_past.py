"""The Papers Past lane (step 8.6) on fake dump lines: the capture takes only Papers Past rows of scraper_results and never
decodes another host's; the reading's named stages reconcile and say why each item is set aside; the profile is recognised
both ways; the outside check's two halves."""
import os

from support.lane import check_folder
import pytest

from registers.papers_past import capture, check, read, store

HEAD = (b"COPY public.scraper_results (id, link, post_date, scrape_date, title, news_url, author_id, raw_content, update_date, "
        b"text_content, error, airtable_record_id, airtable_sync_date, is_english, pipeline_source, pipeline_status) FROM stdin;\n")


def row(i, url, text="Some words of the column.", status="CONTENT_COMPLETE"):
    t = text.replace("\t", "\\t").replace("\n", "\\n") if text is not None else "\\N"
    f = [str(i), "\\N", "1904-07-30 00:00:00+00", "2025-01-01 00:00:00+00", f"Title {i}", url, "\\N", t,
         "2025-01-01 00:00:00+00", t, "\\N", "\\N", "\\N", "\\N", "MIGRATION", status]
    return ("\t".join(f) + "\n").encode()


PP = "https://paperspast.natlib.govt.nz/newspapers/EP19040730.2.115.{}"


def dump(*rows):
    return [b"-- a dump\n", b"COPY public.scraper_result_sources (scraper_result_id, source_id) FROM stdin;\n", b"1\t2\n",
            b"\\.\n", HEAD, *rows, b"\\.\n", b"COPY public.sources (id, description, name) FROM stdin;\n", b"1\t\\N\tx\n", b"\\.\n"]


def test_the_lane_folder_has_the_shape():
    assert check_folder(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) == []


def test_the_capture_takes_only_papers_past_rows_of_the_section_and_never_decodes_another_host(monkeypatch):
    decoded = []
    real = capture.unescape
    monkeypatch.setattr(capture, "unescape", lambda f: decoded.append(f) or real(f))
    lines = dump(row(1, PP.format(1), "a\\tb line one\nline two"), row(2, "https://www.nzherald.co.nz/nz/a-story/"),
                 row(3, PP.format(3)))
    got = list(capture.take(iter(lines), 10))
    assert [r["id"] for r in got] == ["1", "3"]
    assert got[0]["text_content"] == "a\tb line one\nline two" and got[0]["_line"] == 6
    assert not any(b"nzherald" in f for f in decoded), "another host's row is never decoded"
    assert [r["id"] for r in capture.take(iter(lines), 1)] == ["1"], "n items at most"
    assert [r["id"] for r in capture.take(iter(lines), 10, after=6)] == ["3"], "after a line: the next batch"


def test_the_article_id_is_the_key_and_carries_the_paper_and_date():
    assert read.article_of(PP.format(3)) == ("EP19040730.2.115.3", "EP", __import__("datetime").date(1904, 7, 30))
    assert read.article_of("https://paperspast.natlib.govt.nz/newspapers/TC19170911.2.30.13.5")[0] == "TC19170911.2.30.13.5"
    assert read.article_of("https://paperspast.natlib.govt.nz/newspapers/evening-post/1904/07/30") is None
    assert read.article_of("https://paperspast.natlib.govt.nz/newspapers?query=x") is None


def test_the_stages_reconcile_and_every_set_aside_says_its_stage_and_reason():
    rows = list(capture.take(iter(dump(
        row(1, PP.format(1)), row(2, PP.format(2), None, "MIGRATION_ERROR"), row(3, PP.format(1)),
        row(4, "https://paperspast.natlib.govt.nz/newspapers/evening-post/1904"), row(5, PP.format(5), "  "))), 10))
    res = read.read(rows, 1, "a" * 64, held={5, 1})
    assert [it["key"] for it in res.items] == ["EP19040730.2.115.1"]
    assert res.items[0]["held_in_old"] and res.items[0]["place"] == "scraper_results line 6"
    st = {s[0]: s[1:] for s in res.stages}
    assert st["in"] == (5, 5, 0) and st["article id"] == (5, 4, 1) and st["text"] == (4, 2, 2) and st["once"] == (2, 1, 1)
    assert st["landed"] == (1, 1, 0)
    reasons = sorted(c[3] for c in res.catches)
    assert reasons == ["a second row for an article already taken in this batch",
                       "the URL is not a Papers Past article id",
                       "the archive holds no text for it (CONTENT_COMPLETE)",
                       "the archive holds no text for it (MIGRATION_ERROR)"]
    assert sum(1 for c in res.catches if c[4] is not None) == 4, "the first example of each reason kept whole"
    assert check.reconciles([(i, *s) for i, s in enumerate(res.stages, 1)]) == []


def test_the_profile_recognises_the_section_s_papers_past_rows_and_not_the_others():
    """Pinned both ways: a Papers Past article row is taken; a page, an issue, another host or another section is not."""
    yes = [row(1, PP.format(1))]
    no = [row(2, "https://paperspast.natlib.govt.nz/newspapers/evening-post/1904/07/30"), row(3, "https://www.odt.co.nz/news/x")]
    got = list(capture.take(iter(dump(*(yes + no))), 10))
    assert [r["id"] for r in got] == ["1", "2"]                     # the capture takes the host
    assert [read.article_of(r["news_url"]) is not None for r in got] == [True, False]   # the reading takes the article id
    other = [b"COPY public.rss_history (id, news_url) FROM stdin;\n", ("9\t" + PP.format(9) + "\n").encode(), b"\\.\n"]
    assert list(capture.take(iter(other), 10)) == [], "another section's rows are never taken"


def test_the_outside_check_compares_title_and_url_and_the_stages_must_join():
    items = [{"upstream_id": 1, "title": "A", "url": "u1", "held_in_old": True},
             {"upstream_id": 2, "title": "B", "url": "u2", "held_in_old": False}]
    assert check.against_old(items, {1: ("A", "u1")}) == []
    assert len(check.against_old(items, {1: ("A!", "u1"), 2: ("B", "u9")})) == 2
    assert check.against_old(items, {}) == ["1 is marked held in the old estate, which does not hold it"]
    assert check.reconciles([(1, "in", 3, 3, 0), (2, "text", 3, 2, 1), (3, "landed", 2, 2, 0)]) == []
    assert check.reconciles([(1, "in", 3, 3, 0), (2, "text", 3, 2, 1), (3, "landed", 2, 1, 0)])
    assert check.reconciles([(1, "in", 3, 3, 0), (2, "text", 3, 2, 1), (3, "landed", 2, 2, 0),
                             (4, "text files (measured)", 2, 2, 0)]) == []


def test_the_store_appends_frames_and_every_item_reads_back_by_its_place(tmp_path):
    sdir = str(tmp_path / "db.s")
    w = store.Writer(sdir, frame=200)
    texts = {f"EP19040730.2.{i}": ("word " * (i + 3)) + "tēnā\n\ttab" for i in range(40)}
    for k, t in texts.items():
        w.add(k, "EP", 1904, t)
    w.add("TC19170911.2.1", "TC", 1917, "another paper")
    places = w.close()
    texts["TC19170911.2.1"] = "another paper"
    assert set(places) == set(texts)
    assert {p.file for p in places.values()} == {"text/EP/1904.zst", "text/TC/1917.zst"}
    assert w.frames > 2, "a group past the frame size is written in more than one frame"
    for k, p in places.items():
        assert store.text(sdir, p.file, p.frame_at, p.frame_bytes, p.at, p.bytes, p.sha256) == texts[k]
    p = places["EP19040730.2.5"]
    with pytest.raises(RuntimeError):
        store.text(sdir, p.file, p.frame_at, p.frame_bytes, p.at, p.bytes, b"\0" * 32)
    keys = [r[0] for r in store.records(store.frame(sdir, p.file, p.frame_at, p.frame_bytes))]
    assert "EP19040730.2.5" in keys, "a frame says what it holds without the catalogue"
    size = os.path.getsize(os.path.join(sdir, "text/EP/1904.zst"))
    w2 = store.Writer(sdir)
    w2.add("EP19040801.2.1", "EP", 1904, "later")
    q = w2.close()["EP19040801.2.1"]
    assert q.frame_at == size, "append-only: a later batch's frame starts where the file ended"
    assert store.text(sdir, p.file, p.frame_at, p.frame_bytes, p.at, p.bytes, p.sha256) == texts["EP19040730.2.5"]


def test_the_store_refuses_the_old_estate_s_disk_and_wipes_only_its_own_folder(tmp_path):
    with pytest.raises(RuntimeError):
        store.Writer("/mnt/hdd/qv4-papers-past/x")
    with pytest.raises(RuntimeError):
        store.wipe(str(tmp_path / "a" / "b"), str(tmp_path))
    (tmp_path / "s" / "text").mkdir(parents=True)
    store.wipe(str(tmp_path / "s"), str(tmp_path))
    assert not (tmp_path / "s" / "text").exists()


def test_a_spread_sample_takes_every_kth_papers_past_row_and_counts_what_it_passed():
    lines = dump(*[row(i, PP.format(i)) if i % 3 else row(i, "https://www.odt.co.nz/x") for i in range(1, 31)])
    counts = {}
    got = [r["id"] for r in capture.take(iter(lines), 100, every=4, counts=counts)]
    pp = [str(i) for i in range(1, 31) if i % 3]
    assert got == pp[::4] and counts["seen"] == len(pp)


def test_the_streamed_reading_matches_the_whole_one():
    rows = list(capture.take(iter(dump(row(1, PP.format(1)), row(2, PP.format(2), None, "MIGRATION_ERROR"),
                                       row(3, PP.format(1)), row(4, "https://paperspast.natlib.govt.nz/newspapers/x"))), 10))
    r = read.Reading(1, "a" * 64, keep_text=False)
    got = [r.take(x) for x in rows]
    res = r.finish()
    whole = read.read(rows, 1, "a" * 64)
    assert res.stages == whole.stages and res.items == []
    assert [g["key"] for g in got if g] == [i["key"] for i in whole.items]


def test_a_build_lands_a_catalogue_with_no_text_and_its_text_reads_back_from_the_files(tmp_path):
    rows = list(capture.take(iter(dump(row(1, PP.format(1), "first text"), row(2, PP.format(2), None, "MIGRATION_ERROR"),
                                       row(3, PP.format(3), "third text"))), 10))
    from registers.papers_past import load
    assert "text" not in load.ITEM_COLUMNS
    sdir = store.store_dir("db", "s", str(tmp_path))
    w = store.Writer(sdir)
    r = read.Reading(1, "a" * 64, keep_text=False)
    for x in rows:
        it = r.take(x)
        if it:
            w.add(it["key"], it["paper"], load._year(it), it["text"])
    places = w.close()
    assert load._year({"key": "EP19040730.2.115.3", "paper": "EP"}) == 1904
    assert [store.text(sdir, p.file, p.frame_at, p.frame_bytes, p.at, p.bytes, p.sha256) for k, p in sorted(places.items())] \
        == ["first text", "third text"]
    assert r.finish().stages[-1] == ("landed", 2, 2, 0)
