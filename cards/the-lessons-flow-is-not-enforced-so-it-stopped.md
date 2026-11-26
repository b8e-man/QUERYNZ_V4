# The lessons flow is not enforced, so it stopped: no lesson filed 10 to 26 November and no search before the 26 November scheduler change
kind: finding
state: open
use-case: machinery (core.md, Lessons; ruling 359)
session: integrator
opened: 2026-11-26
module: bin, .claude hooks, docs/plan/core.md

Arthur, 26 November 2026: "are you still recording lessons?" No. The last lesson in `lessons/` was filed on 10
November; the integrator's work of 11 to 26 November (the news reader, the reader store's power-cut fixes, the 27B
trial and the scheduled model swap) filed none, and the scheduler and unit change of 26 November was made without
the search core.md requires before building ("search the lessons for the area you are about to touch"). The search,
run afterwards, found a lesson the session had re-learned by hand that day (Radiance echoes the model a request
names). Four lessons were then filed.

This is the failure ruling 359 named in the old estate (6 October 2026): the rule existed and was not happening,
because nothing held it. The old estate held it with `ops/four_questions.py`, `ops/lessons_check.py` and
`ops/card_balance.py` (reference copy /home/user/qnz3-ref/ops/); the new estate kept the rule in core.md and
`bin/lessons` for the search, and nothing that fails when the rule is skipped.

What closes it (Arthur: "fix this so you maintain the doctrine we established earlier"): a mechanical hold on both
halves, cheap enough that it is not routed around:
- at planning: the search is run before a change and its result is in the record (the commit or merge request
  names the lessons searched for and the few it returned, or the hook asks for it on the first edit of a session);
- at close: a commit or merge request that changes code carries a new file in `lessons/` or the line
  "lessons: nothing new" with its reason; the merge gate and a commit-msg check refuse one with neither;
- a light on the board for days since the last lesson filed by an active session, so a silence like 10 to 26
  November is seen within days, not when Arthur asks.
Measured done: a commit without either line is refused in a test; the 26 November commits pass; the light reads the
gap of 10 to 26 November as red on a replay.
