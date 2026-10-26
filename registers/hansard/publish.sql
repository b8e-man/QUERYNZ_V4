-- registers/hansard: what later modules read. The old transcripts' rows are "taken from the old estate's tables;
-- original not held" (ruling 96) and cite the export's hash (`document`), the sitting day and section (`place`) and
-- the page's own address (`url`). The speaker labels, member ids and roster names are as the old estate read them;
-- no model read anything and nothing here is matched by name. The MCP's rows (hansard-2) cite the landed record's
-- hash and the page's or PDF's address; the day's text is in the private twin, opened whole on the board only.

-- one per sitting day of the old transcripts: the MCP's index fields for its page where the url matches, and the
-- daily PDF's record where the MCP holds the same day
CREATE OR REPLACE VIEW pub.hansard_sittings AS
SELECT s.key, s.sitting_on, s.parliament, s.volume, s.progress, s.url, s.sections, s.turns, s.attributed,
       s.unattributed, s.speakers, s.captured_at,
       i.lastmod AS index_lastmod, i.fetched AS index_fetched, i.index_on, i.document AS index_document,
       CASE WHEN i.lastmod IS NULL THEN NULL
            WHEN s.captured_at IS NULL OR i.lastmod > s.captured_at THEN 'the held text may be older than the page'
            ELSE 'the page has not changed since the old capture' END AS index_note,
       d.document AS day_document, d.pdf_url AS day_pdf_url,
       CASE WHEN d.key IS NULL THEN 'the MCP holds no daily PDF for this day'
            ELSE 'also held as the daily PDF''s text (the MCP)' END AS day_note,
       s.source_note, s.document, s.page, s.place, s.read_from, s.reader, s.profile, s.profile_version, s.loaded_at
FROM hansard.sittings s
LEFT JOIN LATERAL (SELECT * FROM hansard.index_pages p WHERE p.url = s.url
                   ORDER BY p.lastmod DESC NULLS LAST, p.fetched DESC NULLS LAST LIMIT 1) i ON true
LEFT JOIN hansard.days d ON d.key = s.key;

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

-- one per sitting day the MCP holds as a daily PDF read by its provider (pdftotext -layout): the PDF's address and
-- the provider's hash of it, page and word counts, and whether the old transcript also holds the day as sections.
-- No text: the board opens the landed record whole (ruling 88). No speech turns: the provider made no split
CREATE OR REPLACE VIEW pub.hansard_days AS
SELECT d.key, d.sitting_on, d.title, d.pdf_url, d.pdf_sha256, d.captured_at, d.page_count, d.word_count, d.versions,
       s.url AS old_url, d.old_sections, d.old_subjects, d.subjects_in_text,
       CASE WHEN s.key IS NULL THEN 'not held as the old transcript''s sections'
            ELSE 'also held as the old transcript''s sections' END AS old_note,
       d.pdf_url AS citation_url,
       d.source_note, d.document, d.page, d.place, d.read_from, d.reader, d.profile, d.profile_version, d.loaded_at
FROM hansard.days d
LEFT JOIN hansard.sittings s ON s.key = d.key;
