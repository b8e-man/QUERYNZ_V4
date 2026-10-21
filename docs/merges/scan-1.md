# scan-1: the register-scan shape (step 6.1)
branch: session/scan-1 (pushed; d3af878)
session: scan-1
raised: 2026-10-21
claims: products/scan/ (new: __init__, __main__, views, settings.toml + settings, template, plan, lines, hubs, run, db, tables.sql, state, out, server, rules, check, spec.md, README, jobs-proposed.toml, units/qv4-scan.service, templates/society-officers-liquidations, templates/donors-named-as-companies, tests/ 3 files); docs/status/scan.md; two lessons (cut-a-streamed-scan-by-stopping-the-fetch-not-with-a-sql-limit, read-a-link-from-either-end-as-a-union-never-as-an-or); five cards opened (links: a-person-step-cannot-reach-a-filed-row-through-the-groups, the-organisation-name-rule-reaches-past-the-exact-filed-name, charity-officers-and-organisation-rows-are-not-in-the-names-table; integrator blocker: the-scan-rerun-job-into-the-catalogue; idea: a-shared-catalogue-of-the-published-views)

The scan shape, in products/scan/, built in tranches each run against the
real published tables from this session's scratch schema
(`QV4_SCAN_STATE=querynz_v4_sample/scratch_scan_1`):

1. A scan is a template folder (`template.toml`): the question in words,
   the published views it reads with licence, attribution and refresh, the
   join as a chain of steps (by row on two columns; by person through the
   links; by a named link rule), the columns carried, the known limits.
   A template outside the contract is refused when loaded (tests).
2. One runner compiles the steps to one query over `pub` per start view
   under the chains setting (follow: `pub.groups`, contested whole where
   flagged; direct: a confirmed link between the two rows), streams it in
   pages through a server-side cursor, grades each line (confirmed, near,
   contested) with its reasons, numbers citations once per row across the
   run as the report does, flags hubs (professional director at fifty,
   nominee or trustee, the Crown, a thousand-company office), records every
   view's max(loaded_at) (the links' built_at) and the time, and writes the
   list into the product's own schema. A failed run closes its row with the
   failure named.
3. The stale rule: `python -m products.scan stale` and `run --stale`; the
   page's index shows it. It fired for real when the links rebuilt at 15:22
   and the re-run brought both scans back to current.
4. The list out: a page on port 8450 (local network only; 200 lines a page,
   filtered by grade, the page's citations beneath, the header stating the
   question, the join, the settings in force, each view's loaded_at, the
   time and the counts), and `answers.csv`, `answers.json`, `citations.csv`
   (`export`), each line carrying its citations inline.
5. The presentation rules (no word of cause, no owner, no absence as a
   finding, no suppressed name, no address shape, every step cited and
   dated, a near or contested line with its reasons) run on every run; a
   run with problems is refused by the page. The mutant test plants ten
   faults and the rules catch each; the check plants a wrong citation key
   and catches it.
6. `python -m products.scan check` (green, 1.5 s): templates, columns,
   settings in force, every citation of every latest run resolving to a row
   today, the rules, the proving facts read back from the tables, the stale
   rule, the page and the files.

Measured on the real tables: society-officers-liquidations 854 lines in
1.4 s (97 confirmed, 757 contested: two watch-flagged professional
directors' groups make 672 of them, each flagged as a hub);
donors-named-as-companies 287 lines in 1.2 s (177 party returns, 110
disclosures, all near by the rule with its reason); a join over the whole
companies register (every company with a liquidation notice) 59,786 lines
in 5.8 s, a page in 0.15 s. Fast tier 22 tests in 0.03 s; slow tests 9 s;
one-way, query-crossing and reading-limit tests green; `bin/fast
products/scan` green.

For the integrator, at the merge (card `the-scan-rerun-job-into-the-catalogue`):
create the tables with `QV4_SCAN_STATE=querynz_v4/register_scan python -m
products.scan state`, run both proving scans once, install and start
`products/scan/units/qv4-scan.service` (port 8450), add
`products/scan/jobs-proposed.toml` to the scheduler's catalogue and delete
the proposed file. The two trust settings stay "default in force" in
`products/scan/settings.toml`; the queue's two items stand.

## Result (integrator, 2026-10-21 20:10 NZDT)

Merged into main as f8a697e (`merge integrate/scan-1: gate green`). Branch `integrate/scan-1` from `session/scan-1` (d3af878), main merged. Card `the-scan-rerun-job-into-the-catalogue` (closed in the next integration commit): `qv4-scan-rerun` in the catalogue at priority 59 (the proposed 40 is taken; the proposed per-job environment is not a catalogue field and the product's defaults are the same values), the proposed file removed; after the merge the scan's tables made in `querynz_v4.register_scan`, the two proving scans run once (society-officers-liquidations run 5: 854 lines, 97 confirmed, 757 contested, 684 with a hub, 597 citations, 0 problems, 1.3 s; donors-named-as-companies run 6: 287 lines, all near, 3 with a hub, 421 citations, 0 problems, 1.1 s), `qv4-scan.service` installed as a user unit, enabled and started on port 8450 (local network only). The two sanctions board views (Sanctions lists, Sanctions listings) carried on this branch, published by sanctions-1's gate; the live check green. The unit was placed by the estate's installer (`support.installer apply --units --only qv4-scan.service`) and enabled by hand. Fast tier green in 442.7 s. Gate green, nothing to load. The two trust settings stay "default in force"; the queue's two items stand for Arthur. Step 6.1 closes with this merge. Branches and the working copy retired.
