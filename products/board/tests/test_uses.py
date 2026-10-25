"""The use cases tab (ruling 87), pure: the plan's table read at render time
from the copy the board runs from (here a fixture copy), seventeen rows in
the plan's order with 17 after 15 as the plan prints it; each row's scan
templates and the registers the reference names, held or not held from the
views present; a missing table is said, not hidden."""
import os
import re
import shutil
import urllib.error
import urllib.request

import pytest

from products.board import panes, server, uses

REAL = os.path.join(uses.REPO, uses.TABLE)
#: the ten subject-report templates of step 5.2, by folder number (the owner line names a session, not a use case)
REPORTS = ((2, "legal"), (3, "banking"), (4, "agriculture"), (5, "credit"), (6, "insurance"), (7, "construction"),
           (8, "recruitment"), (11, "healthcare"), (12, "property"), (13, "ownership"))
#: the report server's form with a template chosen, copied from products/report/server.py (`GET /`, `get("template", …)`)
REPORT_FORM = "/?template="
BASE = {"report": "http://board.lan:8440", "scan": "http://board.lan:8450", "site": "http://board.lan:8430"}


def fixture_repo(tmp_path, table=True):
    repo = tmp_path / "copy"
    for rel in ((uses.TABLE, uses.NOT_HELD) if table else (uses.NOT_HELD,)):
        os.makedirs(repo / os.path.dirname(rel), exist_ok=True)
        shutil.copy(os.path.join(uses.REPO, rel), repo / rel)
    t = repo / "products/scan/templates/a-use-case-nine-scan"
    t.mkdir(parents=True)
    (t / "template.toml").write_text('name = "a-use-case-nine-scan"\ntitle = "Suppliers and donors"\n'
                                     'owner = "products/scan/templates, step 6.2 (use case 9)"\n', encoding="utf-8")
    u = repo / "products/scan/templates/a-fielded-scan"
    u.mkdir(parents=True)
    (u / "template.toml").write_text('name = "a-fielded-scan"\ntitle = "Fielded"\nuse_case = 14\n', encoding="utf-8")
    for n, name in REPORTS:
        d = repo / f"products/templates/{n:02d}-{name}"
        d.mkdir(parents=True)
        (d / "template.toml").write_text(f'name = "{name}"\ntitle = "The {name} report"\n'
                                         f'owner = "products/templates/{n:02d}-{name}, step 5.2 (session {name}-1)"\n', encoding="utf-8")
    t = repo / "products/scan/templates/a-use-case-ten-scan"
    t.mkdir(parents=True)
    (t / "template.toml").write_text('name = "a-use-case-ten-scan"\ntitle = "Awards"\nowner = "products/scan/templates, step 6.2 (use case 10)"\n',
                                     encoding="utf-8")
    t = repo / "products/scan/templates/a-second-nine-scan"
    t.mkdir(parents=True)
    (t / "template.toml").write_text('name = "a-second-nine-scan"\ntitle = "Shareholders"\nuse_case = 9\n', encoding="utf-8")
    p = repo / "products/scan/templates/a-proving-scan"
    p.mkdir(parents=True)
    (p / "template.toml").write_text('name = "a-proving-scan"\ntitle = "Proves the shape"\nowner = "products/scan, step 6.1"\n', encoding="utf-8")
    return str(repo)


def test_seventeen_rows_in_the_plan_s_order_with_17_after_15(tmp_path):
    html = server.render_uses(fixture_repo(tmp_path), held={"grants", "iwi_directory_entities"})
    numbers = re.findall(r"<tr><td>(\d+)</td>", html)
    plan = [c[0] for c in (l.strip("|").split("|") for l in open(REAL, encoding="utf-8") if re.match(r"\|\s*\d+\s*\|", l))]
    assert numbers == [n.strip() for n in plan] and len(numbers) == 17
    assert numbers.index("17") == numbers.index("15") + 1 and numbers[-1] == "16"
    first = html[html.index("<tr><td>1</td>"):html.index("<tr><td>2</td>")]
    for cell in ("Follow the Money", "Reporters, the public", "Who funds parties and candidates, and what followed", "Published site", "<td>4</td>"):
        assert cell in first
    assert 'class="on" href="/uses">use cases</a>' in html and "<script" not in html


