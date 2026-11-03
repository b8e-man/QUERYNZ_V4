-- the Papers Past archive's published view (step 8.6). Searched, never mined (hard limit 17): the article, its paper and date,
-- its title and length, and its citation; no person, no claim, no name index. The text stays in the store's files on
-- /mnt/hdd2, read by the archive product through papers_past.items. links/ never reads this view
-- (tests/test_papers_past_search_only.py).
CREATE OR REPLACE VIEW pub.papers_past_items AS
SELECT i.key, i.paper, i.published_on, i.title, i.chars,
       coalesce(i.url, 'https://paperspast.natlib.govt.nz/newspapers/' || i.key) AS url, i.batch,
       b.document, NULL::integer AS page, 'scraper_results line ' || i.line AS place,
       'the archive dump''s scraper_results row'::text AS read_from, b.reader,
       NULL::text AS profile, NULL::integer AS profile_version, b.loaded_at
FROM papers_past.items i JOIN papers_past.batches b USING (batch);

-- the board's table pane pages the view in issue-date order (products/board/catalogue.py, papers_past_items); without
-- this a page sorts all 86.7M rows. Rebuildable: made again with the table at each publish
CREATE INDEX IF NOT EXISTS items_published_on ON papers_past.items (published_on, key);
