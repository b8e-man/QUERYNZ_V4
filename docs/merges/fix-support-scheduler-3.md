# fix-support-scheduler-3: the standing server's night window (ruling 129)
branch: fix/support-scheduler-1 (pushed; bd02929, on main 883337f)
session: fix-support-scheduler-1 (fix, support/scheduler/), third sitting; the two earlier requests of this working copy are merged (docs/merges/fix-support-scheduler-1.md, -2.md)
raised: 2026-10-30
claims: support/scheduler/night.py (new), cards.py, registry.py, policy.py, queue.py, jobs.toml, profiles.toml, tables.sql (a comment), units/qv4-radiance.service (a comment), spec.md, README.md, __init__.py, __main__.py; tests/test_night_window.py (new, fast, 14 tests); lessons/a-managers-waits-run-on-an-injected-clock.md; docs/status/scheduler.md
closes: the queue item "where the page reader runs on node2 while Flash-Next holds both cards" (ruling 129 already closed it in the queue; this is the build)

1. **The window** is jobs.toml's new top section `[night_window]`: `start_local = "22:00"`, `end_local = "05:45"`,
   `timezone = "Pacific/Auckland"`, `standing = "flash-next"`, `profile = "page-reader"`, `card = 1`. Local hours in a
   named zone, so the April clock change moves nothing; `night.py` says whether a moment is inside (start inclusive,
   end exclusive, wrapping midnight). `python -m support.scheduler check` refuses a window whose hours are not HH:MM,
   whose zone the box does not know, whose `standing` is not a standing server or whose `profile` is a standing server
   or a view, and prints the window. No section means the standing server is never stopped.
