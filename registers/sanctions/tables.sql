-- registers/sanctions: every table this lane owns, in `sanctions` and its private twin, in two parts. The capture's
-- record (capture.py makes it; never wiped): the lists stay in the document store verbatim by sha256. The reading's
-- tables (load.py drops and makes them again at every load). Every element or cell of a listed record is kept whole
-- in the private twin (`sanctions_private.details`, ruling 142): addresses, passport and identity numbers and the
-- lists' narrative comments among them. The published columns carry an address's country and nothing finer.

-- ── the capture ──────────────────────────────────────────────────────────────

-- the listing: one row per document landed, the list itself (`role` list) or a document about it (its terms, its
-- page), with the version the publisher gives it and how it came (fetched through the gate, or by a person's hand)
CREATE TABLE IF NOT EXISTS sanctions.capture_documents (
    list_id     text NOT NULL CHECK (list_id IN ('mfat-russia', 'un-sc', 'nz-police-tsa')),
    role        text NOT NULL,                     -- list, page-1373, page-1267, terms-of-use, copyright, register-page
    url         text NOT NULL,
    sha256      text NOT NULL,
    version     text,                              -- the publisher's own: dateGenerated, the day in the file name or page
    new         boolean NOT NULL,
    how         text NOT NULL,
    by_whom     text,                              -- for a file landed by hand
    at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sanctions.capture_set_aside (
    list_id  text,
    item     text NOT NULL,
    stage    text NOT NULL,
    reason   text NOT NULL,
    at       timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load. Each row cites the list document's sha256, page 1, its
-- place in it (`INDIVIDUALS/INDIVIDUAL[3]`, `Individuals!row 7`), the reader and the profile.

-- one row per list read: the version and the list's own count where it states one
CREATE TABLE IF NOT EXISTS sanctions.lists (
    list_id        text PRIMARY KEY,
    name           text NOT NULL,
    publisher      text NOT NULL,
    law            text NOT NULL,
    document       text NOT NULL,
    version        text,
    stated         integer,                        -- the publisher's own count of current listings, where it states one
    stated_where   text,                           -- where that count was read
    listings       integer NOT NULL,               -- current listings read
    ended          integer NOT NULL,               -- revoked or expired listings read
    set_aside      integer NOT NULL,
    profile        text NOT NULL,
    profile_version integer NOT NULL,
    loaded_at      timestamptz NOT NULL DEFAULT now()
);

-- one row per listed person or entity per list
CREATE TABLE IF NOT EXISTS sanctions.listings (
    key               text PRIMARY KEY,            -- sanctions/<list>/<the list's own identifier>
    list_id           text NOT NULL,
    list_ref          text NOT NULL,               -- the list's own identifier (QDi.001, the Police ID, MFAT's)
    other_ref         text,                        -- another list's identifier the row gives (the UN's, in Police's)
    kind              text NOT NULL CHECK (kind IN ('individual', 'entity')),
    status            text NOT NULL CHECK (status IN ('designated', 'revoked', 'expired')),
    name              text NOT NULL,               -- as published
    aliases           text[] NOT NULL,             -- as published, each once
    original_script   text,
    titles            text[] NOT NULL,
    positions         text[] NOT NULL,             -- the UN's DESIGNATION: a public role
    nationalities     text[] NOT NULL,
    birth_dates       text[] NOT NULL,             -- as the list gives them: a day, a year, a range
    birth_countries   text[] NOT NULL,
    countries         text[] NOT NULL,             -- the countries the list names for its addresses; nothing finer
    regime            text,                        -- the UN regime, the Police list part, MFAT's sanction types
    basis             text NOT NULL,               -- the designation's legal basis, as the lane states it per list
    designated_on     date,
    renewed_on        date[] NOT NULL,
    expires_on        date,
    ended_on          date,                        -- revoked or expired on
    updated_on        date,                        -- the list's last amendment of the row, where stated
    list_version      text,
    document text NOT NULL, page integer NOT NULL, place text NOT NULL, read_from text NOT NULL, reader text NOT NULL,
    profile text NOT NULL, profile_version integer NOT NULL, loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sanctions.read_set_aside (
    list_id   text NOT NULL,
    document  text NOT NULL,
    place     text NOT NULL,
    stage     text NOT NULL,
    reason    text NOT NULL
);

-- every element or cell of each listed record, whole, as the list prints it (ruling 142, 4 November 2026): the
-- addresses, passport and identity numbers and narrative comments the published row does not carry are here, keyed by
-- the row; the private twin, never granted to the session or product logins
CREATE TABLE IF NOT EXISTS sanctions_private.details (
    key       text NOT NULL,                       -- the listing's key
    n         integer NOT NULL,                    -- the value's order in the record
    field     text NOT NULL,                       -- its element path (`INDIVIDUAL_ADDRESS[1]/STREET`) or `row R header`
    value     text NOT NULL,                       -- as printed
    document  text NOT NULL,
    place     text NOT NULL,
    PRIMARY KEY (key, n)
);
