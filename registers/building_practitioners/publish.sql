-- registers/building_practitioners: what later modules read (plan 5.3, use cases 6, 7 and 12). The Building
-- Practitioners Board's published complaint decisions, one row each; and the register of licensed building
-- practitioners, HELD (Building Act 2004, s 307: a search of the register only for a purpose s 299 names; s 308: any
-- other search for personal information is an interference with privacy), so its view is empty and says so by being
-- empty. A suppressed practitioner's name, LBP number and the decision's addresses (which carry the name) are blanked
-- on every view; the row stays (hard limit 16). No address of any kind: a region at most (hard limit 15).
--
-- The window: a decision is shown for three years from its date, the window the register itself keeps for discipline
-- (s 299(a)(iv), s 301(1)(l)(iii)). Older decisions are captured and held, not shown. This is the default of the
-- queue item "how long a Board decision about a named practitioner is shown"; Arthur's ruling changes the interval
-- here, in one place.
CREATE OR REPLACE VIEW pub.building_practitioner_decisions AS
SELECT d.key, d.complaint_number, d.citation, d.decision_kind,
       CASE WHEN d.suppressed THEN 'name withheld by the Board' ELSE d.name END AS name,
       CASE WHEN d.suppressed THEN NULL ELSE d.lbp_number END AS lbp_number,
       d.suppressed, d.region, d.licence_classes, d.decided_on, d.penalties, d.grounds, d.upheld,
       CASE WHEN d.suppressed THEN NULL ELSE d.decision_url END AS decision_url,
       CASE WHEN d.suppressed THEN NULL ELSE d.pdf_url END AS pdf_url,
       d.document, d.page, d.place, d.read_from, d.reader, d.profile, d.profile_version, d.loaded_at
FROM building_practitioners.decisions d
WHERE d.decided_on >= (now() AT TIME ZONE 'Pacific/Auckland')::date - interval '3 years';

CREATE OR REPLACE VIEW pub.building_practitioners AS
SELECT p.key, p.licence_number,
       CASE WHEN p.suppressed THEN 'name withheld by the register' ELSE p.name END AS name,
       p.suppressed, p.licence_classes, p.status, p.area,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM building_practitioners.practitioners p;
