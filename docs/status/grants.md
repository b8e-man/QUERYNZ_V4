# grants: where the step 6.3 grants lane stands

Session grants-1 (Opus), 21 October 2026, node2. Merge request `grants-1`.

## Survey (detail: `registers/grants/survey.md`)

The Department of Internal Affairs publishes every class 4 society's grants in one national file (CSV, 178,739
grants, 2021 to 2025) and the Lottery committees' records of grants as pages. 31 societies (the Department's own
list) publish too: 9 as PDF lists, 12 with no list found yet, 6 with no grants link, 2 with a dead address, 2 on
another host.

## The four questions (positions in `registers/grants/position/`, to move)

| Class | Open? | Lawful copy? | Terms | Statute, privacy | Outcome |
| --- | --- | --- | --- | --- | --- |
| The Department's national file | yes; the catalogue later served a challenge | CC BY 4.0 | none barring | s 110(4) publication; names as reported, some people | **read** |
| Lottery records of grants | yes; then 403 on "ask us" | the Department's CC BY 4.0 | the site's own not read | names organisations | **one page read** |
| Societies' own lists | yes, 2 dead | no licence seen | not read | declined applications, some people | **surveyed, carded** |

Nothing is held on terms.

## Done

- Lane built: capture, read (profiles `dia-class4-grants-csv`, `lottery-record-of-grants-page` v1), load, check,
  views `pub.grants`, `pub.grant_recipients`, `pub.grant_publishers`. Whole file proved in scratch: 178,885 grants,
  91,430 recipients, 39 publishers, every check green, 9.8 s. 44 tests, 25 of them mutants (14 reading, 7 capture, 4 check); fast tier green.

## Half-done

- No capture run yet: the jobs are proposed (card `the-grants-jobs-into-the-catalogue`). Lottery: one record read;
  the rest wait on the walk. Societies' own lists: card `the-societies-own-grants-lists-by-class`.

## Waits on Arthur

- Queue, default applied: a declined application naming an individual (default: kept as the Department shows it,
  inside the estate only).
