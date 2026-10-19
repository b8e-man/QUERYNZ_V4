-- registers/candidate_returns (plan 4.1): what later modules read. One row per return read: the candidate as the
-- Commission lists them, the election, the declared totals as printed, and the Commission's own figures beside them
-- (the headline rule: its figure, linked to its file, with ours beside it). Nothing here is a person's address.
-- Sum only rows whose status is current or unlisted: a replaced return is kept because a figure that changed between
-- filings is a fact about the filing.
CREATE OR REPLACE VIEW pub.candidate_return_totals AS
SELECT r.key, r.document, r.page, r.place, f.year, f.surname, f.given_names, f.electorate, f.party,
       f.status, f.replaced_by, f.placed_by,
       r.donations, r.part_a, r.part_c, r.part_d, r.donations_check,
       r.expenses, r.part_f, r.part_g, r.expenses_check, r.loans, r.loans_check, r.signed,
       c.donations AS commission_donations, c.expenses AS commission_expenses, c.loans AS commission_loans,
       c.file AS commission_file, c.key AS commission_key,
       r.read_from, r.reader, r.profile, r.profile_version, r.loaded_at
FROM candidate_returns.returns r
JOIN candidate_returns.files f ON f.document = r.document
LEFT JOIN candidate_returns.commission c ON c.key = f.sheet_key;

-- Part A's donors: the name and the money, never the address. Empty until Part A is read.
CREATE OR REPLACE VIEW pub.candidate_return_donors AS
SELECT d.key, d.return_key, d.document, d.page, d.ordinal, f.year, f.surname, f.given_names, f.electorate, f.party,
       f.status, f.replaced_by, d.donor, d.amount, d.dates, d.contributions, d.read_from, d.reader, d.profile,
       d.profile_version, d.loaded_at
FROM candidate_returns.donors d JOIN candidate_returns.files f ON f.document = d.document;
