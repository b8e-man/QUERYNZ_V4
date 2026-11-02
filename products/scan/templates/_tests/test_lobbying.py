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