def test_each_row_carries_its_templates_and_the_registers_its_reference_names_held_or_not(tmp_path):
    html = server.render_uses(fixture_repo(tmp_path), held={"grants", "iwi_directory_entities"})

    def row(n):
        at = html.index(f"<tr><td>{n}</td>")
        return html[at:html.index("</tr>", at)]
    assert "a-use-case-nine-scan" in row(9) and "a-use-case-nine-scan" not in row(10)
    assert "a-fielded-scan" in row(14) and "none built" in row(15) and "<code>legal</code>" in row(2)
    assert "a-proving-scan" not in html                                   # a template naming no use case is under none
    assert re.search(r"Grants[^<]*: Grants from[^<]*<span class=\"meta\">held</span>", row(10))
    assert re.search(r"Live tenders[^<]*: Government procurement[^<]*<span class=\"warn\">not held</span>", row(10))
    assert "Iwi and hapū directory" in row(14) and "Stock exchange announcements: <span class=\"note\">not held, no lane</span>" in row(13)
    assert "none named" in row(16)                                        # the reference names no not-held source for history search


def test_the_tab_reads_the_copy_it_is_given_at_render_time(tmp_path):
    repo = fixture_repo(tmp_path)
    with open(os.path.join(repo, uses.TABLE), "a", encoding="utf-8") as f:
        f.write("| 18 | A later use case | Someone | A question | Subject report | 8 |\n")
    assert re.findall(r"<tr><td>(\d+)</td>", server.render_uses(repo, held=set()))[-1] == "18"


def test_a_missing_table_is_said(tmp_path):
    html = server.render_uses(fixture_repo(tmp_path, table=False), held=set())
    assert "not in the copy the board runs from" in html and "<tr><td>" not in html


def test_a_template_s_use_case_is_its_field_else_its_owner_line():
    assert uses.use_case_of({"use_case": 9}) == ("9",) and uses.use_case_of({"use_case": [9, 10]}) == ("9", "10")
    assert uses.use_case_of({"owner": "products/scan/templates, step 6.2 (use case 14)"}) == ("14",)
    assert uses.use_case_of({"owner": "products/scan, step 6.1"}) == ()
    assert all(src.split(":")[0] for src, _ in uses.parse_not_held(open(os.path.join(uses.REPO, uses.NOT_HELD), encoding="utf-8").read()))
    for src, _ in uses.parse_not_held(open(os.path.join(uses.REPO, uses.NOT_HELD), encoding="utf-8").read()):
        assert any(src.startswith(w) for w in uses.cat.REFERENCE_REGISTERS), src     # every source the reference names is mapped


def row_of(html, n):
    at = html.index(f"<tr><td>{n}</td>")
    return html[at:html.index("</tr>", at)]


def test_thirteen_use_cases_have_templates_built_ten_report_and_three_scan_and_three_are_held(tmp_path):
    html = server.render_uses(fixture_repo(tmp_path), held=set(), host="board.lan:8420", env={})
    built = [n for n in re.findall(r"<tr><td>(\d+)</td>", html) if "none built" not in row_of(html, n)]
    assert sorted(built, key=int) == ["2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14"]
    assert sum("Subject report: " in row_of(html, n) for n in built) == 10
    assert [n for n in built if "Register scan: " in row_of(html, n)] == ["9", "10", "14"]
    for n, why in (("15", "held: ruling 79 (no document reading until node1 returns)"), ("16", "held: ruling 63 (step 7)"),
                   ("17", "held: ruling 63 (step 7)")):
        assert "<a " not in row_of(html, n) and why in row_of(html, n)


