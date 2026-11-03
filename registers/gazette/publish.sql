-- registers/gazette: what later modules read. Every notice held, typed, with its address; the celebrants read
-- from the Registrar-General's lists. The notice text is never published (bankruptcy and prohibition notices print
-- home addresses), and no address column is: an independent celebrant's address stays in gazette_private.
-- Every text published here is cut before any street address or property reference it names (cut.py, at the read);
-- the uncut value is in gazette_private.uncut only.
CREATE OR REPLACE VIEW pub.gazette_notices AS
SELECT key, notice, year, section, number, family, format, status, records, supersedes, title, published_on, url, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.notices;

CREATE OR REPLACE VIEW pub.gazette_celebrants AS
SELECT key, notice, published_on, action, statute, period_from, period_to, surname, given_names, organisation,
       list_shape, marks, split, ordinal, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.celebrants;

-- a person named by a notice that was later revoked: the name stays, with what revoked it and how (superseded_how,
-- superseded_in_error) as the flag; one such notice was revoked because it named the wrong person (ruling 142)
CREATE OR REPLACE VIEW pub.gazette_prohibitions AS
SELECT key, notice, published_on, action,
       name, also_known_as,
       named_twice, statute, months, permanent, starts_on, starts_basis, ends_on, dated_on, supersedes, superseded_by,
       superseded_how, superseded_in_error, ordinal, document, page, place, read_from, reader, profile, profile_version,
       loaded_at
FROM gazette.prohibitions;

CREATE OR REPLACE VIEW pub.gazette_liquidations AS
SELECT key, notice, published_on, company, company_number, shape, appointed_by, statute, appointed_on, appointed_at,
       date_basis, dated_on, corrigendum, liquidators, register_key, register_match, ordinal, document, page, place,
       read_from, reader, profile, profile_version, loaded_at
FROM gazette.liquidations;

CREATE OR REPLACE VIEW pub.gazette_liquidators AS
SELECT key, notice, published_on, name, role, named_in_body, companies, ordinal, document, page, place, read_from, reader,
       profile, profile_version, loaded_at
FROM gazette.liquidators;

-- removals (ds), winding-up applications (aw), receiverships (ar), notices to creditors (md), administrations (aa) and the rest:
-- one row per company named, with the register's entity; a plaintiff by name only, never its address for service; a
-- rectification's people by initials and surname only; role and people_named last, added by gazette-5
CREATE OR REPLACE VIEW pub.gazette_company_notices AS
SELECT key, notice, published_on, kind, action, company, company_number, shape, statute, ground, by_whom, party, event_on,
       event_at, event_basis, filed_on, court, reference, dated_on, corrigendum, people, register_key, register_match, ordinal,
       document, page, place, read_from, reader, profile, profile_version, loaded_at, role, people_named
FROM gazette.company_notices;

CREATE OR REPLACE VIEW pub.gazette_practitioners AS
SELECT key, notice, published_on, name, role, named_in_body, companies, ordinal, document, page, place, read_from, reader,
       profile, profile_version, loaded_at
FROM gazette.practitioners;

-- a bankrupt by name, the kind of notice and its day; the address in gazette_private. A person an annulment names is
-- flagged on every row that names them as bankrupt before it by the annulment's number (withheld_by; ruling 142)
CREATE OR REPLACE VIEW pub.gazette_bankruptcies AS
SELECT key, notice, published_on, kind, shape,
       surname, given_names, also_known_as, occupation,
       event_on, event_at, court, statute, dated_on, withheld_by, ordinal, document, page, place, read_from, reader,
       profile, profile_version, loaded_at
FROM gazette.bankruptcies;

-- appointments to public office: the person by name as printed, the office, who appointed and the term
CREATE OR REPLACE VIEW pub.gazette_appointments AS
SELECT key, notice, published_on, body, name, role, statute, by_whom, starts_on, ends_on, dated_on, corrigendum, ordinal,
       document, page, place, read_from, reader, profile, profile_version, loaded_at, action, locality, appointee_kind
FROM gazette.appointments;

-- a school board put under a limited statutory manager, that direction amended or revoked, or the board dissolved and a
-- commissioner directed (offices.py, 2 November 2026)
CREATE OR REPLACE VIEW pub.gazette_board_interventions AS
SELECT key, notice, published_on, action, board, institution_number, statute, directed_by, dated_on, names_notices,
       revoked_by, corrigendum, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.board_interventions;

-- a mortgagee's entry into possession: the lender and a company borrower by name, land or goods, the day; never the
-- property, a registration number or a person's name (gazette_private)
CREATE OR REPLACE VIEW pub.gazette_possessions AS
SELECT key, notice, published_on, action, asset, statute, mortgagee, mortgagee_kind, mortgagee_number, mortgagee_register_key,
       mortgagee_register_match, mortgagor, mortgagor_kind, mortgagor_number, mortgagor_register_key, mortgagor_register_match,
       entered_on, entered_basis, dated_on, corrigendum, property_held, document, page, place, read_from, reader, profile,
       profile_version, loaded_at
FROM gazette.possessions;
