-- registers/limited_partnerships: what later modules read (plan 5.3, use case 13). Every registered limited
-- partnership the Companies Office's file names, as the NZBN register last answered for it, with its registered
-- office (a partnership's office is shown, as a company's is); and its general partners, a person or a body as the
-- register states it. No partner's address of any kind is on a view (hard limit 15): they stay in
-- limited_partnerships_private. A name the register withholds is blanked on every view; the row stays (hard limit
-- 16). A partner's start and end are the register's own; the interface states none, so `dates_stated` says so and
-- `asked_on` is only the day the register was asked. Limited partners are not public and are not here. Run by a
-- session only against its scratch schema (the tests rewrite `pub.`).
CREATE OR REPLACE VIEW pub.limited_partnerships AS
SELECT p.key, p.nzbn, p.number, p.name, p.name_withheld, p.kind, p.type_description, p.status, p.registered_on,
       p.country_of_origin, p.registered_office, p.office_since, p.asked_on,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM limited_partnerships.partnerships p;

CREATE OR REPLACE VIEW pub.limited_partnership_partners AS
SELECT g.key, g.partnership_key, g.nzbn, g.kind,
       CASE WHEN g.suppressed THEN 'name withheld by the register' ELSE g.full_name END AS full_name,
       CASE WHEN g.suppressed THEN NULL ELSE g.first_name END AS first_name,
       CASE WHEN g.suppressed THEN NULL ELSE g.middle_names END AS middle_names,
       CASE WHEN g.suppressed THEN NULL ELSE g.last_name END AS last_name,
       g.body_nzbn, g.suppressed, g.current, g.status, g.started_on, g.ended_on, g.dates_stated, g.asked_on,
       g.document, g.page, g.place, g.read_from, g.reader, g.profile, g.profile_version, g.loaded_at
FROM limited_partnerships.partners g;
