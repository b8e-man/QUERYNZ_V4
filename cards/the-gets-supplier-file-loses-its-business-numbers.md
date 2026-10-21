# The ministry's supplier file has lost its business numbers, so awards cannot be joined to companies by NZBN
kind: finding
state: open
use-case: 9 government procurement integrity (template 2); 10 tender and award intelligence
session: tenders-1
opened: 2026-10-21

The plan describes the award notices as "keyed on official business
number". They are not. In the files of 14 August 2026 the `Supplier NZBN`
column of 31,265 supplier records holds: a number in spreadsheet exponent
form whose digits are gone (`9.42904E+12`: 12,694), nothing (12,977), `NULL`
(3,702), six to nine digits (company or GST numbers, 1,224) and free text
(606). Not one record holds a valid 13-digit NZBN. The ministry's schema
workbook says the field is "not validated". The lane keeps the field as
published (`nzbn_as_published`, `nzbn_form`) and fills `nzbn` only for a
valid one, so `pub.award_suppliers.nzbn` is empty today.

So template 2 (awards joined to directors, shareholders and donors) cannot
join on the number; it must go through the links lane's name matching, with
the exponent's leading digits (`94290…`) as a weak hint at most, never a key.
A six- or seven-digit field may be a company number: the links lane may test
it against `pub.companies` with the name, not alone.

Fix, if any: the ministry republishing the column as text (the same letter
as card `the-ministry-s-gets-files-answer-403`). To decide at template 2's
checkpoint: accept onto its known-limits page, or wait for the letter.
