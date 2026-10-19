owns: schema `expenses` (MPs' and ministers' published expenses, every quarterly release, one row per member or minister and category, by document hash) and `expenses_private` (nothing published lives there)
reads: the released files the old estate already holds under `var/staging/mp-expenses/` and `minister-expenses/`, taken by hash, read-only; fetches nothing until the public site is switched (step 4.1, copied from published files)
publishes: `pub.mp_expenses` and `pub.minister_expenses` (who, the period, the category, the figure as printed, citation)
outside check: a release's own printed total for a period against the sum of its rows
jobs: a `qv4-expenses-load` job on the scheduler once the lane reads; no capture job before the switch
