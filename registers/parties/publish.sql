-- registers/parties: what later modules read. One row per registration (a registration is the party; a renamed
-- party is the same party), every name it has carried with its window, and the notices' resolutions. No contact
-- line: the secretary's address, telephone and email stay in parties_private.
CREATE OR REPLACE VIEW pub.parties AS
SELECT key, document, page, place, name, first_name, registered_on, notice_registered_on, registered_by,
       registered_basis, cancelled_on, status, on_register, register_seen_on, off_register_by, page_basis, "window",
       abbreviation, abbreviation_on_ballot, components, logo_registered_on, statement_deadline, audit, website,
       rules_title, rules_href, secretary, register_document, register_place, cancelled_document, cancelled_place,
       same_name_as, same_name_note, read_from, reader, profile, profile_version, loaded_at
FROM parties.registrations;

CREATE OR REPLACE VIEW pub.party_names AS
SELECT key, party, name, name_key, kind, from_on, to_on, basis, document, page, place,
       read_from, reader, profile, profile_version, loaded_at
FROM parties.names;

CREATE OR REPLACE VIEW pub.party_events AS
SELECT key, notice, published_on, decided_on, kind, party_label, new_name, abbreviation, old_abbreviation, ref,
       party, url, title, source_note, gazette_key, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM parties.events;

-- every party label the other lanes publish, resolved to a registration by name and window; join on
-- (label, "on"): "on" is the filing's day as YYYY-MM-DD, or its year as YYYY where the lane keeps only the year
CREATE OR REPLACE VIEW pub.party_labels AS
SELECT key, label, "on", grain, party, party_name, basis, why, same_name, sources, rows, resolver,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM parties.labels;
