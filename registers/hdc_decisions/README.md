# registers/hdc_decisions — Health and Disability Commissioner decisions

Step 5.3, a source to acquire (for use case 11, healthcare operator
governance). The Commissioner's published decisions and case notes on
complaints about providers, captured verbatim by hash through the fetch
gate under the four questions, read by profile into one row per decision
(case number, date, the provider kind, the findings as the Commissioner
states them) and one row per named provider organisation; a consumer or
an individual practitioner the Commissioner anonymises is never named.

Built by `hdc-1`; `spec.md`, `capture.py`, `read.py`, `load.py`,
`publish.sql`, `check.py`, `sample.list`, `tests/` and the position page
are its deliverable.
