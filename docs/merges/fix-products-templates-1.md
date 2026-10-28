# fix-products-templates-1: the templates' live tests after the links build of 28 October (rulings 114, 116)
branch: fix/products-templates-1 (pushed, c02e079, one commit on main's e9930c7)
session: fix-products-templates-1 (Opus, fix weight, scope products/templates/)
raised: 2026-10-28
claims: products/templates/03-banking/tests/test_banking_real.py, 08-recruitment/tests/test_recruitment_real.py, 12-property/tests/test_property_real.py; cards/the-report-walk-reads-a-namesake-star-one-hop-so-a-spoke-sees-only-the-centre.md (new, blocker); one lesson (regenerate lessons/INDEX.md at the merge); docs/status/templates.md (new, 1,160 bytes)
template rules, template.toml, limits.md, checkpoints: **unchanged**. No DDL, no job.

## Proof

`QV4_INTEGRATOR=1 bin/fast products/templates`: green (52.9 s). Every slow
test under `products/templates` (all ten templates' `*_real.py` and the
rest), live, read only: 33 passed, 1 strict xfail, 2 min 15 s. Before the
change the same run had exactly the three reds in the brief and nothing
else red.

## The three, and why

**03-banking, `test_from_the_company_a_liquidation_names_the_people_checks_block`.**
`TWICE_LIQUIDATED` took the smallest director row of the first uncontested
group on 2 to 10 companies with 2 or more liquidations. The rows of the new
people views joined that group: its id is now a `charities:` officer row
(the group is 9 rows: 4 charity officer, 3 director, 2 shareholder), and
its first director row sits on a company never liquidated, so the
company-side query joining a liquidation to that director found nothing.
The template rule is right; the subject choice leaned on sort position. It
now takes the group's smallest director row on a liquidated company. The
group chosen and the first test (`repeat-insolvency` red) are unchanged.

**12-property, `test_a_director_with_two_failed_companies_…`.**
`SERIAL` started from every going development company and joined every
row of each director's group (a minister's group holds 30,836 rows). Live,
read only, through `bin/q --long`: **over 600 s (cancelled at the
10-minute reader)** before; **1.4 s** after. The query now starts from the
companies in liquidation or receivership, keeps the groups holding two or
more of them, then meets the development companies. The conditions are
the same, so it picks the same subject (the smallest qualifying company
key).

**08-recruitment, `test_the_most_shared_name_keeps_its_namesakes_apart_and_never_confirmed`.**
Not a template fault and not fixable inside this fence. `name-only@1` is a
star: one link from each component's anchor to the anchor that sorts
first; two spokes carry no link between them. `products/report/walk.py`
`links_of` reads the links on the subject's group rows only. The subject's
group (360 rows, contested) is now a spoke: its one near link goes to the
centre, a building practitioner decision row (`building_practitioners:`
sorts before `companies:`) with 157 spokes. Recruitment does not read that
view, so the memo lists 0 namesakes. Resolving the row to its group id
does not help: the walk already passes the group's rows, and the link it
needs is between the centre and the other spokes. The test is split: the
assertions that still hold (none confirmed, every line near,
`namesake-exposure` fired, `bankruptcy` blocked, charity marks amber at
most) stay live; `near > 0` is a new strict xfail naming the blocker card,
so it turns red as XPASS the day the walk is fixed and is then unmarked.

## For the integrator: the walk, and the contract's wording

1. **A false clear.** Of 160 Gazette prohibition rows with a namesake,
   about 90 are spokes of a wider star. A memo from another spoke clears
   `prohibition` ("every link from the subject's rows was read") with the
   notice out of reach. The same holds for every source the templates mark
   "joined by name in pub.links" (02, 03, 04, 05, 06, 07, 08, 11, 12, 13).
   The fix is in `products/report/walk.py`: follow each `name-only@1` near
   link through to the other end's group and read its `name-only@1` links
   of the same name key; and always pass the group id with the group's
   rows (the members limit of 300 orders by `row_key` in the database's
   collation, which need not put the group id first). Carded as a blocker;
   a `bin/fix products/report` session. I did not change the template rules
   to block those clears: that would make every person with a namesake
   blocked, and be undone when the walk is fixed. Say if you want it.
2. **`links/spec.md`'s contract**, as the brief quotes it, is not in this
   copy (main e9930c7). Measured against `links/build.py`: a link's end is
   the component's first row of that name, not its group id: on a
   200,000-link sample, 770 `row_a` and 413 `row_b` are not their group's
   id. And "look for the link between those two keys" finds one only when
   one of the two is the centre. Suggested wording for the links lane:
   "two rows are near when their groups each hold a row of the name and
   one of the two groups' anchors carries the star's centre, or both reach
   it; a reader lists a row's namesakes from the centre's links, reached
   through the one link on the row's group".

## Not printed

No home address and no suppressed name: counts, refs and register keys.
The subjects' public director names appear only in the session's scratch
render, not here.

## Result (integrator, 29 October 04:40 NZDT)
Merged f851e93 as `integrate/fix-products-templates-1`, gate green at the first run (the templates' slow tests; one strict xfail, the recruitment namesake count, until fix-products-report-4 merges and the integrator lifts it). Released. The false-clear finding went to products/report as fix-products-report-4 (launched 28 October 23:47, ready); the wrong clears were left in place meanwhile, Arthur told. The links spec's near-link wording was corrected on integrate/fix-links-5 as this request suggested. Branch and working copy retired.
