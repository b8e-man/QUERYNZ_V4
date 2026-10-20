# disclosures-3: the 50 unread totals measured; the text layer, the struck-out box, the date rule
branch: session/disclosures-3 (pushed; 6d04af7)
session: disclosures-3 (session 3)
raised: 2026-10-20
claims: registers/disclosures/form.py, read.py, load.py, check.py, spec.md, tests/test_disclosures.py; cards `a-struck-out-total-on-a-declaration-is-read-as-the-total` (closed), `two-declarations-sit-in-2023-on-the-frozen-site-and-2024-on-the-rebuilt-one` and `the-frozen-site-read-declaration-donor-names-off-the-scans` (measured, left open for the site), `a-newzeal-declaration-prints-42-200-over-gifts-of-27-000` and `one-2026-declaration-is-dated-by-the-commission-before-its-gift` (new); lesson `a-page-reader-can-drop-a-filled-box-and-keep-the-labels-round-it`; docs/status/disclosures.md

**Measured first.** Of the 50 linked scans with no total read, the stored
GLM-OCR reading of 49 has the form's labels but no "Total amount" line at
all, typed and handwritten alike (crops of the total box alone: 31 typed,
18 handwritten, 1 empty box whose grid of gifts makes the table's figure).
One was a parser fault: a bare "$20,000" taken for the form's boilerplate.

**Changed where the measurement says.** `form.total` takes a figure-only
line, keeps every figure in the box (`figures`), and stops at the next
label, so an empty box is no total rather than the first gift beneath it
(the old test that expected the grid's figure is changed on purpose).
Where the page reading gives no total, `read.form_reading` reads the
scan's own text layer, never on a page under a full-page picture: on typed
pages the layer gave the box's figure 126 of 126 times, on scanner pages
junk 6 of 24. It agrees with the page reading on 104 of 104 scans where
both give a figure. `read.form_check` says "equal, a second figure in the
box" where the box holds two figures and one equals the table.
`read.needs_reading` sets aside each scan still without a total, with its
hash and pages (stage `form`, ruling 62). These lines sit outside the
listing's reconciliation because their rows stand.

**Full build, scratch schema `scratch_disclosures_3_full` of the sample
database** (nothing live written, nothing fetched): 520 rows, 0 set aside
from the listing, the catch log reconciles; 27 scans need a reading. Form
check: 245 equal (was 223), 1 equal with a second figure (the struck-out
Freedoms row), 3 differ (handwritten $59,000; the May/February link; new:
a NewZeal box typed $42,200 over gifts of $18,000 + $9,000 = the table's
$27,000), 27 no total read, 244 no scan held. Frozen site unchanged: 15 of
16 party-years, National 2023 the known double count.

**`check.py` now fails only on a difference no card names,** and it prints
each one with its card. Every difference is carded, so it exits 0 on the
full build. The rule is the one the lane's own test and step 4.5 already
use.

**The received-date rule** is in the spec: the year is `given_on`'s (the
gift, printed after the amount), never `received_on`'s (the Commission's
date, which leads the row). On all 520, 8 gifts were declared in a later
year. The comparison card had the direction reversed: the rebuilt site
buckets by `received_on` (`products/published_site/figures.py:84`, also
`gates.py:187`, `read.py:95`), so the frozen side is right there.

For the integrator: no new job; `qv4-disclosures-read` may later take the
27 set-aside scans when a page-reader job is allowed. The comparison's
cause rules for the two cards want `owner="site"` (and `right="frozen"`
for the date card); that is `checks/`, not this lane.

For the merge: fast tier green bar `tests/test_generators.py`, which needs the board and lessons index regenerated (they are regenerated in this working copy, not committed: generated files are the integrator's).

## Result (integrator, 2026-10-20 18:19 NZDT)

Merged to main at bf24f02, gate green: 520 rows, 0 set aside, 27 scans
set aside for a reading under ruling 62 (stage `form`, by hash and page).
No job added. The money-year rule (`given_on`, never `received_on`) is
handed to the site session (site-3, launched 18:10) with the note that the
comparison's two cards want owner site and right frozen; that cause edit is
the integrator's in `checks/` once site-3 lands. Worktree and branch retired.
