-- links: what later modules and the board read (plan 4.2, 4.9). Confirmed first,
-- near after; each link with its rule, its evidence and the reason it is only
-- near. A link whose pair carries a `not the same` or `contested` decision is
-- shown as near, with the decision as the reason. No home address: nothing in
-- links carries one. The build runs this text with `links.` swapped for its
-- scratch schema and `pub.` for its own.
CREATE OR REPLACE VIEW pub.links AS
WITH last_decision AS (
    SELECT DISTINCT ON (row_a, row_b) row_a, row_b, verdict, made_by, decision_id
    FROM links.decisions ORDER BY row_a, row_b, decision_id DESC)
SELECT l.link_id, l.row_a, l.row_b, l.rule, l.evidence,
       CASE WHEN d.verdict IN ('not the same', 'contested') THEN 'near' ELSE l.grade END AS grade,
       CASE WHEN d.verdict = 'not the same' THEN 'a decision says these are not the same person (' || d.made_by || ')'
            WHEN d.verdict = 'contested' THEN 'a decision contests this link (' || d.made_by || ')'
            ELSE l.reason END AS reason,
       coalesce(w.flags, '[]'::jsonb) AS watch,
       d.verdict AS decision, l.built_at
FROM links.links l
LEFT JOIN last_decision d ON d.row_a = l.row_a AND d.row_b = l.row_b
LEFT JOIN links.watch w ON w.link_id = l.link_id;

CREATE OR REPLACE VIEW pub.groups AS
SELECT group_id, row_key, contested, built_at, settings FROM links.groups;

CREATE OR REPLACE VIEW pub.decisions AS
SELECT decision_id, row_a, row_b, verdict, made_by, made_on, made_at FROM links.decisions;

-- The search table across registers (plan 4.9): every person and organisation
-- name in every published register, under the one shared reading, pointing at
-- its row. Keys only; the row itself is read from its own view.
CREATE OR REPLACE VIEW pub.names AS
SELECT ref, register, view, key, kind, name_filed, name_key, fl_key, full_key, has_middle, entity_ref, politician
FROM links.rows;

-- The old estate's judgments, copied exactly and mapped beside (contract: links, 5).
CREATE OR REPLACE VIEW pub.old_decisions AS
SELECT old_id, source, verdict, row_a, row_b, mapped_how, copied, copied_at FROM links.old_decisions;
