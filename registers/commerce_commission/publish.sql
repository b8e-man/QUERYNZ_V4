-- registers/commerce_commission: what later modules read (plan 5.3, use cases 5, 6 and 7). The Commerce Commission's
-- case register, one row per entry the Commission lists today (a case it takes off the register leaves the views at
-- the next load), and one row per party the entry names, as the Commission publishes it. A name the Commission
-- withholds ('Withheld'), or one a page states is suppressed, is withheld on every view: the row stays, the name, the
-- heading and the page address (which carry it) do not (hard limit 16). No address of any kind (hard limit 15). An
-- open case is an investigation or an application, not a finding: "only a court can make that determination".
CREATE OR REPLACE VIEW pub.commerce_commission_cases AS
SELECT c.key, c.case_number,
       CASE WHEN c.title_withheld THEN 'name withheld by the Commission' ELSE c.title END AS title,
       c.title_withheld, c.category AS kind, c.sub_category, c.act_section, c.acts, c.sections, c.industry, c.status,
       c.outcome, c.opened_on, c.closed_on, c.action_on, c.url,
       c.document, c.page, c.place, c.read_from, c.reader, c.profile, c.profile_version, c.loaded_at
FROM commerce_commission.cases c;

CREATE OR REPLACE VIEW pub.commerce_commission_parties AS
SELECT p.key, p.case_key, p.ordinal,
       CASE WHEN p.withheld THEN 'name withheld' ELSE p.name END AS name,
       p.trading_as, p.withheld, p.withheld_by, p.organisation, p.company_number, p.split_from,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM commerce_commission.parties p;
