"""The one report's news section (step 9.3, 9.4; products/report/news.py), on a fixture: a stage-1 walk and a news index of
invented articles built in a tmp folder. Every person, company, place, publisher and number below is invented. No news table
is read, old or new: the corpus is not copied yet. The checks are the design's (docs/research/step-9-news-search.md, "The
checks that can fail") that a fixture can exercise: 3 folding, 4 a name alone never connects, 5 evidence is real, 6 the
horse farm and its negative, 7 suppression, 8 address, 9 never whole, 10 Papers Past and nothing written, 11 nothing silent,
12 local only."""
import ast
import datetime as dt
import os
import re

import pytest

from products.report import news, rules
from support.textindex import read as tx
from support.textindex import write as txw

pytest.importorskip("tantivy")

D = dt.date
HERE = os.path.dirname(os.path.abspath(__file__))
NEWS_PY = os.path.join(HERE, "..", "news.py")
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

SUBJECT = "companies:companies/9999000000001/director/d1"
FARM = "companies:companies/9999000000001"
FAR = "companies:companies/9999000000002"
HUB = "companies:companies/9999000000003"
CO_OFFICER = "companies:companies/9999000000001/director/d2"
HUB_PERSON = "companies:companies/9999000000003/director/d9"
HIDDEN = "companies:companies/9999000000001/director/d3"
OFFICE = "companies:company_addresses/a1"
HIDDEN_NAME = "Zebedee Ferncastle"            # an invented name on a suppressed row: it must never be a probe


def _it(ref, view, kind, title, row, start=None, end=None, **extra):
    it = {"ref": ref, "view": view, "register": "companies", "kind": kind, "title": title, "row": row,
          "dates": {"start": start, "end": end}, "suppressed": False, "grade": "confirmed", "reason": None, "rule": None,
          "via": None, "flags": [], "entity_title": None}
    it.update(extra)
    return it


def walk_for(company="Kōwhai Downs Equestrian Limited", farm_ref=FARM):
    """A stage-1 walk of one invented director: her own company (hop 1), a farther company (hop 2, near), a hub, a
    co-officer, a person on the hub, a suppressed row and the company's registered office."""
    me = _it(SUBJECT, "directors", "person", "Harriet Anne Quillfeather",
             {"full_name": "Harriet Anne Quillfeather", "role_type": "Director", "key": "9999000000001/director/d1"},
             start=D(2015, 4, 1), entity_title=company)
    hidden = _it(HIDDEN, "directors", "person", "name suppressed", {"full_name": HIDDEN_NAME, "role_type": "Director"},
                 suppressed=True)
    farm = _it(farm_ref, "companies", "organisation", company, {"name": company, "key": farm_ref.rsplit("/", 1)[1]},
               start=D(2014, 6, 1))
    far = _it(FAR, "companies", "organisation", "Tarawhiti Saddlery Limited", {"name": "Tarawhiti Saddlery Limited", "key": "9999000000002"},
              start=D(2001, 1, 1), stage1=True, stage_hop=2, grade="near", reason="an organisation of a director, a person on the subject",
              rule="stage1")
    hub = _it(HUB, "companies", "organisation", "Pohutukawa Megacorp Limited", {"name": "Pohutukawa Megacorp Limited", "key": "9999000000003"},
              stage1=True, stage_hop=1, flags=[{"kind": "stage-hub", "text": "a hub"}])
    co = _it(CO_OFFICER, "directors", "person", "Bartholomew Pemberton-Ngaio", {"full_name": "Bartholomew Pemberton-Ngaio"},
             start=D(2015, 1, 1), stage1=True, stage_hop=2, via=farm_ref)
    hub_person = _it(HUB_PERSON, "directors", "person", "Cornelius Brightwater", {"full_name": "Cornelius Brightwater"},
                     stage1=True, stage_hop=2, via=HUB)
    office = _it(OFFICE, "company_addresses", "place", "Invented Lane", {"entity_key": farm_ref.rsplit("/", 1)[1],
                 "kind": "registered office", "line_1": "Level 9, Invented Lane", "line_2": "Wharekino", "line_3": "Wharekino 3999"})
    return {"found": True, "start": me, "members": [me, hidden], "entities": [farm], "roles": [office],
            "second": [], "stage1": [far, hub, co, hub_person], "hubs": [{"ref": HUB}]}


