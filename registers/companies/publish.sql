-- registers/companies: what later modules read. Every entity the monthly files name, its earlier states, its
-- directors and shareholders with the files that list them, and its registered office (a company's registered
-- address is shown: hard limit 15). No person's residential address is a column of any view: it would live in
-- companies_private, which nothing here reads. A suppressed name is blanked on every view; the row stays.
CREATE OR REPLACE VIEW pub.companies AS
SELECT key, register, nzbn, number, name, entity_type, status, registered_on, removed_on, in_latest, first_file,
       last_file, extra, source_note, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.entities;

CREATE OR REPLACE VIEW pub.company_states AS
SELECT key, entity_key, file, name, entity_type, status, registered_on, removed_on,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.entity_states;

CREATE OR REPLACE VIEW pub.directors AS
SELECT key, entity_key, nzbn, company_number,
       CASE WHEN suppressed THEN NULL ELSE first_name END AS first_name,
       CASE WHEN suppressed THEN NULL ELSE middle_names END AS middle_names,
       CASE WHEN suppressed THEN NULL ELSE last_name END AS last_name,
       CASE WHEN suppressed THEN 'name suppressed' ELSE full_name END AS full_name,
       role_type, appointed_on, ended_on, in_latest, first_file, last_file, suppressed, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.directors;

CREATE OR REPLACE VIEW pub.shareholders AS
SELECT key, entity_key, nzbn, company_number, shareholder_type,
       CASE WHEN suppressed THEN 'name suppressed' ELSE name END AS name,
       holder_nzbn, shares, allocation_status, in_latest, first_file, last_file, suppressed, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.shareholders;

CREATE OR REPLACE VIEW pub.company_addresses AS
SELECT key, entity_key, register, 'registered office'::text AS kind, started_on, care_of, line_1, line_2, line_3,
       line_4, postcode, country, in_latest, last_file, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.registered_offices;
