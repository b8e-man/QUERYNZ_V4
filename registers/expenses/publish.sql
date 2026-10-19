-- registers/expenses: what later modules read. Every row carries its document's hash, page (the sheet) and place
-- (the cell). Only lines whose categories add to their own printed total are published; the rest are catch-log
-- lines. Money a release prints outside its total (role 'outside') is a row of its own and is never added in.

CREATE OR REPLACE VIEW pub.mp_expenses AS
SELECT f.key, f.document, f.page, f.place, r.period_start, r.period_end, r.period_basis, l.member, l.name,
       l.party_label, l.party, l.party_basis, l.marks, f.category, f.role, f.figure, f.printed, l."check" AS line_check,
       l.key AS line, r.key AS release, r.url, f.reader, f.profile, f.profile_version, f.read_from, f.loaded_at
FROM expenses.figures f
JOIN expenses.lines l ON l.key = f.line
JOIN expenses.releases r ON r.key = f.release
WHERE r.publisher = 'parliamentary-service' AND l."check" IN ('adds', 'rounding', 'nothing-to-add');

CREATE OR REPLACE VIEW pub.minister_expenses AS
SELECT f.key, f.document, f.page, f.place, r.period_start, r.period_end, r.period_basis, l.member, l.name,
       l.party_label, l.party, l.party_basis, l.marks, f.category, f.role, f.figure, f.printed, l."check" AS line_check,
       l.key AS line, r.key AS release, r.url, f.reader, f.profile, f.profile_version, f.read_from, f.loaded_at
FROM expenses.figures f
JOIN expenses.lines l ON l.key = f.line
JOIN expenses.releases r ON r.key = f.release
WHERE r.publisher = 'internal-affairs' AND l."check" IN ('adds', 'rounding', 'nothing-to-add');

-- each release table's grand total, as printed, against the sum of its member lines, per column
CREATE OR REPLACE VIEW pub.expense_release_totals AS
SELECT r.key AS release, r.document, r.page, t.line_place AS place, r.publisher, r.period_start, r.period_end,
       t.label, t.heading, t.total_role, t.printed, t.rows_sum, t.equal
FROM expenses.totals t
JOIN expenses.releases r ON r.key = t.release
WHERE t.widest;
