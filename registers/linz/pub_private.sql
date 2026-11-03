-- registers/linz: the lane's private views for the links lane (ruling 142, Arthur, 4 November 2026). Made in
-- `pub_private` by support.db.private_views before each links build; neither reader login is granted the schema.
-- Each title's street address, joined through the property spine (`linz_private.title_addresses`, load.join_sql): the
-- links lane's judgment-address-title@1 reads it, and only it. Not made until the lane's private sources are loaded.
CREATE OR REPLACE VIEW pub_private.linz_title_addresses AS
SELECT title_no, address_id, full_address, titles_on_property, addresses_on_property
  FROM linz_private.title_addresses;

-- Each title's street address by geometry, for the titles the spine gives none (`linz_private.title_address_points`,
-- load.geometry_join: the title's parcels → the parcel's polygon → the address points inside it). No links rule reads it
-- yet (links/opportunities.py: measure owed).
CREATE OR REPLACE VIEW pub_private.linz_title_address_points AS
SELECT title_no, address_id, full_address, titles_on_parcel, addresses_in_parcel
  FROM linz_private.title_address_points;
