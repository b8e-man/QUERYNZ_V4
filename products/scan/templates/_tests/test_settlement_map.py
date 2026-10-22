"""Step 6.2 template 3 (scan-templates-2): the post-settlement governance
map, use case 14, one question in six scans (`settlement-map-*`). Each
loads under the contract and the presentation rules; each starts from the
directory's organisations and governance entities; none reads an address
or a contact column; and the three rules these templates add catch each
planted fault: a scan whose lines name office holders says it is for the
register scan only, never the public site (hard limit 14); a name step onto
a view that suppresses names joins no suppressed row (hard limit 16); and
no step reads a phone, email, location or website column.

The templates need the shape's additions (the directory's three views in
the scan's catalogue, citations numbered per row, the read-back). Until
the integrator applies `_shape/scan-templates-2-shape.diff` these tests
skip, and only while that file is here."""
import os
import re
import tempfile

import pytest

from products.scan import rules, template as tpl, views as cat

HERE = os.path.dirname(os.path.abspath(__file__))
DIFF = os.path.join(os.path.dirname(HERE), "_shape", "scan-templates-2-shape.diff")
SHAPED = "iwi_directory_entities" in cat.BY_NAME
MAP = ("settlement-map-iwi", "settlement-map-settlements", "settlement-map-charities", "settlement-map-companies",
       "settlement-map-societies", "settlement-map-shareholdings")
QUESTION = ("For each iwi organisation or post-settlement governance entity in the iwi and hapū directory, which iwi and settlement "
            "does it stand for, which charity and which company is it, and who holds its offices?")
REGISTER_ONLY = re.compile(r"for the register scan only, never for the public site", re.I)
OFFICE_VIEWS = {"charity_officers", "directors", "society_officers", "shareholders"}
#: a column a settlement-map scan never reads: the directory's contact details live in no published view, and a marae's
#: location or a body's website is the body's own but has no place on a line about office holders
CONTACT = re.compile(r"(^|_)(phones?|mobile|email|e_mail|fax|contacts?|location|website|chair|chief|ceo)(_|$)", re.I)


def test_the_shape_has_the_additions_or_the_diff_is_still_waiting():
    assert SHAPED or os.path.exists(DIFF), "the shape lacks the directory's views and the diff that carries them is gone"


needs_shape = pytest.mark.skipif(not SHAPED, reason="waits on _shape/scan-templates-2-shape.diff (the integrator applies it at the merge)")


def register_only_problems(t) -> list:
    """A scan whose lines name a person in office says, in its limits, that it
    is for the register scan only and never for the public site."""
    if {s.view for s in t.steps} & OFFICE_VIEWS and not any(REGISTER_ONLY.search(x) for x in t.limits):
        return [f"{t.name}: lists office holders without saying it is for the register scan only, never for the public site"]
    return []


def suppressed_join_problems(t) -> list:
    """A name step onto a view that suppresses names must filter the
    suppressed rows out (`where = { <suppressed> = false }`): a suppressed
    name is never compared with anything, or a line would say what it is."""
    out = []
    for s in t.steps[1:]:
        v = cat.BY_NAME[s.view]
        if s.by == "name":
            if v.suppressed and not any(c == v.suppressed and val is False for c, val in s.where):
                out.append(f"{t.name}: step {s.label} joins pub.{s.view} by name without leaving its suppressed rows out")
    return out


def contact_problems(t) -> list:
    named = [c for s in t.steps for c in (*s.columns, *(w for w, _ in s.where), *s.on, *s.number)]
    return [f"{t.name}: reads {c!r}, a contact or location column" for c in named if CONTACT.search(c)]


def text_of(name: str) -> str:
    with open(os.path.join(tpl.TEMPLATES, name, "template.toml"), encoding="utf-8") as f:
        return f.read()


def load_text(text: str):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as f:
        f.write(text)
    return tpl.load(d)


@needs_shape
@pytest.mark.parametrize("name", MAP)
def test_each_scan_loads_asks_the_one_question_and_passes_the_rules(name):
    t = tpl.by_name(name)
    assert t.question == QUESTION and t.version == "1.0" and t.limits
    assert all(r.licence and r.attribution and r.refresh for r in t.reads)
    assert any("Te Kāhui Māngai" in r.attribution for r in t.reads if r.view.startswith("iwi_directory"))
    assert rules.template_problems(t) == [] and register_only_problems(t) == []
    assert suppressed_join_problems(t) == [] and contact_problems(t) == []
    assert REGISTER_ONLY.search(" ".join(t.limits))
    assert os.path.exists(os.path.join(t.folder, "limits.md"))


