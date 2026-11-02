-- registers/linz (step 8.3): the reading's tables, rebuilt whole every load from each source's newest finished pull.
-- The capture's own tables (pulls, pages, surveys) are made by capture.capture_sql. No table holds an address or a
-- geometry (hard limit 15): a title's land district is a place, an owner is a name.

CREATE TABLE linz.titles (
    key                    text NOT NULL,           -- linz/titles/<title_no>
    id                     bigint,
    title_no               text NOT NULL,
    status                 text,
    type                   text,
    land_district          text,
    issue_date             timestamptz,
    guarantee_status       text,
    estate_description     text,
    number_owners          integer,
    spatial_extents_shared text,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE linz.owners (
    key                text NOT NULL,               -- linz/owners/<id>
    id                 bigint,
    tte_id             bigint,                      -- the title estate the owner holds a share of
    title_no           text NOT NULL,
    title_key          text NOT NULL,
    status             text,
    land_district      text,
    estate_share       text,
    owner_type         text,                        -- as LINZ states it
    kind               text NOT NULL,               -- corporate | individual | unstated
    name               text,                        -- the corporate name, or the other names then the surname
    prime_surname      text,
    prime_other_names  text,
    name_suffix        text,
    corporate_name     text,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE linz.place_names (
    key                    text NOT NULL,           -- linz/place_names/<name_id>
    name_id                bigint,
    feat_id                bigint,
    name                   text NOT NULL,
    status                 text,
    feat_type              text,
    maori_name             text,
    land_district          text,
    territorial_authority  text,
    region                 text,
    crd_latitude           double precision,
    crd_longitude          double precision,
    info_origin            text,
    info_description       text,
    treaty_legislation     text,
    nzgb_ref               text,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE linz.read_set_aside (
    source   text NOT NULL,
    document text NOT NULL,
    place    text,
    stage    text NOT NULL,
    reason   text NOT NULL
);

-- what each source's load read from: the pull, the count the service stated, the rows landed and read
CREATE TABLE linz.loaded_pulls (
    source  text NOT NULL,
    pull_id text NOT NULL,
    stated  integer,
    landed  integer NOT NULL,
    read    integer NOT NULL,
    aside   integer NOT NULL
);
