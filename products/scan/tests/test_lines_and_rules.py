"""A joined row to a line, on fixtures: the grade under the two settings,
the citations numbered once per row, a suppressed name on no surface, the
dates; and the presentation rules with planted faults (the mutant check:
each fault must be caught, and the clean line must pass)."""
import copy

from products.scan import lines as L, rules, template as tpl

T = tpl.by_name("society-officers-liquidations")
D = tpl.by_name("donors-named-as-companies")
SET = {"chains": {"value": "follow", "status": "default in force"}, "through_people": {"value": "near", "status": "default in force"}}
SET_CONF = {"chains": {"value": "follow", "status": "x"}, "through_people": {"value": "confirmed", "status": "x"}}


def rec(contested=False, suppressed=False):
    return {"s0__key": "societies/1/officer/a", "s0__full_name": "Jane Ann DOE", "s0__role_type": "Chair", "s0__role_status": "current",
            "s0__started_on": None, "s0__ended_on": None, "s0__first_read_on": "2026-09-01", "s0__last_read_on": "2026-10-01",
            "s0__suppressed": suppressed, "s0__document": "a" * 64, "s0__page": 1, "s0__place": "row 3",
            "s1__key": "companies/1/director/b", "s1__full_name": "Jane Ann DOE", "s1__role_type": "Director", "s1__appointed_on": None,
            "s1__ended_on": None, "s1__first_file": "f1", "s1__last_file": "f2", "s1__suppressed": suppressed, "s1__document": None, "s1__page": None,
            "s1__place": None, "s1__contested": contested, "s1__group": "g1",
            "s2__key": "companies/1", "s2__name": "ACME LIMITED", "s2__status": "Registered", "s2__nzbn": "9", "s2__registered_on": None,
            "s2__removed_on": None, "s2__first_file": "f1", "s2__last_file": "f2", "s2__document": None, "s2__page": None, "s2__place": None,
            "s3__key": "gz/1", "s3__company": "ACME LIMITED", "s3__shape": "notice", "s3__appointed_by": "court", "s3__register_match": "number and name",
            "s3__appointed_on": None, "s3__published_on": None, "s3__document": "b" * 64, "s3__page": 2, "s3__place": "n 4"}


def test_a_line_carries_each_step_cited_and_dated_and_a_grade_from_the_group():
    num = L.Numbering()
    ln = L.line_of(T, SET, "society_officers", rec(), num)
    assert ln["grade"] == "confirmed" and ln["reasons"] == [] and ln["cites"] == [1, 2, 3, 4]
    assert [s["label"] for s in ln["steps"]] == ["officer", "director", "company", "notice"]
    assert ln["steps"][0]["ref"] == "societies:societies/1/officer/a" and ln["steps"][1]["ref"] == "companies:companies/1/director/b"
    assert ln["steps"][0]["dates"] == "undated; in the files from 2026-09-01 to 2026-10-01" and "undated" in ln["steps"][2]["dates"]
    assert ln["steps"][0]["values"] == {"role_type": "Chair", "role_status": "current"}
    assert num.citations[0]["document"] == "a" * 64 and num.citations[1]["document"] is None
    # the same row met again in another line keeps its number
    L.line_of(T, SET, "society_officers", rec(), num)
    assert len(num.citations) == 4
    ln = L.line_of(T, SET, "society_officers", rec(contested=True), L.Numbering())
    assert ln["grade"] == "contested" and "contested as a whole" in ln["reasons"][0]


def test_a_link_step_takes_the_links_grade_and_reason_and_a_contested_decision_contests_the_line():
    r = {"s0__key": "d/1", "s0__donor": "ACME LIMITED", "s0__party": "P", "s0__amount": 100, "s0__year": 2023, "s0__document": "c" * 64, "s0__page": 1,
         "s1__key": "companies/1", "s1__name": "ACME LIMITED", "s1__status": "Registered", "s1__entity_type": "NZ Limited Company", "s1__nzbn": "9",
         "s1__registered_on": None, "s1__removed_on": None, "s1__first_file": "f1", "s1__last_file": "f2", "s1__document": None, "s1__page": None, "s1__place": None,
         "s1__grade": "near", "s1__reason": "a name match to a company", "s1__rule": "organisation-name@1", "s1__decision": None, "s1__link": 7}
    ln = L.line_of(D, SET, "party_return_donors", r, L.Numbering())
    assert ln["grade"] == "near" and ln["reasons"] == ["company: a name match to a company (organisation-name@1)"]
    assert ln["steps"][0]["dates"] == "2023 (the year the row is filed under)"
    r2 = dict(r, s1__grade="confirmed", s1__decision="contested", s1__reason="a decision contests this link (review)")
    assert L.line_of(D, SET, "party_return_donors", r2, L.Numbering())["grade"] == "contested"


