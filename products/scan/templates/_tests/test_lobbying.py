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


ATTENDEE_SCANS = {"lobbying-attendees-suppliers": "lobbying-meetings-suppliers", "lobbying-attendees-donors": "lobbying-meetings-donors"}
ATTENDEE_FILTER = {"attendees_names_address": False, "meeting_names_address": False, "crown": False}


def attendee_scan_problems(t) -> list:
    """What an attendee scan must hold: it starts from the diaries lane's attendee rows, filters both address flags the
    rows carry down from the entry (hard limit 15) and the Crown's own bodies, carries none of the entry's or the
    attendee's own text, and joins a company by the attendee's organisation part, near, its namesakes marked."""
    out = []
    first = t.steps[0]
    if first.view != "minister_diary_attendees":
        out.append("does not start from the attendee rows")
    if dict(first.where) != ATTENDEE_FILTER:
        out.append(f"filters {dict(first.where)}, not {ATTENDEE_FILTER}")
    if {"meeting", "attendees", "attendee", "location"}.intersection(first.columns):
        out.append("carries a text the scan never shows")
    c = t.steps[1]
    if (c.view, c.by, c.on, c.namesakes) != ("companies", "name", ("organisation", "name"), True):
        out.append("does not join a company by the organisation part with its namesakes marked")
    return out


def test_the_attendee_scans_start_from_an_attendee_filter_the_flags_carried_down_and_the_crown_and_join_by_the_organisation_part():
    """The diaries lane's attendee rows (pub.minister_diary_attendees) carry the entry's flags down; each attendee scan
    holds `attendee_scan_problems`, titles a line by the minister, the day, the portfolio and the organisation part
    (never the attendee's own text), and otherwise takes its whole-text scan's steps unchanged."""
    import os
    from products.scan import rules
    v = cat.BY_NAME["minister_diary_attendees"]
    assert v.register == "ministers_diaries" and set(v.title) == {"minister", "entry_on", "portfolio", "organisation"}
    assert "attendee" in v.names and "attendee" not in v.title
    for name, whole in ATTENDEE_SCANS.items():
        t, w = tpl.by_name(name), tpl.by_name(whole)
        assert attendee_scan_problems(t) == [], name
        assert t.views - {"minister_diary_attendees"} == w.views - {"minister_diary_entries"}
        assert t.steps[2:] == w.steps[2:], name
        assert rules.template_problems(t) == [] and rules.template_problems(w) == [], name
        q, _ = plan.sql(t, {"chains": {"value": "follow"}, "through_people": {"value": "near"}}, t.steps[0].view)
        assert all(f"s0.{c} is false" in q for c in ATTENDEE_FILTER), name
        assert os.path.exists(os.path.join(t.folder, "limits.md"))


def test_an_attendee_scan_missing_a_flag_the_crown_filter_or_the_organisation_join_is_caught():
    import dataclasses
    for name in ATTENDEE_SCANS:
        t = tpl.by_name(name)
        first, company = t.steps[0], t.steps[1]
        for drop in ATTENDEE_FILTER:
            bad = dataclasses.replace(first, where=tuple((c, v) for c, v in first.where if c != drop))
            assert attendee_scan_problems(dataclasses.replace(t, steps=(bad,) + t.steps[1:])), (name, drop)
        carried = dataclasses.replace(first, columns=first.columns + ("attendee",))
        assert attendee_scan_problems(dataclasses.replace(t, steps=(carried,) + t.steps[1:]))
        whole = dataclasses.replace(company, on=("attendee", "name"))
        assert attendee_scan_problems(dataclasses.replace(t, steps=(first, whole) + t.steps[2:]))
