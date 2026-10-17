-- The three tables of links (plan 1.9; docs/contracts/links.md).
-- There is no stored person: a person is what you get by reading these together.
-- Schema `links` (and `links_private` for anything that carries a home address;
-- nothing here does). Idempotent.

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
-- rebuilt whole whenever links or decisions change; edited by nobody

CREATE TABLE IF NOT EXISTS links.old_decisions (
    old_id       text PRIMARY KEY,         -- the old estate's ledger id
    copied       jsonb NOT NULL,           -- the old record, exactly as it was
    row_a        text,                     -- the new stable keys, mapped by content; NULL until mapped
    row_b        text,
    copied_at    timestamptz NOT NULL DEFAULT now()
);
