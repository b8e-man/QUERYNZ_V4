# The permission classifier refuses every write into the live old folder, so 1.5 waits on Arthur's hand
kind: blocker
state: open
use-case: -
session: founding-2
opened: 2026-10-18

Claude Code's auto-mode classifier sits above the hooks and refuses a copy
or an edit into `/home/user/Git Repos/QueryNZ_V3`, though the hooks allow
a founding session the four freeze paths and the plan authorises the two
freeze commits. Tried 18 October at 01:xx (cp, Edit) and again at 02:4x on
Arthur's ask (a built file copied in by name). Job stops were allowed, so
1.4 batch 1 went ahead.

What waits: 1.5 both commits and the tag; 1.4's manifest commit; the
`newsscrapers` and `newsscrapers-daily` timers, stopped but still enabled,
so a reboot would bring them back and fetch the NZ Herald until the commit
lands. One old test, `ingestion/tests/test_nzme_capture.py::test_registry_wires_nzme_ready`,
asserts the old state and fails once the patch is in; it is not in the
pre-push gate.

The patch is at `/home/user/querynzv4-work/live/nzme-freeze-commit.patch`
and applies cleanly. Closes when Arthur runs the commands in
`docs/decisions/queue/the-session-cannot-write-the-old-folder.md` on node2,
or adds a permission rule for the live folder's freeze paths and a founding
session commits.

18 October 02:5x: Arthur made the first commit by hand (7f9f0bb5). The push
to the mirror waits for node1; the old pre-push gate runs then. Still open
for the second commit and the tag.
