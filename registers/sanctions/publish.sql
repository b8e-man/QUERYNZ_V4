-- registers/sanctions: what later modules read (plan 5.3, use case 13). One row per listed person or entity per
-- list, as each publisher issues its list, with the list's own identifier, names and aliases as published, the
-- designation's date and basis and the list's version; and one row per list read. An individual's address is never
-- on a view beyond the country the list names (hard limit 15); passport numbers and the lists' narrative comments are
-- not read. A listing is a government's or the Security Council's designation, not a finding of this estate: a name
-- that matches is a name that matches, never the same person, until the dates of birth, nationality and the list's
-- own identifiers agree. While a list is held on its publisher's terms (queue, no default) it has no rows here and
-- no line in pub.sanctions_lists. Run by a session only against its scratch schema (the tests rewrite `pub.`).
CREATE OR REPLACE VIEW pub.sanctions_lists AS
SELECT l.list_id, l.name, l.publisher, l.law, l.version, l.stated, l.stated_where, l.listings, l.ended, l.set_aside,
       l.document, l.profile, l.profile_version, l.loaded_at
FROM sanctions.lists l;

CREATE OR REPLACE VIEW pub.sanctions_listings AS
SELECT s.key, s.list_id, s.list_ref, s.other_ref, s.kind, s.status, s.name, s.aliases, s.original_script, s.titles,
       s.positions, s.nationalities, s.birth_dates, s.birth_countries, s.countries, s.regime, s.basis,
       s.designated_on, s.renewed_on, s.expires_on, s.ended_on, s.updated_on, s.list_version,
       s.document, s.page, s.place, s.read_from, s.reader, s.profile, s.profile_version, s.loaded_at
FROM sanctions.listings s;
