A hook is live the moment .claude/settings.json is saved, so write the scope file before the settings file, and never make the hook's fix path depend on a write the hook refuses.
area: fences, hooks, founding
paid-for-by: 2026-10-18, founding session 1, step 1.1

The plan assumed hooks load when a session starts ("This first session has
no fences yet"). Claude Code 2.1 loads them on save. The founding session
saved the settings file with no `.scope` in the main checkout and was refused
every write from then on, including the launcher that would have written
`.scope`. Arthur had to create the scope file by hand in a terminal.

The old estate paid for the same lesson on 2026-09-15 (`6-working-style.md`:
"A hook is live the moment its file is saved, and a tripwire's honesty is its
list"). It was read before building and still bit, because the trap was in
the ORDER of two saves, not in the hook's text.

How to apply: a session that edits a hook or the settings file writes (or
checks) its own scope file first; a hook that refuses everything must leave
one write open that is enough to repair the state it refuses on.
