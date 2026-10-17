# The session's permission mode refuses every write into the live old folder, so the 1.5 freeze commits need your hand or a permission rule
default: none
blocks: Step 1.5 (both freeze commits and the tag); the `newsscrapers` and `newsscrapers-daily` timers, held stopped until the NZME commit lands; 1.4's second commit of the manifest
recommendation: Apply the rehearsed patch yourself (two commands below, on node2), or add a permission rule that lets a founding session edit the four freeze paths; the patch is the quicker
raised: 2026-10-18 by founding-2 (step 1.5, first commit)

The plan authorises two small commits to the old repository (1.5) and the
hooks allow a founding session to write exactly those paths. But Claude
Code's auto-mode classifier, which sits above the hooks, refused both the
shell copy and the file-editing tool with "Modify Shared Resources", for
`ingestion/newsscrapers/registry.py` and `ingestion/SOURCES.md` in the live
old folder. I did not try to get around it. Stopping old jobs
(`systemctl --user stop`) was allowed, so 1.4 went ahead.

The NZME change was rehearsed in the reference copy and passes the old
status generator's check; the sweep lists both hosts as SKIP, "ruled out by
name (ruling 12)". It is saved outside git as
`/home/user/querynzv4-work/live/nzme-freeze-commit.patch` (registry.py:
`blocked:ruling` for nzherald.co.nz and businessdesk.co.nz, handled in
`runnable()`; SOURCES.md: its generated section). To apply it, on node2 in
the live old folder:

    cd "/home/user/Git Repos/QueryNZ_V3"
    git apply /home/user/querynzv4-work/live/nzme-freeze-commit.patch
    git add ingestion/newsscrapers/registry.py ingestion/SOURCES.md
    git commit -m "ruling 12: NZME out of news capture (blocked:ruling for nzherald.co.nz and businessdesk.co.nz); QueryNZV4 plan step 1.5, first commit"
    git push origin main

The push runs the old pre-push gate; if it asks for a regenerated file or a
ledger line, regenerate it and amend. Then start the two held timers:

    systemctl --user start newsscrapers.timer newsscrapers-daily.timer

Until then nothing fetches NZ Herald: the backfill job is stopped and
disabled and the two news timers are stopped (still enabled, so a reboot
would bring them back; that is the one hole). One old test,
`ingestion/tests/test_nzme_capture.py::test_registry_wires_nzme_ready`,
asserts the old state and will fail once the patch lands; it is not in the
pre-push gate and the old suite is frozen, so I left it.

If you would rather the session did it: a permission rule in
`.claude/settings.json` allowing `Edit` and `Bash(cp *)` on the live old
folder would let the next founding session make both commits itself, with
the hooks still limiting it to the freeze paths.
