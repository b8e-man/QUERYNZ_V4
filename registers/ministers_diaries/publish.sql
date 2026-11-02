-- registers/ministers_diaries: what later modules read. Every minister's monthly diary release the ingest MCP's
-- parliament-diaries corpus holds, and every meeting in it, as released. Each row cites its document (the record's
-- hash) and the PDF's address (`citation_url`: NULL where the provider served a file name only; `file_name` then
-- says which PDF). Names are as the release prints them and are linked to no person's row (that is product (b),
-- after links). The meeting, the attendees and the location are published whole, as released (ruling 102: hard
-- limit 15 binds the products, not the published views); beside them the flags a product applies the limit by at
-- its own surface: `location_names_home`, `location_street_only`, `meeting_names_address`,
-- `attendees_names_address`. The provider's `text` is never published.
CREATE OR REPLACE VIEW pub.minister_diary_releases AS
SELECT r.key, r.pdf_url AS citation_url, r.file_name, r.upload_folder, r.minister, r.ministers_named, r.portfolios,
       r.month, r.month_named, r.entries_month, r.months, r.first_on, r.last_on, r.entries, r.withheld_entries,
       r.locations_flagged, r.source_note,
       r.document, r.page, r.place, r.read_from, r.reader, r.profile, r.profile_version, r.loaded_at
FROM ministers_diaries.releases r;

CREATE OR REPLACE VIEW pub.minister_diary_entries AS
SELECT e.key, e.release, r.pdf_url AS citation_url, r.file_name, r.month, e.rowid, e.minister, e.portfolio,
       e.entry_on, e.date_as_released, e.time, e.meeting, e.attendees, e.location,
       e.location_names_home, e.location_street_only, e.meeting_names_address, e.attendees_names_address,
       e.withheld, e.collected_at, e.updated_at, e.versions, e.source_note,
       e.document, e.page, e.place, e.read_from, e.reader, e.profile, e.profile_version, e.loaded_at
FROM ministers_diaries.entries e
JOIN ministers_diaries.releases r ON r.key = e.release;

COMMENT ON VIEW pub.minister_diary_entries IS
  'One meeting of a minister''s diary release, as released: names as printed and linked to nobody; the release''s withholdings kept as printed (`withheld`); the meeting, attendees and location whole, with the flags a product applies hard limit 15 by (ruling 102): location_names_home, location_street_only, meeting_names_address, attendees_names_address.';

-- One row per attendee of a meeting, in the order the release prints them, split by rules (attendees.py, no model):
-- the attendee as written, folded as the scans fold a name, its kind, and the organisation part where the text gives
-- one ("Name (Organisation)", "Name, Organisation", "Fonterra staff", or a body named alone), with `crown` where that
-- part is the Crown's own. The entry's four flags are carried down from the entry, so a product applies hard limit 15
-- by them here as on the entry (ruling 102). Names as printed and linked to nobody.
CREATE OR REPLACE VIEW pub.minister_diary_attendees AS
SELECT a.key, a.entry, a.position, a.attendee, a.folded, a.kind, a.organisation, a.crown,
       e.release, r.pdf_url AS citation_url, r.file_name, e.minister, e.portfolio, e.entry_on, e.time,
       e.location_names_home, e.location_street_only, e.meeting_names_address, e.attendees_names_address,
       a.document, a.page, a.place, a.read_from, a.reader, a.profile, a.profile_version, a.loaded_at
FROM ministers_diaries.attendees a
JOIN ministers_diaries.entries e ON e.key = a.entry
JOIN ministers_diaries.releases r ON r.key = e.release;

COMMENT ON VIEW pub.minister_diary_attendees IS
  'One attendee of a minister''s diary meeting, split from the entry''s attendees text by rules: as written, folded, its kind (person, organisation, crown, group, role, withheld), the organisation part where the text gives one, and the entry''s four address flags carried down (hard limit 15 applied by them at a product''s surface, ruling 102).';
