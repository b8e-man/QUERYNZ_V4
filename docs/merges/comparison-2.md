# comparison-2: the comparison's second tranche: readers for the template's second version, every section read, eighteen new causes
branch: session/comparison-2 (pushed)
session: comparison-2 (Fable)
raised: 2026-10-20
claims: checks/comparison.py, checks/comparison_figures.py, checks/README.md, checks/tests/test_comparison.py; cards/ (10 new: the frozen's withheld expenses, the cancelled poll, the candidate-donor pages the frozen never wrote, two donor pages for one name, the interests tree, the interests counts, statements by period, expense reconciliation, promoter people, unmatched declarations, and the blocker `a-donor-name-key-on-the-rebuilt-site-carries-a-residence-fragment`; 3 closed: the readers card, sections-the-rebuilt-pages-add, the-lanes-checks-are-not-on-the-checks-board; 1 accepted: the nil return; 2 annotated); lessons/a-reader-that-reads-one-side-reports-the-other-as-absent.md; docs/status/comparison.md

Step 4.5, the second tranche. Today's run on the real folders (frozen
2026-10-20T0620 against rebuilt 2026-10-20T1513) had 614 uncarded
differences and exited 1 because the readers predated the template's
second version. Now: 29,508 differences, 0 uncarded, 7,947 under cards
saying the new side is short; the run exits 0; not clean.

- Readers: the home page's electorates on both sides, by year; the year
  files' own figures; the person page's candidacy money; a party name
  listed twice on the rebuilt home (the entry with most to show); every
  section `products/templates/ftm/ftm.json` `page_sections` lists (the
  home page's eleven money sections, the parties page's three, the party
  page's statements, members, made, sighted, top ten, leaders, rules; the
  person page's received, positions, properties, boards, expenses,
  interests tree; the electorate page's window money); `sections_added`
  read so the shape's own keys are not counted; the frozen gap line as prose.
- Rules: an electorate's year follows its race's causes; the home page's
  candidate sections follow the lane's coverage; an aggregate's parts named
  by its path; "not held" against nothing shown is no difference; the two
  house rules point at `candidacies-the-frozen-site-shows-and-the-house-
  lane-lacks` (house-2's closure); that rule files name forms (93), other
  given names (17) and frozen duplicates (15) under their own cards and
  keeps 41 (Mana and Rongotai 2020 and their follow-ons); the rows rule
  names the rebuilt's twin donor pages (187) instead of two lanes' cards;
  NZ First 2019 and the unresolved labels go to their lane cards.
- Every difference with its cause is written beside the day record
  (`<version>.diffs.jsonl`, figures only), so a card's full list is on disk.

Module checks: 14 run, 3 red, each under its lane's open card
(disclosures: National 2023 and the May declaration; expenses: printed
release totals; party-returns: NZ First 2019, Labour 2017).

Hard limit 15: a donor `name_key` on the rebuilt site (and the same key in
a party page's top ten) carries a residence fragment; carded as a blocker
for links and site; not repeated in any file. It was printed into this
session twice by a sample dump before it was seen.

For the integrator: regenerate the board; the ledger's line for
2026-10-20T0620 is this branch's run (the 19:45 job on main re-records it
with the old readers until merged). house-2's branch closes
`the-house-lane-has-no-result-for-a-race-the-frozen-site-shows-won` and
annotates the lacks card; this branch does not touch either file.

Fast tier: checks/tests 61 passed (the real-pair test among them; a test for the residence-word guard on what the comparison records);
tests/test_imports_one_way.py and test_reading_limits.py green.
Nothing written in the old folder; no address or suppressed name in any
file written. Lesson: `a-reader-that-reads-one-side-reports-the-other-as-absent`.

## Result (integrator, 2026-10-20 18:05 NZDT)

Merged to main at e7de214, gate green. The accepted nil card took its
close date (the board generator requires one). Today's comparison re-run on
main with the new readers: exit 0, every difference carded, not clean. The
residence-fragment blocker is reported to Arthur without the words and goes
to the site session (site-3) with the links; the frozen side's copy of it
is Arthur's emergency-fix decision (hard limit 19). Worktree and branch
retired.
