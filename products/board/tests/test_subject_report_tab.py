"""The subject report tab (Arthur, 9 November 2026): a tab in the board's own page, keeping its state."""
import pytest

from products.board import assets, db, panes, subject_report as S


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


# ── the connections pane (Arthur, 10 November 2026; ruling 159) ─────────────

def _report():
    C = S.connections
    party = C.subject_kind("parties", "parties:p", "A Party")
    return {"found": True, "subject": {"ref": "parties:p"},
            "sections": [{"items": [{"ref": "party_returns:a", "view": "party_return_donors"}, {"ref": "house:x", "view": "hansard_speeches"}]}],
            "connections": {"settings": C.base(party), "set_aside": {"donation": 511}, "kind_words": party["words"]}}


def test_the_pane_holds_types_counts_and_controls_and_no_notes():
    html = S.connections_pane("national", "parties:p", "one", "", _report())
    assert 'class="pane left connections"' in html and 'action="/subject-report"' in html
    assert '<input type="hidden" name="c" value="1">' in html and '<input type="hidden" name="ref" value="parties:p">' in html
    assert 'name="c.donation" value="on" checked' in html and "1 listed · 511 set aside" in html
    assert '<option value="10" selected>10</option>' in html and 'name="c.donation.order"' in html and 'name="c.donation.years"' in html
    assert 'name="c.register:hansard" value="on" checked' in html
    for note in ('class="note"', 'class="reason"', 'class="why"', 'class="warn"', "hard limit", "ruling"):
        assert note not in html, note                       # Arthur: keep the notes out of the pane
    assert S.assets.url("connections.js") in html and "connections.js" in S.assets.FILES


def test_the_pane_s_settings_are_read_from_the_address_and_nothing_else():
    got = S.query_settings({"c": ["1"], "c.donation.top": ["25"], "q": ["x"], "ref": ["y"], "cx": ["1"]})
    assert got == {"c": "1", "c.donation.top": "25"}


def test_a_change_sends_the_pane_s_form():
    js = S.assets.read("connections.js")[0].decode()
    assert 'querySelectorAll("form.connections")' in js and '"change"' in js and "form.submit()" in js


@pytest.mark.slow
def test_the_tab_on_a_party_opens_the_pane_beside_the_report_and_a_setting_rebuilds_it():
    with db.read_connect() as conn:
        key = conn.execute("select party_key from pub.party_return_donors where replaced_by is null group by 1 order by count(*) desc limit 1").fetchone()[0]
        ref = "parties:" + key
        html = S.render(conn, "", ref, "one", "")
        assert html.index('id="connections"') < html.index('id="subject-report"')        # beside the report, first from the left
        assert "Hubs not followed" in html and "the top 10 by size" in html
        assert html.count("ref=party_returns%3A") == 10                     # ten donations, each with its own report link
        wider = S.render(conn, "", ref, "one", "", qs={"c": "1", "c.donation": "on", "c.donation.top": "25", "c.donation.order": "size",
                                                        "c.donation.years": "3"})
        assert '<option value="25" selected>25</option>' in wider and "the top 25 by size" in wider
        assert wider.count("ref=party_returns%3A") == 25
        off = S.render(conn, "", ref, "one", "", qs={"c": "1"})                # the form sent with no tick: every type off
        assert 'name="c.donation" value="on">' in off and "donations are off" in off and "ref=party_returns%3A" not in off
