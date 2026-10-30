-- registers/beehive: what later modules read. Every release, speech and feature of the ingest MCP's beehive
-- corpus, with the ministers and portfolios the site tags it with. Each row cites its document (the record's
-- hash) and the page's own address. The body and text are never published (beehive_private.texts; the board
-- opens the document whole, ruling 88).
CREATE OR REPLACE VIEW pub.beehive_releases AS
SELECT r.key, r.url AS citation_url, r.type, r.kind, r.title, r.published_at, r.published_on, r.word_count,
       ARRAY(SELECT m.name FROM beehive.release_ministers m WHERE m.release = r.key ORDER BY m.ordinal) AS ministers,
       r.portfolios, r.topics, r.quotes, r.versions, r.origin, r.mcp_state, r.mcp_document, r.updated_at,
       r.captured_at, r.capture_status, r.captured_sha256, r.model AS source_model, r.annotation_fields, r.source_note,
       r.reading, r.summary, r.names, r.read_model,
       r.document, r.page, r.place, r.read_from, r.reader, r.profile, r.profile_version, r.loaded_at
FROM beehive.releases r;

-- every person and body the text reader found a release naming, with the role the text gives it: a name as the
-- document prints it, never a link, never a claim; the rows the links lane reads (ruling 123). The site's tagged
-- ministers are pub.beehive_release_ministers and are not here
CREATE OR REPLACE VIEW pub.beehive_people AS
SELECT p.key, p.name, p.kind, p.role, p.role_text, p."of", p.release, p.published_on, p.type, r.title, r.url AS citation_url,
       p.document, p.page, p.place, p.read_from, p.reader, p.model, p.profile, p.profile_version, p.loaded_at
FROM beehive.people p
JOIN beehive.releases r ON r.key = p.release;

COMMENT ON VIEW pub.beehive_people IS
  'Every person and body the text reader found a Beehive release naming, as printed, with the role the text gives it (Arthur, 31 October 2026): never a link, never a claim.';

CREATE OR REPLACE VIEW pub.beehive_release_ministers AS
SELECT m.key, m.release, m.ordinal, m.name, m.slug, r.published_on, r.type, r.title, r.url AS citation_url,
       m.document, m.page, m.place, m.read_from, m.reader, m.profile, m.profile_version, m.loaded_at
FROM beehive.release_ministers m
JOIN beehive.releases r ON r.key = m.release;

-- the source's own annotation, not ours: topics and quotes the provider's model made off-estate. Shown as theirs,
-- marked model-made; never read into a claim or a link (ruling 96)
CREATE OR REPLACE VIEW pub.beehive_release_annotations AS
SELECT t.key, t.release, 'topic'::text AS annotation, t.ordinal, t.topic AS value, NULL::text AS speaker,
       t.model_made, t.made_by, r.published_on, r.url AS citation_url,
       t.document, t.page, t.place, t.read_from, t.reader, t.profile, t.profile_version, t.loaded_at
FROM beehive.release_topics t
JOIN beehive.releases r ON r.key = t.release
UNION ALL
SELECT q.key, q.release, 'quote'::text, q.ordinal, q.quote, q.speaker,
       q.model_made, q.made_by, r.published_on, r.url,
       q.document, q.page, q.place, q.read_from, q.reader, q.profile, q.profile_version, q.loaded_at
FROM beehive.release_quotes q
JOIN beehive.releases r ON r.key = q.release;

COMMENT ON VIEW pub.beehive_release_annotations IS
  'The query-nz provider''s model-made topics and quotes for each Beehive release, kept as the source''s annotation: never a claim or a link (ruling 96).';
