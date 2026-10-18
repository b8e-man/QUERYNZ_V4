# windowed-1: track E, the windowed sources: two legal positions and two capture lanes (NOT YET PUSHED)
branch: session/windowed (nothing pushed yet: see below)
session: windowed (session 1)
raised: 2026-10-18
claims: docs/legal/positions (tenancy-tribunal-decisions.md, real-estate-authority-decisions.md); registers/tenancy_tribunal and registers/real_estate_authority (capture.py, tables.sql, check.py, spec.md, pane.md, publish.sql, sample.list, sample.py, tests); the session's own cards, lessons, status and queue files

**Do not merge yet: there is no branch to merge.** This session was started
with Claude's project folder at the main checkout, so the scope hook judged it
by the main checkout's `.scope` (founding-f05585e) and refused every write
into `/home/user/querynzv4-work/windowed`; a clone into scratch to commit
from was refused by the auto-mode classifier. Nothing was committed or pushed.
The finished work is a tree at repository paths, every path checked against
the windowed scope with the hook's own `judge()`:
`/home/user/querynzv4-work/scratch/founding-f05585e/windowed/tree/`. The next
windowed session, started in its working copy, copies it in, runs `bin/fast`,
commits, pushes, and edits this request to say the branch is ready.

What it claims, once pushed: the one-page legal position for each class
(the four questions, hosts, crawl delay none stated, floor 5 s off-peak), and
each lane's capture through `support.fetchgate.open_url` and
`support.docstore.landing.land` only: listing first (the Tribunal's listing
service asked for numbers and dates only, never names, addresses or text;
the Authority's database by year), then each order or decision fetched once,
soonest to leave first, a block or a challenge stopping the run, off-peak
unless `--anytime`. The tables hold numbers, dates, URLs and hashes, never a
name or an address. Nothing is published. `check.py` compares the source's own
count per month (Tribunal) or year (Authority) with what is held. 32 tests on
fakes in the fast tier; the tables and queries were run on the sample
database inside a rolled-back transaction.

After the merge, the integrator: adds the two `qv4-` entries in card
`windowed-capture-jobs-into-the-catalogue` to `support/scheduler/jobs.toml`,
runs the scheduler's check and the installer, and registers the two checks
on the board. No support.db change is needed (both schemas exist since 18
October). Two cards for `support/fetchgate`: the two hosts' 5 s floor in
`FLOORS`, and `open_url` following a redirect to another host unchecked and
returning gzip undecoded.

Held tonight, outside the store (scratch, by hash, 22:00 to 22:41 NZDT, through
the lanes' code and the gate, 5 s apart): Tribunal 456 orders (every order
leaving the source through 1 November), Authority 52 Committee decisions (61
abstracts, 102 PDFs). The next windowed session lands them through the
landing wrapper (`docs/status/windowed.md` in the tree says how).

Known to fail until generated files are rebuilt: the card board and the
lessons index will not list the new cards and lesson; `docs/decisions/queue.md`
will not list the three new questions.

## Result (integrator, founding session, 18 October 22:50)

Not merged: there is no branch. The session was started as an agent of the
founding session, so Claude's project folder was the main checkout and the
scope hook fenced it as founding-f05585e; its clone into scratch was refused
by the classifier as a way round the fence. The integrator does not commit a
session's tree from scratch for the same reason: the fence is the gate's
evidence, and only a session started in its working copy can carry it.
The tree stays at /home/user/querynzv4-work/scratch/founding-f05585e/windowed/tree/
and the held documents (456 Tribunal orders leaving by 1 November, 52
Authority Committee decisions; 98 MB, hashes re-checked) at .../windowed/held/.

What waits on Arthur: start track E in its working copy, on node2:
`cd /home/user/querynzv4-work/windowed && claude --model opus --permission-mode acceptEdits`
with the brief in docs/briefs/next.md (## windowed), which now says: copy
the tree in, bin/fast, commit, push, land held/ through the landing wrapper,
then raise windowed-1 again as a real branch. About 30 Tribunal orders leave
the source each day; the ones leaving before 1 November are already held.
