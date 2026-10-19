-- registers/party_returns (plan 1.11): what later modules read. One row per return read: its declared total,
-- its parts as printed, and where it came from; Part A's donors and Part H's lenders. Nothing here is a person's address.
-- A row whose return the Commission lists as replaced by an amendment carries replaced_by; sum only rows without it.
CREATE OR REPLACE VIEW pub.party_return_totals AS
SELECT r.key, r.document, r.page, r.place, r.party, r.party_label, r.party_basis, r.year, r.declared_total,
       r.part_a, r.part_c, r.part_d, r.part_f, r.part_g, r.declared_parts, r.total_check, r.read_from, r.reader, r.profile,
       r.profile_version, r.loaded_at, r.year_from,       -- year_from and what follows last: a view gains columns only at its end
       r.loans_h, r.loans_i, r.loans_total, r.donors_check, r.loans_check, a.replaced_by
FROM party_returns.returns r LEFT JOIN party_returns.amendments a ON a.document = r.document;

-- Part A's donors: the name and the money, never the address
CREATE OR REPLACE VIEW pub.party_return_donors AS
SELECT d.key, d.return_key, d.document, d.page, d.ordinal, d.n, r.party, r.party_label, r.year, d.donor, d.amount,
       d.dates, d.contributions, d.paired_by, d.read_from, d.reader, d.profile, d.profile_version, d.loaded_at,
       a.replaced_by
FROM party_returns.donors d JOIN party_returns.returns r ON r.key = d.return_key
LEFT JOIN party_returns.amendments a ON a.document = d.document;

-- Part H's lenders: the name and the loan, never the address or a guarantor
CREATE OR REPLACE VIEW pub.party_return_loans AS
SELECT l.key, l.return_key, l.document, l.page, l.ordinal, r.party, r.party_label, r.year, l.lender, l.amount,
       l.dates, l.interest, l.read_from, l.reader, l.profile, l.profile_version, l.loaded_at, a.replaced_by
FROM party_returns.loans l JOIN party_returns.returns r ON r.key = l.return_key
LEFT JOIN party_returns.amendments a ON a.document = l.document;
