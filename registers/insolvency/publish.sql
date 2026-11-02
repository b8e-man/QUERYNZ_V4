-- registers/insolvency: the published views (2 November 2026). Never an address: the lane reads none.
-- The display window is applied again on the day a view is read, so a row leaves the day its window ends, load or no load;
-- a removed estate is deleted from insolvency.estates by the removals job the moment the API names it.

CREATE OR REPLACE VIEW pub.insolvency_people AS
SELECT e.key, e.estate_number, e.register, e.name, e.alternate_names, e.insolvency_type, e.status,
       e.adjudicated_on, e.discharged_on, e.discharge_type, e.discharge_suspended, e.multiple, e.occupation, e.court,
       e.office, e.partnered_estates, e.shown_until,
       'the Insolvency Register (Insolvency and Trustee Service), as its API answered' AS source_note,
       e.document, e.page, e.place, e.read_from, e.reader, e.profile, e.profile_version, e.loaded_at
FROM insolvency.estates e
WHERE e.kind = 'person' AND (e.shown_until IS NULL OR e.shown_until >= current_date);

CREATE OR REPLACE VIEW pub.insolvency_companies AS
SELECT e.key, e.estate_number, e.register, e.name, e.organisation_name, e.trading_names, e.alternate_names, e.nzbn,
       e.company_number, CASE WHEN c.key IS NOT NULL THEN c.key END AS entity_key,
       e.insolvency_type, e.status, e.adjudicated_on AS liquidated_on, e.discharged_on AS completed_on, e.occupation AS industry,
       e.office, e.partnered_estates,
       'the Insolvency Register (Insolvency and Trustee Service): a liquidation the Official Assignee administers' AS source_note,
       e.document, e.page, e.place, e.read_from, e.reader, e.profile, e.profile_version, e.loaded_at
FROM insolvency.estates e
LEFT JOIN pub.companies c ON c.nzbn = e.nzbn
WHERE e.kind = 'company' AND (e.shown_until IS NULL OR e.shown_until >= current_date);

COMMENT ON VIEW pub.insolvency_people IS
  'A person''s bankruptcy, no asset procedure or debt repayment order as the Insolvency Register''s API answered, shown only within the display window the API states (four years from discharge, five from an order; no limit for a person bankrupt two or more times); never an address, never a month or year of birth.';
COMMENT ON VIEW pub.insolvency_companies IS
  'A company liquidation the Official Assignee administers, as the Insolvency Register''s API answered; entity_key where the NZBN is in the companies file.';
