-- registers/mp_interests: what later modules read. Every row carries its document's hash, page and place. A
-- declaration filed under real property carries no text here: it is held in the private twin (hard limit 15).

CREATE OR REPLACE VIEW pub.mp_interests AS
SELECT d.key, d.document, d.page, d.place, d.as_at, m.member, m.name, m.party_label, m.party, m.party_basis,
       m.electorate, d.category, d.heading, d.number_printed, d.text, d.withheld, m.key AS member_return,
       d.reader, d.profile, d.profile_version, d.read_from, d.loaded_at
FROM mp_interests.declarations d
JOIN mp_interests.members m ON m.key = d.member;

-- each member's return in each edition, with what it prints in place of declarations, if anything
CREATE OR REPLACE VIEW pub.mp_interest_returns AS
SELECT m.key, m.document, m.page, m.place, m.as_at, m.printed, m.member, m.name, m.party_label, m.party,
       m.party_basis, m.electorate, m.statement,
       (SELECT count(*) FROM mp_interests.declarations d WHERE d.member = m.key) AS declarations,
       m.reader, m.profile, m.profile_version, m.read_from, m.loaded_at
FROM mp_interests.members m;

CREATE OR REPLACE VIEW pub.mp_interest_editions AS
SELECT e.key, e.document, e.page, e.place, e.as_at, e.as_at_printed, e.categories, e.members, e.declarations,
       (SELECT bool_and(n.agrees) FROM mp_interests.numbering n WHERE n.edition = e.key) AS numbering_agrees,
       e.reader, e.profile, e.profile_version, e.read_from, e.loaded_at
FROM mp_interests.editions e;
