-- registers/party_finance: the tables this lane owns, in its own schema. Loaded into a staging or scratch schema by
-- replacing `party_finance.` with that schema's name (in the shared scratch schema, `<schema>.party_finance_<table>`).
-- Nothing here is a person's home address; the lane's private twin holds what may never be published.

-- every document the lane holds: its hash, what kind it is, where the old estate kept it and the Commission's URL
-- for it (from the old job's manifest; the listing pages name a document by that URL)
CREATE TABLE IF NOT EXISTS party_finance.files (
    document     text PRIMARY KEY CHECK (document ~ '^[0-9a-f]{64}$'),
    kind         text NOT NULL,          -- expense-return | financial-statements | allocation-page | allocation-decision |
                                         -- promoter-register | promoter-return | expenses-listing |
                                         -- promoter-expenses-listing | financials-listing
    old_path     text NOT NULL,
    url          text,                   -- the Commission's URL, where the manifest gives one
    captured_at  text                    -- when the old job fetched it, by its manifest
);

-- the catch log: one line for every item the lane could not take to a row, with the stage and the reason
-- (capture | listing | link | declaration | allocation | promoter | statement)
CREATE TABLE IF NOT EXISTS party_finance.set_aside (
    item     text NOT NULL,              -- a document hash, or a listing row's key
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- the Commission's own table of party election expenses, one row per party per election, as printed
CREATE TABLE IF NOT EXISTS party_finance.expense_listing (
    key               text PRIMARY KEY,                 -- <listing sha256>/row/<n>
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL DEFAULT 1,
    place             text NOT NULL,                    -- row <n>
    year              integer NOT NULL,                 -- the general election
    party_label       text NOT NULL,                    -- the party as the table names it
    party             text,                             -- the registered party (keys.parties); NULL when unresolved
    party_basis       text NOT NULL,
    note              text,                             -- the Commission's bracketed note, verbatim
    expense_limit     numeric(14,2),
    total_expenses    numeric(14,2),                    -- NIL is 0
    allocation        numeric(14,2),                    -- the broadcasting allocation; NULL where it printed N/A
    allocation_spent  numeric(14,2),
    audited           boolean,                          -- the 2023 table's audit-report column; NULL where blank or absent
    printed           text NOT NULL,                    -- the figure cells as printed, ' | ' between
    reader            text NOT NULL,
    profile           text NOT NULL,
    profile_version   integer NOT NULL,
    read_from         text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    loaded_at         timestamptz NOT NULL
);

-- the Commission's table of registered promoters' expenses, one row per promoter per election, as printed
CREATE TABLE IF NOT EXISTS party_finance.promoter_listing (
    key                              text PRIMARY KEY,  -- <listing sha256>/row/<n>
    document                         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page                             integer NOT NULL DEFAULT 1,
    place                            text NOT NULL,
    year                             integer NOT NULL,
    promoter                         text NOT NULL,     -- as the table names it
    note                             text,
    election_expenses                numeric(14,2),
    cannabis_referendum_expenses     numeric(14,2),     -- 2020 only; held beside, never added to, the election figure
    end_of_life_referendum_expenses  numeric(14,2),     -- 2020 only; likewise
    printed                          text NOT NULL,
    reader                           text NOT NULL,
    profile                          text NOT NULL,
    profile_version                  integer NOT NULL,
    read_from                        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    loaded_at                        timestamptz NOT NULL
);

-- every document a listing row links, in page order; the link text states which is the amendment
CREATE TABLE IF NOT EXISTS party_finance.listing_links (
    row_key    text NOT NULL,                           -- expense_listing.key or promoter_listing.key
    ordinal    integer NOT NULL,
    link_text  text NOT NULL,
    url        text NOT NULL,
    amended    boolean NOT NULL,                        -- the link text says "amended"
    document   text CHECK (document ~ '^[0-9a-f]{64}$'), -- NULL: the lane does not hold it (a catch-log line)
    PRIMARY KEY (row_key, ordinal)
);

-- a party's election expense return: its own stated total, read from the document
CREATE TABLE IF NOT EXISTS party_finance.expense_returns (
    key               text PRIMARY KEY,                 -- <document sha256>/declaration
    document          text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page              integer NOT NULL,                 -- the page the total was read on
    place             text NOT NULL,                    -- Total (A + B + C) | the auditor's total | Parts A to C
    listing_row       text NOT NULL,                    -- the Commission's row that links this return
    year              integer NOT NULL,                 -- the general election, from that row
    party_label       text NOT NULL,                    -- from that row
    party             text,
    party_basis       text NOT NULL,
    current           boolean NOT NULL,                 -- the row's figure is this return's: it is the amendment, or the only link
    total             numeric(14,2) NOT NULL,           -- the return's own total (A + B + C)
    total_check       text NOT NULL,                    -- parts-sum | stated-only | summed-parts | declared-nil
    part_a            numeric(14,2),
    part_b            numeric(14,2),
    part_c            numeric(14,2),
    expense_limit     numeric(14,2),                    -- the limit the form prints, when read
    read_from         text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader            text NOT NULL,
    profile           text NOT NULL,                    -- the profile and version the page reading was made under
    profile_version   integer NOT NULL,
    loaded_at         timestamptz NOT NULL
);
