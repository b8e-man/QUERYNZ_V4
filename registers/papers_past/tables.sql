-- the Papers Past archive (step 7.2; step 8.6, 2 November 2026). Searched, never mined (hard limit 17): no table here holds a
-- person, a claim, a link or a name index. Regenerable from the dump; rebuilt whole by load.py.
CREATE TABLE IF NOT EXISTS papers_past.sources (
    document text PRIMARY KEY,        -- the dump's sha256 as dump.sha256 pins it
    path text NOT NULL,
    bytes bigint NOT NULL,
    verified text                     -- the verification the dump carries (verified.OK)
);
CREATE TABLE IF NOT EXISTS papers_past.items (
    key text PRIMARY KEY,             -- the Papers Past article id: EP19040730.2.115.3
    paper text NOT NULL,              -- the paper's code: EP
    published_on date,                -- the issue's date, from the article id
    title text,
    text text NOT NULL,
    chars integer NOT NULL,
    url text NOT NULL,
    upstream_id bigint NOT NULL,      -- the dump's scraper_results.id
    held_in_old boolean NOT NULL,     -- the old estate's incoming_news holds it by that id
    batch integer NOT NULL,
    document text NOT NULL,           -- the dump's sha256
    place text NOT NULL,              -- 'scraper_results line N'
    reader text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS papers_past.stages (
    batch integer NOT NULL,
    seq integer NOT NULL,
    stage text NOT NULL,
    items_in integer NOT NULL,
    items_out integer NOT NULL,
    set_aside integer NOT NULL,
    bytes bigint,                     -- what the stage's output takes, where measured
    PRIMARY KEY (batch, seq)
);
CREATE TABLE IF NOT EXISTS papers_past.catches (
    batch integer NOT NULL,
    stage text NOT NULL,
    item text NOT NULL,               -- the dump row's id
    place text NOT NULL,              -- 'scraper_results line N'
    reason text NOT NULL,
    example text                      -- the first failing row of each reason, kept whole (its fields as the dump holds them)
);
