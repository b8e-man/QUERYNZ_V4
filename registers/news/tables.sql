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
-- an address over 1,000 characters (an old act.org.nz slug ran 4,279, past the index's limit, 22 Nov 2026) keys as
-- its first 1,000 characters and the md5 of the whole folded address
CREATE OR REPLACE FUNCTION news_private.url_key(u text) RETURNS text LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE WHEN length(k) > 1000 THEN left(k, 1000) || '#md5:' || md5(k) ELSE k END
    FROM (SELECT rtrim(regexp_replace(regexp_replace(lower(split_part(u, '#', 1)), '^https?://(www\.)?', ''),
                                      '[?&](utm_[a-z]+|fbclid|gclid|mc_[a-z]+)=[^&]*', '', 'g'), '/?') AS k) f
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
CREATE INDEX IF NOT EXISTS articles_published ON news_private.articles (published_at);   -- the board's news tab sorts by it

-- every provider page read, and what became of it (never wiped)
CREATE TABLE IF NOT EXISTS news_private.provider_read (
    capture_sha256  text NOT NULL,
    url             text NOT NULL,
    state           text NOT NULL CHECK (state IN ('read', 'stub', 'no text', 'no parser', 'failed')),
    parser          text,
    chars           integer,
    why             text,
    at              timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (capture_sha256, url)
);
-- 'stub' (18 Nov 2026): a page that ends on a paywall prompt is a ledger line, never an article
ALTER TABLE news_private.provider_read DROP CONSTRAINT IF EXISTS provider_read_state_check;
ALTER TABLE news_private.provider_read ADD CONSTRAINT provider_read_state_check
    CHECK (state IN ('read', 'stub', 'no text', 'no parser', 'failed'));

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
    state              text NOT NULL,                  -- old only | provider only | providing, gap | providing, stubs | held elsewhere, gap | ready | retired
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

-- ── comments (Arthur, 18 November 2026: "we want all comments and we want to efficiently link them to both the
-- articles and also the user"; collecting only, the links across sites or to known people are later work) ──

-- one row per comment on a site: its newest form, linked to its article by url_key (joins news_private.articles)
-- and to its commenter by commenter_key (joins news_private.commenters). Read from the provider's pages in fetch
-- order, so a comment a later capture of the article no longer shows gets absent_since, never a deletion.
CREATE TABLE IF NOT EXISTS news_private.comments (
    host             text NOT NULL,
    comment_id       text NOT NULL,                 -- the site's own id
    url_key          text NOT NULL,                 -- the article's address, folded (news_private.url_key)
    url              text NOT NULL,
    parent_id        text,                          -- the comment it replies to, on the same site
    commenter_key    text NOT NULL,                 -- 'user:<site slug>' | 'link:<profile link>' | 'name:<display name>'
    author_name      text,
    author_slug      text,
    author_url       text,
    avatar_url       text,
    posted_at        timestamptz,
    text             text NOT NULL,
    chars            integer NOT NULL,
    votes_up         integer,
    votes_down       integer,
    versions         integer NOT NULL DEFAULT 1,    -- distinct texts seen (news_private.comment_versions)
    first_seen_at    timestamptz NOT NULL,
    last_seen_at     timestamptz NOT NULL,
    capture_sha256   text NOT NULL,                 -- the newest capture showing it
    absent_since     timestamptz,                   -- a later capture of the article did not show it
    PRIMARY KEY (host, comment_id)
);
CREATE INDEX IF NOT EXISTS comments_article ON news_private.comments (url_key);
CREATE INDEX IF NOT EXISTS comments_commenter ON news_private.comments (host, commenter_key);

-- every text a comment has had, with the capture that showed it (an edit is a new line)
CREATE TABLE IF NOT EXISTS news_private.comment_versions (
    host             text NOT NULL,
    comment_id       text NOT NULL,
    text_md5         text NOT NULL,
    text             text NOT NULL,
    capture_sha256   text NOT NULL,
    seen_at          timestamptz NOT NULL,
    PRIMARY KEY (host, comment_id, text_md5)
);

-- one row per commenter per site, rebuilt from the comments at every load. key_kind says how firm the key is: the
-- site's own user mark, a profile link the commenter gave, or only a display name (two people may share one)
CREATE TABLE IF NOT EXISTS news_private.commenters (
    host             text NOT NULL,
    commenter_key    text NOT NULL,
    key_kind         text NOT NULL CHECK (key_kind IN ('site user', 'profile link', 'display name')),
    names            text[] NOT NULL,               -- every display name seen under the key
    comments         bigint NOT NULL,
    articles         bigint NOT NULL,
    first_comment_at timestamptz,
    last_comment_at  timestamptz,
    PRIMARY KEY (host, commenter_key)
);

-- every provider page read for comments (a page read once; a new capture of the article is a new page)
CREATE TABLE IF NOT EXISTS news_private.comment_read (
    capture_sha256   text NOT NULL,
    url              text NOT NULL,
    comments         integer NOT NULL,
    why              text,
    at               timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (capture_sha256, url)
);

-- ── the first read of the corpus (Arthur, 25 November 2026: "apply these rules to the first read we do") ──
-- registers.news.read: each article read by the text reader (the golden sample's passes: the read, quotes, claims,
-- tones), the reading stored whole and ungated in the reader store by the hash of the text read, and its items here
-- with the gate's verdict (registers.news.gates). Reading again replays the store, so the gates can change and the
-- items be rewritten without a model call.

-- one row per article read (never wiped: it names the stored reading, which cost a model's time)
CREATE TABLE IF NOT EXISTS news_private.read_done (
    url_key          text PRIMARY KEY,
    text_sha256      text NOT NULL,                  -- the hash of the masked text the model read
    reading_key      text NOT NULL,                  -- the reader store's key
    reader           text NOT NULL,
    model            text NOT NULL,
    gates            text NOT NULL,
    outcome          text NOT NULL CHECK (outcome IN ('read', 'replayed', 'unusable', 'skipped')),   -- skipped: counts.skipped says why (te reo, a paywall stub)
    seconds          real,
    counts           jsonb NOT NULL DEFAULT '{}',    -- per kind: kept, dropped, citations
    read_at          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS read_done_read_at ON news_private.read_done (read_at);   -- the board's news tab sorts by it

-- the articles read before reader 6 that the subjects pass has since read alone (registers.news.subjects; Arthur, 27
-- November 2026: "lets make the switch then drip feed the already read articles in"), one row an article
CREATE TABLE IF NOT EXISTS news_private.subjects_done (
    url_key      text PRIMARY KEY,
    reading_key  text NOT NULL,          -- the subjects reading in the store
    subjects     integer NOT NULL,       -- kept by the gate
    dropped      integer NOT NULL,
    model        text NOT NULL,
    at           timestamptz NOT NULL DEFAULT now()
);

-- every gated item of a reading, kept or not, with the rule that decided it (rewritten from the store at will)
CREATE TABLE IF NOT EXISTS news_private.read_items (
    url_key          text NOT NULL,
    kind             text NOT NULL CHECK (kind IN ('quotes', 'roles', 'claims', 'sentiment')),
    n                integer NOT NULL,               -- the item's place in the reading's list
    item             jsonb NOT NULL,                 -- the model's record, as read
    kept             boolean NOT NULL,
    citation         boolean NOT NULL DEFAULT false, -- a document's words: kept apart, not speech
    rule             text NOT NULL,
    PRIMARY KEY (url_key, kind, n)
);
CREATE INDEX IF NOT EXISTS read_items_kept ON news_private.read_items (kind) WHERE kept;
