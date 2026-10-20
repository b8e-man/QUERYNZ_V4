-- registers/charities_a: what later modules read, as the charities spec names them: `pub.charities`,
-- `pub.charity_officers`, `pub.charity_returns` (and `pub.charity_groups`), each row with its citation. Run against
-- this build's schema in a scratch or staging schema only, until the build is kept (plan 4.1): the views then move
-- with the tables to the `charities` schema. No view carries an officer's address, birth date or contact detail
-- (the feed holds none); an organisation's address for service is the register's own, like a registered office.
-- A suppressed name is blanked on every view; the row stays (hard limit 16).
CREATE OR REPLACE VIEW pub.charities AS
SELECT key, charity_number, organisation_id, nzbn, companies_office_number, name, other_names, status, registered_on,
       deregistered_on, deregistration_reason, legal_structure, legal_structure_other, main_activity, main_sector,
       main_beneficiary, activities, sectors, beneficiaries, areas_of_operation, sources_of_funds, charitable_purpose,
       address_for_service, postal_address, year_end_day, year_end_month, group_key, group_name, group_type, modified_at,
       lists_document, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_a.charities;

CREATE OR REPLACE VIEW pub.charity_officers AS
SELECT key, officer_id, charity_key, charity_number,
       CASE WHEN suppressed THEN NULL ELSE first_name END AS first_name,
       CASE WHEN suppressed THEN NULL ELSE middle_names END AS middle_names,
       CASE WHEN suppressed THEN NULL ELSE last_name END AS last_name,
       CASE WHEN suppressed THEN 'name suppressed' ELSE full_name END AS full_name,
       body_corporate, CASE WHEN suppressed THEN NULL ELSE body_corporate_name END AS body_corporate_name, name_note,
       role, status, started_on, ended_on, disqualified, disqualification, suppressed, modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_a.charity_officers;

CREATE OR REPLACE VIEW pub.charity_returns AS
SELECT key, annual_return_id, charity_key, charity_number, group_key, period_ended_on, as_at_on, covers_months, tier,
       currency, audited, audit_opinion_modified, audit_opinion, withheld,
       total_gross_income, total_expenditure, net_surplus_deficit, surplus_deficit, total_assets, total_liabilities,
       total_equity, total_assets_less_liabilities, current_assets, non_current_assets, current_liabilities,
       non_current_liabilities, cash_and_bank, investments, land, buildings, land_and_buildings, property_plant_equipment,
       loans_and_borrowings, general_accumulated_funds, restricted_purpose_funds, endowment_funds, reserves,
       accumulated_surplus, donations_koha, bequests, membership_fees, government_grants_contracts,
       government_service_delivery_grants, non_government_service_delivery_grants, service_delivery_grants,
       general_grants_received, capital_grants_and_donations, other_grants_and_sponsorship, grants_from_government,
       grants_from_other_sources, service_trading_income, commercial_revenue, interest_or_dividends,
       other_investment_income, new_zealand_dividends, all_other_income, grants_paid_within_nz, grants_paid_outside_nz,
       grants_or_donations_paid, grants_and_donations_made, salaries_and_wages, employee_remuneration, volunteer_expenses,
       fundraising_expenses, cost_of_trading, cost_of_service_provision, depreciation, interest_paid, all_other_expenditure,
       total_operating_expenditure, fulltime_employees, parttime_employees, paid_hours_per_week, volunteers_per_week,
       volunteer_hours_per_week, figures, modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_a.charity_returns;

CREATE OR REPLACE VIEW pub.charity_groups AS
SELECT key, group_id, registration_number, name, other_names, group_type, status, registered_on, deregistered_on,
       main_activity, main_sector, main_beneficiary, address_for_service, postal_address, modified_at,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM charities_a.charity_groups;
