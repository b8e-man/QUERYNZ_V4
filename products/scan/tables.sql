-- The scan's own state (design rule 2: a product writes its own state only):
-- every run, its lines and its citations. Only ever added to; a run is
-- superseded by a later one, never deleted. {schema} is swapped at apply.
create table if not exists {schema}.runs (
    run_id      serial primary key,
    scan        text not null,
    version     text not null,
    question    text not null,
    started_at  timestamptz not null,
    finished_at timestamptz,
    seconds     numeric,
    lines       integer,
    limited     integer,            -- the --limit given, when the run was cut short on purpose
    starts      jsonb,              -- the views the scan started from, each with its own time and count
    settings    jsonb not null,     -- the trust settings in force
    views       jsonb,              -- every view read, with its loaded_at (or built_at) at the run
    grades      jsonb,              -- {confirmed, near, contested}
    hubs        integer,
    problems    jsonb,              -- the presentation rules' findings; a run with any is refused by the surface
    note        text,
    sql         text
);
create table if not exists {schema}.lines (
    run_id   integer not null references {schema}.runs (run_id),
    n        integer not null,
    grade    text not null,
    reasons  jsonb not null,
    hubs     jsonb not null,
    cites    integer[] not null,
    steps    jsonb not null,
    primary key (run_id, n)
);
create index if not exists lines_grade on {schema}.lines (run_id, grade, n);
create table if not exists {schema}.citations (
    run_id   integer not null references {schema}.runs (run_id),
    n        integer not null,
    view     text not null,
    key      text not null,
    register text not null,
    document text,
    page     integer,
    place    text,
    url      text,
    primary key (run_id, n)
);
