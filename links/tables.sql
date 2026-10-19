-- The tables of links (plan 1.9 and 4.2; docs/contracts/links.md).
-- There is no stored person: a person is what you get by reading these together.
-- Schema `links` (and `links_private` for anything that carries a home address;
-- nothing here does). Idempotent. A build runs the same text with `links.`
-- swapped for its scratch schema (links.ddl).

CREATE TABLE IF NOT EXISTS links.links (
    link_id      bigserial PRIMARY KEY,
    row_a        text NOT NULL,            -- a register row's stable key, schema-qualified: 'companies:1234-D5'
    row_b        text NOT NULL,
    rule         text NOT NULL,            -- the rule that joined them, by name and version: 'full-name@1'
    evidence     jsonb NOT NULL,           -- what the rule saw, enough to show a reader
    grade        text NOT NULL CHECK (grade IN ('confirmed', 'near')),
    reason       text,                     -- for a near link: why it is only near
    built_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT links_pair_order CHECK (row_a < row_b),
    UNIQUE (row_a, row_b, rule)
);
CREATE INDEX IF NOT EXISTS links_row_b ON links.links (row_b);
-- a rebuild deletes and refills millions of rows; autovacuum's truncation of the emptied pages took an exclusive lock
-- against the refill and deadlocked it twice (20 October 2026). The pages are reused on the next build.
ALTER TABLE links.links SET (vacuum_truncate = off);

CREATE TABLE IF NOT EXISTS links.decisions (
    decision_id  bigserial PRIMARY KEY,
    row_a        text NOT NULL,
    row_b        text NOT NULL,
    verdict      text NOT NULL CHECK (verdict IN ('same', 'not the same', 'contested')),
    made_by      text NOT NULL,            -- 'review-agent@2', 'correction:<id>', 'suppression:<id>', 'old-estate:<ledger id>', or a person
    made_on      jsonb NOT NULL,           -- the evidence the decision rested on
    made_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT decisions_pair_order CHECK (row_a < row_b)
);
CREATE INDEX IF NOT EXISTS decisions_rows ON links.decisions (row_a, row_b);
-- only ever added to: no UPDATE, no DELETE
CREATE OR REPLACE FUNCTION links.decisions_are_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'links.decisions is only ever added to'; END $$;
DROP TRIGGER IF EXISTS decisions_append_only ON links.decisions;
CREATE TRIGGER decisions_append_only BEFORE UPDATE OR DELETE ON links.decisions
    FOR EACH ROW EXECUTE FUNCTION links.decisions_are_append_only();

CREATE TABLE IF NOT EXISTS links.groups (
    group_id     text NOT NULL,            -- the smallest row key in the group
    row_key      text NOT NULL,
    contested    boolean NOT NULL DEFAULT false,   -- the watch flagged the group as a whole
    built_at     timestamptz NOT NULL,
    settings     jsonb NOT NULL,           -- the two trust settings the build ran with
    PRIMARY KEY (row_key)
);
CREATE INDEX IF NOT EXISTS groups_group ON links.groups (group_id);
-- rebuilt whole whenever links or decisions change; edited by nobody

CREATE TABLE IF NOT EXISTS links.old_decisions (
    old_id       text PRIMARY KEY,         -- the old estate's ledger id: '<table>:<id>'
    copied       jsonb NOT NULL,           -- the old record, exactly as it was
    row_a        text,                     -- the new stable keys, mapped by content; NULL until mapped
    row_b        text,
    copied_at    timestamptz NOT NULL DEFAULT now(),
    source       text,                     -- the old table: donor_anchors, roster_identity_folds, review_verdicts
    verdict      text,                     -- what it says about the pair: same, not the same, contested; NULL when it names no pair
    mapped_how   text                      -- how the two rows were found, or why they were not (a card)
);

