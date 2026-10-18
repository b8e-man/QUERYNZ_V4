# The permission classifier refuses every write into the live old folder, so 1.5 waits on Arthur's hand
kind: blocker
state: closed
use-case: -
session: founding-2
opened: 2026-10-18
closed: 2026-10-18

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
to the mirror waits for node1. Arthur ran the old gate by hand and started
the two news timers at 09:06; the first daily run skipped NZME by ruling.
Still open for the second commit and the tag.

18 October 18:0x: Arthur made the second commit by hand (8c5d1637: 27 units
marked disabled in the manifest, FLEET.md and SOURCES.md regenerated, from
`manifest-freeze-commit.patch`, rehearsed in a scratch copy because the
classifier refuses the reference copy too) and tagged it
`v3-frozen-2026-10-18`. The live old folder has no remote but node1's mirror
(ruling 55: not confirmed). The reference copy is at the tag. Closed: both
freeze commits and the tag are in; the old repository takes no commit from
here without Arthur's word (hard limit 19).
