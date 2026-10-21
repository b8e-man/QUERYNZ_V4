# Leaked places outside the repository wait on Arthur to clean
kind: finding
state: open
use-case: track H
session: security
opened: 2026-10-22

H.2 says "clean out what can be cleaned". Every place the leak search
found (`docs/security/leaks.md`) is outside the repository: the saved
session transcripts under `~/.claude/projects` and the shell history
`~/.bash_history`. The journals and the Claude settings files hold
nothing. A build session may write outside the repository only under its
own scratch folder, so none of it can be cleaned from here. The old
repository's history holds examples and fixtures only; nothing there is
rewritten.

What is owed, on node2, at Arthur's keyboard (none of it is a secret):

1. The old project's transcript
   `~/.claude/projects/-home-user-Git-Repos-QueryNZ-V3/d51f6658-8166-462e-8432-e293705be9b9.jsonl`
   (6.7 GB) carries the deploy token in use today, both earlier tokens,
   the application role's password, the first alarm topic and the NZBN key
   as it arrived. Rotation makes every one of them dead; the file is then
   a record and can stay or go. Deleting it loses that session's history.
   Four smaller transcripts quote the application role's password (the
   places are in `leaks.md`); this session's own transcript echoed it
   twice in a context window.
2. `~/.bash_history`: lines 475, 479, 496 (the replication password of
   24 August, since rotated), 505, 507, 509 (the application role's
   current connection strings) and 621 to 623 (the serving role's three
   connection strings): delete the lines with an editor, then `history -c`
   in any open shell so it is not rewritten.

Owner: Arthur, after each rotation makes the value dead, which is the
order that matters: a cleaned transcript with a live token helps nobody.
