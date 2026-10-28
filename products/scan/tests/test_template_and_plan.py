"""The template file and the query it compiles to, on the two proving scans
and on refusals: what a scan may read, how a step is declared, and how the
chains setting changes the query."""
import os
import tempfile

import pytest

from products.scan import plan, settings as cfg, template as tpl, views as cat

SETTINGS = cfg.in_force()
DIRECT = {"chains": {"value": "direct", "status": "x"}, "through_people": {"value": "near", "status": "x"}}


def write(toml: str) -> str:
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "template.toml"), "w", encoding="utf-8") as f:
        f.write(toml)
    return d


BASE = '''
name = "t"
title = "T"
question = "Which officers are directors?"
join = "an officer; a director the links say is the same person"
version = "0.1"
owner = "test"
[[reads]]
view = "society_officers"
licence = "public"
[[reads]]
view = "directors"
licence = "public"
'''


def test_the_two_proving_scans_load_and_read_only_published_views():
    for name in ("society-officers-liquidations", "donors-named-as-companies"):
        t = tpl.by_name(name)
        assert t.question.endswith("?") and t.reads and t.steps and t.limits
        assert all(r.licence for r in t.reads)
        for s in t.steps:
            assert s.view in t.views and all(v in t.views for v in s.views)
        assert set(plan.views_read(t)) <= set(cat.BY_NAME) | set(cat.LINKS_VIEWS)
    assert tpl.by_name("donors-named-as-companies").starts() == ("party_return_donors", "disclosures")
    assert tpl.by_name("society-officers-liquidations").person_steps == 1


def test_a_person_step_compiles_to_the_groups_under_follow_and_to_a_confirmed_link_under_direct():
    t = tpl.load(write(BASE + '[[steps]]\nview = "society_officers"\nlabel = "officer"\n[[steps]]\nview = "directors"\nlabel = "director"\nby = "person"\n'))
    text, params = plan.sql(t, SETTINGS, "society_officers")
    assert "join pub.groups ga1 on ga1.row_key = 'societies:' || s0.key" in text and "gb1.row_key <> ga1.row_key" in text
    assert "join pub.names n1 on n1.ref = gb1.row_key and n1.view = 'directors'" in text and "as s1__contested" in text
    assert "pub.links" not in text and params == []
    text, params = plan.sql(t, DIRECT, "society_officers")
    assert "union all select row_b, row_a" in text and "l1.this = 'societies:' || s0.key and l1.grade = 'confirmed'" in text
    assert "pub.groups" not in text and "as s1__grade" in text


def test_a_link_step_to_an_organisation_lands_by_the_register_prefix_and_a_row_step_by_its_columns():
    t = tpl.by_name("donors-named-as-companies")
    text, params = plan.sql(t, SETTINGS, "disclosures", limit=5)
    assert "l.rule = %s" in text and params == ["organisation-name@1", 5]
    assert "l.this = k1.k" in text and "pub.groups m where m.group_id = ha1.group_id" in text and "hb1.group_id = hy1.group_id" in text
    assert "like 'companies:%%'" in text and "split_part(" in text and "pub.names" not in text
    t2 = tpl.by_name("society-officers-liquidations")
    text, _ = plan.sql(t2, SETTINGS, "society_officers")
    assert "join pub.companies s2 on s2.key = s1.entity_key" in text and "join pub.gazette_liquidations s3 on s3.register_key = s2.key" in text
    assert text.rstrip().endswith("order by s0.key, s1.key, s2.key, s3.key")


def test_where_filters_are_parameters_and_optional_citation_columns_follow_the_view():
    t = tpl.load(write(BASE + '[[steps]]\nview = "society_officers"\nlabel = "officer"\nwhere = { role_status = ["current", "x"], suppressed = false, ended_on = "" }\n'
                       '[[steps]]\nview = "directors"\nlabel = "director"\nby = "person"\nwhere = { in_latest = true }\n'))
    text, params = plan.sql(t, SETTINGS, "society_officers", have={"society_officers": {"key", "document", "page"}, "directors": {"key"}})
    assert "s0.role_status = any(%s)" in text and "s0.suppressed is false" in text and "s0.ended_on = %s" in text and "s1.in_latest is true" in text
    assert params == [["current", "x"], ""]
    assert "s0.page as s0__page" in text and "s0.place" not in text and "s1.document" not in text


@pytest.mark.parametrize("extra,word", [
    ('[[steps]]\nview = "directors"\nlabel = "d"\n[[steps]]\nview = "companies"\nlabel = "c"\nby = "row"\non = ["entity_key", "key"]\n', "does not read"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\ncolumns = ["address_for_service"]\n', "address-shaped"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\n[[steps]]\nview = "directors"\nlabel = "d"\nby = "row"\n', "a row step names"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\n[[steps]]\nview = "directors"\nlabel = "d"\nby = "link"\n', "names the rule"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\n[[steps]]\nview = "directors"\nlabel = "o"\nby = "person"\n', "own label"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\nwhere = { "x; drop" = 1 }\n', "not a column name"),
    ('[[steps]]\nview = "society_officers"\nlabel = "o"\n[[steps]]\nview = "directors"\nlabel = "d"\nby = "walk"\n', "by is one of"),
])
def test_a_template_outside_the_contract_is_refused(extra, word):
    with pytest.raises(ValueError, match=word):
        tpl.load(write(BASE + extra))


def test_a_person_step_needs_rows_the_names_table_carries_and_a_question_ends_in_a_question_mark():
    toml = BASE.replace('view = "directors"', 'view = "companies"') + '[[steps]]\nview = "society_officers"\nlabel = "o"\n[[steps]]\nview = "companies"\nlabel = "c"\nby = "person"\n'
    with pytest.raises(ValueError, match="pub.names carries"):
        tpl.load(write(toml))
    with pytest.raises(ValueError, match="question"):
        tpl.load(write(BASE.replace("directors?", "directors") + '[[steps]]\nview = "society_officers"\nlabel = "o"\n'))


def test_the_settings_file_records_the_two_defaults_as_in_force_and_refuses_a_change_without_a_ruling():
    s = cfg.load()
    assert s["chains"]["value"] == "follow" and s["through_people"]["value"] == "near"
    assert all(x["status"] == "default in force" for x in s.values())
    assert cfg.in_force()["chains"] == {"value": "follow", "status": "default in force"}
    d = tempfile.mkdtemp()
    p = os.path.join(d, "settings.toml")
    with open(p, "w") as f:
        f.write('[chains]\nvalue = "direct"\nstatus = "default in force"\nruling = ""\n[through_people]\nvalue = "near"\nstatus = "default in force"\nruling = ""\n')
    with pytest.raises(ValueError, match="without a ruling"):
        cfg.load(p)
    with open(p, "w") as f:
        f.write('[chains]\nvalue = "direct"\nstatus = "ruled"\nruling = "80"\n[through_people]\nvalue = "near"\nstatus = "default in force"\nruling = ""\n')
    assert cfg.in_force(p)["chains"] == {"value": "direct", "status": "ruled (80)"}


def test_every_view_the_catalogue_knows_names_no_address_column_and_person_rows_match_the_names_table():
    for v in cat.VIEWS:
        assert not any(cat.ADDRESS_COLUMN.search(c) for c in cat.columns_read(v)), v.name
        assert v.register and v.kind in ("person", "organisation", "figure", "event")
    assert cat.BY_NAME["directors"].person_row and cat.BY_NAME["society_officers"].person_row and not cat.BY_NAME["companies"].person_row
