# flash-next-1: ruling 121, Flash-Next on Radiance replaces Qwen3.6 on node2
branch: session/flash-next-1 (pushed; three tranche commits, the record and the lessons index on a5776b0)
session: flash-next-1 (Opus, build, scope support/scheduler/ and support/installer/)
raised: 2026-10-29
claims: support/scheduler/ (units/qv4-radiance.service, bench.py, tests/test_radiance_unit.py, test_flash_next.py and
test_bench.py new; registry.py, probe.py, cards.py, worker.py, __main__.py, profiles.toml, jobs.toml, spec.md,
tests/test_registry.py); support/installer/ (__init__.py, spec.md, tests/test_standing.py new, tests/test_installer.py);
lessons/radiance-echoes-the-model-a-chat-call-asks-for.md and lessons/a-card-headroom-for-a-resident-server-is-counted-twice.md;
docs/status/flash-next.md.
publish: nothing. tables: none new (`scheduler.cards` and `swaps` take new values, no new columns).
**units: qv4-radiance.service new**, placed and enabled live from this working copy at 20:18 (the rehearsal text).
**Outside the fence, for the integrator: the model client's read-back patch, below. Apply it in this merge.**

## What it does

1. **`qv4-radiance`** runs Radiance under podman with the recorded shape:
   - the model read-only, `--tp 2`, 16 slots, a 16,384-token bound, 4,096 batched tokens;
   - adaptive drafts, tip-only checkpoints, the n-gram table read from disk;
   - `--gpu-headroom-mib 2560`, so the frozen OCR server keeps its room (hard limit 23);
   - `/dev/kfd` and the render nodes passed one by one, memlock unlimited;
   - published on 127.0.0.1:8060 only, served as `qwen4exp`, `WantedBy=default.target`, `StartLimitBurst=3`.

   **One figure differs from the brief: `--host-pool-mib 11264`, not 10240.** Started after the OCR server, the 10 GiB
   pool stopped at start with "out of memory". Radiance counts the OCR server's ~2.2 GiB a card as already held and still
   keeps the 2.5 GiB headroom, which left the experts 0.44 GiB short. The hand container only fit because it started
   before the OCR server came back. With 11 GiB it starts in either order, for about 2 GB more host memory.
2. **The installer enables standing services**: any `qv4-` service with an `[Install]` section, not a template, `enable --now`.
   The ones already enabled (board, report, scan, site preview) are unchanged by it.
3. **Profiles.**
   - `flash-next` is a standing server: binary `radiance`, unit, port 8060, `cards = 2`.
   - Measured at 20:18: 26.1 GiB a card (rocm-smi: 56.06 GB for radiance over the two cards), host RSS 28.4 GiB, load 21.6 s.
   - `text-reader` and `review` are views (`on = "flash-next"`) with a per-request `request`: the reader's thinking off; review's
     on with `thinking_token_budget = 2048`. Proven live: the reader's answer has 0 reasoning tokens, review's 176, then the answer.
   - The qwen3.6 profiles are gone, and so is the `node2:0` reservation for the frozen chat model.
   - The registry checks views and standing servers. A test holds the unit and the profile equal (served name, slots, bound, port).
4. **The card manager reads the standing server's model back every tick.**
   - On the right model, both cards are `flash-next` on :8060. Otherwise they are reserved, with the reason.
   - It records a `load` swap per card when it first sees the server answer. That load is measured from the unit's start when
     it saw the server down, and a `died` line is written when the server stops.
   - The planner sees those cards as reserved. A planned load of a standing profile or a view is never acted on.
   - The worker resolves a view to its server's cards and hands the job `QV4_MODEL_REQUEST`.
5. **`rehearse bench`** (job `qv4-rehearsal-bench`, priority 89, on demand) sends N synthetic page-sized prompts at once
   through `support.modelclient`. Each prompt is unique from its first line and checked against the server's own token count.
   It reads no document (ruling 79).

## Measured through the worker's own path