def test_a_path_through_more_than_one_person_is_near_under_the_default_and_not_under_confirmed():
    two = tpl.Template("x", "X", "Q?", "j", "0", "o", "", T.reads, T.steps + (tpl.Step("shareholders", "holder", "person"),))
    r = dict(rec(), s4__key="companies/1/sh/1", s4__name="Jane Ann DOE", s4__first_file="f1", s4__last_file="f2", s4__suppressed=False,
             s4__document=None, s4__page=None, s4__place=None, s4__contested=False, s4__group="g1")
    assert two.person_steps == 2
    ln = L.line_of(two, SET, "society_officers", r, L.Numbering())
    assert ln["grade"] == "near" and ln["reasons"] == [L.NEAR_THROUGH_PEOPLE]
    assert L.line_of(two, SET_CONF, "society_officers", r, L.Numbering())["grade"] == "confirmed"


def test_a_suppressed_name_is_on_no_surface_of_the_line():
    ln = L.line_of(T, SET, "society_officers", rec(suppressed=True), L.Numbering())
    assert ln["steps"][0]["title"] == L.SUPPRESSED and ln["steps"][1]["title"] == L.SUPPRESSED and ln["steps"][0]["suppressed"]
    assert "DOE" not in str(ln)
    assert rules.line_problems(dict(ln, n=1)) == []


def clean_line():
    ln = L.line_of(T, SET, "society_officers", rec(), L.Numbering())
    ln["n"] = 1
    return ln


def test_the_clean_line_and_the_two_templates_pass_the_rules():
    assert rules.line_problems(clean_line()) == []
    assert rules.template_problems(T) == [] and rules.template_problems(D) == []
    assert rules.run_problems(T, [], "none found in Companies, Gazette notices") == []


def test_mutants_each_planted_fault_is_caught():
    ln = clean_line()
    m = copy.deepcopy(ln); m["steps"][2]["cite"] = 0
    assert any("no citation (rule 1)" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["steps"][1]["dates"] = ""
    assert any("rule 2" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["grade"] = "near"; m["reasons"] = ["near because the names match"]
    assert any("word of cause" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["hubs"] = [{"step": "company", "kind": "x", "text": "the owner of the company"}]
    assert any("rule 4" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["grade"] = "contested"; m["reasons"] = []
    assert any("no reason (rule 8)" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["grade"] = "likely"
    assert any("rule 9" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["steps"][0]["suppressed"] = True
    assert any("rule 6" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["steps"][0]["suppressed"] = True; m["steps"][0]["title"] = L.SUPPRESSED; m["steps"][0]["values"]["full_name"] = "Jane DOE"
    assert any("suppressed name column is carried" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["steps"][0]["title"] = "12 Smith Street, Epsom"
    assert any("address-shaped" in p for p in rules.line_problems(m))
    m = copy.deepcopy(ln); m["steps"][2]["title"] = "1 SHEA TERRACE LIMITED"
    assert rules.line_problems(m) == []   # a company's own registered name is the register's word
    bad = tpl.Template("x", "X", "Which directors are linked to donors?", "j", "0", "o", "", T.reads, T.steps, ("No officer is a director.",))
    got = rules.template_problems(bad)
    assert any("rule 3" in p for p in got) and any("rule 5" in p for p in got)
    assert any("rule 5" in p for p in rules.run_problems(T, [], "no officer is a director"))


def test_hub_names_and_the_hub_settings():
    from products.scan import hubs
    assert hubs.name_hub("ABC NOMINEES LIMITED")["kind"] == "nominee" and hubs.name_hub("Her Majesty the Queen")["kind"] == "crown"
    assert hubs.name_hub("RANK GROUP LIMITED") is None and hubs.name_hub("name suppressed") is None
    assert hubs.SETTINGS == {"hub_roles": 50, "thousand_address": 1000}
    assert "never shown as an owner" in hubs.name_hub("X Trustees Ltd")["text"] and not rules.CAUSE.search(hubs.name_hub("X Trustees Ltd")["text"])


def test_the_files_carry_every_line_with_its_citations():
    from products.scan import out
    import csv, io, json
    ln = clean_line()
    text = out.csv_text(T, [ln])
    rows = list(csv.reader(io.StringIO(text)))
    assert rows[0][:5] == ["n", "grade", "reasons", "hubs", "cites"] and "officer_citation" in rows[0] and "notice_register_match" in rows[0]
    assert rows[1][rows[0].index("cites")] == "1;2;3;4" and rows[1][rows[0].index("officer_citation")].startswith("pub.society_officers societies/1/officer/a; document aaaa")
    r = {"scan": T.name, "version": T.version, "question": T.question, "run_id": 1, "started_at": None, "finished_at": None, "seconds": 1,
         "lines": 1, "settings": SET, "views": [{"view": "directors", "loaded_at": "2026-10-21T00:00:00"}], "grades": {"confirmed": 1}, "hubs": 0, "starts": [], "problems": [], "note": ""}
    doc = json.loads(out.json_text(T, r, [ln], [{"n": 1, "view": "society_officers", "key": "k", "register": "societies", "document": None, "page": None, "place": None, "url": None}]))
    assert doc["run"]["settings"] == SET and doc["lines"][0]["cites"] == [1, 2, 3, 4] and doc["citations"][0]["n"] == 1
    html = out.scan_html(T, r, [ln], 1, 1, 200, [], ["directors"])
    assert "[1]" in html and "[4]" in html and "loaded since: stale" in html and "default in force" in html
    assert "none found in" in out.table_html(T, [], 0, 1, 200, "/scan/x")
