-- registers/overseas_investment: what later modules read (plan 5.3, use case 12). The Overseas Investment Office's
-- decision summaries from 2017 (ruling 71), one row per summary page any finished pass listed (one the office takes
-- down stays, with `taken_down_on`), and one row per applicant (or consent holder) and vendor the summary names, as
-- the office publishes them. The investment statement is as published, its land addresses whole (ruling 143), with
-- `addresses_named` (the street addresses and legal descriptions its shape names) beside it, the flag every product
-- applies hard limit 15 by. A name the office withholds is flagged, its ownership origins shown; what the cell prints
-- in its place is in overseas_investment_private (ruling 142).
-- Crown copyright, CC BY 4.0: every surface that shows a row attributes it (`attribution`).
CREATE OR REPLACE VIEW pub.overseas_investment_decisions AS
SELECT d.key, d.case_number, d.case_numbers, d.kind, d.outcome, d.granted, d.section, d.decision_maker, d.decided_on,
       d.pathway, d.investment_class, d.investment, d.addresses_named, d.areas_stated, d.area_ha,
       d.consideration_heading, d.consideration_stated, d.consideration_nzd, d.consideration_withheld,
       d.penalty_stated, d.notification_number, d.parent_case, d.applicant_listed, d.rationale, d.rationale_names_address, d.headings, d.url,
       d.taken_down_on,
       'Toitū Te Whenua Land Information New Zealand, CC BY 4.0'::text AS attribution,
       d.document, d.page, d.place, d.read_from, d.reader, d.profile, d.profile_version, d.loaded_at
FROM overseas_investment.decisions d;

CREATE OR REPLACE VIEW pub.overseas_investment_parties AS
SELECT p.key, p.decision_key, p.ordinal, p.role, p.role_stated,
       CASE WHEN p.withheld THEN 'name withheld' ELSE p.name END AS name,
       p.withheld, p.withheld_by, p.status, p.trust, p.organisation, p.company_number, p.ownership_lines,
       p.origins, p.shares, p.ownership_scope,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at,
       (SELECT d.decided_on FROM overseas_investment.decisions d WHERE d.key = p.decision_key) AS decided_on   -- the decision's own date, for a report (1 November 2026)
FROM overseas_investment.parties p;
