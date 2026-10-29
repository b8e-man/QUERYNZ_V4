# The reading limits and time targets of ruling 54
default: As drafted, then re-set from the first week of session timings
blocks: Nothing
recommendation: Keep every module at 60 s. Set the whole-repository fast tier to 700 s, or rule that only the gate runs it. Hansard and disclosures cut their samples to fit 60 s.
raised: 2026-10-18 by founding-1 (copied from the plan, "Decisions waiting on Arthur")

## Measured, week of 22 to 29 October (integrator, 29 October)

From `querynzv4-work/times/fast-tier.jsonl`, 229 runs. A module's fast
tier (target 60 s) held: 212 runs, 20 over, median 43 s. Over by scope:
hansard 4 of 4 (median 136 s), disclosures 4 of 4 (80 s), board 5 of 62
(max 79 s), grants 2 of 11, links 2 of 10, companies 1 of 1 (84 s),
courts 1 of 1 (75 s), mcpsource 1 of 4 (61 s). The whole-repository fast
tier (target 300 s) missed 46 of 46: median 622 s, max 784 s, and it is
run only by gates and nightly jobs, never by a session. So the 60 s
figure is right and the 300 s figure never was; the two scopes over every
time are a sample-size matter for their lanes, not a target matter.
