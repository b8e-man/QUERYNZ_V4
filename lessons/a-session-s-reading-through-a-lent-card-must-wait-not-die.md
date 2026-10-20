A session that reads through a model profile the scheduler placed must expect the planner to lend the card away mid-run: make the run resumable and have it wait and retry for the profile's return, because the two-slot scoring died twice on a connection error when read-pages took the card.
area: links, the review agent, the scheduler, model profiles, sessions
paid-for-by: 2026-10-20, review session, track C

The review profile was brought onto a card by queuing `qv4-rehearsal-review`
(the designed route: a recorded swap). Twenty minutes in, a read-pages job
queued, the planner swapped the card to the page reader (rule 1, yield on
empty: the rehearsal job had finished), and both scoring processes died on
the refused connection with 84 pairs unread. The fix is in the agent: a
reading already recorded is never redone (`run_id` plus `pair_id`), and a
model that has gone away is retried every minute for up to ninety before
the error is raised. Inside the scheduler's own job the worker holds the
profile for the run; a session calling the card from outside has no such
hold, so it is the session's code that waits.
