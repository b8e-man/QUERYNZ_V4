"""Ruling 92 (2): a column naming another view's row shows that row's title
as a link to its pane, the key in the hover title and never bare; a far row
not held says so; the keys of a page are resolved in one query per far view."""
import re

from products.board import catalogue as cat
from products.board import panes, search
from products.board.tests.test_panes import ctx, director


class Cursor:
    def __init__(self, cols, rows):
        self.description = [(c,) for c in cols]
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)


class Conn:
    """Answers `select … from pub.<view> where <col> = any(%s) …` from a fixture, recording each query."""

    def __init__(self, tables):
        self.tables, self.asked = tables, []

    def execute(self, sql, params=()):
        self.asked.append((sql, params))
        view = re.search(r"from pub\.(\w+)", sql).group(1)
        cols = re.findall(r"(\w+) = any\(%s\)", sql)
        rows = [r for r in self.tables.get(view, []) if any(str(r.get(c)) in ps for c, ps in zip(cols, params))]
        names = sorted({k for r in self.tables.get(view, []) for k in r})
        return Cursor(names, [tuple(r.get(n) for n in names) for r in rows])


COMPANY = {"key": "companies/9429050975815", "name": "PAYINDA HOLDINGS LIMITED", "nzbn": "9429050975815"}


def test_every_pointer_names_a_catalogued_view_and_a_shown_column():
    for v in cat.VIEWS:
        shown = {c for _, c in v.fields}
        for c, (fv, fc) in cat.pointers(v).items():
            assert c in shown and fv in cat.BY_NAME, (v.name, c)
    for view, ps in cat.POINTERS.items():
        assert view in cat.BY_NAME and all(fv in cat.BY_NAME for _, fv, _ in ps)
    assert cat.pointers(cat.BY_NAME["directors"]) == {"entity_key": ("companies", "key")}
    assert "party" not in cat.pointers(cat.BY_NAME["disclosures"])          # matched by name: the value is the name already


def test_a_directors_company_reads_its_name_with_the_key_on_hover_and_a_missing_one_says_not_held():
    v = cat.BY_NAME["directors"]
    conn = Conn({"companies": [COMPANY]})
    rows = [director(), director(key="companies/2/director/b", entity_key="companies/2")]
    far = search.far_rows(conn, [(v, r) for r in rows] + [(cat.BY_NAME["charity_officers"], {"charity_key": "charities/CC1"})])
    assert len(conn.asked) == 2                                             # one query per far view: companies, charities
    rows[0]["entity_key"] = COMPANY["key"]
    far = search.far_rows(conn, [(v, r) for r in rows])
    held = panes.hit("doe", v, rows[0], ["doe"], search.Boxes(False, ("companies",)), far=far)
    cell = re.search(r"<th>company</th><td>(.*?)</td>", held).group(1)
    assert "PAYINDA HOLDINGS LIMITED</a>" in cell and f'title="{COMPANY["key"]}"' in cell
    assert "p=companies%3Acompanies%2F9429050975815" in cell and "r=companies" in cell
    assert not re.search(r">companies/9429050975815<", held)                # never the bare key as the text
    missing = panes.hit("doe", v, rows[1], ["doe"], far=far)
    assert re.search(r"<th>company</th><td><code>companies/2</code> <span class=\"note\">\(row not held\)</span>", missing)
    pane = panes.row_pane(ctx(v, rows[0], far=far))
    assert "PAYINDA HOLDINGS LIMITED</a>" in pane and "p=directors%3Acompanies%2F1%2Fdirector%2Fa%7Ccompanies%3A" in pane


def test_a_far_view_not_published_is_not_asked_and_an_nzbn_resolves_by_its_own_column():
    v = cat.BY_NAME["company_lookup_roles"]
    r = {"key": "x", "entity_key": "companies/1", "body_nzbn": "9429050975815"}
    conn = Conn({"companies": [COMPANY]})
    far = search.far_rows(conn, [(v, r)], held={"companies"})
    assert len(conn.asked) == 1 and far[("company_lookups", "key", "companies/1")] is None
    assert far[("companies", "nzbn", "9429050975815")]["name"] == COMPANY["name"]


def test_a_suppressed_far_row_shows_name_suppressed():
    v = cat.BY_NAME["company_lookup_roles"]
    r = {"key": "x", "held_key": "d1", "full_name": "A B"}
    far = {("directors", "key", "d1"): director(key="d1", suppressed=True, full_name="Secret Person")}
    html = panes.hit("", v, r, [], far=far)
    assert "Secret" not in html and panes.SUPPRESSED in html
