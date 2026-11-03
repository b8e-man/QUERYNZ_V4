-- registers/insolvency: the Insolvency Register API's answers and their reading (2 November 2026). Schema `{s}`.
-- The capture's ledger (calls, removals, the cursor) is kept across loads; the reading (estates, unanswered, set_aside,
-- and {p}.suppressed_names) is rebuilt whole.

-- the capture's ledger: never truncated by a load
CREATE TABLE IF NOT EXISTS {s}.calls (
    id          bigserial PRIMARY KEY,
    at          timestamptz NOT NULL,
    day         date NOT NULL,                -- New Zealand day
    why         text NOT NULL,                -- 'search', 'detail', 'removals', 'lookup'
    asked       text NOT NULL,                -- the call's parameters as asked (never the key)
    estate      bigint,                       -- the estate a detail call asked for
    status      int NOT NULL,                 -- HTTP status; 0 for no answer
    document    text,                         -- sha256 of the answer as landed (whole, as received, from 4 November 2026)
    received    text,                         -- sha256 of the bytes as they arrived (before 4 November 2026 the landed
                                              -- answer had its address and birth fields taken out, so the two differed)
    total_items int,                          -- the API's own `totalItems` for a search or removals page
    blocked     text
);
CREATE INDEX IF NOT EXISTS {s}_calls_estate ON {s}.calls (estate) WHERE estate IS NOT NULL;
CREATE INDEX IF NOT EXISTS {s}_calls_day ON {s}.calls (day, why);

-- one line per estate the removals-and-corrections operation named, with the call that named it
CREATE TABLE IF NOT EXISTS {s}.removals (
    estate      bigint NOT NULL,
    removed_on  text,                         -- the API's `removedDate`, as given
    call        bigint NOT NULL,
    seen_at     timestamptz NOT NULL,
    PRIMARY KEY (estate, call)
);

-- every estate a search page named, with the page's call: what the details are asked for
CREATE TABLE IF NOT EXISTS {s}.search_seen (
    estate      bigint PRIMARY KEY,
    register    text NOT NULL,
    call        bigint NOT NULL
);

-- how far the removals have been asked: date_to of the last complete removals run
CREATE TABLE IF NOT EXISTS {s}.cursor (
    what        text PRIMARY KEY,
    value       text NOT NULL,
    at          timestamptz NOT NULL DEFAULT now()
);

-- the identifying fields (every address field, the month and year of birth), in the lane's private schema `{p}`, which
-- the session and product logins are never granted (4 November 2026: it had sat in `{s}` where the read login could),
-- by estate and field, from the latest answer that gave each; never deleted (ruling 142): a field a later detail answer
-- no longer gives is marked `gone_at`, an estate the removals name is marked `removed_at` with the API's words
CREATE SCHEMA IF NOT EXISTS {p};
CREATE TABLE IF NOT EXISTS {p}.identifiers (
    estate      bigint NOT NULL,
    field       text NOT NULL,
    value       text NOT NULL,
    call        bigint NOT NULL,
    at          timestamptz NOT NULL,
    PRIMARY KEY (estate, field)
);
ALTER TABLE {p}.identifiers ADD COLUMN IF NOT EXISTS gone_at timestamptz;        -- a later detail answer no longer gave it
ALTER TABLE {p}.identifiers ADD COLUMN IF NOT EXISTS removed_at timestamptz;     -- the removals named the estate after it
ALTER TABLE {p}.identifiers ADD COLUMN IF NOT EXISTS removal_said text;          -- the API's words, as the removals gave them

-- the reading: rebuilt whole by every load
DROP TABLE IF EXISTS {s}.estates CASCADE;
CREATE TABLE {s}.estates (
    key                 text PRIMARY KEY,     -- 'insolvency/<estate number>'
    estate_number       bigint NOT NULL,
    kind                text NOT NULL,        -- 'person' or 'company'
    register            text NOT NULL,        -- 'Insolvency' or 'DRO'
    name                text NOT NULL,        -- as the register gives it
    alternate_names     text[],
    trading_names       text[],
    organisation_name   text,
    nzbn                text,
    company_number      text,
    insolvency_type     text,
    status              text,
    adjudicated_on      date,                 -- adjudication, the no asset procedure's entry, the order, or the liquidation
    discharged_on       date,                 -- discharge or completion
    discharge_type      text,
    discharge_suspended boolean,
    annulled_on         date,
    multiple            boolean,              -- the register's `multipleInsolvencies`
    occupation          text,                 -- at adjudication, or the industry at liquidation
    court               text,
    office              text,                 -- the Official Assignee's office for enquiries
    partnered_estates   bigint[],
    shown_until         date,                 -- the last day the API's terms let it be shown (NULL: no limit, or no day yet)
    window_unknown      boolean NOT NULL,     -- the terms give no day to count the window from (discharged, no date)
    suppressed          boolean NOT NULL,     -- the register's status or type says suppressed: names in {p}.suppressed_names
    suppressed_said     text,                 -- the register's words that say so
    removed_on          text,                 -- the removals named it at or after this answer: the API's `removedDate`
    removal_seen_at     timestamptz,          -- when the removals named it
    absent_since        timestamptz,          -- the register answered 404 for it after this answer
    read_from           text NOT NULL,        -- 'detail' or 'search'
    document            text NOT NULL,
    page                int,
    place               text,
    reader              text NOT NULL,
    profile             text NOT NULL,
    profile_version     int NOT NULL,
    loaded_at           timestamptz NOT NULL DEFAULT now()
);

-- an estate named with no answer to read: the register answered 404 before any answer was held, or the removals named
-- it before one was (4 November 2026: replaces `withheld`, which also held the estates the terms kept back)
DROP TABLE IF EXISTS {s}.withheld CASCADE;
DROP TABLE IF EXISTS {s}.unanswered CASCADE;
CREATE TABLE {s}.unanswered (
    estate_number   bigint NOT NULL,
    reason          text NOT NULL,
    document        text
);

-- a suppressed estate's names, by key; its row in {s}.estates keeps the flag, the register's words and every other field
CREATE SCHEMA IF NOT EXISTS {p};
DROP TABLE IF EXISTS {p}.suppressed_names CASCADE;
CREATE TABLE {p}.suppressed_names (
    key                 text PRIMARY KEY,
    estate_number       bigint NOT NULL,
    suppressed_said     text,
    name                text NOT NULL,
    alternate_names     text[],
    trading_names       text[],
    organisation_name   text
);

DROP TABLE IF EXISTS {s}.set_aside CASCADE;
CREATE TABLE {s}.set_aside (
    document    text,
    place       text,
    stage       text NOT NULL,
    reason      text NOT NULL
);
