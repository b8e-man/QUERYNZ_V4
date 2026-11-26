# Review the new estate against the old one for critical components it does not have
kind: finding
state: open
use-case: machinery
session: integrator
opened: 2026-11-26

Arthur, 26 November 2026: "review our codebase against v3 to see if we are missing any other critical components".
The lessons flow is one such component found missing in practice: the old estate enforced it (ops/four_questions.py,
ops/lessons_check.py, ops/card_balance.py) and the new one keeps only the rule (card
`the-lessons-flow-is-not-enforced-so-it-stopped`). The question is what else of that kind the move left behind.

Read the reference copy (/home/user/qnz3-ref, never the live old folder) by component, not by file: ops/, checks,
the harness and its arms, the reviewer and its audit, backups and restore drills, alarms and watchers, the fetch
gate and its politeness rules, the release and its freeze, the corrections and quarantine ledgers, the board, and
anything a ruling made mandatory. For each, find what in the new estate does the same job (docs/plan/map.md names
where things are), or record it as missing. Weigh only what holds a hard limit, a ruling, data that cannot be
regenerated, or the estate's running (a job, a check, a guard); a convenience the new design dropped on purpose is
listed with the decision or ruling that dropped it, not as missing.

Deliver: one table (old component, what it held, its new counterpart or "missing", how critical, the ruling or
lesson behind it), a card for each critical gap, and nothing built in this card. Reading only: code and docs, no
old database, no data.
