-- registers/charities_b: what later modules read, once this build is the one kept (plan 4.1; load.KEPT).
-- Every charity on the register with its register's own number as the key; its officers with their role,
-- window, status and the register's disqualification status; its annual returns' period, tier, currency,
-- audit opinion and financial fields (ruling of 14 August 2026). Each row carries its citation: the page's
-- sha256 and the row's key in it. The one address is a charity's own address for service, as the register
-- publishes it, like a company's registered office (hard limit 15; the legal position, question 4). No
-- officer has an address, a birth date, an email or a phone on any table here. Run by a session only
-- against its scratch schema (the tests rewrite `pub.`).
CREATE OR REPLACE VIEW pub.charities AS
SELECT key, number, name, other_names, status, registered_on, deregistered_on, deregistration_reason,
       legal_structure, legal_structure_other, charitable_purpose, main_sector, main_activity, main_beneficiary,
       address_for_service, group_key, group_number, group_name, nzbn, incorporation_number, year_end_month,
       year_end_day, annual_return_due_on, source_modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_b.charities;

CREATE OR REPLACE VIEW pub.charity_officers AS
SELECT key, charity_key, kind, full_name, first_name, middle_name, last_name, role, started_on, ended_on, status,
       disqualified, source_modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_b.officers;

CREATE OR REPLACE VIEW pub.charity_returns AS
SELECT key, charity_key, group_key, period_end, months_covered, began_on, tier, currency, audited, modified_opinion,
       opinion, total_gross_income, total_expenditure, net_surplus, total_assets, total_liabilities, total_equity,
       figures, material_expenses, source_modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_b.returns;
