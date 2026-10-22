"""The disclosures lane's tests (step 4.1). The reader's rules are tested on
small pages shaped like the Commission's (names and addresses invented); the
filled sample is tested against the row contract, the catch log, the join
to the scans and the frozen site's figures. No model is called."""
import datetime as dt
import glob
import os
import re

import pytest

from support import db, lane, rowcontract, sample
from registers.disclosures import capture, check, listing, read, reconcile

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
LANE = os.path.join(REPO, "registers", "disclosures")

HEAD = ('<tr><td>Party, date return<br>received by the<br>Commission</td><td>Name and address</td>'
        '<td>Total donation and date received by party</td></tr>')
NEW = ('<h2>Party donations exceeding $20,000 since 1 January 2026</h2><table>' + HEAD +
       '<tr><td>Example Party<br>5 October 2026<br>(amended return received 9 October 2026)</td>'
       '<td>A Donor<br>1 Invented Street<br>Sometown</td>'
       '<td>$52,000, 28 September 2026<br><a href="/assets/2026-20k+-donations/A_Donor_5_October_2026.pdf">(PDF, 130KB)</a></td></tr>'
       '<tr><td>Example Party<br>27 July 2023<br>(amended on 22 April 2024 and amendment withdrawn on 8 May 2024)</td>'
       '<td>B Donor Limited<br>2 Invented Road</td>'
       '<td>$47,052.53, 25 July 2023<br><a href="/assets/Donation-returns/2023/B-Donor-Limited_27_July_2023.jpg">(JPG, 1MB)</a></td></tr>'
       '<tr><td>Other Party<br>11 August 2023<br>(donation returned to the donor by the party on 18 August 2023)</td>'
       '<td>C Donor</td><td>$50,000, 7 August 2023 - return includes an additional $15,200 of donations</td></tr>'
       '<tr><td>Other Party<br>11 August 2023<br>(revised 15 August 2023)</td><td>D Donor</td><td>$20,000, 1 August 2023</td></tr>'
       '</table>')
OLD = ('<h2>Party donations exceeding $30,000 from 1 January 2011 to 31 December 2022</h2><table>'
       '<tr><td>Party, donation, date received by the Commission</td><td>Name and address of donor</td>'
       '<td>Amount(s) and date(s) of donations</td></tr>'
       '<tr><td>Example Party<br>$35,000<br>23 December 2021</td><td>E Donor<br>3 Invented Lane</td>'
       '<td>$20,000 on 25 May 2021<br>$10,000 on 9 December 2021<br>$5,000 on 22 December 2021</td></tr>'
       '<tr><td>Example Party<br>$350,440<br>13 December 2018, amended 2 May 2019</td><td>F Trust</td>'
       '<td>$120 received on 30 November 2017, and<br>$350,000 received on 29 November 2018.</td></tr>'
       '</table><h2>Party donations exceeding $20,000 from 2008 to 2010</h2><table>'
       '<tr><td>Example Party<br>$39,775.00<br>amended to $41,037.00*<br>7 January 2009<br>amended filed 22 April 2009*</td>'
       '<td>G Donor</td><td>$40,000.00 - 4 September 2008<br>*$1,037.00 - 7 October 2008</td></tr>'
       '<tr><td>Example Party<br>$44,496.65 - 23 June 2008<br>(return amended from<br>$44,571.65 - 16 June 2008)</td>'
       '<td>H Donor</td><td>$44,496.65 - 10 June 2008</td></tr>'
       '<tr><td>Example Party</td><td>I Donor</td><td>$1,000 on 1 May 2009</td></tr>'
       '</table>')


def _rows(html):
    return {r.donor_name: r for r in listing.read(html.encode()).rows}


def test_the_lane_folder_is_complete():
    assert lane.check_folder(LANE) == []


