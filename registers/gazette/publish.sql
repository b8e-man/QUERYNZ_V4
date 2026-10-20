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

-- a person named by a notice that was later revoked is not shown: one such notice was revoked because it named
-- the wrong person. The row stays, with what revoked it.
CREATE OR REPLACE VIEW pub.gazette_prohibitions AS
SELECT key, notice, published_on, action,
       CASE WHEN superseded_how IN ('revoked', 'revoked and replaced') THEN NULL ELSE name END AS name,
       CASE WHEN superseded_how IN ('revoked', 'revoked and replaced') THEN NULL ELSE also_known_as END AS also_known_as,
       named_twice, statute, months, permanent, starts_on, starts_basis, ends_on, dated_on, supersedes, superseded_by,
       superseded_how, ordinal, document, page, place, read_from, reader, profile, profile_version, loaded_at
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

-- a bankrupt by name, the kind of notice and its day; never an address (gazette_private). A person an annulment names
-- is withheld on every row that names them as bankrupt before it: the row stays, with the annulment's number
CREATE OR REPLACE VIEW pub.gazette_bankruptcies AS
SELECT key, notice, published_on, kind, shape,
       CASE WHEN withheld_by IS NULL THEN surname END AS surname,
       CASE WHEN withheld_by IS NULL THEN given_names END AS given_names,
       CASE WHEN withheld_by IS NULL THEN also_known_as END AS also_known_as,
       CASE WHEN withheld_by IS NULL THEN occupation END AS occupation,
       event_on, event_at, court, statute, dated_on, withheld_by, ordinal, document, page, place, read_from, reader,
       profile, profile_version, loaded_at
FROM gazette.bankruptcies;

-- appointments to public office: the person by name as printed, the office, who appointed and the term
CREATE OR REPLACE VIEW pub.gazette_appointments AS
SELECT key, notice, published_on, body, name, role, statute, by_whom, starts_on, ends_on, dated_on, corrigendum, ordinal,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM gazette.appointments;

-- a mortgagee's entry into possession: the lender and a company borrower by name, land or goods, the day; never the
-- property, a registration number or a person's name (gazette_private)
CREATE OR REPLACE VIEW pub.gazette_possessions AS
SELECT key, notice, published_on, action, asset, statute, mortgagee, mortgagee_kind, mortgagee_number, mortgagee_register_key,
       mortgagee_register_match, mortgagor, mortgagor_kind, mortgagor_number, mortgagor_register_key, mortgagor_register_match,
       entered_on, entered_basis, dated_on, corrigendum, property_held, document, page, place, read_from, reader, profile,
       profile_version, loaded_at
FROM gazette.possessions;
