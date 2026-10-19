-- registers/party_returns (plan 1.11): what later modules read. One row per return read: its declared total,
-- its parts as printed, and where it came from. Nothing here is a person's address.
CREATE OR REPLACE VIEW pub.party_return_totals AS
SELECT key, document, page, place, party, party_label, party_basis, year, declared_total,
       part_a, part_c, part_d, part_f, part_g, declared_parts, total_check, read_from, reader, profile,
       profile_version, loaded_at, year_from              -- year_from last: a view gains columns only at its end
FROM party_returns.returns;
