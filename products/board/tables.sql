-- The board's own state (plan step 4.9: a pane can be pinned, a path can be
-- saved). Schema `board` in querynz_v4; a build session applies it to its
-- scratch schema in the sample. Nothing a person typed is deleted: there is
-- no DELETE and no UPDATE anywhere in the board. {schema} is substituted.
CREATE TABLE IF NOT EXISTS {schema}.pins (
    pin_id      bigserial PRIMARY KEY,
    view        text NOT NULL,            -- the pub view
    key         text NOT NULL,            -- the row's stable key
    title       text NOT NULL,            -- as the pane showed it (never a suppressed name: the pane never showed one)
    note        text NOT NULL DEFAULT '',
    made_at     timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS {schema}.paths (
    path_id     bigserial PRIMARY KEY,
    name        text NOT NULL,
    query       text NOT NULL,            -- the search the path began from
    path        text NOT NULL,            -- the panes walked: view:key, one per line
    made_at     timestamptz NOT NULL DEFAULT now()
);
-- ruling 119: the check boxes the path was saved under, as its address carries them (search.Boxes.params, the folds
-- by hand among them), so a saved path reopens as it was seen; '' for a path saved before, which opens as the first view
ALTER TABLE {schema}.paths ADD COLUMN IF NOT EXISTS boxes text NOT NULL DEFAULT '';
