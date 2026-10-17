# The fence went live on save and refused its own founding session
kind: blocker
state: closed
use-case: -
session: founding-1
opened: 2026-10-18
closed: 2026-10-18

Saving `.claude/settings.json` registered both hooks at once; with no
`.scope` in the main checkout the scope hook refused every write, including
the launcher that writes `.scope`. Closed by Arthur creating the scope file
by hand (the exact text `bin/start-session --main founding` now writes).
Lesson: `lessons/fence-live-on-save.md`.