def _art(key, day, text, headline="An invented report", publisher="The Invented Herald", sha=None):
    return {"ref": f"news:fixture/{key}", "publisher": publisher, "published_on": day, "headline": headline,
            "byline": "An Invented Reporter", "url": f"https://news.invalid/{key}", "text": text,
            "text_sha256": sha or f"sha-{key}"}


PAD = "The weather was fine and the crowd was large. " * 3
LONG = ("Filler words about nothing at all. " * 60 + "Harriet Quillfeather opened the show. " +
        "More filler about the day and the weather. " * 60 + "Kowhai Downs Equestrian took a ribbon. " +
        "Closing filler words. " * 60)
ARTICLES = [
    _art("mention", D(2020, 2, 1), PAD + "Harriet Quillfeather spoke at the regional show in an invented town."),
    _art("named-thing", D(2019, 5, 1), PAD + "Harriet Quillfeather, of Kowhai Downs Equestrian, said the season was good."),
    _art("named-thing-copy", D(2019, 5, 2), PAD + "Harriet Quillfeather, of Kowhai Downs Equestrian, said the season was good.",
         publisher="The Invented Courier", sha="sha-named-thing"),
    _art("horse-farm", D(2021, 3, 1), PAD + "Silverfern Stud won the invented cup on Saturday; the stud's colt led throughout."),
    _art("co-officer", D(2018, 8, 1), PAD + "Harriet Quillfeather and Bartholomew Pemberton-Ngaio judged the yearlings."),
    _art("hub-person", D(2018, 8, 2), PAD + "Harriet Quillfeather and Cornelius Brightwater judged the yearlings."),
    _art("role", D(2018, 9, 1), PAD + "The company's director, Harriet Quillfeather, declined to comment."),
    _art("role-far", D(2018, 9, 2), "The director of the invented festival opened it. " + PAD * 2 +
         "Later Harriet Quillfeather was seen at the gate."),
    _art("place", D(2018, 10, 1), PAD + "Harriet Quillfeather was at Wharekino for the sale."),
    _art("out-of-window", D(2005, 1, 1), PAD + "Harriet Quillfeather rode for Kōwhai Downs Equestrian at the trials."),
    _art("near", D(2017, 1, 1), PAD + "Tarawhiti Saddlery opened a second shop."),
    _art("address", D(2016, 1, 1), "Harriet Quillfeather lives at 14 Fictional Street, Imaginary Bay 9999, neighbours say."),
    _art("suppressed", D(2016, 2, 1), PAD + f"Harriet Quillfeather sat beside {HIDDEN_NAME} at the hearing."),
    _art("long", D(2022, 1, 1), LONG),
    _art("folded", D(2023, 1, 1), PAD + "Hārriet Quillfeather at the Kowhai Downs Equestrian open day."),
    _art("other-name", D(2020, 1, 1), PAD + "Henrietta Quillfeather won a prize; Bartholomew Pemberton-Ngaio watched from Wharekino."),
    _art("headline-only", D(2020, 6, 1), PAD + "The prizes were given out.", headline="Quillfeather prize: Harriet Quillfeather wins"),
] + [_art(f"crowd-{i}", D(2001, 1, 1 + i), PAD + f"Item {i}: Harriet Quillfeather attended.") for i in range(22)]
#: the offsets of the one suppressed name in the "suppressed" article: what pub.news_suppressed_spans would hold
SPANS = {"news:fixture/suppressed": [(m.start(), m.end()) for m in re.finditer(HIDDEN_NAME, ARTICLES[12]["text"])]}
#: an article with no searched probe in it: a co-officer, a role and a place, no name and no thing of the subject's
LONE = _art("lone", D(2018, 1, 1), "The director Bartholomew Pemberton-Ngaio sold a horse at Wharekino.")


