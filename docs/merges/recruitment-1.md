# recruitment-1: template 08, the recruitment board screen (step 5.2, use case 8)
branch: session/recruitment (pushed; 66251e0)
session: recruitment
raised: 2026-10-20
claims: products/templates/08-recruitment/ (template.toml, rules.py, limits.md, README.md, tests/); docs/status/recruitment.md; lessons/a-view-no-link-reaches-prints-a-blank-that-is-not-a-clear.md; nine cards (below)

The first use-case template on the subject-report shape. It reads 23 pub
views, each with its licence, attribution and refresh, and nothing else; its
seven sections run in the order a search consultant reads them, the
namesakes set apart first. Thirteen flags stand for the old estate's seven
person rules where the held registers support them; where they cannot see
(bankruptcy, the Charities Register's marks, ComCom) the flag is blocked,
never clear. Red only on the subject's confirmed rows, amber on a
namesake's; a Gazette notice sits beside the subject's dates on the company
with no word between; a removal from the register is not insolvency.

`rules.py` and the tests import nothing of `products.report`: the one-way
test holds `products/templates` to its own code. The rules carry their own
flag contract (re-checked by the shape's rule 9 on every report) and the
tests reach the shape through `python -m products.report`.

Checked on querynz_v4: fast tier `products/templates` green in 24.7 s with
the fill (21 tests of this template); slow 3 passed (real tables through the
CLI); `python -m products.report check` green; tests/test_imports_one_way.py
green. Checkpoint: 12 real subjects, 10 print clean, 2 refused by the
shape's own checks (cards 1 and 2); 0.2 to 4.6 s each; three facts read
against their Gazette notices. `limits.md` is the known-limits page.

Cards, for the report lane: a-surname-lane-trips-the-home-address-check,
a-company-name-with-control-trips-the-cause-check,
a-template-cannot-reach-the-flag-contract-or-the-shapes-rules,
an-mps-declared-interests-are-not-walked-from-a-person-start,
expenses-views-are-not-in-the-report-catalogue,
a-gazette-company-notice-date-does-not-say-what-it-dates,
the-report-header-repeats-group-rows-a-section-lists,
a-donation-row-start-has-no-group. For links:
bankruptcies-and-appointments-are-not-in-pub-names.

For the integrator: nothing to install; the shape's `qv4-report` serves
every template on disk. tests/test_generators.py fails in this working copy
only because the new lesson and cards are not yet in the generated
lessons/INDEX.md and docs/board.md (its run rewrote docs/board.md here,
uncommitted); the gate's rebuild makes them current.

## Result (integrator, 2026-10-20 15:26 NZDT)

Merged into main as 24787e0 (merged main first). Done at the merge:
records regenerated (the lesson and nine cards); the site-2 record and
the next template's folder (`products/templates/04-agriculture/`, a
README) rode in the same commit; status and briefs. Fast tier and gate
green; nothing to install, as the request says: `qv4-report` serves every
template on disk. The eight cards for the report lane were taken up by
session `report-2` (Fable), launched at 15:05 before this merge from the
request's list; the links card waits for the links lane's next session.
The hard-limit 11 note is recorded here and nowhere else. The session ran
headless from the integrator as Opus, about 30 minutes.
