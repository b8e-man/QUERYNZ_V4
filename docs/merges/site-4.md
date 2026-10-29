# site-4: the Commission row's citation, and the party label as filed
branch: session/site-4 (pushed; b2de781)
session: site-4 (Opus, node2)
raised: 2026-10-30
claims: products/published_site/ (render, money_sections, tests/test_commission_rows.py), docs/status/site.md, cards/ (two annotated), lessons/ (one new; the index wants regenerating)

Two causes of step 4.5 that were the template's.

(1) A `pub.candidate_return_totals` row with `read_from` 'commission' (the
Commission's spreadsheet row, no return read) now cites the spreadsheet under
its own label, "EC candidate returns summary (the Commission's spreadsheet
row; no return read)", and its evidence text states the Commission's figures
from the `commission_*` columns, or "the Commission's row prints no figures";
never the empty return columns (`render.cites`, `render.commission_figures`).
675 citations relabelled: 409 state a $0.00 the Commission printed, 266 other
figures, 0 with none.

(2) Where the official result prints no party (`pub.candidates.party` null;
51 in 2020, 84 in 2023), the person and electorate pages show the label as
filed from the return joined to the candidacy (the money's join: year,
electorate, surname) or the Commission's row, with `party_filed_from`
(`result`, `return`, `commission`) and `party_filed_basis` saying it is the
filed label; neither stays blank. 34 from a read return, 71 from a Commission
row, 30 blank. The home page's race sections then group under the label, so
`party_funding` carries a label no registration answers to, with its
candidates' money only and `registered` false (otherwise 9 differences came
back uncarded).

Measured against the frozen 2026-10-30T0617, main's code and this branch's
built in scratch from its listing (out-base, out-branch2), `checks.comparison`
unedited into scratch state folders; the base reproduced candidate-returns-3's
28,619:
- total 28,619 → 28,497; uncarded 0 → 0; new-side-wrong 5,280 → 5,153
- unregistered-label-not-on-candidacy 106 → 20 (person pages). Left: 13 where
  the Commission's row leaves the party cell blank and the frozen wrote
  "Independent" (not inferred here; candidate-returns' to read); 7 with no
  return or row joined
- candidate-returns-not-held: home 311 → 270; donor 1,412, pickers 542, person
  919, electorate 3, electorates 2 unchanged (Part A, ruling 79; the window;
  the two Webbs)
- aggregate-of-a-differing-part home 417 → 404; candidacies-from-the-results
  +18 (the party figure on candidacies the frozen lacks; ruled neither)

Tests: 4 new, all fail on main's code and pass here; module fast tier green
(65, 45 s with the fill); `python -m products.published_site check` green, 9
gates. No model, no reading, no fetch; nothing deployed; the version-3 fall
gate as it is. Lesson: an aggregate takes the groups of the sections it sums.

For the integrator: regenerate the lessons index and the board (the hook
refuses a session's index; the working copy holds an uncommitted one). In
`checks/comparison.py` the unregistered-label cause's owner wants
`candidate-returns` (outside this scope). No new job.

## Result

Merged 30 October 2026, 09:30, as 8e8321a (integrate branch 541bdd6; gate green, marked; no module with a load, nothing
staged). One integrator commit on the way: in `checks/comparison.py` the cause `unregistered-label-not-on-candidacy` is
owned by `candidate-returns` now, its why rewritten for what is left (a Commission row whose party cell is blank where the
frozen wrote "Independent", or a candidacy with no return or row joined); the lessons index regenerated. The two cards stay
open under the measured counts. Nothing to install: `qv4-site-build` (08:00 NZDT daily) builds the next version from the
release copy, so 30 October's comparison (built 08:00, before candidate-returns-3 merged 08:58) still shows the old
figures; 31 October's run is the first to carry both merges.