def test_a_new_regime_row_keeps_both_dates_and_the_link():
    r = _rows(NEW)["A Donor"]
    assert (r.amount, r.received_on, r.given_on) == (52000.0, "2026-10-05", "2026-09-28")
    assert r.href.endswith("A_Donor_5_October_2026.pdf") and r.regime == "over-20000-from-2023"
    assert r.address == ["1 Invented Street", "Sometown"]


def test_a_stray_empty_link_in_front_of_the_row_s_own_is_not_the_row_s():
    cell = ('<a href="/assets/Donation-returns/2023/Other_Union_25_August_2023.pdf"></a>'
            '<a href="/assets/Donation-returns/2023/J_Donor_Limited_4_September_2023.pdf">$23,000, 31 August 2023</a><br>(PDF, 2MB)')
    assert listing.link(cell).endswith("J_Donor_Limited_4_September_2023.pdf")
    assert listing.link('<a href="/a/x.pdf">(PDF, 1MB)</a>') == "/a/x.pdf"
    assert listing.link("$1, 1 May 2023") is None


def test_the_commission_s_amendment_statement_is_read_never_inferred():
    rows = _rows(NEW)
    assert (rows["A Donor"].amendment, rows["A Donor"].amended_on) == ("amended", "2026-10-09")
    w = rows["B Donor Limited"]
    assert (w.amendment, w.amended_on, w.withdrawn_on) == ("amendment withdrawn", "2024-04-22", "2024-05-08")
    assert rows["B Donor Limited"].href.endswith(".jpg"), "the Commission links a photograph for some declarations"
    assert rows["D Donor"].amendment == "unread", "a shape not seen before acts on nothing"
    assert rows["D Donor"].commission_note == "revised 15 August 2023"


def test_a_returned_gift_and_a_trailing_note_are_kept_verbatim():
    r = _rows(NEW)["C Donor"]
    assert r.returned_on == "2023-08-18" and r.amendment == "none"
    assert r.amount == 50000.0 and r.amount_note == "return includes an additional $15,200 of donations"


def test_an_old_regime_row_itemises_its_gifts_as_printed():
    rows = _rows(OLD)
    r = rows["E Donor"]
    assert (r.amount, r.received_on, r.given_on, r.threshold) == (35000.0, "2021-12-23", None, 30000)
    assert [(i.amount, i.first_date) for i in r.items] == [(20000.0, "2021-05-25"), (10000.0, "2021-12-09"), (5000.0, "2021-12-22")]
    s = rows["F Trust"]
    assert (s.received_on, s.amendment, s.amended_on) == ("2018-12-13", "amended", "2019-05-02")


def test_an_inline_amendment_of_2008_carries_the_amended_total_and_the_original():
    rows = _rows(OLD)
    to = rows["G Donor"]
    assert (to.amount, to.amount_original, to.received_on, to.amended_on) == (41037.0, 39775.0, "2009-01-07", "2009-04-22")
    frm = rows["H Donor"]
    assert (frm.amount, frm.amount_original, frm.received_on, frm.amended_on) == (44496.65, 44571.65, "2008-06-16", "2008-06-23")
    assert frm.regime == "over-20000-2008-2010" and frm.threshold == 20000


def test_ruling_66_itemised_gifts_within_100_reconcile_with_an_issue_and_100_or_more_do_not():
    assert reconcile.RECONCILE_TOLERANCE_CENTS == 10000
    assert read.items_check(30000.00, 30000.00, 2) == ("equal", None)
    assert read.items_check(30099.99, 30000.00, 2) == ("reconciled", "+99.99: the 2 itemised gifts against the declared amount")
    assert read.items_check(29900.01, 30000.00, 2) == ("reconciled", "-99.99: the 2 itemised gifts against the declared amount")
    assert read.items_check(30100.00, 30000.00, 2) == ("differs", None)      # exactly $100 is unreconciled
    assert read.items_check(29900.00, 30000.00, 2) == ("differs", None)
    assert read.items_check(30100.01, 30000.00, 2) == ("differs", None)
    assert read.items_check(None, 30000.00, 0) == ("no figures", None)


