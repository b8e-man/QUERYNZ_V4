"""The subject report tab (Arthur, 9 November 2026): on every page's bar, opening the diagnostic report on its own server."""
from products.board import panes, server


def test_every_page_carries_the_subject_report_tab_opening_in_a_new_tab():
    html = panes.page("", [], [])
    assert '<a href="/subject-report" target="_blank" rel="noopener">subject report</a>' in html
    assert html.index("papers past</a>") < html.index("subject report</a>")


def test_the_tab_sends_the_reader_to_the_report_s_server_at_their_own_host_with_the_diagnostic_template():
    assert server.subject_report_url("10.0.0.2:8420", env={}) == "http://10.0.0.2:8440/?template=diagnostic"
    assert server.subject_report_url("node1:8420", env={"QV4_REPORT_URL": "http://reports:9000/"}) == "http://reports:9000/?template=diagnostic"
