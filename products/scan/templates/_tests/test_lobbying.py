"""Use case 15, lobbying (step 8.5, 2 November 2026): every step starts from a diary entry the diaries lane does not flag as
naming an address, a line's title never carries the meeting's text, and every company met is near, marked a namesake."""
from products.scan import plan, template as tpl, views as cat


def test_the_lobbying_scans_never_read_an_address_flagged_entry_and_title_no_meeting_text():
    assert set(cat.BY_NAME["minister_diary_entries"].title) == {"minister", "entry_on", "portfolio"}
    for name in ("lobbying-meetings-suppliers", "lobbying-meetings-donors"):
        t = tpl.by_name(name)
        first = t.steps[0]
        assert first.view == "minister_diary_entries"
        assert dict(first.where) == {"attendees_names_address": False, "meeting_names_address": False}, name
        assert "meeting" not in first.columns and "attendees" not in first.columns
        company = t.steps[1]
        assert (company.view, company.by, company.on, company.namesakes) == ("companies", "name", ("attendees", "name"), True)
        q, _ = plan.sql(t, {"chains": {"value": "follow"}, "through_people": {"value": "near"}}, first.view)
        assert "attendees_names_address" in q and "meeting_names_address" in q, name


def test_an_address_flag_filtered_to_false_is_the_limit_applied_and_any_other_read_of_it_is_refused():
    """The outside check (check_template) once counted the flag columns themselves as address reads, so both scans were red
    for applying hard limit 15. A flag filtered to false passes; filtered to true, or carried as a column, it is refused."""
    import dataclasses
    from products.scan import check, db
    shaped = lambda t: [p for p in check.check_template(pub, t, held) if "address-shaped" in p]
    with db.pub_connect() as pub:
        held = set(db.pub_views(pub))
        for name in ("lobbying-meetings-suppliers", "lobbying-meetings-donors"):
            t = tpl.by_name(name)
            assert shaped(t) == [], name
            first = t.steps[0]
            for bad in (dataclasses.replace(first, where=(("attendees_names_address", True), ("meeting_names_address", False))),
                        dataclasses.replace(first, columns=first.columns + ("meeting_names_address",))):
                assert shaped(dataclasses.replace(t, steps=(bad,) + tuple(t.steps[1:]))), name


def test_the_scan_reader_plans_for_the_whole_result_as_a_cursor_reads_it_all():
    from products.scan import db
    with db.pub_connect() as pub:
        assert pub.execute("show cursor_tuple_fraction").fetchone()[0] == "1"
