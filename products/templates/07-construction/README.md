# Template 07: construction subcontractor vetting and phoenix detection

Step 5.2, sixth in the plan's order; runs on the Gazette's insolvency
notices, prohibitions and bankruptcies and the companies register's roles,
offices and states, with the building practitioners register waiting. A
subject report (the shape in `products/report/`) for a head contractor's
procurement lead: "is this the failed firm again under a new name".

- `template.toml`: the 15 pub views it reads, each with its licence,
  attribution and refresh; depth 2; eight sections in the order a
  procurement lead reads them (the entity and its namesakes apart; its
  officers and holders of record, dated; the phoenix section, every company
  reached with its status and start; registered offices; prohibitions and
  bankruptcies on its people; the people beside them, their society
  roles and the Charities Register's officer rows by name (near); the Gazette on the entity and the companies above; what is not
  held, the building practitioners register, the Official Assignee's
  Insolvency Register, court judgments, employment determinations and the
  change history before 16 August 2026 named); its limits.
- `rules.py`: 26 flags. `phoenix-signature` sets each failure, dated from
  its Gazette notice, beside each going company's start with the gap in
  days, signed, nearest first, whatever the gap: the window is the
  reader's setting (ruling 65), the parameter `window_days` that
  `template.toml` declares, cut only when set, and the flag counts the pairs within 90 and 365 days;
  raised only on a shared
  person or a shared registered office from before the failure, never on a
  name alone; `same-name-failed` shows the name-only case and is never red;
  a hub or a near link is amber at most; a removal is never red. Every rule
  branches on the start; from a company the people checks block. `HISTORY
  = False`. Loaded by path by the shape, with `contract` bound; imports
  nothing of it.
- `limits.md`: the known-limits page and the checkpoint of 2026-10-21.
- `checkpoint.list`: the checkpoint's twelve subjects as register keys.
- `tests/`: fixtures and a mutant check, seventeen mutants (fast); the real
  tables through `python -m products.report render REF --template
  construction` (slow).

Run one: `python -m products.report render companies:companies/<nzbn>
--template construction` (or a director's ref; add `--html` for the page),
or on the report page (port 8440) choose the template "construction". For
the phoenix signature start from a director: from a company its people are
not followed yet.
