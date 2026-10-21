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

-- ── company monitoring (plan 5.5; monitor.py) ────────────────────────────────────────────────────────────────
-- Each dated difference between an answer of the NZBN register's interface and the state held before it. A
-- registered office is a company's or society's (shown: hard limit 15); no person's address is a change. A
-- suppressed name is blanked in the subject and in before and after; the row stays (hard limit 16).
CREATE OR REPLACE VIEW pub.company_changes AS
SELECT key, entity_key, nzbn, kind,
       CASE WHEN suppressed THEN 'name suppressed' ELSE subject END AS subject,
       CASE WHEN suppressed AND kind <> 'registered_office' THEN NULL ELSE before END AS before,
       CASE WHEN suppressed AND kind <> 'registered_office' THEN NULL ELSE after END AS after,
       effective_on, date_basis, seen_on, register_updated_on, compared_with, previous_document, held_key,
       suppressed, source_note, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.changes;

-- every entity as the interface last answered it, sole traders, partnerships and trusts among them
CREATE OR REPLACE VIEW pub.company_lookups AS
SELECT key, entity_key, nzbn, kind, entity_type, type_description, name, status, registered_on,
       register_updated_on, trading_names, asked_at, in_monthly, source_note,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM companies.lookups WHERE latest;

-- the roles of the last answer, with the interface's own end dates; `held_key` joins pub.directors
CREATE OR REPLACE VIEW pub.company_lookup_roles AS
SELECT r.key, r.entity_key, r.nzbn, r.role_uid, r.role_type, r.role_status,
       CASE WHEN r.suppressed THEN NULL ELSE r.first_name END AS first_name,
       CASE WHEN r.suppressed THEN NULL ELSE r.middle_names END AS middle_names,
       CASE WHEN r.suppressed THEN NULL ELSE r.last_name END AS last_name,
       CASE WHEN r.suppressed THEN 'name suppressed' ELSE r.full_name END AS full_name,
       r.is_body, r.body_nzbn, r.started_on, r.ended_on, r.held_key, r.suppressed, r.source_note,
       r.document, r.page, r.place, r.read_from, r.reader, r.profile, r.profile_version, r.loaded_at
FROM companies.lookup_roles r JOIN companies.lookups l ON l.key = r.answer_key AND l.latest;

-- the holdings of the last answer, current and historic (a historic one with the interface's end)
CREATE OR REPLACE VIEW pub.company_lookup_holdings AS
SELECT h.key, h.entity_key, h.nzbn, h.holder_type,
       CASE WHEN h.suppressed THEN 'name suppressed' ELSE h.name END AS name,
       h.holder_nzbn, h.shares, h.allocation, h.started_on, h.ended_on, h.current, h.suppressed, h.source_note,
       h.document, h.page, h.place, h.read_from, h.reader, h.profile, h.profile_version, h.loaded_at
FROM companies.lookup_holdings h JOIN companies.lookups l ON l.key = h.answer_key AND l.latest;

-- the hand-off (design, products rule 2: a product never writes into the estate). Two functions this lane
-- owns, run with the lane's rights, each writing one queue row; the asker is the database login
-- (session_user), never an argument a caller can type. The product reader may execute them; nothing else is
-- granted on the lane's tables. They return the request's id, or nothing.
CREATE OR REPLACE FUNCTION pub.request_company_check(p_nzbn text, p_name text, p_product text) RETURNS bigint
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
    INSERT INTO companies.requests (nzbn, name, product, asked_by)
    VALUES (nullif(btrim(p_nzbn), ''), nullif(btrim(p_name), ''), p_product, session_user)
    RETURNING id
$$;

CREATE OR REPLACE FUNCTION pub.watch_company(p_nzbn text, p_product text, p_every_days integer DEFAULT 7)
RETURNS void LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
    INSERT INTO companies.watch (nzbn, product, asked_by, every_days)
    VALUES (btrim(p_nzbn), p_product, session_user, p_every_days)
    ON CONFLICT (nzbn, product) DO UPDATE SET active = true, every_days = excluded.every_days,
        asked_by = excluded.asked_by, asked_at = now()
$$;

CREATE OR REPLACE FUNCTION pub.unwatch_company(p_nzbn text, p_product text) RETURNS void
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS $$
    UPDATE companies.watch SET active = false WHERE nzbn = btrim(p_nzbn) AND product = p_product
$$;

REVOKE ALL ON FUNCTION pub.request_company_check(text, text, text) FROM PUBLIC;
REVOKE ALL ON FUNCTION pub.watch_company(text, text, integer) FROM PUBLIC;
REVOKE ALL ON FUNCTION pub.unwatch_company(text, text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION pub.request_company_check(text, text, text) TO qv4_product;
GRANT EXECUTE ON FUNCTION pub.watch_company(text, text, integer) TO qv4_product;
GRANT EXECUTE ON FUNCTION pub.unwatch_company(text, text) TO qv4_product;