def _old_row(gifts: str, total: str) -> dict:
    html = ('<h2>Party donations exceeding $30,000 from 1 January 2011 to 31 December 2022</h2><table>'
            '<tr><td>Party, donation, date received by the Commission</td><td>Name and address of donor</td>'
            '<td>Amount(s) and date(s) of donations</td></tr>'
            f'<tr><td>Example Party<br>{total}<br>23 December 2021</td><td>E Donor<br>3 Invented Lane</td>'
            f'<td>{gifts}</td></tr></table>')
    return read.read_listing(html.encode(), "0" * 64, loaded_at="2026-10-21T13:00:00+13:00").rows[0]["filed"]


def test_ruling_66_through_the_listing_reader_the_printed_amount_stands():
    f = _old_row("$20,000 on 25 May 2021<br>$15,099.99 on 9 December 2021", "$35,000")
    assert (f["amount"], f["items_sum"], f["items_check"]) == (35000.0, 35099.99, "reconciled")
    assert f["issue"] == "+99.99: the 2 itemised gifts against the declared amount"
    f = _old_row("$20,000 on 25 May 2021<br>$15,100 on 9 December 2021", "$35,000")
    assert (f["amount"], f["items_check"], f["issue"]) == (35000.0, "differs", None)
    f = _old_row("$20,000 on 25 May 2021<br>$15,000 on 9 December 2021", "$35,000")
    assert (f["items_check"], f["issue"]) == ("equal", None)


def test_a_row_the_table_cannot_answer_for_is_a_catch_log_line():
    reading = listing.read(OLD.encode())
    assert "I Donor" not in {r.donor_name for r in reading.rows}
    assert [why for _, _, why in reading.skipped] == ["no declared total in the first cell"]


def test_keys_are_stable_carry_no_name_and_number_ties_oldest_first():
    one = read.read_listing((NEW + OLD).encode(), "a" * 64, loaded_at="2026-10-19T00:00:00+13:00")
    again = read.read_listing((NEW + OLD).encode(), "b" * 64, loaded_at="2026-10-20T00:00:00+13:00")
    assert [r["key"] for r in one.rows] == [r["key"] for r in again.rows]
    assert all(not re.search(r"donor|party|trust", r["key"], re.I) for r in one.rows)
    tie = NEW.replace("</table>", NEW.split(HEAD)[1].split("</table>")[0].split("</tr>")[0] + "</tr></table>")
    keys = [r["key"] for r in read.read_listing(tie.encode(), "c" * 64).rows]
    assert len(keys) == len(set(keys)) and any(k.endswith("/2") for k in keys)


def test_no_published_row_carries_an_address():
    res = read.read_listing(NEW.encode(), "a" * 64)
    assert all("Invented" not in repr(r) for r in res.rows)
    assert dict(res.addresses)[res.rows[-1]["key"]] == "1 Invented Street, Sometown"


def test_the_join_follows_the_commission_s_link_by_name_and_refuses_a_collision():
    rows = read.read_listing(NEW.encode(), "a" * 64).rows
    a, b = (next(r["key"] for r in rows if r["filed"]["donor_name"] == n) for n in ("A Donor", "B Donor Limited"))
    held = [("1" * 64, "A_Donor_5_October_2026.pdf"), ("1" * 64, "2026-20k+-donations__A-Donor-5-October-2026.pdf"),
            ("2" * 64, "B-Donor-Limited_27_July_2023.jpg"), ("3" * 64, "B_Donor_Limited_27_July_2023.pdf"),
            ("4" * 64, "Unlisted_1_May_2023.pdf")]
    linked, files = read.join(rows, held)
    assert linked == {a: "1" * 64}
    status = {(s, n): st for s, n, _, st in files}
    assert status[("2" * 64, "B-Donor-Limited_27_July_2023.jpg")] == "collision"
    assert status[("4" * 64, "Unlisted_1_May_2023.pdf")] == "not linked by the table"


