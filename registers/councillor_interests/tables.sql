-- registers/councillor_interests: every table this lane owns, in `councillor_interests`, in two parts. The capture's
-- record (capture.py makes it; never wiped): no capture table holds a row of the source; every page and document stays
-- in the document store verbatim by sha256. The reading's tables (load.py drops and makes them again at every load)
-- come from structured HTML registers only: a PDF register is held and never read (ruling 79). A real-property
-- declaration is never put in a table (queue: may-the-interests-register-s-real-property-declarations-be-shown, answer
-- no), and a member's home address, phone or email is never kept (hard limit 15): such a category is counted by its
-- heading and nothing under it is read. So no private twin.

-- ── the capture ──────────────────────────────────────────────────────────────

-- one row per ask: a council's landing page, a register page, a register document
CREATE TABLE IF NOT EXISTS councillor_interests.capture_items (
    item_id   bigserial PRIMARY KEY,
    council   text NOT NULL,
    url       text NOT NULL,
    kind      text NOT NULL CHECK (kind IN ('page', 'document')),
    found_on  text,                                  -- the page that linked it; NULL for the survey's own address
    asked_at  timestamptz NOT NULL DEFAULT now(),
    status    integer,
    sha256    text,                                  -- NULL when the read failed
    why       text
);

-- a host not asked again until a session reads why (hard limit 6)
CREATE TABLE IF NOT EXISTS councillor_interests.capture_held_hosts (
    host   text PRIMARY KEY,
    since  timestamptz NOT NULL DEFAULT now(),
    why    text NOT NULL
);

CREATE TABLE IF NOT EXISTS councillor_interests.capture_set_aside (
    item    text NOT NULL,
    stage   text NOT NULL,
    reason  text NOT NULL,
    at      timestamptz NOT NULL DEFAULT now()
);

-- ── the reading
-- load.py drops these and makes them again at every load, from the newest capture of each page.

-- one row per council: how it publishes its register, and what the estate holds of it
CREATE TABLE IF NOT EXISTS councillor_interests.registers (
    council          text PRIMARY KEY,
    host             text NOT NULL,
    form             text NOT NULL,                  -- html register | pdf register | per-member files | linked, not found | not yet captured | not found | not reached | held: its terms bar automated access
    landing_url      text,
    landing_sha256   text,
    documents_held   integer NOT NULL DEFAULT 0,     -- register documents landed (held, never read)
    members_read     integer NOT NULL DEFAULT 0,     -- members read from a structured page
    why              text,                           -- not reached: the held host's reason
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- every register document held: the council, its address, its hash (held, never read)
CREATE TABLE IF NOT EXISTS councillor_interests.documents (
    sha256      text PRIMARY KEY,
    council     text NOT NULL,
    url         text NOT NULL,
    found_on    text,
    asked_at    timestamptz NOT NULL,
    loaded_at   timestamptz NOT NULL DEFAULT now()
);

-- one row per member and published category, from a structured page: the category as published, and its entries'
-- text only where the category is not real property, a home address or a contact
CREATE TABLE IF NOT EXISTS councillor_interests.interests (
    key              text PRIMARY KEY,               -- <council>/<member>/<category ordinal>
    council          text NOT NULL,
    member           text NOT NULL,                  -- as the page prints the member's name
    role             text,                           -- Mayor, Councillor, …, as printed
    category         text NOT NULL,                  -- the heading as published
    entries          text[] NOT NULL DEFAULT '{}',   -- the entries as printed; empty where the page says nil
    as_at            text,                           -- the register's date as printed
    document         text NOT NULL,
    page             integer NOT NULL DEFAULT 1,
    place            text NOT NULL,
    url              text NOT NULL,
    read_from        text NOT NULL,
    reader           text NOT NULL,
    profile          text NOT NULL,
    profile_version  integer NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

-- the categories a reading met and did not read, by heading and count only (never a value)
CREATE TABLE IF NOT EXISTS councillor_interests.read_withheld (
    council   text NOT NULL,
    category  text NOT NULL,
    why       text NOT NULL,
    members   integer NOT NULL
);

CREATE TABLE IF NOT EXISTS councillor_interests.read_set_aside (
    document  text NOT NULL,
    place     text,
    stage     text NOT NULL,
    reason    text NOT NULL
);
