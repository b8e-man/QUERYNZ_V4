-- the Papers Past archive (step 7.2; step 8.6, 2 November 2026). Searched, never mined (hard limit 17): no table here holds a
-- person, a claim, a link or a name index. Regenerable from the dump; rebuilt whole by load.py. The text is not here: it is in
-- compressed files on /mnt/hdd2 (store.py), and the database keeps the catalogue.
CREATE TABLE IF NOT EXISTS papers_past.sources (
    document text PRIMARY KEY,        -- the dump's sha256 as dump.sha256 pins it
    path text NOT NULL,
    bytes bigint NOT NULL,
    verified text                     -- the verification the dump carries (verified.OK)
);
CREATE TABLE IF NOT EXISTS papers_past.batches (
    batch integer PRIMARY KEY,
    document text NOT NULL,           -- the dump's sha256
    reader text NOT NULL,
    store text NOT NULL,              -- the folder of the text files: /mnt/hdd2/qv4-papers-past/<database>.<schema>
    every integer NOT NULL DEFAULT 1, -- 1: consecutive rows; k: every k-th Papers Past row of the dump (a spread sample)
    loaded_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS papers_past.files (
    file integer PRIMARY KEY,
    path text NOT NULL UNIQUE         -- relative to the store: text/EP/1904.zst
);
-- the catalogue: one row per article, about 0.3 KB; the text is in the store's files (store.py), found by its place
CREATE TABLE IF NOT EXISTS papers_past.items (
    key text PRIMARY KEY,             -- the Papers Past article id: EP19040730.2.115.3
    paper text NOT NULL,              -- the paper's code: EP
    published_on date,                -- the issue's date, from the article id
    title text,
    chars integer NOT NULL,           -- the text's length in characters
    sha256 bytea NOT NULL,            -- of the text's UTF-8 bytes
    upstream_id bigint NOT NULL,      -- the dump's scraper_results.id
    held_in_old boolean NOT NULL,     -- the old estate's incoming_news holds it by that id
    batch integer NOT NULL,
    line bigint NOT NULL,             -- its line in the dump: 'scraper_results line N'
    file integer NOT NULL,            -- papers_past.files
    frame_at bigint NOT NULL,         -- the zstd frame's offset in the file
    frame_bytes integer NOT NULL,     -- and its length
    at integer NOT NULL,              -- the text's offset in the decompressed frame
    bytes integer NOT NULL,           -- and its length in bytes
    url text                          -- only where the dump's URL is not https://paperspast.natlib.govt.nz/newspapers/<key>
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
