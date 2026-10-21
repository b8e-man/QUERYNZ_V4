# products/scan — the register scan shape

Step 6.1. A scan asks one question of every row of a register or a join of
registers ("which suppliers share a director with a donor?") and lists the
answers with their dates, their numbered citations and their grade
(confirmed, near, contested), under the two trust settings and their
defaults (`settings.toml`). It re-runs when a register it read has loaded
since (`run --stale`). Nothing from step 6 goes on the public site; the
surface listens on the local network, port 8450.

A scan is a folder under `templates/<name>/` holding `template.toml`: the
question, the views read with their licences, the join as a chain of
steps (by row, by person through the links, or by a named link rule), the
columns carried, the known limits. `spec.md` is the five-line spec;
`python -m products.scan` lists the commands. Built by `scan-1`; the four
use-case templates of 6.2 are later sessions.
