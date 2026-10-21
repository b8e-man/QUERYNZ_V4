"""The reading's rules on list pages shaped like the Board's (every name
invented), a mutant check of those rules, the register's hold, the capture's
politeness on a fake transport, and the filled sample (real pages,
sample.list) against the row contract, the ledger, suppression, the window
and the views. No model is called and nothing is fetched."""
import datetime as dt
import os
import re
import types

import pytest

from support import db, rowcontract, sample
from registers.building_practitioners import capture, check, load, read
from registers.building_practitioners import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHA = "f" * 64
SAMPLE_SCHEMA = "scratch_test_building_practitioners"


def _item(title, number="CB10001", lbp="BP100001", region="Omitted", classes=("Carpentry,", "Site 1"),
          date="23 September 2026", penalties=("318(1)d Censure",), grounds=("317(1) b Negligent or incompetent work",),
          summary="The Board makes orders under section 318.", slug="invented-practitioner-2026-bpb-10001-final-decision"):
    v = lambda term, vals: ('<li class="process-item"><span class="process-term">' + term + ': </span>'
                            + "".join(f'<span class="process-value">{x}</span>' for x in vals) + "</li>")
    return ('<article class="listing-item processlist-item" id="x"><div class="process">'
            f'<a class="process-link" href="/complaints-and-past-decisions/past-complaint-decisions/{slug}/">\n'
            f'<h3 class="process-title">{title}</h3><ul class="process-details">'
            + v("Complaint number", [number]) + v("LBP number", [lbp]) + v("Region", [region])
            + v("Licence class", classes) + v("Decision date", [date]) + v("Penalty", penalties)
            + v("Disciplinary grounds", grounds)
            + '<li class="process-item process-item--fullwidth"><span class="process-term">Summary: </span>'
              f'<span class="process-value process-value--long">{summary}</span></li></ul>'
            f'<a class="process-pdf" href="/assets/lbp/documents/complaints/{slug}.pdf">PDF</a></div></article>')


def _page(items, total=None):
    head = (f'<h2 class="listing-resultstitle">Displaying <span class="js-listing-numshowing">{len(items)}</span> of '
            f'{total or len(items)} results</h2>')
    return ("<html><body>" + head + "".join(items) + "</body></html>").encode()


def _std():
    return _page([
        _item("Invented Practitioner [2026] BPB 10001 – final decision"),
        _item("[OMITTED] [2026] BPB 10002 – not upheld decision", number="CB10002", lbp="[OMITTED]",
              grounds=("317(1) b Negligent or incompetent work - not upheld",), penalties=("No action taken",),
              slug="omitted-2026-bpb-10002-not-upheld-decision"),
        _item("Second Invented [2025] BPB CB10003", number="CB10003", region="Auckland",
              summary="The Respondent's name must not be published.", slug="second-invented-2025-bpb-10003"),
        _item("Third Invented [2025] BPB 10004 – penalty decision", number="CB10004", date="5 May 2025"),
        _item("Third Invented [2025] BPB 10004 – Reissue", number="CB10004", date="6 May 2025"),
        _item("Not a decision title at all", number="CB10005"),
        _item("[OMITTED] [2026] BPB 10006 – final decision", number="CB10006", slug="omitted-2026-bpb-10006"),
    ], total=1600)


