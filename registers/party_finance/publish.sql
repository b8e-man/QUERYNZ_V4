-- registers/party_finance: what later modules read. Every row carries its document's hash, page and place.
-- Nothing here is a person's home address.

-- a party's election expenses: the Commission's figure, and beside it the return's own total where it was read.
-- `agrees` is NULL where the return was not read, which is neither agreement nor disagreement.
CREATE OR REPLACE VIEW pub.party_expenses AS
SELECT l.key, l.document, l.page, l.place, l.year, l.party, l.party_label, l.party_basis, l.note,
       l.expense_limit, l.total_expenses, l.allocation, l.allocation_spent, l.audited, l.printed,
       r.document AS return_document, r.page AS return_page, r.total AS return_total, r.total_check AS return_check,
       r.read_from AS return_read_from,
       CASE WHEN r.total IS NULL OR l.total_expenses IS NULL THEN NULL
            ELSE abs(r.total - l.total_expenses) < 0.011 END AS agrees,
       l.reader, l.profile, l.profile_version, l.read_from, l.loaded_at
FROM party_finance.expense_listing l
LEFT JOIN party_finance.expense_returns r ON r.listing_row = l.key AND r.current;

-- every expense return read, superseded originals included (current = false)
CREATE OR REPLACE VIEW pub.party_expense_returns AS
SELECT key, document, page, place, listing_row, year, party, party_label, party_basis, current, total, total_check,
       part_a, part_b, part_c, expense_limit, read_from, reader, profile, profile_version, loaded_at
FROM party_finance.expense_returns;

-- registered promoters' expenses, as the Commission's table prints them; referendum spending held beside, never added
CREATE OR REPLACE VIEW pub.promoter_expenses AS
SELECT l.key, l.document, l.page, l.place, l.year, l.promoter, l.note, l.election_expenses,
       l.cannabis_referendum_expenses, l.end_of_life_referendum_expenses, l.printed,
       (SELECT k.document FROM party_finance.listing_links k WHERE k.row_key = l.key ORDER BY k.ordinal LIMIT 1)
           AS return_document,
       l.reader, l.profile, l.profile_version, l.read_from, l.loaded_at
FROM party_finance.promoter_listing l;

-- the broadcasting allocation, every round; `final` marks the allocation that stood at the election
CREATE OR REPLACE VIEW pub.broadcasting_allocations AS
SELECT key, document, page, place, year, round, round_label, final, party, party_label, party_basis, mark, eligible,
       amount, printed, reader, profile, profile_version, read_from, loaded_at
FROM party_finance.allocations;
