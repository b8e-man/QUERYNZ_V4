-- the Papers Past archive's published view (step 8.6). Searched, never mined (hard limit 17): the article, its paper and date,
-- its title and length, and its citation; no person, no claim, no name index. The text stays in papers_past.items for the
-- archive product. links/ never reads this view (tests/test_papers_past_search_only.py).
CREATE OR REPLACE VIEW pub.papers_past_items AS
SELECT i.key, i.paper, i.published_on, i.title, i.chars, i.url, i.batch,
       i.document, NULL::integer AS page, i.place, 'the archive dump''s scraper_results row'::text AS read_from, i.reader,
       NULL::text AS profile, NULL::integer AS profile_version, i.loaded_at
FROM papers_past.items i;
