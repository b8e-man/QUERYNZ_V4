-- registers/linz (step 8.3): the reading's tables, rebuilt whole every load from each source's newest finished pull.
-- The capture's own tables (pulls, pages, surveys) are made by capture.capture_sql. No table of `linz` holds an address
-- or a geometry: a title's land district is a place, an owner is a name. Each title's street address is in
-- `linz_private` only (the tables at the end), never published (hard limit 15 binds a product's surface, ruling 102).

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

-- ── linz_private: the property spine and each title's street address (Arthur, 3 November 2026: "gather everything") ──
-- Never published, never seen by a reader login (support.db: a `_private` schema). Every catalogue source read whole has
-- its own table here too, made by load.whole_sql (every attribute as JSON, the geometry as GeoJSON text and its box).

-- table 113970, NZ Properties: Property-Title Reference: a title on a unit of property (a rating unit)
CREATE TABLE linz_private.property_titles (
    key                  text NOT NULL,             -- linz/property_titles/<id>
    id                   bigint,
    title_no             text NOT NULL,
    unit_of_property_id  text NOT NULL,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

-- table 115638, NZ Properties: Property-Address Reference: an address on a unit of property
CREATE TABLE linz_private.property_addresses (
    key                  text NOT NULL,             -- linz/property_addresses/<id>
    id                   bigint,
    unit_of_property_id  text NOT NULL,
    address_id           bigint NOT NULL,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

-- layer 123113, NZ Addresses (AIMS), read whole from 4 November 2026: the address as LINZ gives it, every attribute,
-- and its point (longitude xmin = xmax, latitude ymin = ymax, NZGD2000)
CREATE TABLE linz_private.addresses (
    key                  text NOT NULL,             -- linz/addresses/<address_id>
    address_id           bigint NOT NULL,
    full_address         text NOT NULL,
    address_lifecycle    text,
    props                jsonb,                     -- every attribute as LINZ gives it (a pull asked whole)
    geom_type            text,
    geom                 text,                      -- the GeoJSON geometry
    xmin double precision, ymin double precision, xmax double precision, ymax double precision,
    document text NOT NULL, page integer, place text, read_from text, reader text, profile text, profile_version integer,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

-- each title's street address: title → unit of property → address id → address, one row per title and address. A unit
-- of property carrying several titles or several addresses says so (titles_on_property, addresses_on_property): the join
-- is the property's, not the title's own. The source rows are named by their keys and their landed pages.
CREATE TABLE linz_private.title_addresses (
    title_no                   text NOT NULL,
    address_id                 bigint NOT NULL,
    full_address               text NOT NULL,
    address_lifecycle          text,
    unit_of_property_id        text NOT NULL,
    joined_by                  text NOT NULL,     -- how it was joined: load.JOINED_BY
    titles_on_property         integer NOT NULL,
    addresses_on_property      integer NOT NULL,
    property_title_key         text NOT NULL,
    property_address_key       text NOT NULL,
    address_key                text NOT NULL,
    property_title_document    text NOT NULL,
    property_address_document  text NOT NULL,
    address_document           text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);

-- each title's street address by geometry (4 November 2026), for the titles the property spine gives none: the title's
-- parcels (table 51569, the title-parcel association) → each parcel's polygon (layer 51571) → the address points
-- (layer 123113) strictly inside it, tested in Python (registers.linz.geo; no PostGIS). One row per title and address. A
-- parcel several titles share (a cross lease, a unit plan) gives each the same addresses: titles_on_parcel says so.
CREATE TABLE linz_private.title_address_points (
    title_no                   text NOT NULL,
    address_id                 bigint NOT NULL,
    full_address               text NOT NULL,
    address_lifecycle          text,
    par_id                     text NOT NULL,
    joined_by                  text NOT NULL,     -- how it was joined: load.GEOMETRY_JOINED_BY
    titles_on_parcel           integer NOT NULL,
    addresses_in_parcel        integer NOT NULL,
    association_key            text NOT NULL,
    parcel_key                 text NOT NULL,
    address_key                text NOT NULL,
    association_document       text NOT NULL,
    parcel_document            text NOT NULL,
    address_document           text NOT NULL,
    loaded_at timestamptz NOT NULL DEFAULT now()
);
