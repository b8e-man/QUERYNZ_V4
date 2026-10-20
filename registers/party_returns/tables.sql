-- registers/party_returns (plan 1.11): the tables this lane owns, in its own schema.
-- Loaded into a staging or scratch schema by replacing `party_returns.` with that schema's name.
-- A donor's or lender's street address is never a column here: it lives in party_returns_private (private.sql),
-- keyed by the row's key (hard limit 15).

CREATE TABLE IF NOT EXISTS party_returns.returns (
    key              text PRIMARY KEY,                       -- <document sha256>/declaration
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL DEFAULT 'declaration',
    party            text,                                   -- the registration's registered name (pub.parties.name); NULL when unresolved
    party_label      text NOT NULL,                          -- the party name as filed on the declaration page
    party_basis      text NOT NULL,                          -- exact | variant | core | fuzzy:<ratio> | unresolved
    year             integer NOT NULL,                       -- the calendar year the return covers, as printed
    year_from        text NOT NULL,                          -- declaration page | loans page | year ended (registers/party_returns/pixels.py)
    declared_total   numeric(14,2) NOT NULL,                 -- the return's own grand total, as printed
    part_a           numeric(14,2),
    part_c           numeric(14,2),
    part_d           numeric(14,2),
    part_f           numeric(14,2),
    part_g           numeric(14,2),
    declared_parts   text,                                   -- the letters in the total's brackets, as printed
    total_check      text NOT NULL,                          -- parts-sum (total equals the parts read) | declared-nil | parts-confirmed (a misread total mended: every part page agrees) | part-pages (parts from the part pages)
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);
-- year_from came with step 4 (the pixel route); a table made before it gains the column, and rows are named by column
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS year_from text;

-- tranche 2: the loans the declaration page declares, and whether each schedule was published whole
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS loans_h numeric(14,2);        -- Part H as printed
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS loans_i numeric(14,2);        -- Part I as printed
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS loans_total numeric(14,2);    -- Total (H + I) as printed
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS donors_check text;            -- parts-sum | declared-nil | NULL: Part A set aside
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS loans_check text;             -- parts-sum | declared-nil | NULL: Part H set aside

-- session 4: the party as the parties lane's registration (keys.parties.party_name(label, rows, on=year)); `party` is
-- then that registration's registered name
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS party_key text;              -- pub.parties.key; NULL when unresolved

-- the catch log: one line for every document the lane could not take to a row (recognise | read | declaration),
-- and one for every part of a published return that could not be published whole (part-a | loans | part-h),
-- and every amended return the Commission lists that the lane does not hold (amendment)
CREATE TABLE IF NOT EXISTS party_returns.set_aside (
    document   text NOT NULL,
    stage      text NOT NULL,
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);

-- Part A: one row per line of the donors' table, in reading order; published only when the part reconciled
CREATE TABLE IF NOT EXISTS party_returns.donors (
    key              text PRIMARY KEY,                       -- <document sha256>/A/<ordinal>
    return_key       text NOT NULL,                          -- party_returns.returns.key
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    ordinal          integer NOT NULL,                       -- the row's place in the part, as read
    n                integer,                                -- the row number the form prints, when it prints one
    donor            text NOT NULL,                          -- the name, cut from the address before the first figure
    amount           numeric(14,2) NOT NULL,
    dates            text,                                   -- the dates as printed
    contributions    text,                                   -- the Yes/No column as printed
    paired_by        text NOT NULL,                          -- layout | table | numbered | stacked
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- Part H: one row per lender block; published only when the part reconciled
CREATE TABLE IF NOT EXISTS party_returns.loans (
    key              text PRIMARY KEY,                       -- <document sha256>/H/<ordinal>
    return_key       text NOT NULL,
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL,
    ordinal          integer NOT NULL,
    lender           text NOT NULL,
    amount           numeric(14,2) NOT NULL,                 -- the loan amount; never the unpaid balance or the running total
    dates            text,                                   -- entered into and repayment, as printed
    interest         text,                                   -- the rate as printed
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);

-- which return an amended return replaces, as the Commission's listing states it (amendments.py)
CREATE TABLE IF NOT EXISTS party_returns.amendments (
    document         text PRIMARY KEY CHECK (document ~ '^[0-9a-f]{64}$'),      -- the replaced return
    replaced_by      text NOT NULL CHECK (replaced_by ~ '^[0-9a-f]{64}$'),
    party_label      text NOT NULL,                          -- the party as the listing names it
    year             integer NOT NULL,
    stated           text NOT NULL,                          -- the amendment's link text, as the Commission wrote it
    listing          text NOT NULL CHECK (listing ~ '^[0-9a-f]{64}$')            -- the listing page, by hash
);
