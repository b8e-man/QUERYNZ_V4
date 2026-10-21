-- registers/commerce_commission: every table this lane owns, in `commerce_commission` and its private twin, in two
-- parts. The capture's record (capture.py makes it; never wiped): no capture table holds a row of the source; the
-- listing pages and entries stay in the document store verbatim by sha256. The reading's tables (load.py drops and
-- makes them again at every load). No address of any kind is read, and `commerce_commission_private` holds nothing:
-- the register publishes no address, and the contact person (Commission staff) is never read.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per pass over a listing: its stated total (the listing's own :total) and how far it has got
CREATE TABLE IF NOT EXISTS commerce_commission.capture_passes (
    pass_id      bigserial PRIMARY KEY,
    list         text NOT NULL,
    stated       integer,                           -- the listing's own count, read from the pass's first page
    next_page    integer NOT NULL DEFAULT 1,        -- the pass resumes from this page
    pages        integer NOT NULL DEFAULT 0,
    items        integer NOT NULL DEFAULT 0,
    started_at   timestamptz NOT NULL DEFAULT now(),
    finished_at  timestamptz
);

-- the listing pages landed, with their hashes
CREATE TABLE IF NOT EXISTS commerce_commission.capture_pages (
    pass_id   bigint NOT NULL REFERENCES commerce_commission.capture_passes (pass_id),
    page_no   integer NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    items     integer NOT NULL,
    PRIMARY KEY (pass_id, page_no)
);

-- what each pass listed: the entry's slug, address and fingerprint (status, outcome, date closed, tag as listed)
CREATE TABLE IF NOT EXISTS commerce_commission.capture_listed (
    pass_id   bigint NOT NULL REFERENCES commerce_commission.capture_passes (pass_id),
    list      text NOT NULL,
    slug      text NOT NULL,
    url       text NOT NULL,
    card      text NOT NULL,
    ordinal   integer NOT NULL,
    PRIMARY KEY (pass_id, slug)
);

-- the entries landed: one row per fetch, so an entry fetched again (its card changed) keeps its older hash too
CREATE TABLE IF NOT EXISTS commerce_commission.capture_items (
    list      text NOT NULL,
    slug      text NOT NULL,
    url       text NOT NULL,
    card      text NOT NULL,
    sha256    text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (list, slug, sha256)
);

-- the documents about the source (the copyright licence, the disclaimer, the privacy notice, the register's own
-- account of what it publishes)
CREATE TABLE IF NOT EXISTS commerce_commission.capture_docs (
    name      text NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    new       boolean NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commerce_commission.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the entry's sha256, page 1, its place, the
-- reader and the profile.

-- the ledger: one row per entry the newest finished pass listed; items in = read + set aside + not captured
CREATE TABLE IF NOT EXISTS commerce_commission.read_items (
    list       text NOT NULL,
    slug       text NOT NULL,
    pass_id    bigint,
    document   text,                                -- NULL: listed and not yet captured
    state      text NOT NULL CHECK (state IN ('read', 'set aside', 'not captured')),
    parties    integer NOT NULL DEFAULT 0,
    PRIMARY KEY (list, slug)
);

CREATE TABLE IF NOT EXISTS commerce_commission.cases (
    key              text PRIMARY KEY,              -- commerce_commission/case/<slug>
    slug             text,                          -- NULL where a suppression withholds a name (the slug carries it)
    case_number      text,                          -- PRJ…, [2026] NZCC 25, [2021] NZHC 2279, or none stated
    title            text,                          -- the heading as published; NULL where the Commission withholds it
    title_withheld   boolean NOT NULL,
    category         text,
    sub_category     text,
    act_section      text,                          -- as stated: 'Commerce Act 1986 ss 30, 80(1)'
    acts             text[] NOT NULL,
    sections         text[] NOT NULL,
    industry         text,
    status           text,
    outcome          text,
    opened_on        date,
    closed_on        date,
    action_on        date,                          -- closed, else opened
    url              text,                          -- NULL where a suppression withholds a name (the address carries it)
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commerce_commission.parties (
    key              text PRIMARY KEY,              -- <case key>/party/<n>
    case_key         text NOT NULL,
    ordinal          integer NOT NULL,
    name             text,                          -- as published; NULL where withheld (hard limit 16)
    trading_as       text,
    withheld         boolean NOT NULL,
    withheld_by      text,
    organisation     boolean NOT NULL,              -- carries an organisation word; false is "not shown to be", never "a person"
    company_number   text,                          -- only where the page prints one beside the name
    split_from       text NOT NULL,                 -- 'semicolon', 'and between two legal names', 'as published'
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS commerce_commission.read_set_aside (
    document  text,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);
