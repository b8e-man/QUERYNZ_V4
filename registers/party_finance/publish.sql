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

-- registered promoters' expenses, as the Commission's table prints them; referendum spending held beside, never added.
-- Beside each column, the part the promoter's own return states for it, and whether the two agree (NULL: not read)
CREATE OR REPLACE VIEW pub.promoter_expenses AS
SELECT l.key, l.document, l.page, l.place, l.year, l.promoter, l.note, l.election_expenses,
       l.cannabis_referendum_expenses, l.end_of_life_referendum_expenses, l.printed,
       (SELECT k.document FROM party_finance.listing_links k WHERE k.row_key = l.key ORDER BY k.ordinal LIMIT 1)
           AS return_document,
       l.reader, l.profile, l.profile_version, l.read_from, l.loaded_at,
       a.figure AS election_return, abs(a.figure - l.election_expenses) < 0.011 AS election_agrees,
       b.figure AS cannabis_referendum_return,
       abs(b.figure - l.cannabis_referendum_expenses) < 0.011 AS cannabis_referendum_agrees,
       c.figure AS end_of_life_referendum_return,
       abs(c.figure - l.end_of_life_referendum_expenses) < 0.011 AS end_of_life_referendum_agrees
FROM party_finance.promoter_listing l
LEFT JOIN party_finance.promoter_returns a ON a.listing_row = l.key AND a.spending = 'election_expenses'
LEFT JOIN party_finance.promoter_returns b ON b.listing_row = l.key AND b.spending = 'cannabis_referendum_expenses'
LEFT JOIN party_finance.promoter_returns c ON c.listing_row = l.key AND c.spending = 'end_of_life_referendum_expenses';

-- each part of a registered promoter's own return, read: one row per part, never added across parts
CREATE OR REPLACE VIEW pub.promoter_expense_returns AS
SELECT key, document, page, place, listing_row, year, promoter, part, spending, figure, figure_check, declared,
       schedule, read_from, reader, profile, profile_version, loaded_at
FROM party_finance.promoter_returns;

-- the broadcasting allocation, every round; `final` marks the allocation that stood at the election
CREATE OR REPLACE VIEW pub.broadcasting_allocations AS
SELECT key, document, page, place, year, round, round_label, final, party, party_label, party_basis, mark, eligible,
       amount, printed, reader, profile, profile_version, read_from, loaded_at
FROM party_finance.allocations;

-- the register of promoters and the people it names in its public roles; never an email or an address
CREATE OR REPLACE VIEW pub.promoters AS
SELECT key, document, page, place, year, promoter, registered_on, registered_for, statement, reader, profile,
       profile_version, read_from, loaded_at
FROM party_finance.promoters;

CREATE OR REPLACE VIEW pub.promoter_people AS
SELECT p.key, p.promoter_key, p.document, p.page, p.place, r.year, r.promoter, p.role, p.name, p.reader, p.profile,
       p.profile_version, p.read_from, p.loaded_at
FROM party_finance.promoter_people p JOIN party_finance.promoters r ON r.key = p.promoter_key;

-- the roster of party financial statements, with the statements each row links (the first, then any amended or
-- audited one); a party listed with no link has not filed yet
CREATE OR REPLACE VIEW pub.party_financial_statements AS
SELECT f.key, f.document, f.page, f.place, f.filed_year, f.party, f.party_label, f.party_basis, f.note, f.mark,
       f.balance_date, f.deadline, f.date_filed, f.balance_printed, f.deadline_printed, f.filed_printed,
       f.audit_requirement,
       ARRAY(SELECT k.document FROM party_finance.listing_links k WHERE k.row_key = f.key ORDER BY k.ordinal)
           AS statements,
       f.reader, f.profile, f.profile_version, f.read_from, f.loaded_at
FROM party_finance.financial_statements f;