def rules(mod) -> list:
    broken = []
    out = mod.read_page(_std(), SHA, 1)
    rows = {r["complaint_number"] + "/" + r["decision_kind"].lower(): r for r in out["rows"]}
    if out["stated"] != (7, 1600):
        broken.append("the page's own stated total is read")
    if len(out["rows"]) != 6 or len(out["set_aside"]) != 1:
        broken.append("every item a row or a catch-log line")
    a = rows.get("CB10001/final decision")
    if not (a and a["name"] == "Invented Practitioner" and a["lbp_number"] == "BP100001" and not a["suppressed"]):
        broken.append("an open decision keeps its name and number")
    if a and (a["licence_classes"] != ["Carpentry", "Site 1"] or a["region"] is not None or a["upheld"] is not True):
        broken.append("classes clean, 'Omitted' region empty, a ground upheld")
    o = rows.get("CB10002/not upheld decision")
    if not (o and o["suppressed"] and o["name"] is None and o["lbp_number"] is None and o["upheld"] is False):
        broken.append("[OMITTED] withholds the name and number; not upheld is not upheld")
    s = rows.get("CB10003/decision")
    if not (s and s["suppressed"] and s["name"] is None and s["region"] == "Auckland"):
        broken.append("a suppression direction in the summary withholds the name")
    w = rows.get("CB10006/final decision")
    if not (w and w["suppressed"] and w["name"] is None and w["lbp_number"] is None):
        broken.append("an [OMITTED] name withholds the number too")
    if any("invented" in r["key"].lower() or "omitted" in r["key"].lower() for r in out["rows"]):
        broken.append("a key never carries the practitioner's name")
    if len({r["key"] for r in out["rows"]}) != 6:
        broken.append("two decisions of one complaint are two rows")
    if not all(r["decided_on"] for r in out["rows"]) or rows.get("CB10004/penalty decision", {}).get("decided_on") != dt.date(2025, 5, 5):
        broken.append("decision dates are days")
    if any("summary" in k for r in out["rows"] for k in r):
        broken.append("the summary is never kept")
    bad = mod.read_page(_page([_item("Invented [2026] BPB 1")]).replace(b"Displaying", b"Showing"), SHA, 1)
    if bad["rows"] or len(bad["set_aside"]) != 1:
        broken.append("a page that is not the shape is set aside whole")
    short = _page([_item("Invented [2026] BPB 1 – final decision")]).replace(b'numshowing">1<', b'numshowing">2<')
    if mod.read_page(short, SHA, 1)["rows"]:
        broken.append("a page whose heading count differs from its items is set aside whole")
    return broken


def test_every_rule_holds():
    assert rules(read) == []


MUTANTS = {
    "the summary's suppression ignored": ("or SUPPRESSION.search(summary)", "or False"),
    "[OMITTED] kept as a name": ('suppressed = bool((name and OMITTED.search(name))', 'suppressed = bool((False)'),
    "the name withheld only on the view": ('"name": None if suppressed else name', '"name": name'),
    "the key from the decision's address": ('"key": f"{KEY_PREFIX}/{number}/{kind_slug(kind)}"',
                                            '"key": f"{KEY_PREFIX}/{href}"'),
    "the key without the kind": ('"key": f"{KEY_PREFIX}/{number}/{kind_slug(kind)}"', '"key": f"{KEY_PREFIX}/{number}"'),
    "the prefixed number not read": (r"BPB\s*(?:[A-Z]{1,3})?(?P<number>\d+)", r"BPB\s*(?P<number>\d+)"),
    "upheld from the first ground": ('any(not g.lower().endswith("not upheld") for g in grounds)', 'True'),
    "any page read": ('    if len(items) != shown:\n', '    if False:\n'),
}


def _mutant(old, new):
    src = open(read.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant's anchor is not in read.py once: {old}"
    mod = types.ModuleType("read_mutant")
    mod.__file__ = read.__file__
    exec(compile(src.replace(old, new), read.__file__, "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name):
    try:
        broken = rules(_mutant(*MUTANTS[name]))
    except (KeyError, TypeError, AttributeError, ValueError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


def test_the_register_is_held_and_asks_nothing(tmp_path):
    (tmp_path / "building-practitioners-register.md").write_text("hosts: lbp.govt.nz, mbie.govt.nz\n")
    with pytest.raises(capture.Held):
        capture.register(str(tmp_path))
    (tmp_path / "building-practitioners-register.md").write_text(
        "hosts: lbp.govt.nz, mbie.govt.nz\nauthorised: register 2026-11-01 Arthur's ruling\n")
    with pytest.raises(NotImplementedError):          # authorised, but no reading built until its shape is seen
        capture.register(str(tmp_path))
    real = os.path.join(LANE, "position")
    assert capture.authorisation("register", real) is None


def test_a_block_stops_the_run_and_the_pass_resumes_from_its_page():
    class T:
        def __init__(s):
            s.pages, s.asides, s.p = [], [], None

        def open_pass(s):
            return s.p

        def last_full_done(s):
            return None

        def begin(s):
            s.p = {"pass_id": 1, "next_start": 0, "pages": 0, "stated": None}
            return s.p

        def add_page(s, p, start, url, sha, n, new, stated):
            s.pages.append(start)
            p["next_start"], p["stated"] = start + 20, stated

        def add_doc(s, *a):
            pass

        def finish(s, p):
            pass

        def set_aside(s, pid, item, stage, why):
            s.asides.append(why)

    t, clock, answers = T(), [0.0], iter([200, 200, 200, 200, 403])
    page = _page([_item(f"Invented [2026] BPB {i} – final decision", number=f"CB{i}") for i in range(20)], total=100)

    def opener(url, timeout):
        clock[0] += 0.1
        st = next(answers)
        return types.SimpleNamespace(status=st, body=page if st == 200 else b"", final_url=url,
                                     blocked="HTTP 403" if st == 403 else "")

    run = capture.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256="a" * 64), True), opener=opener,
                      clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                      now=lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ))
    out = run.run()
    assert out["stopped"].startswith("stopped:") and t.asides == ["HTTP 403"]
    assert t.pages == [0] and t.p["next_start"] == 20          # three documents, one page, then the block
    assert clock[0] >= 4 * capture.FLOOR_S


