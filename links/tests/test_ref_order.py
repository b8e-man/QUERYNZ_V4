"""The lane's one order of refs (fix-links-5, 28 October 2026): bytes,
which for UTF-8 is Python's code-point order. The database collates text
by en_NZ.UTF-8, which ignores spaces and punctuation and folds case at its
first level, so `links.pair` (Python) and an SQL least() or CHECK under the
database's collation disagreed on refs with capitals, spaces or punctuation,
and the first build after rulings 114 and 116 died on `links_pair_order`.
Fast tests read the SQL text; a slow test builds, groups and publishes refs
the two orders disagree on, on the real engine (a sample-database schema,
rolled back), and the same build with the plain comparison put back fails."""
import os
import re

import pytest

import links

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: refs on which the database's collation and Python disagree, or nearly do (checked against the engine in the slow test)
REFS = ["x:a b", "x:a-b", "x:a c", "x:ab", "x:A", "x:a", "x:B", "x:Hawke's", "x:hawkes", "x:b"]
DISAGREE = [("x:A", "x:a"), ("x:a", "x:B"), ("x:Hawke's", "x:hawkes"), ("x:a c", "x:ab")]


def _code(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def test_pair_orders_by_bytes():
    for a in REFS:
        for b in REFS:
            if a != b:
                ra, rb = links.pair(a, b)
                assert ra.encode() < rb.encode()


def test_every_pair_order_check_compares_bytes():
    sql = links.tables_sql()
    checks = re.findall(r"CHECK \(\(?row_a[^)]*\)?\s*<\s*row_b\)", sql)
    assert len(checks) == 6                                     # three in CREATE TABLE, three in the migration
    assert all('COLLATE "C"' in c for c in checks), checks


@pytest.mark.parametrize("name", ["build.py", "pairs.py", "measure.py", "check.py", "rows.py", "old.py", "review.py"])
def test_every_least_greatest_and_smallest_ref_in_the_lane_s_sql_is_in_the_lane_s_order(name):
    """A ref compared in SQL without COLLATE "C" is compared by the locale: a static audit, so a new rule cannot bring it back."""
    code = _code(name)
    for m in re.finditer(r"\b(least|greatest)\(([^,]+),", code):
        assert 'COLLATE "C"' in m.group(2), (name, m.group(0))
    for m in re.finditer(r"\bmin\(((?:\w+\.)?(?:ref|entity_ref|row_a|row_b|row_key|body))\b([^)]*)\)", code):
        assert 'COLLATE "C"' in m.group(2), (name, m.group(0))
    for m in re.finditer(r"ORDER BY ((?:\w+\.)?(?:ref|entity_ref|row_a|row_b|row_key|body))\b(\s*COLLATE \"C\")?", code):
        assert m.group(2), (name, m.group(0))
    for m in re.finditer(r"((?:\w+\.)?(?:ref|entity_ref))( COLLATE \"C\")? [<>] ", code):
        assert m.group(2), (name, m.group(0))


# ── the real engine ──────────────────────────────────────────────────────

#: the published views build.py reads, as empty stubs with the columns it reads
PUB_STUBS = {
    "members": "key text, candidate text, election text, electorate text, from_on date, ended_on date, to_by date, party_registered text, route text",
    "candidates": "key text, party_registered text, election text, electorate text, list_place int",
    "candidate_return_totals": "key text, replaced_by text, year int, electorate text",
    "shareholders": "key text, holder_nzbn text, shareholder_type text, name text",
    "companies": "key text, nzbn text, number text, register text, name text",
    "gazette_liquidations": "key text, company_number text, notice text",
    "electorates": "key text, name text",
    "mp_interest_returns": "key text, electorate text",
    "mp_interests": "key text, text text",
    "party_return_donors": "key text, party text, year int",
    "disclosures": "key text, party text, given_on date",
}


class _Cur:
    def __init__(self, cur, fix):
        object.__setattr__(self, "_c", cur)
        object.__setattr__(self, "_f", fix)

    def execute(self, q, *a, **k):
        return self._c.execute(self._f(q), *a, **k)

    def executemany(self, q, *a, **k):
        return self._c.executemany(self._f(q), *a, **k)

    def copy(self, q, *a, **k):
        return self._c.copy(self._f(q), *a, **k)

    def __enter__(self):
        self._c.__enter__()
        return self

    def __exit__(self, *e):
        return self._c.__exit__(*e)

    def __iter__(self):
        return iter(self._c)

    def __getattr__(self, n):
        return getattr(self._c, n)

    def __setattr__(self, n, v):
        setattr(self._c, n, v)


class _Scratch:
    """The real connection in one transaction the test rolls back; `pub.` read from the scratch stubs; with `plain`, every
    COLLATE in the SQL taken out (the comparison as it was before fix-links-5)."""

    def __init__(self, conn, pub, plain=False):
        self.conn, self.pub, self.plain = conn, pub, plain

    def fix(self, q):
        q = re.sub(r"\bpub\.", f"{self.pub}.", q)
        return q.replace(' COLLATE "C"', "").replace(' COLLATE "default"', "") if self.plain else q

    def execute(self, q, *a, **k):
        return self.conn.execute(self.fix(q), *a, **k)

    def cursor(self, *a, **k):
        return _Cur(self.conn.cursor(*a, **k), self.fix)

    def commit(self):
        pass

    def __getattr__(self, n):
        return getattr(self.conn, n)


def _row(ref, given, middle, family):
    fl = f"{given} {family}"
    full = f"{given} {middle} {family}" if middle else fl
    return (ref, "x", "fixture", ref[2:], "person", f"{given} {middle or ''} {family}", given, middle, family, full, fl, full, bool(middle))


ROWS = [_row(r, "jane", "mary", "doe") for r in ("x:A", "x:a", "x:B")] + [_row("x:b", "jane", None, "doe")] \
     + [_row(r, "john", "paul", "hawke") for r in ("x:Hawke's", "x:hawkes")] \
     + [_row(r, "sam", None, "lee") for r in ("x:a b", "x:a-b", "x:a c", "x:ab")]


@pytest.mark.slow
def test_refs_the_two_orders_disagree_on_build_group_and_publish_and_the_plain_comparison_fails():
    import support.db as db
    from links import build, check
    if not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no credential file on this box")
    import psycopg
    s = "scratch_links_order_test"
    p = f"{s}_pub"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as raw:
        try:
            # the fixture is worth something only where the engine's own collation disagrees with Python
            for a, b in DISAGREE:
                assert raw.execute("SELECT %s::text < %s::text", (a, b)).fetchone()[0] != (a < b), (a, b)
            raw.execute(f"CREATE SCHEMA {s}")
            raw.execute(f"CREATE SCHEMA {p}")
            # a table made before the fix: the CHECKs under the database's collation, a link stored in its order
            old = links.ddl(s).split("-- The pair order is bytes")[0].replace('(row_a COLLATE "C") < row_b', "row_a < row_b")
            raw.execute(old)
            raw.execute(f"INSERT INTO {s}.links (row_a, row_b, rule, evidence, grade) VALUES ('x:a', 'x:A', 'full-name@1', '{{}}', 'confirmed')")
            raw.execute(f"INSERT INTO {s}.test_pairs (kind, truth, band, row_a, row_b, basis, seed) "
                        f"VALUES ('k', 'one person', 'rare', 'x:ab', 'x:a c', '{{}}', 1)")
            with pytest.raises(psycopg.errors.CheckViolation):     # the fault: Python's pair refused by the locale's CHECK
                with raw.transaction():
                    raw.execute(f"INSERT INTO {s}.decisions (row_a, row_b, verdict, made_by, made_on) VALUES (%s, %s, 'same', 'person:test', '{{}}')",
                                links.pair("x:a c", "x:ab"))
            kept = raw.execute(f"SELECT link_id FROM {s}.links").fetchone()[0]
            raw.execute(links.ddl(s))                              # the job's own start: the migration
            for t, c in (("links", "links_pair_order"), ("decisions", "decisions_pair_order"), ("test_pairs", "test_pairs_order")):
                assert 'COLLATE "C"' in raw.execute(f"""SELECT pg_get_constraintdef(oid) FROM pg_constraint
                                                       WHERE conrelid = '{s}.{t}'::regclass AND conname = %s""", (c,)).fetchone()[0]
            assert raw.execute(f"SELECT link_id, row_a, row_b FROM {s}.links").fetchall() == [(kept, "x:A", "x:a")]   # turned round in place
            assert raw.execute(f"SELECT row_a, row_b FROM {s}.test_pairs").fetchall() == [("x:a c", "x:ab")]
            raw.execute(links.ddl(s))                              # and again: a no-op
            raw.execute(f"INSERT INTO {s}.decisions (row_a, row_b, verdict, made_by, made_on) VALUES (%s, %s, 'same', 'person:test', '{{}}')",
                        links.pair("x:a c", "x:ab"))
            for v, cols in PUB_STUBS.items():
                raw.execute(f"CREATE TABLE {p}.{v} ({cols})")
            with raw.cursor() as w:
                w.executemany(f"""INSERT INTO {s}.rows (ref, register, view, key, kind, name_filed, given, middle, family, name_key, fl_key,
                                  full_key, has_middle) VALUES ({', '.join(['%s'] * 13)})""", ROWS)

            # the mutation: the same build with the plain comparison put back goes red
            with pytest.raises(psycopg.errors.CheckViolation):
                with raw.transaction():
                    plain = _Scratch(raw, p, plain=True)
                    build.build_all(plain, s, log=lambda *_: None, reader=plain)

            conn = _Scratch(raw, p)
            build.build_all(conn, s, log=lambda *_: None, reader=conn)
            raw.execute(links.publish_ddl(s, p))
            got = raw.execute(f"SELECT row_a, row_b, rule, grade FROM {p}.links").fetchall()
            assert got and all(a.encode() < b.encode() for a, b, *_ in got)
            assert {(a, b) for a, b, r, _ in got if r == "full-name@1"} == {("x:A", "x:B"), ("x:A", "x:a"), ("x:Hawke's", "x:hawkes")}
            near = {(a, b) for a, b, r, _ in got if r == "name-only@1"}
            assert ("x:A", "x:b") in near                          # the jane doe component, by its smallest ref, to the row without a middle name
            assert ("x:a b", "x:a c") in near and ("x:a b", "x:a-b") in near and ("x:a b", "x:ab") not in near   # x:ab joins x:a c by the decision
            groups = dict(raw.execute(f"SELECT row_key, group_id FROM {p}.groups").fetchall())
            members: dict = {}
            for r, g in groups.items():
                members.setdefault(g, []).append(r)
            assert {g: sorted(rs) for g, rs in members.items()} == {"x:A": ["x:A", "x:B", "x:a"], "x:Hawke's": ["x:Hawke's", "x:hawkes"],
                                                                     "x:a c": ["x:a c", "x:ab"]}
            assert all(g == min(rs) for g, rs in members.items())   # the group id is the smallest row key, in Python's order
            sql_min = dict(raw.execute(f'SELECT group_id, min(row_key COLLATE "C") FROM {p}.groups GROUP BY 1').fetchall())
            assert all(g == m for g, m in sql_min.items())          # and in SQL's
            assert all(r["ok"] for r in check.check_published(raw, s, p))
        finally:
            raw.rollback()
