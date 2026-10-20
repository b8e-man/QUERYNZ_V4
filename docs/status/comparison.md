# comparison: where it stands

**Date:** 2026-10-20. **Step:** 4.5, the comparison with the frozen site,
`checks/`. **Merge request:** `comparison-1`.

## Done

- `checks/comparison.py` + `comparison_figures.py`: pairs the frozen
  current version with the rebuilt version built from its listing; reads
  every file of the ten kinds on both sides into the same figures (money
  in cents, no tolerance); 48 cause rules, each with a card in `cards/`;
  day record `<live>/checks/comparison/days/<version>.json`, ledger
  `ledger.jsonl`, streak of clean days; board item `comparison`
  (registered in `board.py`); job `qv4-site-compare` proposed in
  `checks/jobs-proposed.toml` (19:45 UTC, after `qv4-site-build`).
- First day recorded (2026-10-20T0620 vs 2026-10-20T1134): 43,062
  differences, 0 uncarded, 23,067 under cards saying the new side is
  short; not clean. 40 new cards, 4 existing ones reused. 27 tests.
- Tranche 2: `checks/module_checks.py` runs every `registers/*/check.py`
  with a main (bar track E's two, on `windowed`) and the board's and the
  published site's checks as commands with a timeout (120 s; all answer
  in under 2 s); board item `module-checks`. Today 14 run, 4 red:
  disclosures (National 2023, carded by that lane), expenses (printed
  totals, carded by that lane), party-returns (Labour 2017, carded by
  that lane), board (four gazette tables not in the catalogue, new card
  `four-gazette-tables-are-published-and-not-on-the-board`).

## Half-done

- Nothing.

## Next

1. Integrator: merge `comparison-1`; append `qv4-site-compare` to the
   jobs catalogue from `checks/jobs-proposed.toml`; add the four gazette
   tables to the board's catalogue; run `python -m
   checks.comparison run` once after each `qv4-site-build` until the job
   is installed.
2. Lanes: the cards owned by candidate-returns (9,618), party-returns
   (Part A rows 1,909; two no-total party-years; rows only one side has),
   house (results, roster, labels, name forms), site (sections, boards,
   financials, list candidacies), disclosures (names, dates), parties
   (renames).
3. Arthur: the queue question on which frozen sections belong in the
   template; the two-returns default; ruling 253's reach over coupled
   names ("A & B Surname").
