# companies: where it stands

**Date:** 2026-10-20. **Step:** 4.1, companies, `registers/companies/`.
**Merge request:** `companies-1`.

## Done

- Raw files: none survive (deleted after loading under the old retention
  rule). The loaded tables of `companies-2026-07` and `companies-2026-08`
  were exported once on 20 October 2026, 05:56 to 05:57 NZDT (old read-only
  login, statement limit, server-side cursors, 48 s) to four gzip parts,
  pinned in `capture.py` and landed in the store by the sample fill.
- Reading, measured on every real row: 1,920,468 entities (1,821,454
  companies; 59,981 societies and the like; 35,599 charitable trust boards;
  2,922 public sector; 512 retirement villages), 5,629 earlier states,
  1,185,805 director roles, 1,581,955 shareholdings, 867,277 registered
  offices. Every export line is a row or a catch-log line; each file's
  count reconciles with the old loader's own, folds logged with their
  count. No end date is carried: a role's window is the files it is in.
- Outside check: the Companies Office's statistics; 30 June 2026 live
  756,999 against 756,821 (+0.02%); monthly incorporations equal or within
  one, removals within 1%, April 2025 to July 2026. Green on all real rows.
- Fast tier green (lane 20 tests; whole repository 117 s).

## Carded

- `the-companies-office-statistics-file-has-no-legal-position`.
- `the-old-loader-folded-shareholdings-and-kept-no-role-numbers`.
- `no-monthly-company-file-is-held-for-the-18-november-step`.
- Queue: `the-company-package-carries-sole-traders` (default: not taken).

## Next

1. The merge gate's full load (about 5.6 M rows) and the SQL check on it.
2. The insolvency appointments and the other package tables, if a product
   asks; a reader for the raw CSVs when a package is held as a file.
