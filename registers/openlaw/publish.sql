-- registers/openlaw: what later modules read (plan 5.4 item 1). Every case OpenLaw NZ holds that the capture landed,
-- keyed by the interface's own id; its parties by role; the citation graph; the statute links. Each row carries its
-- citation: the page's sha256, the place of the record in it, the reader and the profile.
--
-- A court's suppression order binds every surface (hard limit 16): a case whose text or title carries a suppression
-- or anonymisation marker, or names an anonymised party, shows no title, and every party of it but the Crown shows no
-- name; the rows, the roles and the case stay. Names and titles come from openlaw_private, joined here and nowhere
-- else. No address is held (hard limit 15). Held until OpenLaw authorises copies (API terms 3.6(a)): nothing is
-- published from this file before then. Run by a session only against its scratch schema (the tests rewrite `pub.`).
CREATE OR REPLACE VIEW pub.court_cases AS
SELECT c.key, c.openlaw_id, c.citation, c.citations, c.court, c.court_name, c.registry, c.filing_number, c.decided_on,
       CASE WHEN c.suppressed THEN NULL ELSE t.title END AS title,
       c.suppressed, c.suppression_marks, c.pdf_url, c.parties_from, c.source_modified_at,
       c.document, c.page, c.place, c.read_from, c.reader, c.profile, c.profile_version, c.loaded_at
FROM openlaw.cases c
LEFT JOIN openlaw_private.case_titles t ON t.key = c.key;

CREATE OR REPLACE VIEW pub.court_case_parties AS
SELECT p.key, p.case_key, p.role, p.position,
       CASE WHEN p.withheld THEN NULL ELSE n.name END AS name,
       p.withheld AS name_withheld, p.anonymised, p.crown, p.from_source,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM openlaw.parties p
LEFT JOIN openlaw_private.party_names n ON n.key = p.key;

CREATE OR REPLACE VIEW pub.court_case_citations AS
SELECT key, citing_key, cited_key, citation_count,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM openlaw.citations;

CREATE OR REPLACE VIEW pub.court_case_statutes AS
SELECT key, case_key, legislation_id, legislation_title, legislation_year, section, mentions, extraction_confidence,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM openlaw.statutes;
