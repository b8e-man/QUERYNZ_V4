"""The reading on ACC's real file (sample.list), its recognition refusing other shapes, the check green on the real
rows and red on each planted fault, the view free of contact columns, and the position against what it cites.
Reads the document store and the sample database; skips where either is absent. No model, no network."""
import io
import os
import re
import zipfile

import pytest

import support.fetchgate as fg
from support import db, sample
from support.docstore.landing import path_for, read_bytes
from support.lane import check_folder
from registers.contract_disclosures import check, load, read, workbook
from registers.contract_disclosures import sample as S

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(LANE))
NAME = "agency-contract-disclosures.md"
ITEMS = sample.read_list(os.path.join(LANE, "sample.list"))
ACC = next(i.split()[-1] for i in ITEMS if i.startswith("key: data "))
SCHEMA = "scratch_test_contract_disclosures"


def _store_or_skip():
    if not os.path.exists(path_for(ACC)):
        pytest.skip("no document store here")


def _db_or_skip():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here")


def _position():
    for p in (os.path.join(LANE, "position", NAME), os.path.join(REPO, "docs", "legal", "positions", NAME)):
        if os.path.exists(p):
            return p
    raise AssertionError(f"{NAME} is on file nowhere")


def test_the_lane_folder_has_the_shape():
    assert check_folder(LANE) == []


def test_the_real_file_reads_to_every_cell_with_its_levels():
    _store_or_skip()
    r = read.read(ACC, read_bytes(ACC))
    assert len(r.rows) == 80860 and not r.set_aside
    levels = {}
    for row in r.rows:
        levels[row["level"]] = levels.get(row["level"], 0) + 1
    assert levels == {"region": 180, "territorial authority": 810, "class": 79860, "total": 10}
    assert {row["financial_year"] for row in r.rows} == {str(y) for y in range(2013, 2023)}
    assert r.meta["reference"] == "AR-3944" and r.meta["classes"] == 158
    sup = [row for row in r.rows if row["active_claims_as_published"] == "<4"]
    assert sup and all(row["active_claims"] is None and row["suppressed"] for row in sup)
    assert all(row["territorial_authority"] and row["region"] for row in r.rows if row["level"] == "class")


def _rezip(data: bytes, edit) -> bytes:
    zin, out = zipfile.ZipFile(io.BytesIO(data)), io.BytesIO()
    with zipfile.ZipFile(out, "w") as zo:
        for n in zin.namelist():
            b = zin.read(n)
            zo.writestr(n, edit(n, b))
    return out.getvalue()


def test_a_file_of_another_shape_is_refused_before_anything_is_read():
    _store_or_skip()
    data = read_bytes(ACC)
    with pytest.raises(read.NotTheShape):
        read.recognise(b"not a workbook")
    with pytest.raises(read.NotTheShape):     # the heads say something else
        read.recognise(_rezip(data, lambda n, b: b.replace(b"Total Costs", b"Total Paid") if "sharedStrings" in n else b))
    with pytest.raises(read.NotTheShape):     # another title
        read.recognise(_rezip(data, lambda n, b: b.replace(b"Health Contract Data", b"Health Purchase Data")
                              if "sharedStrings" in n else b))


def test_serial_dates_are_read_only_in_their_range():
    assert str(workbook.serial_date("45011")) == "2023-03-26" and workbook.serial_date("2013") is None


def _filled(conn):
    load.build(conn, SCHEMA, S.files_of(ITEMS), shared=True)


def test_the_check_reconciles_the_real_rows_and_goes_red_on_a_cent_planted_wrong():
    """The fast tier's half: green on the real rows, red on one class cost five cents out."""
    _store_or_skip()
    _db_or_skip()
    T = f"{SCHEMA}.contract_disclosures_costs"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        try:
            _filled(conn)
            assert check.reading(conn, SCHEMA, {ACC: "x"}, shared=True) == []
            conn.execute(f"UPDATE {T} SET total_costs_nzd = total_costs_nzd + 0.05 WHERE level = 'class' "
                         "AND territorial_authority = 'Christchurch City' AND financial_year = '2022' "
                         "AND contract_class = (SELECT contract_class FROM " + T + " WHERE level = 'class' AND "
                         "territorial_authority = 'Christchurch City' AND financial_year = '2022' AND "
                         "total_costs_nzd > 0 ORDER BY contract_class LIMIT 1)")
            wrong = check.reading(conn, SCHEMA, {ACC: "x"}, shared=True)
            assert wrong and "territorial authority figures are not the sum" in wrong[0], wrong
        finally:
            conn.rollback()


