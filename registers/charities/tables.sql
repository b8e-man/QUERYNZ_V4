-- registers/charities: the tables this lane owns, in `charities` and `charities_private`.
-- The capture's own record is here (charities-capture session). The reading's tables are added by the build
-- that is kept (charities_a or charities_b, plan step 4.1). No capture table holds a row of the register: the
-- pages themselves stay in the document store, verbatim, keyed by sha256. The feed's Officers set carries no
-- address; an organisation's street and postal address are in its page, as the register publishes them.

-- one row per pass over one entity set of the feed: a full copy, or the rows changed since a date
CREATE TABLE IF NOT EXISTS charities.capture_passes (
    pass_id       bigserial PRIMARY KEY,
    entity_set    text NOT NULL,                     -- the feed's name: Organisations, Officers, AnnualReturn, ...
    mode          text NOT NULL CHECK (mode IN ('full', 'changes', 'whole')),   -- whole: a small set in one request
    since         timestamptz,                       -- changes: ModifiedOn on or after this; NULL for full
    stated        integer,                           -- the feed's own count for the pass's filter ($inlinecount), at its first page
    next_key      bigint,                            -- the last key landed; the pass resumes after it
    pages         integer NOT NULL DEFAULT 0,        -- pages landed
    rows_landed   integer NOT NULL DEFAULT 0,        -- rows in the pages landed
    set_aside     integer NOT NULL DEFAULT 0,        -- pages that failed (catch log lines for this pass)
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz                        -- NULL while the pass is half-done
);
CREATE INDEX IF NOT EXISTS capture_passes_open ON charities.capture_passes (entity_set) WHERE finished_at IS NULL;

-- the listing: one row per page landed, in order, with its hash; a pass's pages are its documents
CREATE TABLE IF NOT EXISTS charities.capture_pages (
    pass_id     bigint NOT NULL REFERENCES charities.capture_passes (pass_id),
    page_no     integer NOT NULL,                    -- 1, 2, ... within the pass
    entity_set  text NOT NULL,
    url         text NOT NULL,                       -- exactly as asked
    sha256      text NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    rows        integer NOT NULL,
    first_key   bigint,
    last_key    bigint,
    new         boolean NOT NULL,                    -- false: the same bytes were already held
    fetched_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (pass_id, page_no)
);
CREATE INDEX IF NOT EXISTS capture_pages_sha ON charities.capture_pages (sha256);

-- the catch log: one line for every page the capture could not take, with the stage and the reason
CREATE TABLE IF NOT EXISTS charities.capture_set_aside (
    pass_id   bigint REFERENCES charities.capture_passes (pass_id),
    item      text NOT NULL,                         -- the URL asked
    stage     text NOT NULL,                         -- fetch | parse | order | land
    reason    text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);
