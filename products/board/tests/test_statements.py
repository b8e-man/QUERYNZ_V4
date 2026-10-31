"""The statements one search and one dossier run, counted on a connection
that answers from fixtures (fix-products-board-7, 31 October 2026): a
search is one statement per published view and one for the catalogue of
views, each view's statement testing the words loosely over the row's text
as held before the fold (two thirds of a scan's cost on the live tables)
and the fold's exact test after; a dossier of a group past the many-rows
line is one statement for the group's rows, one per view that can
suppress, one page per view and a fixed few for its links, never one per
row. The counts are pinned so a statement per row, or a fold over every
row, cannot come back unseen."""
import datetime as dt
import re
import threading

import pytest

from products.board import catalogue as cat
from products.board import dossier, people, search

V = cat.BY_NAME
TWO_WORDS = "Graeme Hart"


class Cursor:
    def __init__(self, names, rows):
        self.description = [(n,) for n in names]
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def fetchone(self):
        return self._rows[0] if self._rows else None


class Counting:
    """A connection recording every statement; `answer(sql, params)` gives (column names, rows)."""
    closed = False

    def __init__(self, answer):
        self.answer, self.sql, self.params, self._lock = answer, [], [], threading.Lock()

    def execute(self, sql, params=()):
        with self._lock:
            self.sql.append(sql)
            self.params.append(params)
        return Cursor(*self.answer(sql, params))


def views_only(sql, params):
    if "information_schema.tables" in sql:
        return ["table_name"], [(v.name,) for v in cat.VIEWS]
    return ["key"], []


@pytest.fixture
def counting(monkeypatch):
    conn = Counting(views_only)
    monkeypatch.setattr(search, "_conn", lambda: conn)
    return conn


def test_a_search_is_one_statement_per_view_with_the_loose_test_before_the_fold(counting):
    search.search(counting, TWO_WORDS)
    assert len(counting.sql) == 1 + len(cat.VIEWS)
    scans = [(s, p) for s, p in zip(counting.sql, counting.params) if "information_schema" not in s]
    assert len(scans) == len(cat.VIEWS)
    for sql, params in scans:
        v = V[re.search(r"from pub\.(\w+)", sql).group(1)]
        raw = "concat_ws(' ', " + ", ".join(v.search) + ")"
        assert sql.count(f"{raw} ~* %s") == 2 and sql.count(" ~ %s") == 2, sql       # each word: the loose test, and the exact
        assert sql.index("translate(lower(") < sql.index(f"{raw} ~* %s")             # the exact test's parameters come first
        assert params[:2] == [r"\mgraeme", r"\mhart"] and params[-1] == search.LIMIT
        assert params[-3:-1] == [r"\mgr[aāĀ][eēĒ]m[eēĒ]", r"\mh[aāĀ]rt"]
    counting.sql.clear()
    regs = search.held_registers({v.name for v in cat.VIEWS})
    res = search.search(counting, TWO_WORDS, limit=search.RESULTS_LIMIT, registers=regs, tabs=True)
    assert res["tabs"] == search.BOX and len(counting.sql) == 1 + len(cat.VIEWS)      # the results pane's tabs: still one per view
    counting.sql.clear()
    people.gather(counting, [], people.named_groups(counting, TWO_WORDS, registers=regs))
    assert len(counting.sql) == 1                                                     # the entity state on top: one on pub.names' keys


def test_the_loose_pattern_holds_every_word_the_fold_matches():
    assert search.loose_re("tamaki") == "t[aāĀ]m[aāĀ][k\u212a][iīĪ]"                 # the Kelvin sign folds to k under lower()
    assert search.loose_re("garry|gareth") == r"(?:g[aāĀ]rry|g[aāĀ]r[eēĒ]th)"
    assert search.loose_re("a.b(c") == r"[aāĀ]\.b\(c"
    assert search.prefilter_sql(V["companies"], ["foley"], "123") == ("", [])         # a number's rows need not hold the words
    clause, params = search.prefilter_sql(V["companies"], ["hart"], None, whole=True)
    assert clause == " and concat_ws(' ', name) ~* %s" and params == [r"\mh[aāĀ]rt\M"]


# ── the dossier of a group past the many-rows line ──────────────────────────

GID = "hansard:t/0"
SPEECHES = [{"key": f"t/{i}", "sitting_on": dt.date(2020, 1, 1) + dt.timedelta(days=i), "member_name": "A Member", "document": None}
            for i in range(dossier.MANY_AT + 50)]
DIRECTORS = [{"key": "c/1/director/a", "full_name": "A Member", "suppressed": False, "document": None},
             {"key": "c/7/director/s", "full_name": "Hidden Person", "suppressed": True, "document": None}]


def group_rows(sql, params):
    if sql.startswith("select n.view, n.name_filed, count(*) as n, array_agg(n.key)"):
        return (["view", "name_filed", "n", "keys", "contested"],
                [("hansard_speeches", "A Member", len(SPEECHES), [r["key"] for r in SPEECHES], False),
                 ("directors", "A Member", 1, [DIRECTORS[0]["key"]], False),
                 ("directors", "Hidden Person", 1, [DIRECTORS[1]["key"]], False)])
    if sql.startswith("select r.key::text as key from pub.directors r"):
        return ["key"], [(DIRECTORS[1]["key"],)]
    if sql.startswith("with d as materialized (select r."):
        rows = SPEECHES if "pub.hansard_speeches r" in sql else DIRECTORS[:1]
        keys, limit, offset = set(params[0]), *params[-2:]
        page = [r for r in rows if r["key"] in keys][::-1][offset:offset + limit]
        names = list(page[0]) + ["_first_day", "_last_day"] if page else ["key"]
        return names, [tuple(r.values()) + (None, None) for r in page]
    return ["key"], []


def test_a_many_rows_dossier_is_one_statement_for_the_group_one_per_view_and_none_per_row(monkeypatch):
    conn = Counting(group_rows)
    monkeypatch.setattr(dossier.document, "statuses", lambda conn, shas: {})
    x = dossier.gather(conn, people.entity_id(GID))
    assert x["many"] and x["hidden_count"] == 1 and sorted((v.name, k) for v, k in x["views"]) == [("directors", 1), ("hansard_speeches", len(SPEECHES))]
    assert len(x["rows"]) == 1 + dossier.VIEW_ROWS
    heads = [s.split(" from ")[0][:60] for s in conn.sql]
    group = [s for s in conn.sql if s.startswith("select n.view, n.name_filed, count(*) as n, array_agg")]
    hidden = [s for s in conn.sql if s.startswith("select r.key::text as key from pub.")]
    pages = [s for s in conn.sql if s.startswith("with d as materialized")]
    links = [s for s in conn.sql if "pub.links" in s or "pub.decisions" in s]
    assert len(group) == 1 and len(hidden) == 1 and len(pages) == 2, heads                # the group once; directors can suppress; a page per view
    assert len(links) == 4, heads                                                       # own links, near, related, decisions: by every ref at once
    assert len(conn.sql) == 1 + 1 + 2 + 4, heads                                       # and nothing per row
    for s in pages:
        assert "pub.groups" not in s and "pub.names" not in s                           # the group's rows are never joined again
