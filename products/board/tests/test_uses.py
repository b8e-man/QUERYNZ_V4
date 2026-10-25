"""The use cases tab (ruling 87), pure: the plan's table read at render time
from the copy the board runs from (here a fixture copy), seventeen rows in
the plan's order with 17 after 15 as the plan prints it; each row's scan
templates and the registers the reference names, held or not held from the
views present; a missing table is said, not hidden."""
import os
import re
import shutil

from products.board import server, uses

REAL = os.path.join(uses.REPO, uses.TABLE)


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
    assert "a-fielded-scan" in row(14) and "none built" in row(2)
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
