-- registers/council_minutes: what later modules read (plan 6.3). The meetings of the councils on the InfoCouncil
-- platform, as each council's own listing shows them: the body, the date, the kind, and what the estate holds of the
-- minutes (the PDF's sha256 where held). The minutes are held and never read: this view says a meeting happened and
-- where its minutes are, never who attended or what was resolved. No venue is kept (a body can meet in a person's
-- home). Position `council-meeting-platform-infocouncil`.
CREATE OR REPLACE VIEW pub.council_meetings AS
SELECT m.key, m.council, m.host, m.body, m.meeting_date, m.meeting_time, m.kind, m.code, m.documents,
       m.minutes_file, m.minutes_url, m.minutes_sha256, m.minutes_held,
       'the council''s own meeting listing on its InfoCouncil site'::text AS source,
       m.document, m.page, m.place, m.listing_url, m.read_from, m.reader, m.profile, m.profile_version, m.loaded_at
FROM council_minutes.meetings m;