def test_a_challenge_shell_and_a_cut_file_are_not_documents(tmp_path):
    shell = tmp_path / "x.pdf"
    shell.write_bytes(b"<html><head><script src='/_Incapsula_Resource'></script></head></html>")
    cut = tmp_path / "y.pdf"
    cut.write_bytes(b"%PDF" + b"0" * (capture.TRUNCATED_AT - 4))
    real = tmp_path / "z.pdf"
    real.write_bytes(b"%PDF" + b"0" * 5000)
    assert "challenge" in capture.is_real_document(str(shell))
    assert "1 MiB" in capture.is_real_document(str(cut))
    assert capture.is_real_document(str(real)) == ""
    assert capture.commission_name("/x/archive/2026-20k+-donations__A_1_May_2026.pdf") == "A_1_May_2026.pdf"


FORM_PAGE = """Party Donation Disclosure
Donations exceeding $20,000 must be disclosed within 10 working days
Total donation and date received
Total amount
$ 21,563.88
Amount Date received Amount Date received
$ 3,593.98 1/6/26 $ 3,593.98 2/6/26
"""


def test_the_form_s_total_is_the_figure_under_its_label_never_the_boilerplate():
    from registers.disclosures import form
    got = form.total({1: FORM_PAGE})
    assert (got.amount, got.page) == (21563.88, 1)
    assert form.total({1: FORM_PAGE.replace("$ 21,563.88", "")}).amount is None, \
        "an empty box is no total: the grid of gifts under it is the next label's (J Marcroft 2023, gifts $27,000 + $5,000)"
    assert form.total({1: "Donations exceeding $20,000\nTotal amount\n\n\n\n\n\n$ 5.00"}).amount is None
    assert form.total({}).why


def test_a_bare_20_000_in_the_box_is_the_total_not_the_boilerplate():
    from registers.disclosures import form
    page = "Total donation and date received\nFor multiple donations, the date the final donation was received\n\nTotal amount\n$20,000\n\nDate received\n28 February 2023"
    assert form.total({1: page}).amount == 20000.0
    assert form.total({1: "Total amount\nDonations over $20,000 must be disclosed\n$ 31,000.00"}).amount == 31000.0
    assert form.total({1: "Total amount\n20020\n\nDate received\n01/04/2026"}).amount == 20020.0, "the $ is printed outside the box"
    assert form.total({1: "Total amount\n1\nDate received"}).amount is None, "a bare figure under $100 is not a total"


def test_a_struck_out_total_and_its_correction_are_both_kept_and_the_check_names_it():
    from registers.disclosures import form
    page = "Total donation and date received\n$26,066.66\n$19,250.22\n\nDate received\n23/10/23"
    got = form.total({1: page})
    assert got.amount == 26066.66 and got.figures == (26066.66, 19250.22)
    forms = {"1" * 64: {"held": True, "total": got.amount, "figures": got.figures, "stamp": "s"}}
    assert read.form_check(19250.22, "1" * 64, forms) == {"form_total": 19250.22, "form_check": read.SECOND_FIGURE, "form_reading": "s"}
    assert read.form_check(26066.66, "1" * 64, forms)["form_check"] == read.SECOND_FIGURE, "which one is struck is not seen"
    assert read.form_check(30000.00, "1" * 64, forms)["form_check"] == "differs"
    assert form.total({1: "Total amount   $ 50,000.00      Date received  12/06/2023"}).figures == (50000.0,), \
        "the next label on the same line ends nothing: one figure"


