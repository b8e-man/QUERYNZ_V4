# grants-1: the step 6.3 grants lane (class 4 societies and the Lottery Grants Board), the national file read, nothing held
branch: session/grants-1 (pushed; b6f9440)
session: grants-1 (Opus)
raised: 2026-10-21
claims: registers/grants/ (capture, read, load, check, tables, publish, sample, sample.list, pane, spec, survey.md, profiles-proposed.jsonl, position/, tests); docs/status/grants.md; four cards; one queue item (default applied); one lesson

## What the lane is

- **The national file.** The Department of Internal Affairs publishes every class 4 society's grants, approved and
  declined, as societies report them, in one CSV on the data catalogue ("Grants from Gaming Machine Profits",
  CC BY 4.0): 178,739 records, decisions 2021 to 2025, 47 society name forms mapped to 37 societies. Read by
  profile `dia-class4-grants-csv` v1: 178,729 grants, 10 set aside (no recipient). No purpose column (the
  Department's two categories instead). NZBN and charity number kept only where valid; every field also as
  published. 18,685 grants name a recipient no organisation word or number shows to be one: kept as printed,
  never looked up.
- **The Lottery's records of grants.** Pages on Community Matters, Name and Amount, an asterisk for multi-year.
  Read by profile `lottery-record-of-grants-page` v1; one record held and read (2024/25 round two, Community
  National: 156 grants, $14,710,725, 61 multi-year). The records hang off no index, so the capture walks the
  site whole.
- **Views.** `pub.grants`, `pub.grant_recipients` (per grantor, as published), `pub.grant_publishers` (the
  Department, the Lottery Grants Board, 37 societies with sites and the Department's list flag), each with
  licence and attribution. No address anywhere.
- **The societies' own sites.** All 31 on the Department's list surveyed (`registers/grants/survey.md`): 9 publish
  PDF lists, 12 no list found among their first grants pages, 6 no grants link, 2 dead addresses, 2 on other hosts.
  Carded by class; they add 2017 to 2020 and the purpose as printed.

Proof: the whole file and the record loaded in `scratch_grants_full` (querynz_v4_sample): 178,885 grants, 91,430
recipients, 39 publishers; `check.reading`, `check.views` and `check.outside` all green; 9.8 s. 105 page requests
in all through the gate, daytime, serial, 5 s apart (10 s for the catalogue). Nothing held on terms.

## For the integrator at the merge (card `the-grants-jobs-into-the-catalogue`)

1. Add `grants` to `support/db` `LANES`.
2. Move `registers/grants/position/*.md` (two pages) to `docs/legal/positions/`.
3. Append the two `profiles-proposed.jsonl` lines to `support/profiles/profiles.jsonl`.
4. Gate floors 5 s for `www.communitymatters.govt.nz` and `www.dia.govt.nz`.
5. Two jobs as `spec.md` proposes (`qv4-grants-capture` nightly 22:45, `qv4-grants-load` nightly 06:35).
6. Regenerate `docs/decisions/queue.md`, the lessons index and the board: `tests/test_generators.py` is red on this
   branch only because the new queue item, cards and lesson make the committed generated files stale. Everything
   else in the fast tier passes (the lane's 44 tests; the whole repository in 451 s, over its 300 s target).
   The check is red on the live database until the first capture and load have run, correctly.

## Also raised

- Card `the-fetch-gate-misses-an-imperva-interstitial-and-follows-redirects-unasked` (support/fetchgate, a fix
  session): Imperva's "Pardon Our Interruption" page with a 200 passes `looks_challenged`; `open_url` follows a
  redirect to a host the gate never judged. The lane works round both itself.
- Queue: whether a declined application naming an individual is shown (default: as the Department shows it,
  inside the estate only).
- Lesson: look for the regulator's own collected file before surveying many publishers.

## Result (integrator, 2026-10-22 00:10 NZDT)

Merged into main as 122cfc0 (`merge integrate/grants-1: gate green`). Branch `integrate/grants-1` from `session/grants-1` (b6f9440), main merged. Card `the-grants-jobs-into-the-catalogue`, now closed: `grants` in the lane list with its schema applied with grants on both databases; the two positions moved to `docs/legal/positions/` (`class-4-society-grant-publications.md`, `dia-gambling-and-lottery-grants.md`); the two profiles appended as version 1 (109 slugs), the proposed file removed; the gate floors `www.communitymatters.govt.nz` and `www.dia.govt.nz` at 5 s; `qv4-grants-capture` (priority 69, nightly 22:45 NZDT, at most 4 hours) and `qv4-grants-load` (70, 06:35) in the catalogue, `support.scheduler check` green. The lane's `load.py` gained the staging contract's `load(conn, schema)` (the job's build, its check's problems logged). Fast tier green in 502.8 s. The gate's first run was refused at the staging step: the lane's listing reads `grants.capture_docs`, which the capture makes, and the capture has never run on the live database (the session kept to the sample database, as it should); the staging load now makes the reading tables empty when that table is absent, fast tier again green in 501.2 s. Gate green; staging: the capture has never run on the live database, so the three tables were made empty (0 rows) and published; the nightly jobs fill them. The three grants views (`pub.grants`, `pub.grant_recipients`, `pub.grant_publishers`) are catalogued on the board in the merge after this one, once published. The fetch-gate card (the Imperva interstitial passed as a 200; a redirect followed to an unjudged host) stands for a fix session. The queue item on declined applications naming an individual stands with its default (shown as the Department shows it, inside the estate only). Branches and the working copy retired.
