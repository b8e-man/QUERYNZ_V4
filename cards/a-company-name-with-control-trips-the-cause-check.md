# A company named "… CONTROL …" trips the word-of-cause check, and the report is refused
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`products/report/rules.py` rule 3 (`CAUSE`) reads `controls?` anywhere in a
title or statement. A company name such as a pest-control firm's
(`companies:companies/9429030206168`) is the register's own words, but the
check refuses every report that reaches it: the recruitment screen on
`companies:companies/9429000001458/director/8944b48ae1b8` is refused for
three such lines. For the report lane: apply the cause words to the
pattern's own text, not to the register's values that fill it (a name, a
title), or exempt the name columns the catalogue lists. Found at the
recruitment checkpoint.

Closed 2026-10-20 by the report session (report-2). Rules 3 and 4 now read
the report's own words: the register's values that fill a statement (every
text column of the row, and the title of the row it sits on) are masked out
before the search for a word of cause or of ownership, so `PEST CONTROL
RESEARCH NZ LIMITED` and an owners' trust held of record are the register's
words, quoted. The report's wording is still judged: a pattern, a reason, a
note or a fired flag that says "because" refuses (fixtures in
`test_template_and_rules.py`). Measured: `python -m products.report check`
builds a report on a company whose name carries a cause word, taken from the
tables at run time (today `SMITH ELEMENTS & CONTROLS LIMITED`), and fails on
a rule 3 or 4 refusal; the card's own screen
`companies:companies/9429000001458/director/8944b48ae1b8` prints.