def test_the_text_layer_is_read_only_where_the_reading_has_no_total_and_never_under_a_picture(monkeypatch):
    from registers.disclosures import form
    typed = "Total donation and date received\n      Total amount        $  50,000.00\n\nDate received   12/06/2023\n" + "x" * 80
    monkeypatch.setattr(form.textpages, "text_pages", lambda data: {1: typed, 2: "Total amount  $ 9\n" + "y" * 80})
    monkeypatch.setattr(form, "picture_pages", lambda data: {2})
    assert form.text_layer(b"%PDF-1.7") == {1: typed}
    assert form.text_layer(b"\xff\xd8 a photograph") == {}
    monkeypatch.setattr(form, "stored", lambda sha: [])
    got = read.form_reading("a" * 64, b"%PDF-1.7")
    assert (got["total"], got["held"]) == (50000.0, True) and got["stamp"].startswith(read.TEXT_LAYER)
    monkeypatch.setattr(form, "picture_pages", lambda data: {1, 2})
    none = read.form_reading("a" * 64, b"%PDF-1.7")
    assert none["held"] is False and none["total"] is None


def test_a_scan_with_no_total_read_is_set_aside_with_its_hash_and_pages():
    forms = {"1" * 64: {"held": True, "total": None, "pages": 2, "stamp": "s"}, "2" * 64: {"held": True, "total": 5.0},
             "3" * 64: {"held": False, "total": None, "pages": 1}}
    got = read.needs_reading(forms, {"k1": "1" * 64, "k2": "2" * 64, "k3": "3" * 64, "k4": "1" * 64})
    assert [g[0] for g in got] == ["1" * 64, "3" * 64] and all(g[1] == "form" for g in got)
    assert "2 page(s)" in got[0][2] and "ruling 62" in got[0][2]


def test_the_form_check_names_what_it_could_not_compare():
    forms = {"1" * 64: {"held": True, "total": 21563.88, "stamp": "s"}, "2" * 64: {"held": True, "total": None, "stamp": "s"}}
    assert read.form_check(21563.88, "1" * 64, forms)["form_check"] == "equal"
    assert read.form_check(21000.00, "1" * 64, forms)["form_check"] == "differs"
    assert read.form_check(1.0, "2" * 64, forms)["form_check"] == "no total read"
    assert read.form_check(1.0, "3" * 64, forms)["form_check"] == "no reading held"
    assert read.form_check(1.0, None, forms)["form_check"] == "no scan held"


def test_the_read_job_reads_on_the_worker_s_card_and_never_the_default(monkeypatch, capsys):
    """Card the-disclosures-read-job-reads-through-the-carve-out-s-server:
    the piece hands the worker's server to the reader, and without one it
    refuses rather than fall back to the carve-out's."""
    seen = []

    class Got:
        readings, replayed, unread = [], 0, []

    monkeypatch.setattr(read, "read_document", lambda *a, **k: seen.append(k) or Got())
    monkeypatch.setattr("support.docstore.landing.read_bytes", lambda sha: b"not a pdf")
    monkeypatch.delenv("QV4_MODEL_URL", raising=False)
    monkeypatch.delenv("QV4_MODEL", raising=False)
    assert read.main(["--scan", "a" * 64]) == 2 and not seen, "no worker's card: refused, nothing read"
    monkeypatch.setenv("QV4_MODEL_URL", "http://127.0.0.1:8101/v1/chat/completions")
    monkeypatch.setenv("QV4_MODEL", "glm-ocr")
    assert read.main(["--scan", "a" * 64]) == 0
    assert (seen[0]["url"], seen[0]["model"]) == ("http://127.0.0.1:8101/v1/chat/completions", "glm-ocr")
    assert seen[0]["page_reader"] is True


