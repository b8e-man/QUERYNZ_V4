"""The three Beehive views as registers/beehive/pane.md states them, and the
Hansard lane's daily PDF (registers/hansard/pane.md, "A day's pane"): a
release titled with its title and type, citing the page's address, saying
where its reading came from (the old estate's scraper, the provider's
capture not yet read, the newest of several versions); its ministers as the
site tags them, given name first, pointing at the release and at no
person; the provider's topics and quotes under "The source's annotation
(made by its model, not ours)", never a link or a graph edge; a sitting
day's daily PDF citing the PDF and pointing at the sitting by its day."""
import datetime as dt

from products.board import catalogue as cat
from products.board import graph, panes, search
from products.board.tests.test_panes import ctx

URL = "https://www.beehive.govt.nz/release/major-milestone-reached-waioweka-gorge-recovery"
DOC = {"document": "cd" * 32, "page": None, "place": "record", "read_from": "json", "reader": "registers.beehive.read",
       "profile": "mcp-beehive-record", "citation_url": URL}


def release(**kw):
    r = {"key": URL, "type": "release", "kind": "item", "title": "Major milestone reached in Waioweka Gorge recovery",
         "published_on": dt.date(2026, 10, 20), "word_count": 421, "ministers": ["Hon Jane Doe"],
         "portfolios": ["Transport"], "topics": 6, "quotes": 10, "versions": 1, "origin": "mcp", "mcp_state": "read",
         "captured_at": dt.datetime(2026, 10, 22, 19, 40, tzinfo=dt.timezone.utc),
         "source_note": "captured off-estate by the query-nz provider (ruling 78)", **DOC}
    r.update(kw)
    return r


def minister(**kw):
    r = {"key": URL + "#minister/1", "release": URL, "ordinal": 1, "name": "Hon Jane Doe", "slug": "hon-jane-doe",
         "published_on": dt.date(2026, 10, 20), "type": "release",
         "title": "Major milestone reached in Waioweka Gorge recovery", **DOC}
    r.update(kw)
    return r


def annotation(**kw):
    r = {"key": URL + "#quote/1", "release": URL, "annotation": "quote", "ordinal": 1,
         "value": "The slip has been one of the most challenging sites.", "speaker": "Jane Doe", "model_made": True,
         "made_by": "the query-nz provider's model: deepseek/deepseek-v4.1-flash", "published_on": dt.date(2026, 10, 20), **DOC}
    r.update(kw)
    return r


PDF = "https://www.parliament.nz/media/0000/daily-2026-09-23.pdf"


def day(**kw):
    r = {"key": "2026-09-23", "sitting_on": dt.date(2026, 9, 23), "title": "Hansard (debates) for 23 September 2026",
         "pdf_url": PDF, "pdf_sha256": "ef" * 32, "captured_at": dt.datetime(2026, 10, 20, 2, 0, tzinfo=dt.timezone.utc),
         "page_count": 88, "word_count": 61234, "versions": 1, "old_url": "https://hansard.parliament.nz/x",
         "old_sections": 31, "old_subjects": 25, "subjects_in_text": 24,
         "old_note": "also held as the old transcript's sections", "citation_url": PDF,
         "source_note": "captured and read off-estate by the query-nz provider (ruling 78)", "document": "ef" * 32,
         "page": None, "place": "record", "read_from": "text", "reader": "registers.hansard.read_mcp",
         "profile": "mcp-hansard-day"}
    r.update(kw)
    return r


def test_the_register_sits_after_hansard_in_the_house_s_family():
    regs = [r for r, _ in cat.REGISTERS]
    assert regs.index("beehive") == regs.index("hansard") + 1
    assert dict(cat.REGISTERS)["beehive"] == "Beehive: releases, speeches and features"
    assert cat.FAMILY_OF["beehive"] == "the House" and cat.REGISTER_COLOUR["beehive"] == cat.REGISTER_COLOUR["house"]
    assert cat.main_view_of("beehive") == "beehive_releases"
    assert [v.name for v in cat.views_of("beehive")] == ["beehive_releases", "beehive_release_ministers",
                                                         "beehive_release_annotations", "beehive_people"]
    assert "hansard_days" in [v.name for v in cat.views_of("hansard")]


