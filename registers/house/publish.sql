-- registers/house: what later modules read. Candidates per election and by-election, electorates joined to Stats
-- NZ's names, who sat in the House with a window per seat, and the elections with their polling days; each row with
-- its citation. Nothing private exists in this lane.
CREATE OR REPLACE VIEW pub.elections AS
SELECT key, kind, name, electorate, polled_on, polled_basis, results_href,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM house.elections;

CREATE OR REPLACE VIEW pub.electorates AS
SELECT key, election, name, number, statsnz_code, statsnz_name, layer, statsnz_document, join_basis, votes_counted,
       candidate_total, candidate_informals, party_total, party_informals, poll_cancelled, result_held,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM house.electorates;

CREATE OR REPLACE VIEW pub.candidates AS
SELECT key, election, name, display_name, name_key, party, party_registered, party_basis, electorate, list_place,
       list_document, list_place_cite, votes, poll_cancelled, joined_basis,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM house.candidates;

CREATE OR REPLACE VIEW pub.members AS
SELECT key, election, name, display_name, name_key, party, party_registered, party_basis, route, electorate, candidate,
       from_on, from_basis, to_by, to_basis, ended_on,
       document, page, place, read_from, reader, profile, profile_version, loaded_at
FROM house.members;