# ── the filled sample: real pages ─────────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


def _rows(conn, q):
    cur = conn.execute(q)
    cols = [d.name for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


@pytest.fixture(scope="module")
def filled():
    _db_or_skip()
    items = sample.read_list(os.path.join(LANE, "sample.list"))
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        conn.execute(f"CREATE SCHEMA IF NOT EXISTS {SAMPLE_SCHEMA}")
        S.fill(conn, SAMPLE_SCHEMA, items)
        conn.execute(load.sql("publish.sql", SAMPLE_SCHEMA, True).replace("pub.", f"{SAMPLE_SCHEMA}.v_"))
        conn.commit()
        T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
        yield {"conn": conn, **{t: _rows(conn, f"SELECT * FROM {T(t)}") for t in load.TABLES},
               "view": _rows(conn, f"SELECT * FROM {SAMPLE_SCHEMA}.v_building_practitioner_decisions")}


def test_every_item_of_every_page_is_a_decision(filled):
    assert len(filled["decisions"]) == 80 and not filled["read_set_aside"]
    assert all(p["items"] == p["typed"] + p["superseded"] + p["set_aside"] and p["stated"] == 1600
               for p in filled["read_pages"])


def test_every_row_meets_the_row_contract(filled):
    for r in filled["decisions"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]


def test_the_hard_cases_read_as_the_list_says(filled):
    by = {r["key"]: r for r in filled["decisions"]}
    om = by["building_practitioners/decision/CB26816/not-upheld"]
    assert om["suppressed"] and om["name"] is None and om["upheld"] is False
    assert "building_practitioners/decision/CB26862/decision" in by
    assert {"building_practitioners/decision/CB26758/penalty", "building_practitioners/decision/CB26758/reissue"} <= set(by)
    assert any(r["citation"] == "[2025] BPB 26720" for r in filled["decisions"])
    assert not any("," in c for r in filled["decisions"] for c in r["licence_classes"])


def test_the_view_withholds_and_keeps_to_the_window(filled):
    sup = [r for r in filled["view"] if r["suppressed"]]
    assert sup and all(r["name"] == "name withheld by the Board" and r["lbp_number"] is None and r["decision_url"] is None
                       and r["pdf_url"] is None for r in sup)
    cutoff = dt.date.today() - dt.timedelta(days=3 * 366)
    assert all(r["decided_on"] >= cutoff for r in filled["view"])
    assert check.views(filled["conn"], f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(filled["conn"], SAMPLE_SCHEMA, shared=True) == []


def test_the_check_goes_red_on_a_name_shown_or_a_broken_ledger(filled):
    conn = filled["conn"]
    T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
    conn.execute(f"UPDATE {T('read_pages')} SET typed = typed + 1 WHERE document = (SELECT min(document) FROM {T('read_pages')})")
    try:
        assert check.reading(conn, SAMPLE_SCHEMA, shared=True) != []
    finally:
        conn.rollback()
    v = load.sql("publish.sql", SAMPLE_SCHEMA, True).replace("pub.", f"{SAMPLE_SCHEMA}.v_")
    conn.execute(v.replace("CASE WHEN d.suppressed THEN NULL ELSE d.decision_url END", "d.decision_url"))
    try:
        assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") != []
    finally:
        conn.rollback()
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []
