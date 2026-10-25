Read a name column's printed form (a count of commas and of where the capitals sit, then a handful of public rows) before declaring its order: a column a lane's reader calls given-first can still carry the source's surname-first rows that its rule never turned round.
area: products, the board's catalogue (FIELDS_OF name orders), any matcher that reads a one-string name by position
paid-for-by: 2026-10-26, fix-products-board-1d (ruling 85)

Ruling 85 has the board match first, middle and last names by each view's
order, declared as data. `expenses/read.py` says its `name` is "given-first,
honorifics off", and it is for "Surname, Given": `person()` turns a comma
round. But 744 rows of `pub.mp_expenses` come from a workbook that prints
"Logie Jan" with no comma. `person()` leaves those as they are, so `name`
holds both orders. Declaring it given-family on the reader's word would
have cut those MPs from an exact last-name search without a sound. One
aggregate query per column (rows with a comma, Title-case words followed by
a word in capitals, a capitalised first word) showed it, and five rows
confirmed it. The same pass showed `pub.candidates.name` is all commas
(the Commission's "SURNAME, Given") and `display_name` is given-first.

When the order is not stated, `ambiguous` is the safe default. It can only
widen an exact match. A wrong stated order narrows one silently.

Proving the tests: some of the new tests hold behaviour board-3 already
had (a comma read family-first, a given-first name's last word). Run
against board-3's own rule, those tests stay green. Show each of them
failing against a mutant that breaks that one rule (comma ignored, every
order read as ambiguous), not only against the old code.
