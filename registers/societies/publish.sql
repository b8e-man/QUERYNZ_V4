-- registers/societies: what later modules read. Every incorporated society the register names, its earlier states,
-- and its officers with the register's own window and the days they were read. No address is a column of any view:
-- an officer's address would live in societies_private, which nothing here reads (hard limit 15). A suppressed
-- name is blanked on every view; the row stays (hard limit 16).
CREATE OR REPLACE VIEW pub.societies AS
SELECT key, nzbn, number, name, status, registered_on, removed_on, act, reregistered_on, charity_number, in_latest,
       last_file, party_society, source_note, document, page, place, read_from, reader, profile, profile_version,
       loaded_at
FROM societies.societies;

CREATE OR REPLACE VIEW pub.society_states AS
SELECT key, society_key, file, name, status, registered_on, removed_on,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM societies.society_states;

CREATE OR REPLACE VIEW pub.society_officers AS
SELECT key, society_key, nzbn,
       CASE WHEN suppressed THEN NULL ELSE first_name END AS first_name,
       CASE WHEN suppressed THEN NULL ELSE middle_names END AS middle_names,
       CASE WHEN suppressed THEN NULL ELSE last_name END AS last_name,
       CASE WHEN suppressed THEN 'name suppressed' ELSE full_name END AS full_name,
       role_type, role_status, started_on, ended_on, first_read_on, last_read_on, suppressed, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM societies.officers;
