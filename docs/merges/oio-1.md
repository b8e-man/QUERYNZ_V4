# oio-1: the overseas investment decisions lane (step 5.3, use case 12), captured, not held
branch: session/oio-1 (pushed; beaa52d)
session: oio-1 (Opus)
raised: 2026-10-21
claims: registers/overseas_investment/ (capture, read, load, check, tables, publish, sample, sample.list, pane, spec, profile-proposed.jsonl, position/, tests); docs/status/overseas-investment.md

## What the lane is

`pub.overseas_investment_decisions` and `pub.overseas_investment_parties`. The office's listing at
`www.linz.govt.nz/our-work/overseas-investment-regulation/decisions`, filtered by decision year from 2017, 60 rows a
page; each summary page read by profile, no model. One row per summary page (case numbers, Decision or Notification,
outcome and section as stated, decision maker, date, pathway, class, the land statement with street addresses and
legal descriptions withheld, areas as stated and in hectares, the money row as headed, penalty, rationale as stated);
one row per applicant / consent holder, vendor and issuer (name as published, status, trust, company number where
printed, ownership origins and shares as stated). Street addresses: `overseas_investment_private.investments` only
(hard limit 15). A name withheld under the Official Information Act is withheld with its origins (16). The agent's
contact block is never read. Crown copyright, CC BY 4.0; views carry the attribution.

Proof, daytime, 58 requests through the gate: all ten years' listings (27 pages): **1,337 rows on 1,318 pages**,
every year matching its pager; 24 summaries read clean. 34 lane tests (17 mutants), none skipped; whole-repository
fast tier green (399 s, over the 300 s target, recorded). check.py is red until the first full capture, correctly.

## For the integrator at the merge

1. Add `overseas_investment` to `support/db` `LANES`.
2. Move `registers/overseas_investment/position/overseas-investment-decisions.md` to `docs/legal/positions/`
   (`hosts: www.linz.govt.nz`; it covers only the decisions listing and the copyright, disclaimer and privacy pages).
3. Append the three `profile-proposed.jsonl` lines to `support/profiles/profiles.jsonl`.
4. Gate floor 5 s for `www.linz.govt.nz` in `support/fetchgate` `FLOORS`.
5. Two jobs as spec.md proposes: `qv4-overseas-investment-capture` nightly 23:10 (first nights about 1,320 summaries)
   and `qv4-overseas-investment-load` nightly 06:35.
6. The proof's scratch schema `scratch_oio_1_capture` (sample database) can be dropped with the session's scratch.

## To file (the brief fenced this session out of queue/, lessons/ and cards/)

- **Queue item, default applied:** the land's street address is withheld from every view, for companies too.
  Recommendation: keep it; a company's land is not its registered address and a sale often has a person on the
  other side. Alternative, a setting: show it where every party is an organisation. Blocks nothing.
- **Queue item, default applied** (same as regulators-1's): how long a row naming an individual is shown. Default:
  while the office shows it.
- **Lesson** (area: capture, privacy, hard limit 15, government decision summaries): A government summary's land
  statement carries the street address of homes, and a street-word test misses a number before a name with no street word ("12 Invented Creek"): withhold by the
  house-number shape and test the withholding against business phrases it must keep. Paid for by oio-1, 21 October
  2026.
- **Lesson** (area: tests, mutants): Run the mutant check before trusting the rules: four of seventeen mutants
  (table date over meta date, a partly withheld figure, a non-OIO page, rural delivery numbers) passed every rule
  until the rules were widened.

Nothing held on terms. Not compared with the old estate's held copy.

## Result (integrator, 2026-10-21 22:19 NZDT)

Merged into main as c3ae259 (`merge integrate/oio-1: gate green`). Branch `integrate/oio-1` from `session/oio-1` (beaa52d), main merged. Integrator items: `overseas_investment` in the lane list with its schemas applied with grants on both databases; the position moved to `docs/legal/positions/overseas-investment-decisions.md`; the three profiles appended as version 1 (103 slugs); `www.linz.govt.nz` floored at 5 s; `qv4-overseas-investment-capture` (nightly 23:10 NZDT, three-hour budget) and `qv4-overseas-investment-load` (06:35) in the catalogue at priorities 67 and 68, `support.scheduler check` green; the lane's `load.py` gained the staging contract's `load(conn, schema)`. Filed for the session, whose fence kept it from queue/, lessons/ and cards/: two queue items with their defaults applied (the land address withheld from every view, companies too; a row naming an individual shown while the office shows it) and two lessons (withhold a land statement by the house-number shape; run the mutant check before trusting the rules). The regulator board views carried with it. The fast tier was first red in 34 s: the lane's package had no `__init__.py` on the session's branch, so its two test modules collected as the root tests package and failed to import; the file added on this branch, the lane's 34 tests green, fast tier then green in 486.8 s. The integration script stopped at a lesson first line of 263 characters after applying everything before it; the two lessons were written by hand within the limit. Gate green; staging: no finished pass of any year's listing is held in the working copy, so the tables were made empty (0 rows) and published; the nightly jobs fill them. The two board views go in at the next merge. The drop of `scratch_oio_1_capture` in the sample database is Arthur's. Branches and the working copy retired.
