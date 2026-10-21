# report-3: the subject-report shape, third tranche (step 5.1)
branch: session/report-3 (pushed; 248d425)
session: report-3
raised: 2026-10-21
claims: products/report/ (catalogue, rows, walk, template, build, rules, contract, memo, server, check, __main__, templates/subject/, tests/test_reaches.py new, spec.md); docs/status/report.md; lessons/filter-a-row-by-what-it-is-not-by-the-route-that-reached-it.md; cards: twenty-one closed (sixteen on main: the-catalogue-does-not-know-gazette-possessions, confirmed-expense-links-put-every-category-line-in-a-members-report, the-walk-does-not-follow-a-company-holder-up-the-chain, a-company-start-does-not-follow-its-officers, the-walk-counts-the-companies-at-an-office-and-does-not-list-them, a-section-cannot-set-the-starts-own-rows-apart-from-its-peoples, a-holders-count-of-companies-is-not-read-for-a-hub-flag, the-catalogue-names-no-overseas-registers-or-trusts-as-not-held, the-not-held-list-lacks-employment-determinations-and-the-change-history, not-held-lacks-unincorporated-entities-and-mpi, the-not-held-list-lacks-disciplinary-findings-and-tribunals, a-company-named-like-a-street-address-refuses-every-report-that-meets-it, insolvency-practitioners-are-not-reached-from-a-notice, a-crown-entity-holder-is-not-flagged-as-the-crown, group-standing-calls-a-filed-row-with-no-group-an-organisation, a-contested-groups-near-row-can-make-the-start-rows-own-company-near; five copied from session/credit-1 and session/insurance-1 with the closing added: the-catalogue-does-not-know-company-states, a-report-takes-no-since-date, a-section-cannot-select-the-rows-that-changed-between-files, the-not-held-list-lacks-credit-bureau-and-the-business-number-interface, the-not-held-list-has-no-key-for-the-safety-registers); two amended and open (four-templates-still-say-no-link-reaches-a-bankruptcy on main; the-report-keeps-no-watched-list copied from session/credit-1, carded on to 5.5)

The templates' open cards against the shape, worked in the brief's order,
each closed with a fixture test and a route in `python -m products.report
check` on a row taken from the tables at run time (green, about 40 s):

1. The catalogue knows `gazette_possessions` (pointed at from a company
   as lender and as borrower; dated "entered") and `company_states` (a
   company's earlier state, dated "as in the file …"); `gazette_liquidators`
   sits on its notice by number and the walk lists the practitioners under
   every notice on a company. One not-held list, each entry with the key a
   template cites: fourteen keys added (overseas, trusts, employment,
   company_history, worksafe, regulators, disputes, fire, tribunals,
   disciplinary, unincorporated, mpi, credit_bureau, nzbn_interface);
   limited_partnerships reworded to the partners.
2. Expense rows are listed only as totals and money outside the total by
   every route (the lane's confirmed `seat-and-window@1` links put them in
   the seat's group); the check's route 9b is green again.
3. Three reaches a template asks for by naming a walk bucket in a section's
   `sources`: `officers` (an organisation start's officers followed one
   step, near, through the officer's row), `office` (the other companies at
   a registered office that is not a hub, near), `chain` (company holders
   of record followed up to `chain_depth`, at most 4; by business number
   confirmed, by a name one company carries near; shares as filed; a cut
   chain says it goes on; a company met twice listed once). The walk runs
   only the buckets some section names.
4. A section's `own = true|false`, `statuses = [...]` and `changed = true`
   filters; a row one section leaves goes to the next naming its view.
5. A holder's `holdings` (a company holder counted on its name, a person on
   its group) and a `holding-hub` flag at fifty; a Crown entity, Crown
   research institute or State enterprise is a hub by its register name
   (`walk.CROWN_BODIES`, 130 names as read 21 October 2026).
6. Rule 7 no longer refuses a company's own registered name ("1 SHEA
   TERRACE LIMITED"); a person's street-shaped name and an address in a
   statement are still refused. `group-standing` on a filed row with no
   group says so. In a contested group the start's own company is confirmed.
7. A since date: `?since=YYYY-MM-DD`, `render --since`, `build(since=)`;
   `report["since"]` for rules, every row `new` (True, False, or None when
   it cannot say), the memo's header and NEW marks.

The checkpoint lists of the five templates that have one were re-rendered
on main's code and on this branch (60 subjects): construction's one REFUSED
report (the address-named company) is no longer refused; banking subject 7
and legal and ownership subjects in the same contested group now list the
subject's own company and its notices confirmed, so `young-entity`,
`insolvency-notices` and `repeat-insolvency` fire where they were clear or
blocked; `hubs-met` fires on three more subjects (holding hubs); otherwise
the same rows, with "holder of record in N companies" lines added. No new
sections appear in the templates until each names the new buckets.

Checked: fast tier `products/report` 34 passed with the fill; fast tier
`products/templates` green; `python -m products.report check` green;
tests/test_imports_one_way.py and test_reading_limits.py green.

For the integrator:
1. Restart `qv4-report` after the merge.
2. The six card files from session/credit-1 and session/insurance-1 (five
   closed, one amended) will collide add/add when those branches merge:
   take this branch's copies, which carry the originals whole.
3. tests/test_generators.py will fail in this working copy until the gate's
   rebuild indexes the lesson and the cards, as before.
4. Each closed card names the fix its template needs (sources, chain_depth,
   the new views and keys); those are fixes in the template folders.
Lesson: filed (filter a row by what it is, never by the route that reached it).

## Result (integrator, 2026-10-21 13:11 NZDT)

Merged into main as d9254e2 (`merge integrate/report-3: gate green`). Branch `integrate/report-3` from `session/report-3` (7407d24 after main): six card add/add conflicts taken as report-3's closed copies; fast tier green in 316.8 s (target 300 missed under load, recorded). First gate red on one agriculture real-data test asserting the catalogue's old not-held name "Limited partnerships register", which report-3 renamed to "Limited partnerships' partners"; the test now asserts the new name (ad865d3). Second gate green; its merge met a conflict on the generated `docs/board.md` only, regenerated. `qv4-report` restarted 13:1x; `python -m products.report check` green on main. `credit-1`'s merge record copied to `docs/merges/` on this branch. Branches and the working copy retired.
