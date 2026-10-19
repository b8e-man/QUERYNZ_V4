-- registers/party_returns (plan 1.11): the tables this lane owns, in its own schema.
-- Loaded into a staging or scratch schema by replacing `party_returns.` with that schema's name.
-- party_returns_private holds nothing yet: the slice reads declaration pages only, which carry no home address.

CREATE TABLE IF NOT EXISTS party_returns.returns (
    key              text PRIMARY KEY,                       -- <document sha256>/declaration
    document         text NOT NULL CHECK (document ~ '^[0-9a-f]{64}$'),
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL DEFAULT 'declaration',
    party            text,                                   -- the registered party (keys.parties); NULL when unresolved
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
    total_check      text NOT NULL,                          -- parts-sum (total equals the parts read) | declared-nil
    read_from        text NOT NULL CHECK (read_from IN ('text', 'pixels')),
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL
);
-- year_from came with step 4 (the pixel route); a table made before it gains the column, and rows are named by column
ALTER TABLE party_returns.returns ADD COLUMN IF NOT EXISTS year_from text;

-- the catch log: one line for every document the lane could not take to a row
CREATE TABLE IF NOT EXISTS party_returns.set_aside (
    document   text NOT NULL,
    stage      text NOT NULL,                                -- recognise | read | declaration
    reason     text NOT NULL,
    at         timestamptz NOT NULL DEFAULT now()
);
