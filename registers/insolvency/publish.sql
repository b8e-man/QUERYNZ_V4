-- registers/insolvency: the published views (2 November 2026). Never an address: the identifying fields are only in
-- insolvency_private. Every estate read is here (ruling 142, 4 November 2026): the API's terms are flags beside the
-- row, applied at a product's export. `past_window` is worked out on the day the view is read; `removed_on` and
-- `removal_seen_at` are set by the removals job the moment the API names an estate; a suppressed estate's names are
-- kept in insolvency_private.suppressed_names by `key`, and its `name` here is empty.

CREATE OR REPLACE VIEW pub.insolvency_people AS
SELECT e.key, e.estate_number, e.register, e.name, e.alternate_names, e.insolvency_type, e.status,
       e.adjudicated_on, e.discharged_on, e.discharge_type, e.discharge_suspended, e.multiple, e.occupation, e.court,
       e.office, e.partnered_estates, e.shown_until,
       'the Insolvency Register (Insolvency and Trustee Service), as its API answered' AS source_note,
       e.document, e.page, e.place, e.read_from, e.reader, e.profile, e.profile_version, e.loaded_at,
       e.suppressed, e.suppressed_said, e.annulled_on, (e.window_unknown OR e.shown_until < current_date) AS past_window,
       e.removed_on, e.removal_seen_at, e.absent_since
FROM insolvency.estates e
WHERE e.kind = 'person';

CREATE OR REPLACE VIEW pub.insolvency_companies AS
SELECT e.key, e.estate_number, e.register, e.name, e.organisation_name, e.trading_names, e.alternate_names, e.nzbn,
       e.company_number, CASE WHEN c.key IS NOT NULL THEN c.key END AS entity_key,
       e.insolvency_type, e.status, e.adjudicated_on AS liquidated_on, e.discharged_on AS completed_on, e.occupation AS industry,
       e.office, e.partnered_estates,
       'the Insolvency Register (Insolvency and Trustee Service): a liquidation the Official Assignee administers' AS source_note,
       e.document, e.page, e.place, e.read_from, e.reader, e.profile, e.profile_version, e.loaded_at,
       e.suppressed, e.suppressed_said, e.annulled_on, (e.window_unknown OR e.shown_until < current_date) AS past_window,
       e.removed_on, e.removal_seen_at, e.absent_since
FROM insolvency.estates e
LEFT JOIN pub.companies c ON c.nzbn = e.nzbn
WHERE e.kind = 'company';

COMMENT ON VIEW pub.insolvency_people IS
  'A person''s bankruptcy, no asset procedure or debt repayment order as the Insolvency Register''s API answered, every estate read: past_window where the display window the API states has ended (four years from discharge, five from an order; no limit for a person bankrupt two or more times), suppressed (names in insolvency_private.suppressed_names), annulled_on, removed_on where the removals named it after this answer; never an address, never a month or year of birth.';
COMMENT ON VIEW pub.insolvency_companies IS
  'A company liquidation the Official Assignee administers, as the Insolvency Register''s API answered; entity_key where the NZBN is in the companies file; the same flags as pub.insolvency_people.';
