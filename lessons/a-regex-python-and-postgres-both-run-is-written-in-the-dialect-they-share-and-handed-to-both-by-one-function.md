A regex Python and Postgres both run is written in the dialect they share (anchored, no \b, which Postgres reads as a backspace, no \d, \s or flags) and handed to both by one function, pattern inlined, so no caller orders arguments.
area: courts, suppression, hard limit 16, regex, PostgreSQL ~, re.match, check vs load, one rule in two engines, psycopg argument order
paid-for-by: 2026-10-31, fix-registers-courts-1 (the first night of the courts lane on live: `qv4-courts-load` built and refused to publish, 76 names "published on a document a suppression reaches")

The load kept a model-read name under a suppression by Python
(`CROWN.match(name.upper())`); the check and the lever applied the same
pattern in SQL (`upper(name) ~ pattern`). The pattern held
`ATTORNEY[- ]GENERAL\b.*`. To Python `\b` is a word boundary; to
Postgres's regex engine it is a backspace character, so the Crown's own
law officers matched in Python and never in SQL, and 75 of 6,797 names on
documents a suppression reaches (every one an Attorney-General or
Solicitor-General shape) were kept by the load and flagged by the check.
The check was right to refuse: the two engines disagreed, and only a
measurement said which way.

How to apply: when one rule must hold in Python and in SQL, write it once
in one module and give it out in both forms from there (`kept_under_suppression`
for rows, `kept_sql(alias)` for a fragment), and write the pattern in the
regex both engines share: `^…$` anchors, `(?:…)`, classes, `.*`, no `\b`
(use `(?:[^A-Z0-9].*)?`), no `\d`, `\s` or `\w`, no flags. Inline the
pattern in the SQL fragment as a literal rather than returning it as an
argument: a fragment that appears before another parameterised clause
takes that clause's argument, silently (the lever's `reach()` would have
counted with the pattern and the citation swapped). Then test the two
forms against each other on the real rows and on the shapes the rule
names, in the engine, not in the head. See also
[[order-text-keys-one-way-in-python-and-sql-collate-c]].