class Source:
    def __init__(self, articles=ARTICLES, trading=None):
        self.by = {a["ref"]: a for a in articles}
        self.trading = {FARM: ["Silverfern Stud"]} if trading is None else trading
        self.asked = []

    def articles(self, refs):
        self.asked.append(sorted(refs))
        return {r: self.by[r] for r in refs if r in self.by}

    def spans(self, refs):
        return {r: SPANS[r] for r in refs if r in SPANS}

    def trading_names(self, refs):
        return {r: self.trading[r] for r in refs if r in self.trading}


def _index(path, articles):
    txw.build(iter({"ref": a["ref"], "headline": a["headline"], "text": a["text"], "publisher": a["publisher"],
                    "day": a["published_on"].year * 10_000 + a["published_on"].month * 100 + a["published_on"].day}
                   for a in articles), path, txw.NEWS, threads=1, heap=15_000_000)
    tx.forget(path)
    return path


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    return _index(str(tmp_path_factory.mktemp("news") / "index"), ARTICLES + [LONE])


@pytest.fixture(scope="module")
def got(index):
    return news.news(None, walk_for(), index, Source(ARTICLES + [LONE]))


def by_ref(got):
    return {it["ref"].rsplit("/", 1)[1]: it for it in got["news"]}


def _refs_of(w):
    return {it["ref"] for k, v in w.items() if isinstance(v, list) for it in v if isinstance(it, dict) and "ref" in it} | {w["start"]["ref"]}


# ── the probes ──────────────────────────────────────────────────────────────

def test_the_probes_come_from_the_records_and_a_suppressed_row_gives_none():
    ps, stats = news.probes(walk_for(), Source())
    kinds = {(p["kind"], p["text"]) for p in ps}
    assert ("name", "harriet anne quillfeather") in kinds and ("name", "harriet quillfeather") in kinds
    assert ("company", "kowhai downs equestrian") in kinds, "legal ending optional, macron folded"
    assert ("trading name", "silverfern stud") in kinds and ("co-officer", "bartholomew pemberton ngaio") in kinds
    assert ("role", "director") in kinds and ("place", "wharekino") in kinds
    assert ("company", "tarawhiti saddlery") in kinds and ("company", "pohutukawa megacorp") in kinds
    assert not any("brightwater" in p["text"] for p in ps), "a hub's people are not co-officers"
    assert not any(w in p["text"] for p in ps for w in news.words_of(HIDDEN_NAME)), "hard limit 16: no probe from a suppressed row"
    assert stats["suppressed_rows"] == 1
    assert all(p["origin_ref"] in _refs_of(walk_for()) for p in ps)
    assert not any("invented lane" in p["text"] or "level" in p["text"] for p in ps), "a place is its town, never a street line"


def test_distinctive_things_only_are_searched_alone():
    assert news.distinct("kowhai downs equestrian") and news.distinct("silverfern")
    assert not news.distinct("national holdings") and not news.distinct("trust") and not news.distinct("farm")
    assert news.stem("Kōwhai Downs Equestrian Limited") == "kowhai downs equestrian" == news.stem("Kowhai Downs Equestrian Ltd")


# ── 9.4: what a hit means ──────────────────────────────────────────────────

def test_a_name_alone_is_a_mention(got):
    it = by_ref(got)["mention"]
    assert it["grade"] == "mention" and it["reason"] == news.MENTION and it["via"] is None


def test_a_name_and_a_thing_of_the_subjects_own_records_connects(got):
    items = by_ref(got)
    for key, kind in (("named-thing", "company"), ("co-officer", "co-officer"), ("role", "role"), ("place", "place"),
                      ("folded", "company")):
        it = items[key]
        assert it["grade"] == "connection", key
        assert any(e["kind"] == kind and e["graded"] for e in it["evidence"]), key


def test_a_hub_person_a_far_role_and_an_old_article_only_mention(got):
    items = by_ref(got)
    for key in ("hub-person", "role-far", "out-of-window"):
        assert items[key]["grade"] == "mention", key
    old = [e for e in items["out-of-window"]["evidence"] if e["kind"] == "company"]
    assert old and not any(e["graded"] for e in old), "outside the date window the match is kept and does not grade"