def test_compare_buckets_by_the_day_the_party_received_the_gift():
    rows = [{"party": "Example Party", "party_label": "Example Party", "regime": check.COMPARED, "amount": 30000, "given_on": dt.date(2023, 12, 30)},
            {"party": "Example Party", "party_label": "Example Party", "regime": check.COMPARED, "amount": 25000, "given_on": dt.date(2024, 1, 2)},
            {"party": None, "party_label": "Gone Party", "regime": check.COMPARED, "amount": 21000, "given_on": dt.date(2023, 5, 1)},
            {"party": "Example Party", "party_label": "Example Party", "regime": "over-30000-2011-2022", "amount": 40000, "given_on": None}]
    out = check.compare(rows, {("Example Party", 2023): 30000.0, ("Example Party", 2024): 1.0}, {"Example Party": 2})
    assert [(e["party"], e["year"]) for e in out["equal"]] == [("Example Party", 2023)]
    assert [(d["year"], d["ours"]) for d in out["differ"]] == [(2024, 25000.0)]
    assert out["count_differs"] == [] and out["earlier_regimes"] == 1 and out["unresolved_parties"] == {"Gone Party": 1}


# --- the filled sample -------------------------------------------------------

def _schema() -> str:
    for base in (os.environ.get("CLAUDE_PROJECT_DIR"), REPO):
        try:
            with open(os.path.join(base or "", ".scope"), encoding="utf-8") as f:
                for line in f:
                    if line.startswith("name:"):
                        return sample.scratch_name(line.split(":", 1)[1].strip())
        except OSError:
            continue
    return "scratch_gate_disclosures"


@pytest.fixture(scope="module")
def filled():
    if os.environ.get("QV4_NO_DB") or not os.path.exists(os.path.join(db.CRED_DIR, "v4.env")):
        pytest.skip("no sample database environment here (QV4_NO_DB, or no credential file)")
    schema = _schema()
    sample.fill_schema(schema, lambda: db.connect(db.OWNER_KEY, "querynz_v4_sample"), REPO, log=lambda *a: None)
    with db.connect(db.OWNER_KEY, "querynz_v4_sample") as conn:
        def q(sql):
            cur = conn.execute(sql)
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur]
        yield {"schema": schema, "conn": conn,
               "rows": q(f"SELECT * FROM {schema}.disclosures_declarations ORDER BY key"),
               "items": q(f"SELECT * FROM {schema}.disclosures_items"),
               "files": q(f"SELECT * FROM {schema}.disclosures_files"),
               "aside": q(f"SELECT * FROM {schema}.disclosures_set_aside"),
               "private": q(f"SELECT key FROM {schema}_private.disclosures_donor_addresses")}


def _sample_hashes():
    return [i.split()[0] for i in sample.read_list(os.path.join(LANE, "sample.list")) if not i.startswith("key:")]


def test_both_listings_read_whole_and_the_catch_log_reconciles(filled):
    by_doc = {}
    for r in filled["rows"]:
        by_doc[r["document"]] = by_doc.get(r["document"], 0) + 1
    assert sorted(by_doc.values()) == [244, 276], by_doc
    assert [a for a in filled["aside"] if a["stage"] == "listing"] == []
    assert len({r["key"] for r in filled["rows"]}) == len(filled["rows"])


def test_every_row_keeps_the_row_contract_and_no_address_is_published(filled):
    today = dt.date.today()
    for r in filled["rows"]:
        row = {k: r[k] for k in ("key", "document", "page", "place", "reader", "profile", "profile_version", "read_from")}
        row["loaded_at"] = r["loaded_at"].isoformat()
        row["filed"] = {k: (r[k].isoformat() if r[k] else None) for k in ("received_on", "given_on", "amended_on", "withdrawn_on", "returned_on")}
        assert rowcontract.validate(row, today) == [], r["key"]
    assert not any("address" in c for c in filled["rows"][0])
    assert len(filled["private"]) > 400, "the donor cells' address lines go to the private schema"


def test_the_commission_s_ten_amendment_notes_from_2023_are_read(filled):
    new = [r for r in filled["rows"] if r["regime"] == "over-20000-from-2023"]
    states = {}
    for r in new:
        states[r["amendment"]] = states.get(r["amendment"], 0) + 1
    assert states == {"none": 266, "amended": 9, "amendment withdrawn": 1}
    assert sum(1 for r in new if r["returned_on"]) == 2
    assert all(r["href"] for r in new) and all(r["given_on"] for r in new)


