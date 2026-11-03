-- registers/insolvency: the lane's private views for the links lane (ruling 142, Arthur, 4 November 2026). Made in
-- `pub_private` by support.db.private_views before each links build; neither reader login is granted the schema.
-- An estate's address at adjudication as the register answered it (`insolvency_private.identifiers`), by estate
-- number: the links lane's judgment-address-insolvency@1 reads it, and only it.
CREATE OR REPLACE VIEW pub_private.insolvency_addresses AS
SELECT estate AS estate_number, value AS address
  FROM insolvency_private.identifiers
 WHERE field = 'addressAtAdjudication' AND coalesce(value, '') <> '';