def test_a_release_is_titled_title_and_type_and_cites_the_page():
    v = cat.BY_NAME["beehive_releases"]
    r = release()
    assert panes.title_of(v, r) == "Major milestone reached in Waioweka Gorge recovery · release"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert f'href="{URL}"' in html and "did not fetch this page" in html and "20 October 2026" in html
    assert "Hon Jane Doe" in html and "Transport" in html and "421" in html
    assert cat.ANNOTATION in [j.label for j in v.joins]
    assert "read from the newest" not in html and "not yet read" not in html and "scraper's reading" not in html
    assert "person: the group" not in html


def test_a_release_says_where_its_reading_came_from():
    v = cat.BY_NAME["beehive_releases"]
    assert "read from the newest of 3 versions" in panes.row_pane(ctx(v, release(versions=3), same_words=[]))
    old = release(origin="old estate", mcp_state=None, ministers=[], topics=0, quotes=0)
    assert "the old estate&#x27;s: its scraper&#x27;s reading, original not held" in panes.hit("", v, old, [])
    caught = release(origin="old estate", mcp_state="captured only")
    html = panes.row_pane(ctx(v, caught, same_words=[]))
    assert "captured by the provider on 22 October 2026, not yet read" in html and "scraper&#x27;s reading" in html


def test_a_minister_is_the_site_s_tag_given_name_first_pointing_at_the_release_and_no_person():
    v = cat.BY_NAME["beehive_release_ministers"]
    r = minister()
    assert panes.title_of(v, r) == 'Hon Jane Doe · tagged on "Major milestone reached in Waioweka Gorge recovery" · 20 October 2026'
    assert [(n.whole, n.order) for n in cat.fields_of(v).names] == [("name", cat.GIVEN_FAMILY)]
    assert cat.pointers(v) == {"release": ("beehive_releases", "key")}     # the release, and nothing naming a person
    assert v.relations == () and v.kind != "person"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "hon-jane-doe" in html and "not a link to any person" in html and "person: the group" not in html


def test_the_annotation_is_the_source_s_never_a_link_never_the_graph():
    v = cat.BY_NAME["beehive_release_annotations"]
    r = annotation()
    assert panes.title_of(v, r).startswith(cat.ANNOTATION + " · quote: The slip")
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert "never a link and never read into the graph" in html and "deepseek" in html
    assert v.relations == () and v.names == () and v.kind != "person"
    assert cat.pointers(v) == {"release": ("beehive_releases", "key")}
    assert "speaker" not in v.search and v.name not in cat.FIELDS_OF
    assert not any(src.name == v.name for srcs in graph.INCOMING.values() for src, _ in srcs)


def test_a_release_s_annotations_are_asked_in_their_order():
    seen = []

    def rows(conn, sql, params):
        seen.append(sql)
        return []
    real = search.db.rows
    search.db.rows = rows
    try:
        search.children(object(), cat.BY_NAME["beehive_releases"], release())
    finally:
        search.db.rows = real
    assert "from pub.beehive_release_ministers where release = %s order by ordinal" in seen[0]
    assert "from pub.beehive_release_annotations where release = %s order by annotation, ordinal" in seen[1]


def test_a_daily_pdf_is_titled_its_day_cites_the_pdf_and_points_at_the_sitting():
    v = cat.BY_NAME["hansard_days"]
    r = day()
    assert panes.title_of(v, r) == "23 September 2026 · daily PDF"
    html = panes.row_pane(ctx(v, r, same_words=[]))
    assert f'href="{PDF}"' in html and "88" in html and "61234" in html
    assert "also held as the old transcript&#x27;s sections" in html and "no section or speaker split" in html
    to_sitting = v.joins[0]
    assert to_sitting.view == "hansard_sittings" and [r.get(own) for _, own in to_sitting.pairs()] == [dt.date(2026, 9, 23)]
    assert "hansard_days" in [j.view for j in cat.BY_NAME["hansard_sittings"].joins]
    assert v.relations == () and cat.pointers(v) == {}
