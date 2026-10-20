A presentation rule that judges wording (a word of cause, "owner") reads the report's own words, with every register value masked out first; a rule that guards a hard limit (no home address) reads values too, and recognises its target by shape, never by one token.
area: subject reports, products/report, presentation rules, templates, checks that refuse
paid-for-by: 2026-10-20, report session, step 5.1 (report-2), the recruitment checkpoint's two refusals

Rule 3 read "controls" anywhere in a statement and refused every report that
reached PEST CONTROL RESEARCH NZ LIMITED; rule 7 read a street word and a
later four-digit number and refused every donor surnamed Lane with a year on
the line. Both read a register's own words as if the report had written
them. The fix was the rule, never the row: rules 3 and 4 now strip every
text value of the row and the title of the row it sits on before searching
(`rules.own_words`), so the pattern, the reasons, the notes and the flags
are judged and the register is quoted. Rule 7 is different: a street in a
name column is exactly the fault it exists for, so it keeps reading values,
but it recognises an address by its shape (a street number standing alone
before the street word, or a comma, a locality and a postcode after it) and
reads a title and a statement apart, so "Lane · 2023" is not a numbered
street. A rule that refuses needs two fixtures: the fault it is for, which
must still refuse, and the register's own words, which must not.
