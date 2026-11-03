-- registers/hdc_decisions: what later modules read (plan 5.3, use case 11, healthcare operator governance). The
-- Health and Disability Commissioner's published decisions and case studies from 2017 (ruling 71), one row per page
-- the Commissioner has listed (one it takes down stays, with taken_down_on; ruling 142), and one row per provider
-- organisation a page names, as the Commissioner names it. Kept in hdc_decisions_private and never on a view: the
-- page's heading (it describes the consumer's care), the parties block as printed, an individual practitioner's
-- name (a named individual is a role and the naming policy's ground here), every value the consumer-detail guard
-- leaves off, and a case study's own address (its slug is its summary). A finding is the Commissioner's opinion under the Code of
-- Health and Disability Services Consumers' Rights, not a court's.
CREATE OR REPLACE VIEW pub.hdc_decisions AS
SELECT d.key, d.kind_of_page, d.case_number, d.case_numbers, d.web_id, d.decided_on, d.kind, d.findings,
       d.provider_kinds, d.occupations, d.rights_tagged, d.rights_breached, d.recommendation_headings,
       d.recommended_to, d.named_roles, d.naming_grounds, d.names_removed, d.providers_named, d.url, d.taken_down_on,
       d.document, d.page, d.place, d.read_from, d.reader, d.profile, d.profile_version, d.loaded_at
FROM hdc_decisions.decisions d;

CREATE OR REPLACE VIEW pub.hdc_decision_providers AS
SELECT p.key, p.decision_key, p.ordinal, p.name, p.abbreviation, p.also_called, p.found_by, p.findings,
       p.rights_breached, p.recommended, p.company_number, p.charity_number, p.decided_on,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM hdc_decisions.providers p;
