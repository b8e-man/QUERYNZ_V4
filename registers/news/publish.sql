-- registers/news: what the board reads of the news read (Arthur, 26 November 2026: "a list of read news articles
-- sortable by article publish date and sortable by read date. searchable"). One row an article the read has
-- finished with: where and when it was published, when it was read, how, and how many of each kind of item the
-- gates kept. Metadata only: the article's text stays in news_private.articles (the board opens a document whole,
-- ruling 88, through its capture).
CREATE OR REPLACE VIEW pub.news_read AS
SELECT d.url_key, a.url, a.host, a.title, a.author, a.published_at, d.read_at, d.outcome, d.model, d.reader,
       d.gates, d.seconds, a.capture_sha256, d.reading_key,
       coalesce((d.counts->'quotes'->>'kept')::int, 0) AS quotes_kept,
       coalesce((d.counts->'roles'->>'kept')::int, 0) AS roles_kept,
       coalesce((d.counts->'sentiment'->>'kept')::int, 0) AS tones_kept,
       d.counts->>'skipped' AS skipped_why,
       left(a.text, 700) AS opening        -- the first words, for the board's newspaper blurb (26 November 2026)
FROM news_private.read_done d JOIN news_private.articles a USING (url_key);

-- Every gated item of an article's reading, kept or not, with the rule that decided it: the board's news inspector
-- shows them beside the stored reading (26 November 2026: "an inspector pane that shows all the extracted data held").
CREATE OR REPLACE VIEW pub.news_read_items AS
SELECT url_key, kind, n, item, kept, citation, rule FROM news_private.read_items;
-- The read articles' text, for the links lane's name pass (curation step 1, Arthur, 26 November 2026: "add that",
-- the name pass on every type it lacks; rules match read articles only). `document` is the sha256 of the text as held,
-- the key a sighting carries; `url_key` joins it back to the article and its reading.
CREATE OR REPLACE VIEW pub.news_read_text AS
SELECT encode(sha256(convert_to(a.text, 'UTF8')), 'hex') AS document, a.url_key, a.host, a.title, a.text,
       a.published_at::date AS dated, d.read_at
FROM news_private.read_done d JOIN news_private.articles a USING (url_key)
WHERE d.outcome IN ('read', 'replayed') AND coalesce(a.text, '') <> '';