-- The rows the rules read: every person row of every published register,
-- under the one shared reading of names (keys.names). Rebuilt with the registers.
CREATE TABLE IF NOT EXISTS links.rows (
    ref          text PRIMARY KEY,         -- '<register>:<key>'
    register     text NOT NULL,            -- the lane folder name, as the board uses it
    view         text NOT NULL,            -- the pub view the row is in
    key          text NOT NULL,
    kind         text NOT NULL,            -- person | organisation | estate | party
    name_filed   text NOT NULL,
    given        text, middle text, family text,
    name_key     text NOT NULL,            -- keys.names.person_key / organisation_key
    fl_key       text,                     -- given and family, folded: the first-and-last key
    full_key     text,                     -- given, middle names and family in order, folded
    has_middle   boolean NOT NULL DEFAULT false,
    entity_ref   text,                     -- the company, society or party row the role or gift sits on
    started_on   date, ended_on date,      -- as filed
    election     text, electorate text,
    politician   boolean NOT NULL DEFAULT false,
    document     text
);
CREATE INDEX IF NOT EXISTS rows_fl ON links.rows (fl_key);
CREATE INDEX IF NOT EXISTS rows_full ON links.rows (full_key);
CREATE INDEX IF NOT EXISTS rows_entity ON links.rows (entity_ref);
CREATE INDEX IF NOT EXISTS rows_name ON links.rows (name_key);
CREATE INDEX IF NOT EXISTS rows_view_name ON links.rows (view, lower(name_filed));   -- the old decisions map by filed name

-- A company's registered office under the one reading of addresses (keys.addresses).
-- No person's address: the address arm reads the office of the company a role sits on.
CREATE TABLE IF NOT EXISTS links.entity_addresses (
    entity_ref   text NOT NULL,
    address_key  text NOT NULL,
    kind         text NOT NULL,            -- 'registered office'
    started_on   date,
    last_file    text,
    in_latest    boolean,
    region       text,                     -- the postcode's first digit, for the watch
    source_key   text NOT NULL,            -- the pub.company_addresses row
    PRIMARY KEY (entity_ref, address_key, source_key)
);
CREATE INDEX IF NOT EXISTS entity_addresses_key ON links.entity_addresses (address_key);

-- Companies by the organisation key, for the name match a donation row needs
-- (it carries no official number).
CREATE TABLE IF NOT EXISTS links.org_names (
    entity_ref   text NOT NULL,
    org_key      text NOT NULL,
    registered_on date, removed_on date,
    PRIMARY KEY (entity_ref, org_key)
);
CREATE INDEX IF NOT EXISTS org_names_key ON links.org_names (org_key);

-- The watch: signs that a confirmed link covers two people. Regenerable.
CREATE TABLE IF NOT EXISTS links.watch (
    link_id      bigint PRIMARY KEY,
    flags        jsonb NOT NULL            -- [{kind, text, evidence}]; empty = nothing contests the link
);

-- The test pairs of plan 4.3, drawn from the registers; no person labels them.
CREATE TABLE IF NOT EXISTS links.test_pairs (
    pair_id      bigserial PRIMARY KEY,
    kind         text NOT NULL,            -- the kind of pair, by name
    truth        text NOT NULL CHECK (truth IN ('two people', 'one person')),
    band         text NOT NULL,            -- rare | middling | common
    row_a        text NOT NULL, row_b text NOT NULL,
    basis        jsonb NOT NULL,           -- what makes the truth known
    drawn_at     timestamptz NOT NULL DEFAULT now(),
    seed         integer NOT NULL,
    CONSTRAINT test_pairs_order CHECK (row_a < row_b),
    UNIQUE (kind, row_a, row_b)
);

-- The measurements, one row each per build.
CREATE TABLE IF NOT EXISTS links.measurements (
    measured_at  timestamptz NOT NULL DEFAULT now(),
    name         text NOT NULL,
    figures      jsonb NOT NULL,
    PRIMARY KEY (measured_at, name)
);

-- The review agent's readings of confirmed links: an agent's judgment, recorded, not applied until track C passes it.
CREATE TABLE IF NOT EXISTS links.readings (
    reading_id   bigserial PRIMARY KEY,
    link_id      bigint NOT NULL,
    row_a        text NOT NULL, row_b text NOT NULL,
    agent        text NOT NULL,            -- 'review-agent@1 (<model>)' or 'session:<name>'
    verdict      text NOT NULL CHECK (verdict IN ('no reason to doubt', 'contested', 'not the same')),
    reasoning    text,
    web_searched boolean NOT NULL DEFAULT false,
    read_at      timestamptz NOT NULL DEFAULT now()
);
