"""The subject report tab (Arthur, 9 November 2026): a tab in the board's own page, keeping its state."""
from products.board import assets, panes, subject_report as S


def test_every_page_carries_four_tabs_each_named_for_the_script_and_the_on_one_marked():
    html = panes.page("", [], [], tab="subject report")
    for name, label in (("search", "search"), ("uses", "use cases"), ("papers past", "papers past"), ("subject report", "subject report")):
        assert f'data-tab="{name}"' in html and f">{label}</a>" in html, name
    assert 'class="on" data-tab="subject report" href="/subject-report"' in html
    assert "target=" not in html.split("</nav>")[0]                       # a tab of this page, never a new window
    assert assets.url("tabs.js") in html and "tabs.js" in assets.FILES


def test_the_memo_s_links_stay_in_the_tab_with_the_template_and_the_since_date():
    body = ('<a href="/report/companies:companies/94/director/ab?template=banking&amp;since=2026-01-01">report from here</a> '
            '<a href="/report/insolvency:insolvency/1">x</a> <a href="/doc/abc">doc</a>')
    got = S.in_tab(body, "diagnostic")
    assert 'href="/subject-report?ref=companies%3Acompanies%2F94%2Fdirector%2Fab&amp;template=banking&amp;since=2026-01-01"' in got
    assert 'href="/subject-report?ref=insolvency%3Ainsolvency%2F1"' in got     # the default template goes unsaid
    assert 'href="/doc/abc"' in got and "/report/" not in got


def test_the_tab_s_state_is_its_address():
    assert S.href() == "/subject-report"
    assert S.href("ann roe", "", "banking", "2026-01-01") == "/subject-report?q=ann+roe&template=banking&since=2026-01-01"
    assert S.chosen("no-such-template") == S.DEFAULT_TEMPLATE and S.chosen("banking") == "banking"


def test_the_script_keeps_only_the_board_s_own_addresses():
    js = assets.read("tabs.js")[0].decode()
    assert "sessionStorage" in js and 'kept.charAt(0) === "/"' in js and 'kept.charAt(1) !== "/"' in js
