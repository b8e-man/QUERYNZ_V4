Order text keys one way in Python and in SQL: a database collated by locale (en_NZ) ignores spaces and punctuation and folds case, so `a < b` in Python and in a CHECK or least() disagree; compare COLLATE "C" there.
area: links, PostgreSQL, collation, CHECK constraints, least/greatest, min, ORDER BY, pair order, group ids
paid-for-by: 2026-10-28, fix-links-1 (fix-links-5: the live `qv4-links-build` died on `links_pair_order` at the first run after rulings 114 and 116)

`links.pair` ordered two refs in Python (code points); `links_pair_order
CHECK (row_a < row_b)` ordered them by the database's collation,
en_NZ.UTF-8. Every ref was lowercase ASCII without spaces until the people
and member views brought capitals, spaces, apostrophes, bars and commas,
and then `'x:a' < 'x:A'` is true in the database and false in Python, so
a Python-ordered near link broke the CHECK after 16 minutes of build.
The same split hid in every SQL `least()`, `min(ref)` and `ORDER BY ref`:
a star centre or group id chosen in SQL could differ from the one chosen
in Python, silently. Three live links already broke byte order.

How to apply: when Python and SQL both order or take the least of a text
key, make the SQL compare `COLLATE "C"` (bytes, which for UTF-8 is
Python's order), in the CHECK as well as in the queries, and test it on
keys the two orders disagree on, checked against the engine first. A C
value joined on again loses the column's index (an index serves only its
own collation): hand it back `COLLATE "default"`. Changing a CHECK on a
table that holds rows needs the rows turned round first, in the same
migration. See also [[a-restore-must-carry-the-source-collation]].
