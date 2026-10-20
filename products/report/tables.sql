-- The report's own state (plan step 5.1: a report can be saved and its memo
-- kept). Schema `subject_report` in querynz_v4; a build session applies it to
-- its scratch schema in the sample. Nothing a person typed is deleted: there is
-- no DELETE and no UPDATE anywhere in the report. {schema} is substituted.
CREATE TABLE IF NOT EXISTS {schema}.reports (
    report_id   bigserial PRIMARY KEY,
    ref         text NOT NULL,             -- the subject row, register:key
    template    text NOT NULL,             -- the template's name
    version     text NOT NULL,             -- the template's version
    as_of       date NOT NULL,
    title       text NOT NULL,             -- the subject as the memo showed it (never a suppressed name: the memo never showed one)
    note        text NOT NULL DEFAULT '',  -- what the person who saved it typed
    memo        text NOT NULL,             -- the plain-text memo, as printed
    report      jsonb NOT NULL,            -- the report without the rows themselves
    problems    integer NOT NULL DEFAULT 0,
    made_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS reports_ref ON {schema}.reports (ref, made_at);
