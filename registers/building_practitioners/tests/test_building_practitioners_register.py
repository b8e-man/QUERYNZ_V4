"""The register of practitioners (ruling 132): its two readers on pages shaped
like the register's (every name, number and id invented), a mutant check of
those rules, the run's politeness and cache on a fake transport, and the
filled sample (real pages, sample.list `key: reglist` and `key: regdetail`)
against the ledger, the row contract and the views. No model is called and
nothing is fetched."""
import datetime as dt
import os
import types

import pytest

from support import db, rowcontract, sample
from registers.building_practitioners import capture, check, load, register as R
from registers.building_practitioners import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_SCHEMA = "scratch_test_building_practitioners_register"
G1, G2, G3 = ("0000000a-0000-0000-0000-000000000001", "0000000a-0000-0000-0000-000000000002",
              "0000000a-0000-0000-0000-000000000003")


def _list(rows, field="lclass", value="Site", extra_tr=""):
    opts = lambda name, vals, sel: (f'<select name="{name}" class="form-control" id="{name}" value=""><option value="">'
                                    + "".join(f'<option {"selected " if v == sel else ""}value="{v}">{v}' for v in vals)
                                    + "</select>")
    body = "".join(f'<tr> <td> <a href="/practitioner/?id={g}">{n}</a> </td> <td> {t} </td> <td> {r} </td> '
                   f'<td> Yes </td> </tr>' for g, n, t, r in rows)
    return ('<html><form method=GET action="/advanced-building-practitioner-search/">'
            + opts("lclass", R.CLASSES, value if field == "lclass" else None)
            + opts("aop", list(R.AREAS), value if field == "aop" else None)
            + '</form><table class="public-register"><tbody><tr><th>For this type of</th><th>Search</th></tr></tbody></table>'
            '<table id="data" aria-live="polite" role="grid" class="table table-striped table-fluid"><thead><tr>'
            '<th class="sort-enabled">Full Name</th><th>Town/City</th><th>Region</th><th>Licensed?</th></tr></thead>'
            f'<tbody style="">{body}{extra_tr}</tbody></table></html>').encode()


def _detail(guid=G1, number="BP100001", first="Invented", middle="", last="Builder",
            granted="2012-03-14T11:00:00.0000000Z", region="Invented Region", town="Inventedtown"):
    inp = lambda i, v: f'<input name="x${i}" type="text" value="{v}" maxlength="100" id="{i}" class="text form-control" readonly />'
    return ('<html><h3>Practitioner Details</h3>'
            f'<input type="hidden" name="EntityID" id="EntityFormControl_1_EntityFormView_EntityID" value="{guid}" />'
            + inp("firstname", first) + inp("middlename", middle) + inp("lastname", last)
            + inp("olp_practitionerid", number) + inp("olp_datefirstgranted", granted)
            + inp("olp_address1_regionalcouncil", region) + inp("address1_city", town)
            + inp("address1_postalcode", "9999") + inp("olp_primaryemailpr", "invented@example.invalid")
            + inp("olp_mobilenumberpr", "000 000 0000") + '<h3>Contact Information</h3></html>').encode()


def rules(mod) -> list:
    broken = []
    out, why = mod.read_list(_list([(G1, "Invented Builder", "Inventedtown", "Invented Region"),
                                    (G2, "Second Invented", "12 Invented Street", "")]))
    if not out or out["query"] != ("lclass", "Site") or len(out["rows"]) != 2:
        broken.append("a search page's rows and its one criterion are read")
    if out and any("name" in r for r in out["rows"]):
        broken.append("the listed name is not kept")
    bad, _ = mod.read_list(_list([(G1, "A", "B", "C")], extra_tr="<tr><td>a row not of the shape</td></tr>"))
    if bad is not None:
        broken.append("a table with a row not read is refused whole")
    other, _ = mod.read_list(_list([(G1, "A", "B", "C")]).replace(b"<th>Licensed?</th>", b"<th>Status</th>"))
    if other is not None:
        broken.append("a page without the four headings is refused")
    d, why = mod.read_detail(_detail())
    if not d or d["number"] != "BP100001" or d["first_granted"] != dt.date(2012, 3, 15) or d["guid"] != G1:
        broken.append("a practitioner's page gives the number, the New Zealand day first granted and the id")
    if d and set(d) != {"guid", "number", "first", "middle", "last", "first_granted", "region", "town"}:
        broken.append("the postcode, email and telephones are never read")
    if mod.read_detail(_detail(number="not a number"))[0] is not None:
        broken.append("a page with no number of the register's shape is set aside")
    if mod.read_detail(_detail().replace(b"Practitioner Details", b"Sign in"))[0] is not None:
        broken.append("a page without its section is set aside")
    if not mod.names_address("12 Invented Street") or not mod.names_address("R.D. 2 Inventedtown") \
            or mod.names_address("Inventedtown") or mod.names_address("9999") or mod.names_address("Stratford"):
        broken.append("a town is flagged by an address's shape, a postcode or a plain town never")
    cl = mod.classes_of({("lclass", "Site"): [{"guid": G1}], ("aop", "Site 2"): [{"guid": G1}],
                         ("aop", "Veneer"): [{"guid": G2}]})
    if cl.get(G1) != [{"class": "Site", "areas": ["Site 2"]}] or cl.get(G2) != [{"class": "Bricklaying and Blocklaying",
                                                                                  "areas": ["Veneer"]}]:
        broken.append("an area of practice names its class")
    now = dt.datetime(2026, 11, 3, 1, tzinfo=R.NZ)
    if mod.due({G1, G2, G3}, {G2: now - dt.timedelta(days=100), G3: now - dt.timedelta(days=5)}, now) != [G1, G2]:
        broken.append("never fetched first, then the stale; a fresh page is not asked again")
    return broken