def test_the_horse_farm_connects_through_the_register_without_the_name(got, index):
    it = by_ref(got)["horse-farm"]
    assert it["grade"] == "connection" and it["via"] == FARM
    assert not any(e["kind"] == "name" for e in it["evidence"])
    assert "Silverfern Stud" in it["reason"] and "the subject's name is not in the article" in it["reason"]
    # the same article against a subject the registers do not tie to the stud gives no item
    other = news.news(None, walk_for("Rangitoto Invented Orchards Limited", "companies:companies/9999000000099"), index,
                      Source(ARTICLES + [LONE], trading={}))
    assert "horse-farm" not in by_ref(other)


def test_a_thing_only_hop_two_reaches_is_near_never_confirmed(got):
    it = by_ref(got)["near"]
    assert it["grade"] == "near" and it["via"] == FAR and "second hop" in it["reason"]


def test_a_co_officer_a_role_or_a_place_alone_never_makes_anything(got):
    ps, _ = news.probes(walk_for(), Source())
    assert news.judge(ps, LONE) is None
    assert "lone" not in by_ref(got) and "other-name" not in by_ref(got)


def test_check_4_no_connection_rests_on_a_name_alone(got):
    for it in got["news"]:
        if it["grade"] == "connection":
            assert any(e["kind"] != "name" and e["graded"] for e in it["evidence"]), it["ref"]


def test_check_5_evidence_is_real(got):
    arts = {a["ref"]: a for a in ARTICLES}
    refs = _refs_of(walk_for())
    n = 0
    for it in got["news"]:
        for e in it["evidence"]:
            span = arts[it["ref"]][e["field"]][e["offset"]:e["end"]]
            assert " ".join(tx.fold(span).split()) == e["text"], (it["ref"], e)
            assert e["origin_ref"] in refs
            n += 1
    assert n > len(got["news"]), "the check read evidence"


def test_order_connections_first_newest_first_then_near_then_mentions(got):
    grades = [it["grade"] for it in got["news"]]
    assert grades == sorted(grades, key=news.GRADES.index)
    for g in news.GRADES:
        dates = [it["date"] for it in got["news"] if it["grade"] == g]
        assert dates == sorted(dates, reverse=True)


# ── what an item may show ───────────────────────────────────────────────────

def test_check_9_never_whole_at_most_two_excerpts_of_320(got):
    allowed = {"ref", "view", "kind", "title", "publisher", "byline", "date", "url", "excerpts", "grade", "reason", "rule",
               "via", "evidence", "also_at", "flags"}
    for it in got["news"]:
        assert set(it) == allowed, set(it) - allowed
        assert len(it["excerpts"]) <= news.EXCERPTS
        assert all(len(x["text"]) <= news.SNIPPET for x in it["excerpts"])
        assert sum(len(x["text"]) for x in it["excerpts"]) <= 640
        assert "text" not in it
    long = by_ref(got)["long"]
    assert len(long["excerpts"]) == 2 and len(LONG) > 3 * news.SNIPPET
    assert "Kowhai Downs Equestrian" in long["excerpts"][0]["text"], "the first window is around the evidence that grades"
    assert "Harriet Quillfeather" in long["excerpts"][1]["text"]


def test_check_7_a_suppressed_span_never_shows(got):
    it = by_ref(got)["suppressed"]
    shown = " ".join(x["text"] for x in it["excerpts"])
    assert news.SUPPRESSED in shown and HIDDEN_NAME not in shown
    for x in it["excerpts"]:
        assert all(w not in x["text"] for w in HIDDEN_NAME.split())


def test_check_8_an_address_shaped_window_is_withheld(got):
    it = by_ref(got)["address"]
    assert rules.address_shaped(ARTICLES[11]["text"])
    assert it["excerpts"] == [] and any(f["kind"] == "excerpt-withheld" for f in it["flags"])
    assert not any(rules.address_shaped(x["text"]) for i in got["news"] for x in i["excerpts"])


