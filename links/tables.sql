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
    grade        text NOT NULL CONSTRAINT links_grade_check CHECK (grade IN ('confirmed', 'near', 'related')),
    reason       text,                     -- for a near link: why it is only near
    built_at     timestamptz NOT NULL DEFAULT now(),
    relation     text,                     -- for a related link (ruling 106): what the one row is to the other, read row by row in `evidence`
    CONSTRAINT links_pair_order CHECK (row_a < row_b),
    CONSTRAINT links_relation_graded CHECK ((grade = 'related') = (relation IS NOT NULL)),
    UNIQUE (row_a, row_b, rule)
);
CREATE INDEX IF NOT EXISTS links_row_b ON links.links (row_b);
-- a rebuild deletes and refills millions of rows; autovacuum's truncation of the emptied pages took an exclusive lock
-- against the refill and deadlocked it twice (20 October 2026). The pages are reused on the next build.
ALTER TABLE links.links SET (vacuum_truncate = off);
-- The third grade (ruling 106, links-3): a relation between two rows that is not an identity ('succeeded by'). A table made
-- before it has the two-grade check and no `relation`; the check is replaced once, only where it still lacks the grade.
ALTER TABLE links.links ADD COLUMN IF NOT EXISTS relation text;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'links.links'::regclass AND conname = 'links_grade_check'
                   AND pg_get_constraintdef(oid) LIKE '%related%') THEN
        ALTER TABLE links.links DROP CONSTRAINT IF EXISTS links_grade_check;
        ALTER TABLE links.links ADD CONSTRAINT links_grade_check CHECK (grade IN ('confirmed', 'near', 'related'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid = 'links.links'::regclass AND conname = 'links_relation_graded') THEN
        ALTER TABLE links.links ADD CONSTRAINT links_relation_graded CHECK ((grade = 'related') = (relation IS NOT NULL));
    END IF;
END $$;

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
-- Columns added since the table first shipped (card the-links-tables-do-not-migrate-an-existing-column):
-- CREATE TABLE IF NOT EXISTS leaves an existing table as it was, so each later column is added here too.
ALTER TABLE links.old_decisions ADD COLUMN IF NOT EXISTS source text;
ALTER TABLE links.old_decisions ADD COLUMN IF NOT EXISTS verdict text;
ALTER TABLE links.old_decisions ADD COLUMN IF NOT EXISTS mapped_how text;

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
    document     text,
    part_of      text                      -- a coupled donor row's part (ruling 73): the donor row's ref; NULL on every filed row
);
ALTER TABLE links.rows ADD COLUMN IF NOT EXISTS part_of text;
CREATE INDEX IF NOT EXISTS rows_fl ON links.rows (fl_key);
CREATE INDEX IF NOT EXISTS rows_part_of ON links.rows (part_of) WHERE part_of IS NOT NULL;
CREATE INDEX IF NOT EXISTS rows_full ON links.rows (full_key);
CREATE INDEX IF NOT EXISTS rows_entity ON links.rows (entity_ref);
CREATE INDEX IF NOT EXISTS rows_name ON links.rows (name_key);
CREATE INDEX IF NOT EXISTS rows_view_name ON links.rows (view, lower(name_filed));   -- the old decisions map by filed name
CREATE INDEX IF NOT EXISTS rows_register ON links.rows (register, view);         -- one register's rows are refilled alone (rule 10)

-- The rows' catch log (design, register rule 8): per published view, the rows read, the rows written and the
-- rows set aside with the reason; `check.py` counts each view again and fails when the links have fallen behind a lane.
CREATE TABLE IF NOT EXISTS links.rows_catch (
    view         text PRIMARY KEY,
    register     text NOT NULL,
    read         integer NOT NULL,
    written      integer NOT NULL,
    set_aside    integer NOT NULL,
    reasons      jsonb NOT NULL,
    gathered_at  timestamptz NOT NULL DEFAULT now()
);

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

-- Bodies by the organisation key on four registers (ruling 114): every row of pub.companies (all its registers), pub.societies,
-- pub.limited_partnerships and pub.charities, each with its own register's dates, and `body`, the one entity it is: a row whose
-- register carries a Companies Office body's NZBN (or a charity its company number) is that body. The donation rules
-- `organisation-sole-company@2` and `organisation-one-live-company@2` read it; the company rules read org_names. Regenerable.
CREATE TABLE IF NOT EXISTS links.bodies (
    entity_ref   text NOT NULL,            -- the row on its own register: 'companies:…', 'societies:…', 'limited_partnerships:…', 'charities:…'
    org_key      text NOT NULL,
    register     text NOT NULL,            -- companies | societies | limited_partnerships | charities
    kind         text,                     -- a Companies Office row's own register (pub.companies.register); NULL on the others
    number       text, nzbn text, name text,
    registered_on date, removed_on date,   -- a charity's: registered and deregistered as a charity
    removal_undated boolean NOT NULL DEFAULT false,   -- the status says removed, dissolved or deregistered and no date is published
    body         text NOT NULL,            -- the entity: the Companies Office row where the body has one, else this row
    PRIMARY KEY (entity_ref, org_key)
);
CREATE INDEX IF NOT EXISTS bodies_key ON links.bodies (org_key);
CREATE INDEX IF NOT EXISTS bodies_body ON links.bodies (body);

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
    read_at      timestamptz NOT NULL DEFAULT now(),
    run_id       text,                     -- the scoring or review run this reading belongs to
    pair_id      bigint,                   -- a test pair's id when the reading scores the agent (links.test_pairs); NULL for a watched link
    kind         text,                     -- the test pair's kind, and its truth and band, copied so a score needs no join
    truth        text,
    band         text,
    screen       text,                     -- what the screen said before the model was asked, or 'model' when it decided nothing
    evidence     jsonb,                    -- what the reader was shown (registered offices and roles; never a home address)
    citations    jsonb,                    -- the web pages the verdict cites, each fetched in this run; [] when none
    model        text,                     -- the served model, read back
    seconds      real
);
-- columns added since the table first shipped (track C; card the-links-tables-do-not-migrate-an-existing-column)
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS run_id text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS pair_id bigint;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS kind text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS truth text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS band text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS screen text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS evidence jsonb;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS citations jsonb;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS model text;
ALTER TABLE links.readings ADD COLUMN IF NOT EXISTS seconds real;
CREATE INDEX IF NOT EXISTS readings_run ON links.readings (run_id);
CREATE INDEX IF NOT EXISTS readings_link ON links.readings (link_id);

-- The scores of the review agent on the test pairs (track C), one row per scoring run: the figures the pass mark reads.
CREATE TABLE IF NOT EXISTS links.scores (
    run_id       text PRIMARY KEY,
    agent        text NOT NULL,            -- 'review-agent@N'
    fingerprint  text NOT NULL,            -- a hash of everything that decides a verdict; a changed judgment is a new measurement
    model        text,
    scored_at    timestamptz NOT NULL DEFAULT now(),
    figures      jsonb NOT NULL,           -- by truth and band: pairs, wrongly split, caught; the pass mark and whether it passed
    passed       boolean NOT NULL
);
