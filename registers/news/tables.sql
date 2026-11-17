-- registers/news: the news register (Arthur, 17 November 2026: "take everything under News, by site (the old
-- estate's copy) and move it into the new estate so we can retire the old estate"; "go site by site. after the site
-- is migrated and the provider is providing, retire the old").
--
-- `news_private.articles` is one row per article address: the old estate's copy and the ingest MCP's provider
-- (`estate-news`, its pages read by the old estate's own parsers, registers/news/extract) in one table, the longer
-- text kept where both hold it. Private by the suffix: article text can print a home address (hard limit 15).
-- Regenerable from its two sources, so a load may rebuild it; the ledgers below are never wiped.

CREATE SCHEMA IF NOT EXISTS news_private;
CREATE SCHEMA IF NOT EXISTS news;

-- an address folded for matching: no scheme, no www., no fragment, no tracking parameters, no trailing slash
CREATE OR REPLACE FUNCTION news_private.url_key(u text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT rtrim(regexp_replace(regexp_replace(lower(split_part(u, '#', 1)), '^https?://(www\.)?', ''),
                                '[?&](utm_[a-z]+|fbclid|gclid|mc_[a-z]+)=[^&]*', '', 'g'), '/?')
$$;

CREATE OR REPLACE FUNCTION news_private.host_of(u text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT lower(regexp_replace(substring(u FROM '^https?://([^/:?#]+)'), '^www\.', ''))
$$;

CREATE TABLE IF NOT EXISTS news_private.articles (
    url_key         text PRIMARY KEY,
    url             text NOT NULL,
    host            text NOT NULL,
    title           text,
    author          text,
    published_at    timestamptz,
    categories      text[],
    text            text,
    chars           integer NOT NULL DEFAULT 0,
    source          text NOT NULL CHECK (source IN ('old estate', 'provider')),   -- whose text this row holds
    held_by         text[] NOT NULL,                                               -- every source holding the address
    old_id          uuid,                                                          -- the old estate's article id
    capture_sha256  text,                                                          -- the provider's page, in the store
    parser          text,                                                          -- the extract module that read it
    fetched_at      timestamptz
);
CREATE INDEX IF NOT EXISTS articles_host ON news_private.articles (host, published_at);

-- every provider page read, and what became of it (never wiped)
CREATE TABLE IF NOT EXISTS news_private.provider_read (
    capture_sha256  text NOT NULL,
    url             text NOT NULL,
    state           text NOT NULL CHECK (state IN ('read', 'no text', 'no parser', 'failed')),
    parser          text,
    chars           integer,
    why             text,
    at              timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (capture_sha256, url)
);

-- how far the old estate's copy has been taken (never wiped)
CREATE TABLE IF NOT EXISTS news_private.old_taken (
    upto     timestamptz NOT NULL,
    rows     bigint NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- each site's move, rebuilt at every load: what each source holds, and whether the old collection may stop
CREATE TABLE IF NOT EXISTS news.sites (
    host               text PRIMARY KEY,
    old_articles       bigint NOT NULL DEFAULT 0,
    old_newest         date,
    old_last_fetch     date,
    provider_articles  bigint NOT NULL DEFAULT 0,
    provider_earliest  date,
    provider_newest    date,
    provider_week      bigint NOT NULL DEFAULT 0,      -- the provider's articles published in the last 7 days
    state              text NOT NULL,                  -- old only | provider only | providing, gap | ready | retired
    why                text NOT NULL,
    at                 timestamptz NOT NULL DEFAULT now()
);

-- a site whose old collection was stopped, and how (never wiped)
CREATE TABLE IF NOT EXISTS news.retirements (
    host      text PRIMARY KEY,
    how       text NOT NULL,
    by_word   text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);
