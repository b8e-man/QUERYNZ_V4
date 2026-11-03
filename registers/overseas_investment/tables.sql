-- registers/overseas_investment: every table this lane owns, in `overseas_investment` and its private twin, in two
-- parts. The capture's record (capture.py makes it; never wiped): no capture table holds a row of the source; the
-- listing pages and summaries stay in the document store verbatim by sha256. The reading's tables (load.py drops and
-- makes them again at every load). The investment statement as the office publishes it (street addresses and legal
-- descriptions of land, some of it a person's home) is on the decision row whole, flagged by `addresses_named` (ruling
-- 143); `overseas_investment_private` holds what a withheld name's cell prints and every headed row of the page.
-- A summary the office takes down stays, flagged with the date of the first finished pass that no longer listed it.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per pass over one year's listing (decision date in that year): the pager's last page, read from the first
-- page, and the rows the office's listing showed, known when the last page lands
CREATE TABLE IF NOT EXISTS overseas_investment.capture_passes (
    pass_id       bigserial PRIMARY KEY,
    list          text NOT NULL,                     -- year-2017, year-2018, …
    stated_pages  integer,                           -- the pager's last page + 1, from the pass's first page
    stated        integer,                           -- the rows the listing showed: 60 a page, then the last page's
    next_page     integer NOT NULL DEFAULT 0,        -- the pass resumes from this page (0-based, as the pager counts)
    pages         integer NOT NULL DEFAULT 0,
    items         integer NOT NULL DEFAULT 0,        -- distinct (page, case number) rows listed so far
    started_at    timestamptz NOT NULL DEFAULT now(),
    finished_at   timestamptz
);

-- the listing pages landed, with their hashes
CREATE TABLE IF NOT EXISTS overseas_investment.capture_pages (
    pass_id   bigint NOT NULL REFERENCES overseas_investment.capture_passes (pass_id),
    page_no   integer NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    items     integer NOT NULL,
    PRIMARY KEY (pass_id, page_no)
);

-- what each pass listed: the summary page's slug and address, the case number listed, and the row's fingerprint
-- (case number, applicant, date as listed). A page carrying two case numbers is listed twice.
CREATE TABLE IF NOT EXISTS overseas_investment.capture_listed (
    pass_id      bigint NOT NULL REFERENCES overseas_investment.capture_passes (pass_id),
    list         text NOT NULL,
    slug         text NOT NULL,
    url          text NOT NULL,
    case_number  text NOT NULL,
    card         text NOT NULL,
    ordinal      integer NOT NULL,
    PRIMARY KEY (pass_id, slug, case_number)
);

-- the summaries landed: one row per fetch, so a page fetched again (its listed rows changed) keeps its older hash too
CREATE TABLE IF NOT EXISTS overseas_investment.capture_items (
    slug      text NOT NULL,
    url       text NOT NULL,
    card      text NOT NULL,                         -- the page's listed rows' fingerprints, joined in case order
    sha256    text NOT NULL,
    at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (slug, sha256)
);

