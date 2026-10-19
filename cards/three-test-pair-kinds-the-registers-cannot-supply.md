# Three test-pair kinds the registers cannot supply yet
kind: finding
state: open
use-case: 1
session: links
opened: 2026-10-20
closed:

Plan 4.3 names five kinds of pair whose truth the registers state. Two are
supplied (`links/pairs.py`: two directors with one name on one company at
once; two candidates with one name in different electorates at one
election). Three are not, and the known-one-person side is thin because
of it:

- **The same role across monthly company files.** The companies lane keeps
  one row per role across the files (`first_file` to `last_file`), and the
  monthly file carries no role identifier (15 of 1.19 M old roster rows had
  one). There is no second row to pair. A later month's file gives nothing
  new on this.
- **The same charity officer across annual returns.** The charities
  register is captured (`charities-capture`) and not yet published; the
  feed's officer identifier will supply this kind in volume once a
  charities lane publishes. Re-run `links.pairs` then.
- **A candidate across an original and an amended return.** The
  candidate-returns lane is not built.

Two substitutes from the sources' own statements stand in: a seat and the
candidacy the official result says won it (the house lane's own join, 142
pairs), and the same donor by name and amount across a party return and
the amendment the Commission says replaces it. The error rate on the
one-person side is therefore measured on a few hundred pairs, mostly
politicians, which the rules never confirm by name. Accept until charities
publishes; then re-draw.

**On the "two directors" kind's truth (added after measurement 3).** 61
of 430 drawn pairs carry an identical full name and middle name on one
company in the latest file. The register lists a re-appointed director
beside the earlier row, so some of these are one person twice, not two
people; the kind's truth is clean only where the middle names differ or
are absent. The measurement counts them apart. A later month's file, or
the register's own appointment history, would settle them.
