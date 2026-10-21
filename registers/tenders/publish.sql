-- registers/tenders: what later modules read (step 6.2, template 1). Every award notice the ministry's GETS open data
-- publishes, July 2014 on, keyed by its era and GETS's own RFx ID, and every supplier a supplier file names on a
-- notice, keyed by the notice and the supplier as published. Each row carries its citation (the file's sha256, the
-- page and the record's place, the reader and the profile) and the licence and attribution the data is published
-- under (CC BY 3.0 NZ: attribution to the ministry on every surface). No address of any kind is on any view here: the
-- supplier file's address and website columns are never read (hard limit 15), and the notices' free-text overview,
-- comments and tender-box address are not read. Run by a session only against its scratch schema (`pub.` rewritten).

CREATE OR REPLACE VIEW pub.award_notices AS
SELECT n.key, n.rfx_id, n.era, n.posting_agency, n.department, n.rfx_type, n.competition_type, n.tender_coverage,
       n.prequalification_required, n.title, n.reference_number, n.opened_on, n.closed_on, n.awarded_on, n.award_type,
       n.awarded_amount_as_published, n.value_nzd, n.value_note, n.regions, n.categories, n.suppliers_named,
       n.report_date,
       'CC BY 3.0 NZ'::text AS licence,
       'Source: Ministry of Business, Innovation and Employment, New Zealand Government procurement award notices '
       '(GETS open data), licensed under CC BY 3.0 NZ'::text AS attribution,
       n.document, n.page, n.place, n.read_from, n.reader, n.profile, n.profile_version, n.loaded_at
FROM tenders.notices n;

CREATE OR REPLACE VIEW pub.award_suppliers AS
SELECT s.key, s.notice_key, s.rfx_id, s.era, s.business_name, s.nzbn_as_published, s.nzbn, s.nzbn_form, s.country,
       n.posting_agency, n.title, n.awarded_on, n.award_type, n.value_nzd AS notice_value_nzd, s.report_date,
       'CC BY 3.0 NZ'::text AS licence,
       'Source: Ministry of Business, Innovation and Employment, New Zealand Government procurement award notices '
       '(GETS open data), licensed under CC BY 3.0 NZ'::text AS attribution,
       s.document, s.page, s.place, s.read_from, s.reader, s.profile, s.profile_version, s.loaded_at
FROM tenders.suppliers s
JOIN tenders.notices n ON n.key = s.notice_key;