A `Worker` from the scratch copy (this branch plus the patch) with its card manager, on a scratch schema of
`querynz_v4_sample`: it registered both cards, marked them flash-next, recorded swaps 1 and 2, then claimed and ran the
queued bench row under the runner's limits.

| Streams × prompt | Wall time | Request median / max | Prompt tokens a second, pooled |
| --- | --- | --- | --- |
| 8 × 4,000 | 5.7 s | 4.5 s / 5.7 s | 5,614 |
| 16 × 4,000 | 10.4 s | 7.0 s / 10.4 s | 6,131 |

The pooled figure is below the experiment's ~8,000 at 8 streams. Possible reasons: a whole request timed here, not time to
first token, and the larger pool. Not chased. The script is `/home/user/querynzv4-work/scratch/flash-next-1/worker_bench.py`.
It left the scratch schema `scratch_flash_next_bench_*` in the sample database (regenerable; no drop is run from a session).

## The model client patch (support/modelclient, outside this fence)

`/home/user/querynzv4-work/scratch/flash-next-1/modelclient-readback.patch` (89 lines: `__init__.py` and two tests).
Radiance answers a chat call for **any** name and echoes it. Measured: a call for "qwen3.6-35b-a3b-q4km" came back 200
under that name. So `chat()`'s check on the answer passes whatever it asks. The patch reads `/v1/models` before
sending (not when a test passes `post` without `get`), refuses with nothing sent, and accepts Radiance's answer shape.

Proven:
- In a scratch copy, the modelclient, board, links, docread, trials and scheduler fast tests pass. The one failure is
  `test_reload`, because the copy is not a git checkout.
- Live on :8060: the old name was refused before sending, `qwen4exp` was accepted.
- Until this lands, the worker's path is still safe, because the card manager reads the model back. The board's chat pane
  and every other caller are not.

## Tests: fail on main, pass on the branch

- **Tranche 1**: `test_radiance_unit.py` (7) and `test_standing.py` (3). All 10 seen failing before the unit and the
  installer change existed.
- **Tranche 2**: `test_flash_next.py` (15). All 15 seen failing on main's code and files (10 failed, 5 errored at the fixture).
- **Tranche 3**: `test_bench.py` (6). `bench.py` is new and the two command-line tests failed before the command existed.
  The size check was added after the first live run measured 7,400 tokens for 4,000 asked (the characters-a-token guess
  was wrong). That run's figure is not in the table above.
- The scheduler and installer suites, including the slow tests, pass. Whole-repository fast tier: the final run
  (714 s, over its 300 s target, recorded) failed on one test alone, `tests/test_generators.py`, because the lessons index
  was stale for the two new lessons. The index is regenerated and committed, and that test now passes.

## After the merge (node2, /home/user/querynzv4)

1. Apply the patch, gate, push, release.
2. Install units. The shipped `qv4-radiance` differs from the placed one only by the rehearsal comment, so it needs a
   daemon-reload and no restart.
3. Restart `qv4-worker@node2` while it is idle. It will write a standing `load` row for cards 0 and 1 (rows 514 and 515
   were the hand ones).

## Not done, for later

- `links/review.py` should merge `QV4_MODEL_REQUEST` into its call. Until then the review lane gets the server's default,
  thinking off. This is a fix for links/.
- `scheduler.cards` holds a stale row for node2 card 2 (the probe sees two cards). The planner can still see it as free;
  a load there of a standing profile is refused, but a llama profile would be tried and fail.
- `querynz-agent-llm` stays stopped and is Arthur's to disable. Nothing of the frozen product was touched.
- No reading is queued (ruling 79).

Lessons: the two named above. Cards: none raised.


## Result

MERGED 30 October 2026 08:16 NZDT (838e048; `integrate/flash-next-1` off main with the session's model-client read-back patch applied
by literal edits, since `patch` and `git apply` are refused by the scope hook). The first gate run was refused on the scan product's live
test: the gate carried no integrator mark and support.db's live guard refuses the owner login to an unmarked session; the second run,
`QV4_INTEGRATOR=1 bin/merge-gate`, was green (~27 min). Units installed and the worker restarted at the release (below). No tables.
