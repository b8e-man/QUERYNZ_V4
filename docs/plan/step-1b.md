## Step 1b: the quick-work tools

**Goal.** The tools that keep the estate quick to work on (ruling 54): light sessions, a fast tier of checks on a small sample, and a timer on every prompt.

**When.** Inside step 1, after 1.10 and before 1.11, by a founding session using the step 1 brief. The thin slice of 1.11 is the first real use of these tools. **Model.** Fable.

### Do

**1b.1 The weight in the fence.** The launcher writes the session's name and weight into the scope file. For the weight "question", the scope hook refuses every edit inside the repository, the always-allowed paths included, and the safety hook refuses any command that commits, pushes, merges, runs the installer, controls a job, or names a credential file other than `~/.querynz/v4-read.env`. Outside the repository a question session may write only its scratch folder and `inbox/cards/`; a fix or build session, its scratch folder and `inbox/merge-requests/`. For every weight but founding and integrator, the scope hook refuses `.claude/`, `bin/`, `docs/plan/`, the orientation file and any scope file. The hooks are a fence. The wall is the session reader, which cannot write whatever a session does.

**1b.2 `bin/ask`.** It makes a throwaway working copy of the main line at `/home/user/querynzv4-work/ask-<time>`, with a question scope file and a scratch folder beside it, removes copies more than a day old that no session is using, and prints the folder to start in and the rules for a question session. There is no brief.

**1b.3 `bin/fix <module folder>`.** It accepts only a module folder: `keys/`, `links/`, or one folder under `support/`, `registers/`, `products/` or `checks/`. It refuses a folder held by a build session, meaning one named in the scope file of a working copy that `bin/start-session` made and the integrator has not yet removed. It reopens an existing copy whose request was refused. It makes the working copy `fix-<module>-<n>`, a branch, a scope file and a scratch schema. The integrator removes a working copy, fix or build, once its last request is merged.

**1b.4 `bin/q`.** One command for looking at data in the two new databases: the session reader, 30 seconds, 200 rows. `--long` allows ten minutes, takes a lock so that only one runs at a time, writes the full result to the scratch folder and shows the first 200 rows. `--old`, for fix and build sessions only, reads the old databases through the old-estate reader under the same limits. A question session has no route to the old databases, because they hold home addresses.

**1b.5 The inbox.** `/home/user/querynzv4-work/inbox/`, outside git. It holds `merge-requests/`, which the launchers link into every working copy, and `cards/` for notes from question sessions. The integrator commits a copy of each finished request under `docs/merges/`.

**1b.6 The sample.** Each module keeps `sample.list` in its own folder: document hashes and source keys, never bytes or rows. One command gathers the lists and fills a named scratch schema in `querynz_v4_sample`, through the code of the branch it is run from. Tables that hold a person's home address go in a schema whose name ends `_private`, there as everywhere. The first list is the thin slice's, in 1.11. The integrator's own fill, from the main line, is what other sessions read as published tables.

**1b.7 The two tiers.** Two commands. The fast tier takes a module or the whole repository, fills the session's sample, replays stored readings, fails on an unmarked slow test, and records its own time. The merge gate of 1.1 becomes the full tier at a merge. It loads only the modules the branch touches into a staging schema of the real database, and on a pass moves those tables into place, so nothing is loaded twice. A load expected to take more than ten minutes runs as a scheduler job that writes its result into the request, and before 7 November it stays inside the bulk-loading limit under "Shared things on the boxes". The nightly run goes on the checks board of 1.6.

**1b.8 The reading-limit check,** in the fast tier: each file against its limit in the index, each status file against 3 KB, and the orientation file's limits against `docs/plan/limits.md`.

**1b.9 The timer.** Two hooks, on the events Claude Code raises when a prompt is submitted and when the session stops. Each adds one line to `/home/user/querynzv4-work/times/session-times.jsonl`: the session's name and weight from the scope file, the event, and the time. Never the prompt. A checks-board job reports the typical and the worst wait for each weight over seven days, and trims the file to 30 days.

**1b.10 The lessons search.** One command, over the first line of every file in `lessons/` in the main checkout and the old estate's one-line index brought across in 1.7. It returns at most eight rules, one line each, with the file to open. Test it on the eight real pairs the old tool was measured on; the old tool found five.

**Then stop.** Hooks load only when a session starts, and a session cannot start another. Arthur starts one question session with `bin/ask` and asks it anything. The next founding session does 1.11 and then works through the list below.

### Done when

- [ ] The question session Arthur started gave its answer, and its two lines are in the times file.
- [ ] The hooks, run against a question scope file, refuse an edit, a commit and the owner's credential file, and allow a note in `inbox/cards/`.
- [ ] `bin/fix` refuses `.claude/hooks`, and refuses a folder a build session holds.
- [ ] Two fills of the sample from different branches, run at the same time, do not disturb each other.
- [ ] A test not marked slow that sleeps for six seconds fails the fast tier.
- [ ] The reading-limit check fails on a file made one byte too long.
- [ ] The thin slice's tests pass in the fast tier, and the checks board shows the first timings.
- [ ] The lessons search returns at most eight rules, and its recall on the eight pairs is recorded.

