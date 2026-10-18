# windowed-1: track E, the windowed sources: two legal positions and two capture lanes
branch: session/windowed (pushed; head 35e67f3)
session: windowed (session 2; the work is session 1's, 18 October)
raised: 2026-10-18; re-raised on a real branch 2026-10-19
claims: docs/legal/positions (tenancy-tribunal-decisions.md, real-estate-authority-decisions.md); registers/tenancy_tribunal and registers/real_estate_authority (capture.py, tables.sql, check.py, spec.md, pane.md, publish.sql, sample.list, sample.py, tests); the session's own cards, lesson, status and queue files

**Ready to merge.** Session 2 was started in its working copy (fence: the
windowed scope), copied session 1's tree in unchanged at its repository
paths (every path accepted by the scope hook) and committed it as 5d4e9b1,
with one change: the fence card is closed. 35e67f3 is the status file.

What it claims: the one-page legal position for each class (the four
questions, hosts, crawl delay none stated, floor 5 s off-peak), and each
lane's capture through `support.fetchgate.open_url` and
`support.docstore.landing.land` only: listing first (the Tribunal's listing
service asked for numbers and dates only, never names, addresses or text;
the Authority's database by year), then each order or decision fetched once,
soonest to leave first, a block or a challenge stopping the run, off-peak
unless `--anytime`. The tables hold numbers, dates, URLs and hashes, never a
name or an address. Nothing is published. `check.py` compares the source's
own count per month (Tribunal) or year (Authority) with what is held.

Fast tier (run with the main checkout's Python; card
`bin-fast-falls-back-to-the-system-python-in-a-working-copy`): green except
`tests/test_generators.py::test_the_committed_records_generate_cleanly`,
which is the card board, lessons index and decision queue not yet listing
the new cards, lesson and questions: generated at the merge.

**Already live, no load needed for what is held:** on 19 October the
session landed session 1's preserved capture of 18 October through the
landing wrapper (621 documents, every hash re-verified, the original fetch
times kept) and loaded their rows into the lanes' own tables in
`querynz_v4` (created by the lanes' `tables.sql`): Tribunal 1,307 orders
listed, 456 held (every order leaving through 1 November); Authority 84
cases listed for 2023, 52 Committee decisions held (52 abstracts, 102
PDFs). The first nightly run continues from there and fetches nothing twice.

After the merge, the integrator:
1. adds the two `qv4-` entries in card `windowed-capture-jobs-into-the-catalogue`
   to `support/scheduler/jobs.toml`, runs the scheduler's check and the
   installer, and registers the two checks on the board. Urgent: about
   thirty Tribunal orders reach their three years each day; those through
   1 November are held, later ones are lost if the job is not on by then.
2. drops `docs/decisions/queue/restart-the-windowed-session-in-its-working-copy.md`
   (answered by this session starting; deleting it here was refused by the permission check).
3. takes two cards for `support/fetchgate` (outside this fence): the two
   hosts' 5 s floor in `FLOORS`; `open_url` following a redirect to another
   host unchecked and returning gzip undecoded.

No support.db change is needed (both schemas exist since 18 October).

## Earlier result (integrator, founding session, 18 October 22:50)

Not merged then: there was no branch (session 1 was fenced as the main
checkout). Overtaken by this request.

**Added 19 October (0d57b55):** Arthur answered both track E questions,
"Decisions held - yes": the defaults of `tenancy-orders-past-their-three-years`
and `rea-decisions-beyond-in-house-use` are rulings. Number them in
`docs/decisions/rulings.md` and drop the two queue files at the merge.

## Result (integrator, founding session, 19 October 07:45)

Merged into main as 82b169d together with windowed-2 (integration branch
integrate/windowed-1 from session/windowed at 0d57b55, gate green). Out of the
windowed fence, done here as the cards asked: the two capture jobs in
support/scheduler/jobs.toml (qv4-tenancy-tribunal-capture 09:30 UTC at
priority 33, since 30 was qv4-embed's; qv4-real-estate-authority-capture
10:00 UTC at 31; scheduler check green, 32 job types); both hosts in
support.fetchgate.FLOORS at 5 s; the two lane checks on the board through
checks/windowed.py, which runs each as a command and is red until the
capture catches the source up (Tribunal 2023-11: source 896, held 45;
Authority 2023: 84 listed, 52 held). The overtaken queue item was dropped,
the two cards closed, the lesson's rule shortened to the index's limit.
Still open: the gate's redirect and gzip card (support/fetchgate, a fix
session). The worker reloads the catalogue on its own clock; the first
scheduled runs are tonight unless the hand run on Arthur's word is first.
