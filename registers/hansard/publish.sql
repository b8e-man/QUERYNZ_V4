-- registers/hansard: what later modules read. Every row is "taken from the old estate's tables; original not held"
-- (ruling 96) and cites the export's hash (`document`), the sitting day and section (`place`) and the page's own
-- address (`url`). The speaker labels, member ids and roster names are as the old estate read them; no model read
-- anything and nothing here is matched by name.

-- one per sitting day, with the MCP's index fields for its page where hansard-2 has joined them by url (null until then)
CREATE OR REPLACE VIEW pub.hansard_sittings AS
SELECT s.key, s.sitting_on, s.parliament, s.volume, s.progress, s.url, s.sections, s.turns, s.attributed,
       s.unattributed, s.speakers,
       i.lastmod AS index_lastmod, i.fetched AS index_fetched, i.index_on, i.document AS index_document,
       s.source_note, s.document, s.page, s.place, s.read_from, s.reader, s.profile, s.profile_version, s.loaded_at
FROM hansard.sittings s
LEFT JOIN LATERAL (SELECT * FROM hansard.index_pages p WHERE p.url = s.url
                   ORDER BY p.lastmod DESC NULLS LAST, p.fetched DESC NULLS LAST LIMIT 1) i ON true;

-- one per section of a day's transcript, with its text as captured
CREATE OR REPLACE VIEW pub.hansard_sections AS
SELECT key, sitting_on, section_index, parliament, volume, proceeding, subject, bill_title, bill_id, progress,
       text, chars, turns, url,
       source_note, document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM hansard.sections;

-- one per speech turn: who spoke (Parliament's member id and the old roster's name, or only a role such as the
-- Speaker), when, on what, in what order, with the citation
CREATE OR REPLACE VIEW pub.hansard_speeches AS
SELECT t.key, t.sitting_on, t.section_index, t.ordinal, t.member_id, t.roster_name AS member_name,
       t.label AS label_as_read, t.role, s.proceeding, s.subject, s.bill_title, s.bill_id, s.progress, s.url,
       t.source_note, t.document, t.page, t.place, t.read_from, t.reader, t.profile, t.profile_version, t.loaded_at
FROM hansard.turns t
JOIN hansard.sections s ON s.key = t.section;
