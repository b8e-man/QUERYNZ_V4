-- registers/insolvency: the Insolvency Register API's answers and their reading (2 November 2026). Schema `{s}`.
-- The capture's ledger (calls, removals, the cursor) is kept across loads; the reading (estates, set_aside) is rebuilt whole.

-- the capture's ledger: never truncated by a load
CREATE TABLE IF NOT EXISTS {s}.calls (
    id          bigserial PRIMARY KEY,
    at          timestamptz NOT NULL,
    day         date NOT NULL,                -- New Zealand day
    why         text NOT NULL,                -- 'search', 'detail', 'removals', 'lookup'
    asked       text NOT NULL,                -- the call's parameters as asked (never the key)
    estate      bigint,                       -- the estate a detail call asked for
    status      int NOT NULL,                 -- HTTP status; 0 for no answer
    document    text,                         -- sha256 of the answer as landed (address fields removed before landing)
    received    text,                         -- sha256 of the bytes as they arrived, before the removal
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
    shown_until         date,                 -- the last day the record may be shown (NULL: no limit the API states)
    read_from           text NOT NULL,        -- 'detail' or 'search'
    document            text NOT NULL,
    page                int,
    place               text,
    reader              text NOT NULL,
    profile             text NOT NULL,
    profile_version     int NOT NULL,
    loaded_at           timestamptz NOT NULL DEFAULT now()
);

-- an estate held and not published, with why: removed, suppressed, past its window, annulled, unreadable
DROP TABLE IF EXISTS {s}.withheld CASCADE;
CREATE TABLE {s}.withheld (
    estate_number   bigint NOT NULL,
    reason          text NOT NULL,
    document        text
);

DROP TABLE IF EXISTS {s}.set_aside CASCADE;
CREATE TABLE {s}.set_aside (
    document    text,
    place       text,
    stage       text NOT NULL,
    reason      text NOT NULL
);
