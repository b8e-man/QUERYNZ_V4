A feed that publishes no birth-date or address field still carries them where a filer typed one into a name field: read every name field for a date, a street number or a box before publishing it, withhold that field with a note, and keep the row.
area: charities, officers, reading registers, hard limits 11 and 15, names
paid-for-by: 2026-10-21, charities-a session (Fable), step 4.1

The Charities Register's Officers set has no birth-date field and no address
field, and its page on restricted information says neither is published. On
the first full copy (589,148 rows) 15 name fields held a date (13 of them a
day, month and year in a MiddleName or LastName: a birth date typed where a
name goes), 11 held a street address with its number, and about 200 held
stray digits. A reading that trusts the field list would have published them
all as names.

How to apply: run `name_fault` (registers/charities_a/read.py) on each name
field: a date, a leading street number or a box phrase, or digits that are
not a lone year. The field is withheld and `name_note` says which and why;
the full name is rebuilt from the clean parts; the row stays with its role
and window (recover over exclude). A thoroughfare word alone never flags in
a structured name field: Street, Lane, Court, Way, Close and Grove are
surnames, and "Ann Peter Street" is a person. Never print the offending
value anywhere, the catch log included; look at it through a letters-to-x
mask if you must look.
