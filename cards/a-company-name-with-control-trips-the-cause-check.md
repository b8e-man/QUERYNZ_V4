# A company named "… CONTROL …" trips the word-of-cause check, and the report is refused
kind: finding
state: open
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20

`products/report/rules.py` rule 3 (`CAUSE`) reads `controls?` anywhere in a
title or statement. A company name such as a pest-control firm's
(`companies:companies/9429030206168`) is the register's own words, but the
check refuses every report that reaches it: the recruitment screen on
`companies:companies/9429000001458/director/8944b48ae1b8` is refused for
three such lines. For the report lane: apply the cause words to the
pattern's own text, not to the register's values that fill it (a name, a
title), or exempt the name columns the catalogue lists. Found at the
recruitment checkpoint.