def test_each_name_opens_its_interface_in_a_new_tab_on_its_own_server(tmp_path):
    html = server.render_uses(fixture_repo(tmp_path), held=set(), host="board.lan:8420", env={})
    links = re.findall(r"<a [^>]*>", html[html.index('<table class="uc">'):])
    assert len(links) == 13 + 1 + 1                   # thirteen names and Follow the Money's, one more scan for 9
    assert all('target="_blank"' in a and 'rel="noopener"' in a for a in links)
    assert 'href="http://board.lan:8440/?template=legal"' in row_of(html, 2)
    assert 'href="http://board.lan:8430/"' in row_of(html, 1)
    nine = row_of(html, 9)                            # the first template on the name, the rest beside
    assert re.search(r'href="http://board.lan:8450/scan/a-second-nine-scan"[^>]*><strong>Government', nine)
    assert "also: " in nine and 'href="http://board.lan:8450/scan/a-use-case-nine-scan"' in nine
    assert "127.0.0.1" not in html


def test_the_report_link_is_the_report_server_s_form_with_its_template():
    assert uses.href_of({"name": "legal", "server": "report"}, BASE) == BASE["report"] + REPORT_FORM + "legal"
    text = open(os.path.join(uses.REPO, "products", "report", "server.py"), encoding="utf-8").read()   # read, never imported
    assert 'if url.path == "/":' in text and 'render("", get("template", "subject")' in text
    assert uses.href_of({"name": "tender-awards", "server": "scan"}, BASE) == BASE["scan"] + "/scan/tender-awards"


def test_the_servers_take_the_request_s_host_unless_the_environment_names_one():
    assert uses.bases("10.0.0.2:8420", {}) == {"report": "http://10.0.0.2:8440", "scan": "http://10.0.0.2:8450", "site": "http://10.0.0.2:8430"}
    assert uses.bases("[fe80::1]:8420", {})["scan"] == "http://[fe80::1]:8450"
    assert uses.bases("node2", {"QV4_SCAN_URL": "http://scan.lan:9/"})["scan"] == "http://scan.lan:9"
    assert uses.bases("", {})["report"].endswith(":8440") and "127.0.0.1" not in uses.bases("", {})["report"]


def test_a_template_with_no_field_or_owner_number_takes_its_folder_s():
    assert uses.use_case_of({"owner": "products/templates/02-legal, step 5.2 (session legal-1)"}, "/x/products/templates/02-legal") == ("2",)
    assert uses.use_case_of({"owner": "x"}, "/x/products/templates/11-healthcare") == ("11",)
    assert uses.use_case_of({}, "/x/products/templates/ftm") == ()


def test_the_connection_counter_reads_db_in_use_over_max_with_the_logins_on_hover():
    bar = panes.db_counter({"max": 100, "by": {"qv4_product": 3, "qv4_read": 2, "postgres": 1, "querynz_api": 4}})
    assert ">db 10/100<" in bar
    assert 'title="qv4_product 3, qv4_owner 0, qv4_read 2, qv4_oldread 0, other 5"' in bar
    assert ">db ?<" in panes.db_counter(None)
    page = panes.page("", [], [], db={"max": 100, "by": {"qv4_product": 1}})
    assert ">db 1/100<" in page[page.index("<header>"):page.index("</header>")]
    assert ">db ?<" in server.render_uses(held=set(), env={})          # no answer given: the page still renders


@pytest.mark.slow
def test_every_link_on_the_tab_answers_on_the_local_servers():
    html = server.render_uses(held=set(), host="localhost", env={})
    urls = re.findall(r'<a [^>]*href="([^"]+)" target="_blank"', html)
    assert urls
    down = set()
    for url in urls:
        base = url.split("/", 3)[2]
        if base in down:
            continue
        try:
            with urllib.request.urlopen(url.replace("&amp;", "&"), timeout=10) as r:
                assert r.status == 200, url
        except urllib.error.HTTPError as e:
            pytest.fail(f"{url} answered {e.code}")
        except OSError as e:
            down.add(base)
            print(f"skipped {base}: the server is down ({e})")
    if down:
        pytest.skip(f"servers down: {sorted(down)}")