@needs_shape
@pytest.mark.parametrize("name", MAP)
def test_each_scan_starts_from_the_directory_s_bodies_and_reads_no_address(name):
    t = tpl.by_name(name)
    body = t.steps[0]
    assert t.starts() == ("iwi_directory_entities",) and dict(body.where) == {"kind": ("organisation", "governance entity")}
    named = [c for s in t.steps for c in (*s.columns, *(w for w, _ in s.where), *s.on, *s.number)]
    assert named and not [c for c in named if cat.ADDRESS_COLUMN.search(c)]
    assert all(s.optional for s in t.steps[1:]), "a body with nothing there is still listed"
    assert "location" not in cat.BY_NAME["iwi_directory_entities"].title


@needs_shape
def test_the_register_joins_go_by_number_where_both_carry_one_else_by_name_with_namesakes_marked_on_bodies_only():
    want = {"settlement-map-charities": ("charities", ("charity_number", "number"), True, "officer", "charity_key"),
            "settlement-map-companies": ("companies", ("nzbn", "nzbn"), True, "director", "entity_key"),
            "settlement-map-societies": ("societies", ("nzbn", "nzbn"), True, "officer", "society_key"),
            "settlement-map-shareholdings": ("shareholders", ("nzbn", "holder_nzbn"), False, "company", "key")}
    for name, (view, number, namesakes, label, key) in want.items():
        t = tpl.by_name(name)
        _, there, office = t.steps
        assert there.view == view and there.by == "name" and there.on == ("name", "name") and there.number == number
        assert there.namesakes is namesakes, "a shareholding row is a holding, not a body: never counted as a namesake"
        assert office.by == "row" and office.label == label and key in office.on
    assert tpl.by_name("settlement-map-charities").steps[1].fold_note == "by charity number or by name"
    assert tpl.by_name("settlement-map-companies").steps[1].fold_note == "by business number or by name"


@needs_shape
def test_the_iwi_and_the_settlement_are_the_directory_s_own_and_the_limits_say_what_is_not_held():
    iwi = tpl.by_name("settlement-map-iwi")
    _, listing, to = iwi.steps
    assert listing.view == "iwi_directory_relations" and dict(listing.where) == {"relation": "organisation of iwi"}
    assert to.view == "iwi_directory_entities" and to.on == ("to_key", "key")
    st = tpl.by_name("settlement-map-settlements")
    assert st.steps[1].view == "iwi_directory_settlements" and st.steps[1].on == ("key", "entity_key") and "stage" in st.steps[1].columns
    text = " ".join(st.limits)
    assert "Te Haeata" in text and "login" in text and "mandate" in text
    for name in MAP:
        lim = " ".join(tpl.by_name(name).limits)
        assert "Māori Land Court" in lim and "Waitangi Tribunal" in lim and "Arthur's question" in lim


@needs_shape
@pytest.mark.parametrize("name", MAP)
@pytest.mark.parametrize("old, new, why", [
    ('licence = "', 'licensing = "', "without its licence terms"),
    ('?"\n', '"\n', "is a question"),
    ('columns = ["legal_entity", "listed_as"]', 'columns = ["legal_entity", "listed_as", "postal_address"]', "address-shaped"),
    ('by = "row"', 'by = "fuzzy"', "by is one of"),
    ('optional = true\n', 'optional = "yes"\n', "optional is true or false"),
])
def test_a_scan_moved_outside_the_contract_is_refused(name, old, new, why):
    text = text_of(name)
    if old not in text:
        pytest.skip(f"{name} has no {old!r}")
    with pytest.raises(ValueError, match=re.escape(why)):
        load_text(text.replace(old, new, 1))


@needs_shape
@pytest.mark.parametrize("name", MAP)
def test_mutants_the_three_rules_catch_each_planted_fault(name):
    clean = text_of(name)
    t = load_text(clean)
    assert register_only_problems(t) == suppressed_join_problems(t) == contact_problems(t) == []
    if {s.view for s in t.steps} & OFFICE_VIEWS:
        for what, text in {
            "the limit dropped": re.sub(r'  "For the register scan only[^\n]*\n', "", clean),
            "the limit softened": clean.replace("never for the public site", "not yet for the public site"),
        }.items():
            assert text != clean and register_only_problems(load_text(text)), what
    carried = clean.replace('columns = ["legal_entity", "listed_as"]', 'columns = ["legal_entity", "listed_as", "website"]')
    assert carried != clean and contact_problems(load_text(carried))
    if name == "settlement-map-shareholdings":
        open_ = clean.replace('where = { suppressed = false }\n', "")
        assert open_ != clean and suppressed_join_problems(load_text(open_))
        flipped = clean.replace("suppressed = false", "suppressed = true")
        assert suppressed_join_problems(load_text(flipped))
    caused = clean.replace("who holds its offices?", "who controls it?")
    assert any("rule 3" in p for p in rules.template_problems(load_text(caused)))


@needs_shape
def test_every_template_on_disk_that_joins_by_name_onto_a_suppressing_view_leaves_suppressed_rows_out():
    for name in tpl.folders():
        assert suppressed_join_problems(tpl.by_name(name)) == [], name