def test_the_scans_join_by_the_commission_s_link(filled):
    files = {f["document"]: f for f in filled["files"] if f["kind"] == "declaration"}
    linked = {r["declaration_document"] for r in filled["rows"] if r["declaration_document"]}
    lines = {l.split()[0]: l for l in open(os.path.join(LANE, "sample.list"), encoding="utf-8") if re.match(r"^[0-9a-f]{64}", l)}
    for sha, line in lines.items():
        if "listing:" in line:
            continue
        if "not linked by the table" in line:
            assert files[sha]["status"] == "not linked by the table", line
            assert sha not in linked
        elif "linked" in line or "archive" in line:
            assert files[sha]["status"] == "linked" and sha in linked, line


def test_the_form_s_own_total_never_differs_from_the_table_where_a_reading_is_held(filled):
    checks = {}
    for r in filled["rows"]:
        checks[r["form_check"]] = checks.get(r["form_check"], 0) + 1
    assert checks.get("differs", 0) == 0, [(r["key"], r["amount"], r["form_total"]) for r in filled["rows"] if r["form_check"] == "differs"]
    assert checks.get("equal", 0) >= 1, "the sample holds a scan with a stored reading; none compared means the replay broke"
    assert all(r["form_check"] == "no scan held" for r in filled["rows"] if r["regime"] != "over-20000-from-2023"), \
        "the Commission links no scan before 2023"


def test_each_party_year_equals_the_frozen_site_or_has_a_card(filled):
    assert os.path.exists(check.HOME_JSON), f"the frozen site's figures are read from {check.HOME_JSON}, which is not here"
    out = check.compare(filled["rows"], *check.frozen())
    cards = " ".join(open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(REPO, "cards", "*.md")))
    uncarded = [d for d in out["differ"] if f"{d['party']} {d['year']}" not in cards]
    assert uncarded == [], "differences from the frozen site with no card: " + "; ".join(
        f"{d['party']} {d['year']} ours {d['ours']:.2f} frozen {d['frozen']:.2f}" for d in uncarded)
    assert len(out["equal"]) >= 13   # 15 until 21 October (ACT New Zealand 2026, its card); 14 until 22 October (the Green Party 2026 moved on that day's release, its card)


def test_the_published_views_build_on_the_lane_s_tables(filled):
    from registers.disclosures import load as L
    schema, conn = filled["schema"], filled["conn"]
    conn.execute(L.sql("publish.sql", schema, shared=True).replace("pub.", f"{schema}.disclosures_pub_"))
    n = conn.execute(f"SELECT count(*) FROM {schema}.disclosures_pub_disclosures").fetchone()[0]
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {schema}.disclosures_pub_disclosures LIMIT 0").description]
    conn.rollback()
    assert n == len(filled["rows"]) and not any("address" in c for c in cols)
    assert cols[-1] == "issue", "ruling 66's flag is published, at the view's end"


def test_ruling_66_the_sample_s_listed_keys_carry_their_outcome_and_the_check_counts_them(filled):
    by_key = {r["key"]: r for r in filled["rows"]}
    keys = [l.split()[1] for l in sample.read_list(os.path.join(LANE, "sample.list")) if l.startswith("key: ec-listing/")]
    assert len(keys) == 3
    admitted = by_key[keys[0]]
    assert (admitted["items_check"], admitted["issue"]) == ("reconciled", "+0.16: the 8 itemised gifts against the declared amount")
    assert float(admitted["amount"]) == 41037.00, "the published total is the printed one"
    for k in keys[1:]:
        assert (by_key[k]["items_check"], by_key[k]["issue"]) == ("differs", None)
    flagged = check.issues(filled["rows"])
    assert flagged == [(keys[0], admitted["issue"])]
    assert all(r["items_check"] == "reconciled" for r in filled["rows"] if r["issue"])


