-- registers/courts: the published views, the only thing a later module reads (contract: the lane).
-- A withheld name is NULL in courts.judgment_parties already; the view never joins courts_private.
-- No address is read from a judgment (hard limit 15); no suppressed name is published (hard limit 16).

CREATE OR REPLACE VIEW pub.court_judgments AS
SELECT key, citation, court, court_name, registry, case_numbers, judgment_date, judges, heading, outcome,
       paragraphs, parties, suppression, suppression_kinds, withheld IS NOT NULL AS names_withheld, status, missing,
       source, source_url, document, page, place, read_from, reader, profile, profile_version, loaded_at
  FROM courts.judgments;

CREATE OR REPLACE VIEW pub.court_judgment_parties AS
SELECT p.key, p.judgment, p.citation, j.court, j.judgment_date, p.position, p.role,
       CASE WHEN p.withheld THEN NULL ELSE p.name END AS name,
       p.withheld, p.anonymised, p.crown, p.confidence,
       CASE WHEN p.withheld THEN NULL ELSE p.capacity END AS capacity,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
  FROM courts.judgment_parties p
  JOIN courts.judgments j ON j.key = p.judgment;
