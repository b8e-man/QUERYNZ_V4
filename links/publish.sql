-- links: what later modules and the board read (plan 4.2, 4.9). Confirmed first,
-- near after; each link with its rule, its evidence and the reason it is only
-- near. A link whose pair carries a `not the same` or `contested` decision is
-- shown as near, with the decision as the reason.
-- A third grade, `related` (ruling 106): the two rows are two entities, and
-- `relation` says what the one is to the other. Today one relation, "succeeded
-- by" (`successor-name@1`): two companies, the earlier registered succeeded by
-- the later; `evidence.earlier` and `evidence.later` name which is which, and
-- `evidence.shared_rows` the people confirmed on both. A related link is never
-- an identity: the groups do not follow it, and a reader that knows only
-- confirmed and near must not show it as confirmed. A `contested` decision on
-- the pair shows it as near; `not the same` agrees with it and changes nothing. No home address: nothing in
-- links carries one. The build runs this text with `links.` swapped for its
-- scratch schema and `pub.` for its own.
CREATE OR REPLACE VIEW pub.links AS
WITH last_decision AS (
    SELECT DISTINCT ON (row_a, row_b) row_a, row_b, verdict, made_by, decision_id
    FROM links.decisions ORDER BY row_a, row_b, decision_id DESC)
SELECT l.link_id, l.row_a, l.row_b, l.rule, l.evidence,
       CASE WHEN l.grade = 'related' AND d.verdict IS DISTINCT FROM 'contested' THEN l.grade
            WHEN d.verdict IN ('not the same', 'contested') THEN 'near' ELSE l.grade END AS grade,
       CASE WHEN l.grade = 'related' AND d.verdict IS DISTINCT FROM 'contested' THEN l.reason
            WHEN d.verdict = 'not the same' THEN 'a decision says these are not the same person (' || d.made_by || ')'
            WHEN d.verdict = 'contested' THEN 'a decision contests this link (' || d.made_by || ')'
            ELSE l.reason END AS reason,
       coalesce(w.flags, '[]'::jsonb) AS watch,
       d.verdict AS decision, l.built_at, l.relation
FROM links.links l
LEFT JOIN last_decision d ON d.row_a = l.row_a AND d.row_b = l.row_b
LEFT JOIN links.watch w ON w.link_id = l.link_id;

CREATE OR REPLACE VIEW pub.groups AS
SELECT group_id, row_key, contested, built_at, settings FROM links.groups;

CREATE OR REPLACE VIEW pub.decisions AS
SELECT decision_id, row_a, row_b, verdict, made_by, made_on, made_at FROM links.decisions;

-- The search table across registers (plan 4.9): every person and organisation
-- name in every published register, under the one shared reading, pointing at
-- its row. Keys only; the row itself is read from its own view (by `view` and
-- `key`: a coupled donor's part, ref '<donor ref>#<n>', carries its donor
-- row's view and key, and `part_of` names the donor row; ruling 73).
CREATE OR REPLACE VIEW pub.names AS
SELECT ref, register, view, key, kind, name_filed, name_key, fl_key, full_key, has_middle, entity_ref, politician, part_of
FROM links.rows;

-- The old estate's judgments, copied exactly and mapped beside (contract: links, 5).
CREATE OR REPLACE VIEW pub.old_decisions AS
SELECT old_id, source, verdict, row_a, row_b, mapped_how, copied, copied_at FROM links.old_decisions;

-- One row per entity (ruling 123): a group, or a row in no group as a single-row
-- entity. `entity_id` is the group id or the lone row's ref; `display_name` is
-- chosen by the one ordering every reader shares (links/pane.md: the most
-- words, then the most characters, then the smallest ref COLLATE "C", among
-- the entity's rows of pub.names); `registers` is sorted; `contested` is the
-- group's; `politician` where any row is. A reader draws the entity from here
-- and never re-derives its name. Built whole beside pub.groups.
CREATE OR REPLACE VIEW pub.entities AS
SELECT entity_id, kind, display_name, rows, registers, contested, politician, built_at FROM links.entities;
