"""The source lights beside the registers: the one file under <live>/checks,
read once a minute; stale or missing, every dot grey; the dot's reason on
hover and in words for a screen reader; the colours held by the sheet."""
import datetime as dt
import json
import re

from products.board import catalogue as cat
from products.board import lights, panes, search

NOW = dt.datetime(2026, 11, 3, 23, 0, tzinfo=dt.timezone.utc)
HELD = [r for r, _ in cat.REGISTERS][:5]


def file(tmp_path, age_minutes=10, rows=None):
    p = tmp_path / "source-lights.json"
    p.write_text(json.dumps({"computed_at": (NOW - dt.timedelta(minutes=age_minutes)).isoformat(),
                             "lights": rows if rows is not None else [
                                 {"register": "tenancy_tribunal", "light": "red",
                                  "reason": "the fetch gate holds forms.justice.govt.nz since 4 Nov 00:24: reset <every> PDF"},
                                 {"register": HELD[0], "light": "green", "reason": "up to date"},
                                 {"register": HELD[1], "light": "orange", "reason": "a gap"}]}))
    return str(p)


def dots(html):
    return re.findall(r'<span class="light (\w+)" title="([^"]*)" data-light="\w+"><span class="sr">([^<]*)</span></span>', html)


def fresh(path, monkeypatch=None):
    lights._CACHE.update(at=None, path=None, data=None)
    return lights.current(path, now=NOW)


def test_a_fresh_file_lights_each_register(tmp_path):
    L = fresh(file(tmp_path))
    html = panes.register_boxes(HELD, search.FIRST, "q", lights=L)
    got = dots(html)
    assert len(got) == len(cat.REGISTERS) + len(cat.NOT_HELD)          # one dot per register, held or not
    by = {c: [t for k, t, _ in got if k == c] for c in lights.LIGHTS}
    assert len(by["red"]) == 1 and by["red"][0].startswith("updates not working: the fetch gate holds forms.justice.govt.nz")
    assert "&lt;every&gt;" in by["red"][0]                               # escaped
    assert len(by["green"]) == 1 and len(by["orange"]) == 1
    assert all(t.endswith(lights.UNKNOWN) for t in by["grey"])           # the file names no other register
    assert any(sr.startswith("red light, updates not working") for _, _, sr in got)


def test_the_held_and_not_held_rows_carry_their_dot(tmp_path):
    html = panes.register_boxes(HELD, search.FIRST, None, lights=fresh(file(tmp_path)))
    li = [x for x in html.split("<li") if "Tenancy Tribunal" in x][0]
    assert 'class="light red"' in li and "not held" in li
    li = [x for x in html.split("<li") if dict(cat.REGISTERS)[HELD[0]] in x][0]
    assert 'class="light green"' in li


def test_a_stale_file_greys_every_dot(tmp_path):
    L = fresh(file(tmp_path, age_minutes=2 * 60 + 5))
    got = dots(panes.register_boxes(HELD, search.FIRST, "q", lights=L))
    assert got and {k for k, _, _ in got} == {"grey"}
    assert all("the lights are stale" in t for _, t, _ in got)


def test_a_missing_or_broken_file_greys_every_dot(tmp_path):
    (tmp_path / "bad.json").write_text("{")
    for L in (fresh(str(tmp_path / "none.json")), fresh(str(tmp_path / "bad.json"))):
        got = dots(panes.register_boxes(HELD, search.FIRST, "q", lights=L))
        assert {k for k, _, _ in got} == {"grey"} and all("the lights are stale" in t for _, t, _ in got)


def test_an_unknown_light_is_not_shown(tmp_path):
    L = fresh(file(tmp_path, rows=[{"register": HELD[0], "light": "purple", "reason": "x"}]))
    assert lights.light_for(L, HELD[0]) == ("grey", lights.UNKNOWN)


