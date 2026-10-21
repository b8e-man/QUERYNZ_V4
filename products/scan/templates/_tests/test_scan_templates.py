"""The step-6.2 templates (scan-templates-1): tender-awards (use case 10)
and the two halves of the procurement template (use case 9). Each loads
under the contract and the presentation rules; none reads an address; a
template moved outside the contract is refused; and the rule these
templates add (a scan that joins donors to awards says in its limits that
it is for the register scan only, never the public site) catches each
planted fault.

The templates need the shape's additions (the award views, the name step,
the optional step, a link step of several rules). Until the integrator
applies `_shape/scan-templates-1-shape.diff` to products/scan/ these tests
skip, and only while that file is here: a shape without the additions and
without the file fails."""
import os
import re
import tempfile

import pytest

from products.scan import rules, template as tpl, views as cat

HERE = os.path.dirname(os.path.abspath(__file__))
DIFF = os.path.join(os.path.dirname(HERE), "_shape", "scan-templates-1-shape.diff")
SHAPED = "name" in tpl.BYS and "award_suppliers" in cat.BY_NAME
TENDER = "tender-awards"
PROCUREMENT = ("procurement-directors-donors", "procurement-shareholders-donors")
DONOR_VIEWS = {"party_return_donors", "disclosures", "candidate_return_donors", "disclosure_items"}
AWARD_VIEWS = {"award_notices", "award_suppliers"}
REGISTER_ONLY = re.compile(r"for the register scan only, never for the public site", re.I)


def test_the_shape_has_the_additions_or_the_diff_is_still_waiting():
    assert SHAPED or os.path.exists(DIFF), "the shape lacks the step-6.2 additions and the diff that carries them is gone"


needs_shape = pytest.mark.skipif(not SHAPED, reason="waits on _shape/scan-templates-1-shape.diff (the integrator applies it at the merge)")


def public_site_problems(t) -> list:
    """The rule these templates add: a scan that joins a donor to an award
    says, in its limits, that it is for the register scan only and never
    for the public site (step 6.2 row 2; step 6.4 is Arthur's)."""
    views = set(t.starts()) | {s.view for s in t.steps}
    if views & DONOR_VIEWS and views & AWARD_VIEWS and not any(REGISTER_ONLY.search(x) for x in t.limits):
        return [f"{t.name}: joins donors to awards without saying it is for the register scan only, never for the public site"]
    return []


def text_of(name: str) -> str:
    with open(os.path.join(tpl.TEMPLATES, name, "template.toml"), encoding="utf-8") as f:
        return f.read()


def load_text(text: str):
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as f:
        f.write(text)
    return tpl.load(d)


@needs_shape
@pytest.mark.parametrize("name", (TENDER,) + PROCUREMENT)
def test_each_template_loads_under_the_contract_and_the_rules(name):
    t = tpl.by_name(name)
    assert t.question.endswith("?") and t.limits and t.version == "1.0"
    assert all(r.licence and r.attribution and r.refresh for r in t.reads)
    assert rules.template_problems(t) == [] and public_site_problems(t) == []
    assert os.path.exists(os.path.join(t.folder, "limits.md"))


@needs_shape
@pytest.mark.parametrize("name", (TENDER,) + PROCUREMENT)
def test_no_template_reads_an_address(name):
    t = tpl.by_name(name)
    named = [c for s in t.steps for c in (*s.columns, *(w for w, _ in s.where), *s.on, *s.number)]
    assert named and not [c for c in named if cat.ADDRESS_COLUMN.search(c)]
    assert not any("address" in v for v in t.views)
    assert "title" not in cat.BY_NAME["award_notices"].title   # 754 notice titles carry a street address


@needs_shape
def test_the_award_template_lists_every_supplier_and_joins_its_company_by_number_else_by_name():
    t = tpl.by_name(TENDER)
    award, supplier, company = t.steps
    assert t.starts() == ("award_notices",) and supplier.by == "row" and supplier.on == ("key", "notice_key")
    assert company.by == "name" and company.on == ("business_name", "name") and company.number == ("nzbn", "nzbn")
    assert company.optional and company.namesakes
    assert {"awarded_amount_as_published", "value_note", "categories"} <= set(award.columns)


@needs_shape
@pytest.mark.parametrize("name", PROCUREMENT)
def test_the_procurement_template_asks_who_also_appears_and_lists_a_coincidence_as_one(name):
    t = tpl.by_name(name)
    q = t.question.lower()
    assert re.search(r"who among a winning supplier's people\b.*\balso appears as a donor", q) and "coincidence" in q
    assert REGISTER_ONLY.search(" ".join(t.limits)) and any("coincidence of record" in x for x in t.limits)
    donor, person, company, supplier, award = t.steps
    assert set(donor.views) == {"party_return_donors", "disclosures", "candidate_return_donors"}
    assert person.by == "link" and person.rules == ("full-name@1", "name-only@1")
    assert company.by == "row" and supplier.by == "name" and supplier.number == ("nzbn", "nzbn") and not supplier.namesakes
    assert award.by == "row" and award.on == ("notice_key", "key")


@needs_shape
@pytest.mark.parametrize("name", (TENDER,) + PROCUREMENT)
@pytest.mark.parametrize("old, new, why", [
    ('licence = "', 'licensing = "', "without its licence terms"),
    ('?"\n', '"\n', "is a question"),
    ('columns = ["status", "nzbn"]', 'columns = ["status", "nzbn", "registered_office_address"]', "address-shaped"),
    ('columns = ["status", "entity_type", "nzbn"]', 'columns = ["status", "entity_type", "nzbn", "registered_office_address"]', "address-shaped"),
    ('view = "companies"\nlabel = "company"', 'view = "company_addresses"\nlabel = "company"', "which the template does not read"),
    ('by = "name"', 'by = "fuzzy"', "by is one of"),
    ('number = ["nzbn", "nzbn"]', 'number = ["nzbn"]', "number = [column here, column there]"),
])
def test_a_template_moved_outside_the_contract_is_refused(name, old, new, why):
    text = text_of(name)
    if old not in text:
        pytest.skip(f"{name} has no {old!r}")
    with pytest.raises(ValueError, match=re.escape(why)):
        load_text(text.replace(old, new, 1))


@needs_shape
@pytest.mark.parametrize("name", PROCUREMENT)
def test_mutants_the_register_only_rule_catches_each_planted_fault(name):
    clean = text_of(name)
    assert public_site_problems(load_text(clean)) == []
    faults = {
        "the limit dropped": re.sub(r'  "For the register scan only[^\n]*\n', "", clean),
        "the limit softened": clean.replace("never for the public site", "not yet for the public site"),
        "the limit moved into the title only": clean.replace("For the register scan only, never for the public site", "Kept apart"),
    }
    for what, text in faults.items():
        assert text != clean, what
        assert public_site_problems(load_text(text)), what
    # a word of cause in the question is the shape's own rule 3
    caused = clean.replace("also appears as a donor", "also appears as a donor because of an award")
    assert any("rule 3" in p for p in rules.template_problems(load_text(caused)))


@needs_shape
def test_the_award_template_needs_no_register_only_limit_and_the_rule_does_not_fire_on_it():
    t = tpl.by_name(TENDER)
    assert not (set(t.starts()) | {s.view for s in t.steps}) & DONOR_VIEWS and public_site_problems(t) == []