2. **Opening.** Each tick inside the window, with the manager standing: if page pieces are queued for job types on
   `page-reader` that this box may claim, and no piece of a view on flash-next (text-reader, review) is running here
   or leased anywhere (the planner's Demand gained a `leased` count from the queue), and the unit is answering, the
   manager runs `systemctl --user stop qv4-radiance.service`, then waits until :8060 is down AND rocm-smi shows each
   of the two cards within 2 GB of (total less 26.1 GB), i.e. the model released, up to 150 s. Two `stop` lines go in
   the swap ledger (one per card) with the reason and the measured seconds. Card 0 is then marked reserved with the
   reason "held for the frozen product's OCR server (:8032, hard limit 23)"; card 1 is left cold and unreserved, and
   the planner, which inside the window sees only the page job types, loads page-reader on it (a cold card: no
   rule-5 floor) and the worker runs the pieces. A marker `<live>/scheduler/night-window.json` records the stop.
   If `systemctl stop` returns non-zero or the cards do not release: two `failed` lines, the unit is started again,
   and no new stop is tried for 15 minutes.
3. **Closing.** While the page reader holds card 1 the manager watches for: the window's end; the page queue empty
   (no visible demand on the page job types; a load that failed makes them invisible too, so the window closes
   rather than idles); or a view piece due, read as rule 8 reads it: a `waiting`-class row, or a `due` row within
   `due_horizon_seconds`. A bulk `whenever` text queue does not close the window (assumption; one line in
   `_views_due` if Arthur wants it to). On any of the three the page card is set draining and kept so each tick,
   so a running pieced job gives its row back at the next piece boundary (never killed); when no page job runs here
   the page reader is unloaded (an `unload` line), `systemctl --user reset-failed` then `start` are run, the model
   is read back on :8060 for up to 330 s (the unit's TimeoutStartSec is 300; it answered in 21.6 s on 29 October),
   and both cards are marked standing as today, with two `start` lines carrying the measured seconds. Then 15
   minutes' rest before any new stop, so a page row given back for two minutes is not a new night.
4. **A start that fails** (non-zero return, nothing on the port, or another model) is two `failed` lines, both cards
   reserved with the reason, ONE alarm and ONE note appended under
   `/home/user/querynzv4-work/inbox/cards/<date>-qv4-radiance-did-not-start-after-the-night-window.md` (the unit,
   the failure, the commands to look with on node2; no person named), and the manager tries again each tick, each
   try a `failed` line, until the port answers with qwen4exp, by its own start or by anyone's: then the episode
   ends. Text-reader and review jobs are not claimable meanwhile (no card holds flash-next), as the brief wants.
5. **A worker restarted mid-window** finds the marker at start and starts the unit on its first tick, whatever the
   clock says, before anything is planned. Outside the window nothing changes: the standing cards are reserved to
   the planner, a load of flash-next or a view is still never acted on (the ruling-121 tests stand).
6. **Also:** `_wait_ready` (the ordinary load wait) now runs on the manager's injected clock and sleep (the lesson:
   a mutant that let the page reader take card 0 hung a test for the 900-second real timeout). `held()` no longer
   asks a card whose port is NULL. The swaps table comment lists `stop`, `start`, `died`, `stray`.

Tests (fast, on the fake worker: fake systemctl, fake card memory, fake ports, fake clock; no model, no second
sleeps): the shipped window and the registry's refusals; the clock at 21:59/22:00/05:44/05:45 and in July (NZST);
nothing stopped or planned outside the window; the stop at 22:00 with the measured lines, card 0 reserved, the page
reader on card 1 only (one popen, HIP_VISIBLE_DEVICES=1), the marker; the close at 05:45 with pages still queued
(unload, start, both cards standing, marker gone); the early close on an empty queue and the 15-minute rest; a
running text piece and a leased review row each block the stop; a due text piece closes the window and the page
reader drains first; a bulk text queue does not; the OCR server's card never taken under 500 queued pages; a stop
that fails is ledgered and the unit started again; a failed start alarmed once, noted once, retried, then
recovering; a unit back on its own ends the episode; a worker restart mid-window. Mutants seen failing: window
always open (2 tests), nothing blocks the stop (1), card 0 not held (7), no retry (2).
`QV4_INTEGRATOR=1 bin/fast support/scheduler` green in 48.3 s (175 tests). No slow test added: the window needs a
box with the unit, which the fake stands in for; the first night is the real run.

**What the integrator must do after the merge (node2, /home/user/querynzv4):**

1. Push main, `.venv/bin/python -m support.installer release`, then with the worker idle
   `systemctl --user restart qv4-worker@node2`: the manager reads the window and builds its pieces at start (the
   catalogue reloads on the probe's clock, but not the manager's injectables). The unit file changed only in a
   comment; no `daemon-reload` is owed for the window itself.
2. Queue the page work before 22:00 (`qv4-read-pages-candidates`, `qv4-read-pages`, the disclosures pages, the
   courts scans when courts-2 lands). Nothing happens on a night with no page row.
3. The first night, 22:00 NZDT: if no text-reader or review piece is running or leased, Radiance stops (about 30 s
   to release), card 0 is held, page-reader loads on card 1 (~30 s from a warm cache), and the page pieces run
   until the queue is empty or 05:45, then Radiance is back in ~22 s. The board's chat pane says the model is not
   running meanwhile (ruling 122). The morning's `python -m support.scheduler status` shows the `stop`/`start`
   lines with their seconds. If a text piece is leased all night (a long qv4-reread row), the window never opens and
   one log line says which row.
4. A `failed` start is an alarm and a note in `/home/user/querynzv4-work/inbox/cards/`; file it as a card.

Lesson filed: lessons/a-managers-waits-run-on-an-injected-clock.md.

## Result

Merged 30 October 2026, 13:48, as 44ecfec (integrate branch 941589f; gate green, marked, every slow test since
support/ changed; nothing staged). Two integrator commits on the way: the lesson's first line cut to 233 characters
(it was 278) with the lessons index regenerated, and `docs/status/scheduler.md` trimmed from 3,194 bytes to 2,875
(a first gate at 13:20 was refused on the reading-limits test for it). Released after the push; `python -m
support.scheduler check` prints the window (22:00 to 05:45 Pacific/Auckland, flash-next stopped for page-reader on
card 1); `qv4-worker@node2` restarted with the queue empty at 13:49 so the manager built its pieces on the new code.
Queued for the first night: `qv4-read-pages-candidates` (658 pieces, every candidate return at stage read) and
`qv4-disclosures-read` (27 pieces, every declaration at stage form that needs a reading); party returns and expense
returns have no document waiting. The party-finance statements with no text layer (45 rows) are a different
profile and not a job yet. Working copy `fix-support-scheduler-1` and the local branches retired;
`fix/support-scheduler-1` on the remote is Arthur's to delete.