def test_read_at_most_once_a_minute(tmp_path):
    p = file(tmp_path)
    lights._CACHE.update(at=None, path=None, data=None)
    t = [1000.0]
    assert lights.current(p, now=NOW, clock=lambda: t[0])[HELD[0]][0] == "green"
    file(tmp_path, rows=[{"register": HELD[0], "light": "red", "reason": "x"}])
    t[0] += 30
    assert lights.current(p, now=NOW, clock=lambda: t[0])[HELD[0]][0] == "green"   # cached
    t[0] += 31
    assert lights.current(p, now=NOW, clock=lambda: t[0])[HELD[0]][0] == "red"


def test_no_lights_given_no_dots():
    assert "span class=\"light" not in panes.register_boxes(HELD, search.FIRST, "q")


def test_the_left_pane_carries_the_lights(tmp_path):
    html = panes.left_pane("q", HELD, search.FIRST, lights=fresh(file(tmp_path)))
    assert len(dots(html)) == len(cat.REGISTERS) + len(cat.NOT_HELD)
    assert "<script" not in html                                       # no script: the dots stand without one


def test_the_colours_are_the_sheet_s_and_hold_the_floor():
    assert panes.contrast_problems() == []
    broken = panes.CSS.replace("span.light.red{border-color:#f05050}", "span.light.red{border-color:#301010}")
    assert any("red light" in p for p in panes.contrast_problems(broken))
    assert {c for c, _ in panes.LIGHT_COLOURS} == set(lights.LIGHTS)


def test_an_mcp_fed_register_shows_its_copy_s_freshness_in_one_line(tmp_path):
    """Ruling 159: the light of a register the ingest MCP feeds carries one short line on the provider's copy, after
    its reason, on hover and for a screen reader; a register without one shows its reason alone."""
    line = "provider's copy: newest 8 Nov 00:15; its source publishes about weekly"
    L = fresh(file(tmp_path, rows=[
        {"register": HELD[0], "light": "green", "reason": "up to date", "fresh": line},
        {"register": HELD[1], "light": "orange", "reason": "a gap"},
        {"register": HELD[2], "light": "green", "reason": "", "fresh": line}]))
    assert lights.light_for(L, HELD[0]) == ("green", f"up to date; {line}")
    assert lights.light_for(L, HELD[1]) == ("orange", "a gap")
    assert lights.light_for(L, HELD[2]) == ("green", line)
    got = dots(panes.register_boxes(HELD, search.FIRST, "q", lights=L))
    green = [(t, sr) for k, t, sr in got if k == "green"]
    assert any(t.endswith("up to date; " + line.replace("'", "&#x27;")) and sr.endswith("up to date; " + line.replace("'", "&#x27;"))
               for t, sr in green), green


def test_the_sources_tab_links_each_name_and_gives_its_line_on_hover():
    from products.board import panes
    rows = [{"kind": "register", "name": "x", "label": "X & co", "url": "https://x.govt.nz", "light": "red",
             "line": "Red: the last run failed"},
            {"kind": "news", "name": "odt.co.nz", "label": "odt.co.nz", "url": "https://odt.co.nz", "light": "green",
             "line": "Green: newest 2 days old"},
            {"kind": "request", "name": "r", "label": "asked", "url": "/sources#news", "light": "orange",
             "line": "Orange: asked 13 Nov"}]
    html = panes.page("", [], [panes.sources_pane(rows)], tab="sources")
    assert '<a href="https://x.govt.nz" target="_blank" rel="noopener noreferrer">X &amp; co</a>' in html
    assert 'title="Red: the last run failed"' in html and 'title="Green: newest 2 days old"' in html
    assert '<a href="/sources#news">asked</a>' in html                       # a board address stays in this tab
    assert 'class="on" data-tab="sources" href="/sources"' in html
    assert html.index("Registers") < html.index("News, by site") < html.index("Asked of the provider")


def test_the_sources_tab_says_when_there_is_nothing_to_show():
    from products.board import panes
    assert "no sources in the lights file yet" in panes.sources_pane([], "the lights are stale: no lights file")