@pytest.mark.slow
def test_the_check_reconciles_the_real_rows_and_goes_red_on_each_planted_fault():
    _store_or_skip()
    _db_or_skip()
    T = f"{SCHEMA}.contract_disclosures_costs"
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        try:
            _filled(conn)
            assert check.reading(conn, SCHEMA, {ACC: "x"}, shared=True) == []
            s = check.sums(conn, SCHEMA, shared=True)
            assert sum(v[0] for v in s.values()) >= check.MIN_COMPARED and all(v[2] == 0 for v in s.values())
            # a class row in an authority-year whose every class prints the figure planted wrong (a fault behind
            # a suppressed part cannot be seen, by design: the sum is skipped, not guessed)
            def whole(col):
                return (f"SELECT k.key FROM {T} k WHERE k.level = 'class' AND k.{col} > 0 AND NOT EXISTS ("
                        f"SELECT 1 FROM {T} o WHERE o.level = 'class' AND o.region = k.region AND o.territorial_authority"
                        f" = k.territorial_authority AND o.financial_year = k.financial_year AND o.{col} IS NULL)"
                        " ORDER BY k.key LIMIT 1")
            # every authority-year suppresses some class's claims ("<4"), so class claims are never summable:
            # claims are held at the region and total levels, class costs in the authority-years printed whole
            costs = whole("total_costs_nzd")
            assert conn.execute(whole("active_claims")).fetchone() is None and conn.execute(costs).fetchone()
            ta = (f"SELECT key FROM {T} WHERE level = 'territorial authority' AND region = 'Otago' "
                  "AND financial_year = '2019' ORDER BY key LIMIT 1")
            faults = (
                # a class's cost read five cents wrong
                f"UPDATE {T} SET total_costs_nzd = total_costs_nzd + 0.05 WHERE key = ({costs})",
                # an authority's claims read one wrong
                f"UPDATE {T} SET active_claims = active_claims + 1 WHERE key = ({ta})",
                # a class row lost
                f"DELETE FROM {T} WHERE key = ({costs})",
                # a class filed under another authority
                f"UPDATE {T} SET territorial_authority = 'Clutha District' WHERE key = ({costs})",
                # a region's claims doubled
                f"UPDATE {T} SET active_claims = active_claims * 2 WHERE level = 'region' AND region = 'Otago' "
                "AND financial_year = '2016'",
                # a year dropped from one row
                f"DELETE FROM {T} WHERE key = (SELECT key FROM {T} WHERE level = 'total' ORDER BY key LIMIT 1)",
            )
            for f in faults:
                conn.execute("SAVEPOINT m")
                conn.execute(f)
                assert check.reading(conn, SCHEMA, {ACC: "x"}, shared=True), f"not caught: {f[:80]}"
                conn.execute("ROLLBACK TO SAVEPOINT m")
            conn.execute(f"DELETE FROM {SCHEMA}.contract_disclosures_read_files")
            assert any("listed and was not read" in p for p in check.reading(conn, SCHEMA, {ACC: "x"}, shared=True))
        finally:
            conn.rollback()


def test_a_check_that_compares_too_little_is_red():
    _store_or_skip()
    _db_or_skip()
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        try:
            _filled(conn)
            conn.execute(f"UPDATE {SCHEMA}.contract_disclosures_costs SET total_costs_nzd = NULL, active_claims = NULL "
                         "WHERE level <> 'class'")
            assert any("printed totals compared" in p for p in check.reading(conn, SCHEMA, shared=True))
        finally:
            conn.rollback()


def test_the_view_carries_no_contact_column_and_its_columns_are_the_table_s():
    sqltext = open(os.path.join(LANE, "publish.sql"), encoding="utf-8").read()
    cols = re.search(r"SELECT (.*?)\nFROM", sqltext, re.S).group(1)
    assert tuple(c.strip() for c in cols.replace("\n", " ").split(",")) == check.VIEW_COLUMNS == load.COLUMNS["costs"]
    assert not any(b in c for c in check.VIEW_COLUMNS for b in check.BARRED)


QUOTES = {
    "ad5219f9": '"license_id": "CC-BY-NZ-3.0"',
    "eef2490b": "SUITABLE FOR EXTERNAL USE.",
    "139f0d22": '"license_id": ""',
}


def test_the_position_names_the_catalogue_and_its_citations_are_held_and_say_what_it_quotes():
    pos = fg.positions(os.path.dirname(_position()))
    assert pos["www.acc.co.nz".split(".", 1)[1]] == NAME[:-3]
    _store_or_skip()
    body = open(_position(), encoding="utf-8").read()
    cited = re.findall(r"`([0-9a-f]{8})…`", body)
    assert sorted(cited) == sorted(QUOTES)
    held = [i.split()[-1] for i in ITEMS]
    for p, q in QUOTES.items():
        h = next(h for h in held if h.startswith(p))
        raw = read_bytes(h)
        text = (" ".join(c for _, cells in workbook.sheets(raw)[0][1] for c in cells.values())
                if raw[:2] == b"PK" else raw.decode("utf-8"))
        assert q in text, f"{p}… does not say {q!r}"
    notes = " ".join(c for _, cells in workbook.sheets(read_bytes(ACC))[0][1] for c in cells.values())
    assert "Cell suppression of claim counts fewer than 4 show as “<4” to ensure client privacy" in notes
    assert "Cell suppression of claim counts fewer than 4 show as “<4” to ensure client privacy" in " ".join(body.split())