def test_a_difference_passes_the_check_only_when_a_card_names_it(tmp_path):
    (tmp_path / "a-card.md").write_text("# x\nstate: open\n\n`ec-listing/2023-06-13/5912c64f7260` differs; National 2023 too\n")
    (tmp_path / "other.md").write_text("# y\nstate: open\nnothing\n")
    cards = check.carded(str(tmp_path))
    assert check.card_for("ec-listing/2023-06-13/5912c64f7260", cards) == "a-card"
    assert check.card_for("National 2023", cards) == "a-card"
    assert check.card_for("ec-listing/2024-07-17/76b5df1420ab", cards) is None
    assert check.card_for("nothing", cards) == "other", "the name is the card's own, not its neighbour's"
    assert check._short("The New Zealand National Party") == "National"


class _Conn:
    """A stand-in for the live connection: the job's steps are monkeypatched."""
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *a, **k):
        return self

    def transaction(self):
        return self


def _job(monkeypatch, uncarded: int, rows: int = 522):
    from registers.disclosures import load as L
    from support import jobrun
    calls, runs = [], []
    monkeypatch.setattr(db, "connect", lambda key, database=None, **k: calls.append(("connect", database)) or _Conn())
    monkeypatch.setattr(capture, "copy_all", lambda conn: calls.append(("capture",)) or ([], []))
    monkeypatch.setattr(L, "build", lambda conn, schema, *a, shared=False: calls.append(("build", schema, shared)) or
                        {"listings": 2, "table_rows": rows, "rows": rows, "set_aside": 0, "linked": rows})
    monkeypatch.setattr(check, "held", lambda conn, relation: calls.append(("held", relation)) or [])
    monkeypatch.setattr(check, "frozen", lambda: ({}, {}))
    monkeypatch.setattr(check, "carded", lambda: "")
    monkeypatch.setattr(check, "verdict", lambda *a: calls.append(("verdict",)) or (uncarded, ["equal: 45 party-years"]))
    monkeypatch.setattr(L, "frozen_release", lambda: "2026-10-23T0618")
    monkeypatch.setattr(L, "publish", lambda conn, staging: calls.append(("publish", staging)))
    monkeypatch.setattr(jobrun, "record", lambda job, ok, detail, *a, **k: runs.append((job, ok, detail)))
    return L.job(log=lambda *_: None), calls, runs


def test_the_job_publishes_only_after_the_check_is_green(monkeypatch):
    rc, calls, runs = _job(monkeypatch, uncarded=0)
    steps = [c[0] for c in calls]
    assert rc == 0 and steps == ["connect", "capture", "build", "held", "verdict", "publish"]
    assert calls[0] == ("connect", "querynz_v4") and calls[2] == ("build", "staging_disclosures_load", False)
    assert calls[3] == ("held", "staging_disclosures_load.declarations"), "the check reads the staged rows, not the live"
    assert calls[-1] == ("publish", "staging_disclosures_load")
    assert runs == [("qv4-disclosures-load", True, runs[0][2])] and runs[0][2].startswith("published: 522 declarations")


def test_the_job_publishes_nothing_when_a_difference_has_no_card(monkeypatch):
    rc, calls, runs = _job(monkeypatch, uncarded=1)
    assert rc == 1 and "publish" not in [c[0] for c in calls] and "verdict" in [c[0] for c in calls]
    assert runs[0][:2] == ("qv4-disclosures-load", False) and runs[0][2].startswith("nothing published")


def test_the_job_publishes_nothing_when_no_declaration_was_read(monkeypatch):
    rc, calls, runs = _job(monkeypatch, uncarded=0, rows=0)
    assert rc == 1 and "publish" not in [c[0] for c in calls] and runs[0][1] is False


def test_a_session_loads_only_a_scratch_or_staging_schema_of_the_sample():
    from registers.disclosures import load as L
    assert L.main(["--schema", "disclosures"]) == 2
    assert L.main(["--schema", "staging_disclosures_load", "--database", "querynz_v4"]) == 2
