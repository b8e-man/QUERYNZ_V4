# flash-next: where ruling 121's build stands

Session `flash-next-1`, branch `session/flash-next-1`, scope
`support/scheduler/` and `support/installer/`. 29 October 2026, 20:45, node2.
Merge request `flash-next-1`.

## Done

- `qv4-radiance` (support/scheduler/units/): Radiance, Flash-Next, both
  cards, 127.0.0.1:8060, served as `qwen4exp`; placed and enabled through
  `support.installer` (from this working copy: a REHEARSAL line in the
  unit until the merge's install). The hand container `radiance-fn` is
  gone; the unit runs since 20:18. The pinned pool is 11 GiB a rank,
  not 10: at 10 it ran out of card memory when it started after the OCR
  server.
- Profile `flash-next`, measured: 26.1 GiB a card (rocm-smi), host
  28.4 GiB, load 21.6 s. `text-reader` and `review` are views on it
  (thinking off; on with a 2,048-token budget, proven live). Qwen3.6
  profiles gone; the card-0 reservation gone.
- Card manager: marks the standing server's cards, records its load in
  the ledger, never plans or loads it. Proven against a scratch schema.
- Bench through the worker's path: 8 x 4,000 tokens in 5.7 s (5,614
  prompt tokens/s), 16 in 10.4 s (6,131).

## Waits on the integrator

- Apply the model client's read-back patch (outside this fence), at
  `/home/user/querynzv4-work/scratch/flash-next-1/modelclient-readback.patch`.
  Without it, a chat call naming the wrong model passes against Radiance.
- At the merge: install units (the shipped `qv4-radiance` differs from
  the placed one by the rehearsal comment alone: no restart of it),
  release, then restart `qv4-worker@node2` while it is idle.

## Not done

- links/review.py does not pass QV4_MODEL_REQUEST yet, so review thinks
  only when that lane asks for it itself (outside the fence).
- The stale `scheduler.cards` row node2:2 is still in the table.
- No reading is queued (ruling 79).
