# Insolvency capture held after four nights of transport errors
kind: finding
state: open
use-case: 6 insurance, 7 construction and phoenix; step 5.3
session: integrator
opened: 2026-11-25

`qv4-insolvency-capture` stopped on a transport error four nights running:
- 21 and 22 November: DNS failure;
- 23 November: SSL EOF;
- 24 November: a dropped connection.

Each run stopped politely (it stops at a failed read) and exited 1, so its `then` load did not run. The ledger grew to 14,022 estates while the published views stayed at 19 November's build. A load queued by hand on 25 November (row 6183) published 13,991 read plus 7 unanswered.

Arthur, 25 November 2026: "hold and card". The capture is switched off in support/scheduler/jobs.toml (`enabled = false`). `qv4-insolvency-removals` still runs.

Two questions for Arthur:

1. Should a capture that stopped politely still queue its load, so what it did land is published? Today a stop is a failed run and nothing downstream runs.
2. Do four nights of transport errors from `api.business.govt.nz` count as throttling under ruling 141 (a refused host stops gathering)? That host also serves the NZBN API, so a gate hold on it would stop the companies lanes too. The hold here is on the job, not the host.

To resume: answer both questions, set `enabled` back (or remove the line), release, and enqueue `qv4-insolvency-capture`.
Blocks: nothing else; the insolvency views stay at 25 November's load until then.
