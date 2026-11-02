-- registers/linz: what later modules read (step 8.3, use cases 4 and 12; Arthur, 2 November 2026). The LINZ Data
-- Service's property titles, the owners of each title, and the New Zealand Geographic Board's place names, each row as
-- LINZ states it with its citation (the landed WFS page's hash and the row's place in the pull). No address, no
-- geometry: a title's land district is a place; an owner is a name (hard limit 15 binds every product's surface).
-- The owners are published under the LINZ Licence for Personal Data: never indexed by a public search engine, supplied
-- onward only under the licence, refreshed weekly, corrected within five business days by the next pull (the lane
-- rebuilds whole from the newest pull). Titles and place names: CC BY 4.0, "sourced from the LINZ Data Service".
CREATE OR REPLACE VIEW pub.linz_titles AS
SELECT t.key, t.title_no, t.status, t.type, t.land_district, t.issue_date::date AS issued_on, t.guarantee_status,
       t.estate_description, t.number_owners, t.spatial_extents_shared,
       t.document, t.page, t.place, t.read_from, t.reader, t.profile, t.profile_version, t.loaded_at
FROM linz.titles t;

COMMENT ON VIEW pub.linz_titles IS
  'A property title as the LINZ Data Service states it (layer 50804, without its geometry): number, status, type, land district, issue date, guarantee status, estate, number of owners. CC BY 4.0.';

CREATE OR REPLACE VIEW pub.linz_title_owners AS
SELECT o.key, o.title_key, o.title_no, o.status, o.land_district, o.estate_share, o.owner_type, o.kind, o.name,
       o.prime_surname, o.prime_other_names, o.name_suffix, o.corporate_name,
       o.document, o.page, o.place, o.read_from, o.reader, o.profile, o.profile_version, o.loaded_at
FROM linz.owners o;

COMMENT ON VIEW pub.linz_title_owners IS
  'An owner of a property title as the LINZ Data Service states it (table 51564): corporate or individual, the name as printed, the estate share, the title and its land district; never an address; linked to nobody. LINZ Licence for Personal Data.';

CREATE OR REPLACE VIEW pub.linz_place_names AS
SELECT p.key, p.name_id, p.feat_id, p.name, p.status, p.feat_type, p.maori_name, p.land_district,
       p.territorial_authority, p.region, p.crd_latitude AS latitude, p.crd_longitude AS longitude, p.info_origin,
       p.info_description, p.treaty_legislation, p.nzgb_ref,
       p.document, p.page, p.place, p.read_from, p.reader, p.profile, p.profile_version, p.loaded_at
FROM linz.place_names p;

COMMENT ON VIEW pub.linz_place_names IS
  'An official or recorded place name in the New Zealand Gazetteer (NZGB, layer 51681): the name, its Māori name, feature type, status, district, region and its point. CC BY 4.0.';