-- the documents about the source (the copyright licence, the disclaimer, the privacy statement)
CREATE TABLE IF NOT EXISTS overseas_investment.capture_docs (
    name      text NOT NULL,
    url       text NOT NULL,
    sha256    text NOT NULL,
    new       boolean NOT NULL,
    at        timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS overseas_investment.capture_set_aside (
    pass_id  bigint,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the summary's sha256, page 1, its place,
-- the reader and the profile.

-- the ledger: one row per (summary page, case number) the newest finished pass of each year listed;
-- items in = read + set aside + not captured
CREATE TABLE IF NOT EXISTS overseas_investment.read_items (
    list         text NOT NULL,
    slug         text NOT NULL,
    case_number  text NOT NULL,
    pass_id      bigint,
    document     text,                               -- NULL: listed and not yet captured
    state        text NOT NULL CHECK (state IN ('read', 'set aside', 'not captured')),
    parties      integer NOT NULL DEFAULT 0,         -- on the page's first ledger line only, so the sum is the parties
    taken_down_on date,                              -- the first finished pass that no longer listed it; NULL: listed now
    PRIMARY KEY (list, slug, case_number)
);

CREATE TABLE IF NOT EXISTS overseas_investment.decisions (
    key                     text PRIMARY KEY,        -- overseas_investment/decision/<slug>
    slug                    text NOT NULL,
    url                     text NOT NULL,
    taken_down_on           date,                    -- every listing line of the page taken down, the latest of their dates
    case_numbers            text[] NOT NULL,         -- as stated; a page can carry two
    case_number             text,
    kind                    text,                    -- Decision | Notification, as the page types it
    outcome                 text,                    -- as stated: 'Consent granted', 'Consent Declined', …
    granted                 boolean,                 -- NULL for a notification
    section                 text,                    -- the section the outcome cites, as stated
    decision_maker          text,
    decided_on              date,
    pathway                 text,                    -- the kind of consent, as stated
    investment_class        text,                    -- sensitive land | significant business assets | fishing quota
    investment              text,                    -- the statement as published, street addresses and legal descriptions whole
    addresses_named         integer NOT NULL,        -- street addresses and legal descriptions the statement's shape names
    areas_stated            text[] NOT NULL,
    area_ha                 numeric[] NOT NULL,
    consideration_heading   text,                    -- Consideration | Asset Value, as headed
    consideration_stated    text,
    consideration_nzd       numeric,                 -- only where one dollar figure is stated and nothing withheld
    consideration_withheld  boolean NOT NULL,
    penalty_stated          text,
    notification_number     text,
    parent_case             text,
    applicant_listed        text,                    -- the meta block's applicant; NULL where a name is withheld
    rationale               text[] NOT NULL,         -- as stated, whole
    rationale_names_address boolean NOT NULL,        -- an item's shape names a street address or a legal description
    headings                text[] NOT NULL,
    attachments             integer NOT NULL,
    document                text NOT NULL,
    page                    integer NOT NULL,
    place                   text NOT NULL,
    read_from               text NOT NULL,
    reader                  text NOT NULL,
    profile                 text NOT NULL,
    profile_version         integer NOT NULL,
    loaded_at               timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS overseas_investment.parties (
    key              text PRIMARY KEY,               -- <decision key>/party/<n>
    decision_key     text NOT NULL,
    ordinal          integer NOT NULL,
    role             text NOT NULL CHECK (role IN ('applicant', 'vendor', 'issuer')),
    role_stated      text NOT NULL,                  -- Applicant, Consent holder, Vendor(s), Issuer, as headed
    name             text,                           -- as published; NULL where the office withholds it (what it prints: withheld_values)
    withheld         boolean NOT NULL,
    withheld_by      text,
    status           text,                           -- printed beside the name: '(in receivership)'
    trust            text,                           -- the trust a trustee acts for, as named
    organisation     boolean NOT NULL,               -- carries an organisation word; false is "not shown to be", never "a person"
    company_number   text,                           -- only where printed beside the name
    ownership_lines  integer NOT NULL,
    origins          text[],                         -- each ownership line's origin as stated
    shares           numeric[],                      -- each line's share as stated (NULL in the array where none)
    ownership_scope  text,                           -- 'this party' | 'every party named in the cell'
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- the investment statement as published, street addresses and all (the same text is on decisions.investment since
-- ruling 143)
CREATE TABLE IF NOT EXISTS overseas_investment_private.investments (
    key                text PRIMARY KEY,             -- the decision's key
    investment_stated  text NOT NULL,
    document           text NOT NULL
);

-- what the cell prints in a withheld name's place, with any status, trust and company number beside it (keyed by the
-- party), and the meta block's applicant where the office withholds it (keyed by the decision): kept whole (ruling 142)
CREATE TABLE IF NOT EXISTS overseas_investment_private.withheld_values (
    key              text NOT NULL,
    field            text NOT NULL,                  -- name | status | trust | company_number | applicant_listed
    value            text NOT NULL,
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (key, field)
);

-- every headed row of a summary's table, as printed (More information, the Background, the attachments' addresses)
CREATE TABLE IF NOT EXISTS overseas_investment_private.page_rows (
    key              text NOT NULL,                  -- the decision's key
    ordinal          integer NOT NULL,
    heading          text NOT NULL,
    text             text,
    links            text[],
    document         text NOT NULL,
    page             integer NOT NULL,
    place            text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (key, ordinal)
);

-- the private statements' count, written by the load (which can see the private twin) beside the ledger, so a check
-- run under the session reader (which has no grant on the twin, by design) still answers: one row
CREATE TABLE IF NOT EXISTS overseas_investment.read_statements (
    statements  integer NOT NULL,                    -- rows in overseas_investment_private.investments
    stray       integer NOT NULL                     -- of them, rows whose key is no decision's
);

CREATE TABLE IF NOT EXISTS overseas_investment.read_set_aside (
    document  text,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);
