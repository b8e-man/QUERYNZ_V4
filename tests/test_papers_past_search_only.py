"""Hard limit 17 as a test (step 7.1; step 8.6, 2 November 2026): Papers Past is searched, not mined. No people, claims or
links are built from it, and its name index never feeds the links. In the old estate only a status value kept it out of
extraction; here the rule is code: nothing in links/ reads it, no names job takes it, the lane publishes no name, person or
claim, and the live pub.names and pub.links hold no row of it."""
import os
import re
import tomllib

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANE = os.path.join(REPO, "registers", "papers_past")
MARK = re.compile(r"papers[_-]?past|paperspast", re.I)


def _files(root, exts=(".py", ".sql", ".toml")):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "tests")]
        for f in files:
            if f.endswith(exts):
                yield os.path.join(dirpath, f)


def test_nothing_in_links_reads_papers_past():
    hits = [os.path.relpath(p, REPO) for p in _files(os.path.join(REPO, "links")) if MARK.search(open(p, encoding="utf-8").read())]
    assert hits == [], f"links/ names Papers Past: {hits}"
    from links import rows, sightings
    assert not any(MARK.search(reg) or MARK.search(view) or MARK.search(sql) for reg, view, sql in rows.SOURCES)
    assert not any(MARK.search(l) for l in sightings.LANES), "the sightings pass never scans Papers Past"


def test_no_job_feeds_its_names_or_links():
    jobs = tomllib.load(open(os.path.join(REPO, "support", "scheduler", "jobs.toml"), "rb"))["jobs"]
    bad = []
    for name, j in jobs.items():
        cmd = " ".join(j.get("command") or [])
        feeds = name.startswith("qv4-names-") or name.startswith("qv4-links") or "links." in cmd or "sightings" in name
        if feeds and (MARK.search(name) or MARK.search(cmd)):
            bad.append(name)
        if MARK.search(name) and any(t.startswith(("qv4-names-", "qv4-links")) for t in j.get("then") or []):
            bad.append(f"{name} then {j['then']}")
    assert bad == [], bad


def test_the_lane_publishes_no_person_name_or_claim():
    publish = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    views = re.findall(r"create\s+(?:or\s+replace\s+)?view\s+([a-z_]+)\.([a-z_]+)", publish, re.I)
    assert views and all(s == "pub" and v.startswith("papers_past_") for s, v in views), views
    assert not re.search(r"\bpub\.(names|links|groups|entities)\b|\blinks\.", publish, re.I)
    for path in (os.path.join(LANE, "tables.sql"), os.path.join(LANE, "publish.sql")):
        sql = open(path, encoding="utf-8").read()
        cols = re.findall(r"^\s+([a-z_]+)\s+(?:text|integer|bigint|boolean|date|timestamptz)\b", sql, re.I | re.M)
        cols += re.findall(r"\bAS\s+([a-z_]+)", sql, re.I) + re.findall(r"\bi\.([a-z_]+)", sql)
        bad = [c for c in cols if re.search(r"name|person|people|claim|author|mention|entity", c, re.I)]
        assert bad == [], f"{os.path.basename(path)} carries {bad}"


def test_only_the_archive_product_may_read_it():
    readers = []
    for root in ("links", "products", "registers"):
        for p in _files(os.path.join(REPO, root), (".py",)):
            rel = os.path.relpath(p, REPO)
            if rel.startswith(os.path.join("registers", "papers_past")) or rel.startswith(os.path.join("products", "archive")):
                continue
            src = open(p, encoding="utf-8").read()
            if re.search(r"registers\.papers_past|pub\.papers_past|papers_past\.items", src):
                readers.append(rel)
    assert readers == [], readers


def test_the_board_shows_it_only_as_its_pane_md_says():
    """registers/papers_past/pane.md: one board pane row per article (title, paper, issue date, length, link), searched
    by title; no person, no name, no link, never joined to another register. The catalogue entry is the board's only
    hold on it, so it is held to that here: no names, no joins, no parent, no relations, nothing points at it, and it
    stays out of the all-views search."""
    from products.board import catalogue as cat
    v = cat.BY_NAME["papers_past_items"]
    assert v.names == () and v.joins == () and v.parent == () and v.relations == () and v.searched is False
    assert v.search == ("title",) and cat.fields_of(v).names == () and not cat.fields_of(v).address
    assert not any(r.view == "papers_past_items" for w in cat.VIEWS for r in w.relations)
    assert not any(j.view == "papers_past_items" for w in cat.VIEWS for j in w.joins)
    assert not any(w.parent and w.parent[1] == "papers_past_items" for w in cat.VIEWS)


@pytest.mark.slow
def test_the_live_names_and_links_hold_no_row_of_it():
    from support import db
    try:
        conn = db.connect(db.READ_KEY, "querynz_v4", connect_timeout=5)
    except Exception as exc:                                   # no database here: the static tests above still hold the rule
        pytest.skip(f"no live database: {type(exc).__name__}")
    with conn:
        conn.execute("SET statement_timeout = '60s'")
        assert conn.execute("SELECT count(*) FROM pub.names WHERE register ~* 'papers.?past' OR view ~* 'papers.?past' "
                            "OR ref ~* 'papers.?past'").fetchone()[0] == 0
        assert conn.execute("SELECT count(*) FROM pub.links WHERE row_a ~* '^papers.?past' OR row_b ~* '^papers.?past'").fetchone()[0] == 0