def test_every_rule_holds():
    assert rules(R) == []


MUTANTS = {
    "a row miscounted": ("if tb.group(1).count(\"<tr\") != len(rows):", "if False:"),
    "the UTC day kept": ("return t.astimezone(NZ).date()", "return t.date()"),
    "any number": ('if not out["number"] or not _NUMBER.fullmatch', 'if not out["number"] or not bool'),
    "no refresh": ("now - fetched[g] >= dt.timedelta(days=REFRESH_DAYS)", "True"),
    "rural delivery unflagged": (r"|\bR\.?\s?D\.?\s*\d", ""),
    "an area's class lost": ('cls = value if field == "lclass" else AREAS.get(value)', "cls = value"),
}


def _mutant(old, new):
    src = open(R.__file__, encoding="utf-8").read()
    assert src.count(old) == 1, f"the mutant's anchor is not in register.py once: {old}"
    mod = types.ModuleType("register_mutant")
    mod.__file__ = R.__file__
    exec(compile(src.replace(old, new), R.__file__, "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_each_mutant_is_caught(name):
    try:
        broken = rules(_mutant(*MUTANTS[name]))
    except (KeyError, TypeError, AttributeError, ValueError):
        broken = ["crashed"]
    assert broken, f"the mutant '{name}' passes every rule"


# ── the run, on a fake transport ──────────────────────────────────────────────

class RegTables:
    def __init__(s, store=None):
        s.p, s.lists, s.details, s.asides, s.done, s.store = None, [], {}, [], None, store or {}

    def reg_open_pass(s):
        return s.p

    def reg_last_done(s):
        return s.done

    def reg_begin(s):
        s.p = {"pass_id": 1, "next_query": 0}
        return s.p

    def reg_add_list(s, p, n, field, value, url, sha, rows, new):
        s.lists.append((sha, field, value))
        p["next_query"] = n + 1

    def reg_finish(s, p):
        s.p, s.done = None, dt.datetime(2026, 11, 2, 23, tzinfo=R.NZ)

    def reg_lists(s):
        return s.lists

    def reg_fetched(s):
        return {g: t for g, t in s.details.items()}

    def reg_add_detail(s, guid, url, sha, new, fetched_at=None):
        s.details[guid] = fetched_at or dt.datetime(2026, 11, 2, 23, tzinfo=R.NZ)

    def reg_adopt(s, guid, url):
        if url in s.store:
            s.reg_add_detail(guid, url, s.store[url], False)
            return True
        return False

    def set_aside(s, pid, item, stage, why):
        s.asides.append(why)


def _run(t, answer, bodies, clock):
    def opener(url, timeout):
        clock[0] += 0.1
        st = answer(url)
        return types.SimpleNamespace(status=st, body=bodies.get(url, b"") if st == 200 else b"<html>error</html>",
                                     final_url=url, location="", headers={},
                                     blocked="" if st == 200 else f"HTTP {st}: a block or a challenge")
    return R.Run(t, land_fn=lambda d, **k: (types.SimpleNamespace(sha256=k["name"]), True), opener=opener,
                 clock=lambda: clock[0], sleep=lambda s: clock.__setitem__(0, clock[0] + s),
                 now=lambda: dt.datetime(2026, 11, 2, 23, tzinfo=R.NZ),
                 read_bytes=lambda sha: bodies[sha])


def _bodies():
    b = {R.search_url(f, v): _list([(G1, "A", "B", "C"), (G2, "D", "E", "F")] if (f, v) == ("lclass", "Site") else [],
                                   field=f, value=v) for f, v in R.QUERIES}
    b[R.detail_url(G1)] = _detail(G1, "BP100001")
    b[R.detail_url(G2)] = _detail(G2, "BP100002")
    return b


def test_a_pass_asks_each_search_once_then_each_page_once_slowly():
    t, clock, bodies, asked = RegTables(), [0.0], _bodies(), []
    out = _run(t, lambda u: asked.append(u) or 200, bodies, clock).run()
    assert out["stopped"] == "" and out["searches"] == len(R.QUERIES) and out["details"] == 2
    assert len(asked) == len(set(asked)) == len(R.QUERIES) + 2
    assert clock[0] >= (len(asked) - 1) * capture.FLOOR_S
    again = []
    _run(t, lambda u: again.append(u) or 200, bodies, [0.0]).run()       # the next night: searches weekly, pages fresh
    assert again == []


def test_a_block_stops_and_a_server_error_is_set_aside():
    t, bodies = RegTables(), _bodies()
    out = _run(t, lambda u: 403 if "Carpentry" in u else 200, bodies, [0.0]).run()
    assert out["stopped"].startswith("stopped:") and t.p["next_query"] == 1 and not t.details
    t2 = RegTables()
    out = _run(t2, lambda u: 503 if u == R.detail_url(G1) else 200, bodies, [0.0]).run()
    assert out["stopped"] == "" and list(t2.details) == [G2] and any("server's own error" in a for a in t2.asides)


def test_a_page_the_store_holds_is_adopted_not_fetched():
    t, bodies, asked = RegTables(store={R.detail_url(G1): "held-sha"}), _bodies(), []
    out = _run(t, lambda u: asked.append(u) or 200, bodies, [0.0]).run()
    assert out["adopted"] == 1 and R.detail_url(G1) not in asked and set(t.details) == {G1, G2}


def test_the_reading_accounts_for_every_page_and_listed_practitioner():
    bodies = {"l1": _list([(G1, "A", "B", "C"), (G2, "D", "E", "F"), (G3, "G", "H", "I")]),
              "d1": _detail(G1, "BP100001", town="12 Invented Street"), "d2": _detail(G2, "BP100001"),
              "d3": b"<html>not a page</html>"}
    out = load.read_register({"pass_id": 1, "lists": ["l1"], "details": ["d1", "d2", "d3"]}, bodies.get,
                             {R.PROFILE_LIST: 1, R.PROFILE_DETAIL: 1})
    led = out["ledger"]
    assert led["pages"] == led["typed"] + led["set_aside"] == 3 and led["typed"] == 1
    assert led["listed"] == 3 and led["awaiting"] == 1                      # G3: listed, its page not yet fetched
    (r,) = out["rows"]
    assert r["area_names_address"] is True and r["status"] == "licensed" and r["key"] == "building_practitioners/lbp/BP100001"


# ── the filled sample: real pages ─────────────────────────────────────────────

def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")


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
        cur = conn.execute(f"SELECT * FROM {T('practitioners')}")
        cols = [d.name for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        led = conn.execute(f"SELECT searches, listed, pages, typed, set_aside, awaiting FROM {T('read_register')}").fetchone()
        yield {"conn": conn, "rows": rows, "ledger": led, "regdetails": sum(1 for i in items if i.startswith("key: regdetail "))}


def test_every_sampled_page_is_a_practitioner(filled):
    searches, listed, pages, typed, aside, awaiting = filled["ledger"]
    assert searches == 1 and listed > 1000 and pages == filled["regdetails"] == typed and aside == 0
    assert awaiting == listed - typed


def test_every_practitioner_row_meets_the_row_contract_and_is_listed(filled):
    for r in filled["rows"]:
        assert rowcontract.validate({**r, "loaded_at": r["loaded_at"].isoformat()}) == [], r["key"]
        assert r["status"] == "licensed" and r["licence_classes"] and r["first_granted_on"] and r["licence_number"].startswith("BP")


def test_the_register_view_carries_no_address_column_and_the_check_holds(filled):
    conn = filled["conn"]
    assert check.views(conn, f"{SAMPLE_SCHEMA}.v_") == []
    assert check.reading(conn, SAMPLE_SCHEMA, shared=True) == []
    T = lambda t: load.table(SAMPLE_SCHEMA, t, True)
    conn.execute(f"UPDATE {T('practitioners')} SET area = '12 Invented Street', area_names_address = false "
                 f"WHERE key = (SELECT min(key) FROM {T('practitioners')})")
    try:
        assert any("without their flag" in p for p in check.reading(conn, SAMPLE_SCHEMA, shared=True))
    finally:
        conn.rollback()
