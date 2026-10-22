-- registers/councillor_interests: what later modules read (plan 6.3). Councillors' registers of pecuniary interests,
-- council by council, as each council publishes its summary (Local Government Act 2002, Part 4 subpart 3). Two views:
-- how each of the 78 councils publishes its register and what the estate holds of it; and, from a council that
-- publishes a structured page, each member's categories as published. A PDF register is held and never read (ruling
-- 79). Real property, a home, an address, a contact, and a spouse's or partner's interests are never read or shown
-- (hard limit 15; the queue's answer on real property). Position `councillors-registers-of-interests`.
CREATE OR REPLACE VIEW pub.councillor_interest_registers AS
SELECT r.council, r.host, r.form, r.landing_url, r.landing_sha256, r.documents_held, r.members_read, r.why, r.loaded_at
FROM councillor_interests.registers r;

CREATE OR REPLACE VIEW pub.councillor_interests AS
SELECT i.key, i.council, i.member, i.role, i.category, i.entries, i.as_at,
       'the council''s own published summary of its register of members'' pecuniary interests'::text AS source,
       i.document, i.page, i.place, i.url, i.read_from, i.reader, i.profile, i.profile_version, i.loaded_at
FROM councillor_interests.interests i;