def test_one_article_in_several_places_is_shown_once(got):
    items = by_ref(got)
    assert "named-thing-copy" not in items or "named-thing" not in items
    one = items.get("named-thing") or items["named-thing-copy"]
    assert len(one["also_at"]) == 1 and got["news_stats"]["syndicated"] == 1


def test_a_headline_hit_still_shows_a_window_of_the_text(got):
    it = by_ref(got)["headline-only"]
    assert it["grade"] == "mention" and it["title"].startswith("Quillfeather prize") and len(it["excerpts"]) == 1


# ── nothing silent ──────────────────────────────────────────────────────────

def test_check_11_listed_and_counted_equal_the_hits(got):
    s = got["news_stats"]
    by = s["by_grade"]
    assert sum(b["listed"] for b in by.values()) == len(got["news"])
    assert sum(b["listed"] + b["counted"] for b in by.values()) + s["no_item"] + s["syndicated"] == s["hits"]
    assert by["mention"]["listed"] == news.LISTED["mention"] and by["mention"]["counted"] > 0
    assert s["probes"]["name"] >= 2 and s["suppressed_rows"] == 1 and s["searched"] > 0


def test_a_thing_too_common_to_search_alone_is_counted_and_still_corroborates(index, monkeypatch):
    monkeypatch.setattr(news, "CEILING", 1)
    out = news.news(None, walk_for(), index, Source(ARTICLES + [LONE]))
    s = out["news_stats"]
    assert s["too_common"] >= 1 and "Kōwhai Downs Equestrian Limited" in s["too_common_things"]
    assert by_ref(out)["named-thing"]["grade"] == "connection", "a name finds it, the thing still corroborates"


def test_no_index_says_so_and_reads_nothing():
    src = Source()
    out = news.news(None, walk_for(), None, src)
    assert out["news"] == [] and out["news_stats"]["unavailable"] == news.NOT_BUILT and src.asked == []


# ── Papers Past, and nothing written ────────────────────────────────────────

def test_check_10_papers_past_is_results_only_from_names_only(got, index):
    asked = []

    def pp(query, limit=20):
        asked.append(query)
        return {"count": 2, "hits": [{"key": "XX19010101.2.1", "paper": "XX", "published_on": D(1901, 1, 1), "title": "Local news",
                                      "url": "https://paperspast.invalid/XX19010101.2.1", "snippet": "… " + "word " * 100 + " …"},
                                     {"key": "XX19020101.2.1", "paper": "XX", "published_on": D(1902, 1, 1), "title": "Notices",
                                      "url": "https://paperspast.invalid/XX19020101.2.1", "snippet": "at 3 Imaginary Street, Nowhere"}]}
    out = news.news(None, walk_for(), index, Source(ARTICLES + [LONE]), papers_past=pp)
    assert asked and all(q.strip('"') in ("harriet anne quillfeather", "harriet quillfeather") for q in asked)
    rs = out["news_results"]
    assert len(rs) == 2 and all(r["kind"] == "result" and r["grade"] is None for r in rs)
    assert all(len(x["text"]) <= news.SNIPPET for r in rs for x in r["excerpts"])
    assert rs[1]["excerpts"] == [] and rs[1]["flags"][0]["kind"] == "excerpt-withheld"
    assert not any(it["ref"].startswith("papers_past") for it in out["news"])


def test_nothing_in_news_writes_or_reaches_a_network_or_a_model():
    src = open(NEWS_PY, encoding="utf-8").read()
    assert not re.search(r"\b(insert\s+into|update\s+\w+\s+set|delete\s+from|truncate|create\s+table|copy\s+\w)", src, re.I)
    assert not re.search(r"\bpub\.links\b|\blinks\.", src)
    mods = {a.name for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module for n in ast.walk(ast.parse(src)) if isinstance(n, ast.ImportFrom)}
    assert not any(m and m.split(".")[0] in ("socket", "urllib", "http", "requests", "httpx") for m in mods), mods
    assert not any(m and "modelclient" in m for m in mods)


def test_nothing_in_links_imports_the_news_section():
    for dirpath, dirs, files in os.walk(os.path.join(REPO, "links")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                assert "products.report.news" not in open(os.path.join(dirpath, f), encoding="utf-8").read(), f
