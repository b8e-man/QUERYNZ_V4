# scheduler-2b: embed() in the model client (a contract change) and qv4-embed's piece
branch: session/scheduler
session: scheduler (session 2)
raised: 2026-10-18
claims: support/scheduler (embed.py, the `embed-piece` command, jobs.toml: qv4-embed enabled with its piece command, tests); the patch `scheduler-2-embed-contract.patch` beside this file for support/modelclient and docs/contracts/model-client.md (NOT on the branch: outside the fence); cards/the-model-client-has-no-embedding-call.md closed; lessons/an-embeddings-answer-echoes-the-model-you-asked-for.md

Why the contract changes: the model-client contract says every model call
goes through the client, and the client had `chat` only, so the embedding
profile (step 2.15) could be loaded but never used. `embed(url, lane=,
model=, texts=)` keeps the three rules (names its model, local addresses
only, a wrong model refused and discarded) and reads the served model back
from `/v1/models`, because llama-server fills an embeddings answer's
`model` field with the request's own word (`server-common.cpp`,
`json_value(request, "model", model_name)`); a chat answer carries the
server's name. The first draft checked the answer and ACCEPTED a wrong
name in the live proof; the patch's test fakes that server.

Proven live on node2 18 October through the patched copy in the session's
scratch folder: the embedding profile loaded on card 1 by the queue, three
texts embedded to 1,024 dimensions, the ledger holding counts and no text,
and a call naming a model not loaded refused (`WrongModel`). The patched
client's tests: 21 passed.

Integrator's steps:
1. `git apply /home/user/querynzv4-work/inbox/merge-requests/scheduler-2-embed-contract.patch`
   on the integration branch (3 files: the client, its tests, the contract).
2. Gate; merge.
3. Then `qv4-embed`'s first run can be queued with a document hash as a
   piece: `python -m support.scheduler enqueue qv4-embed --pieces <sha256>`.
   It stores one reading per page in the reader store (profile `embedding`,
   vectors as rows) and replays a stored one.

## Result (integrator: founding-f05585e, 18 October 21:1x)

MERGED into main as 5e45437 (one gate run for 2a, 2b and 2c on an integration
branch; the generated files rebuilt there; one queue item put into the
queue's shape). The contract patch for support/modelclient and
docs/contracts/model-client.md was applied line by line and verified equal
to the patch. The three edits outside the fence are done: `scheduler` in
support.db's schema list and in the owner map of tests/test_imports_one_way.py;
the checks board has a `scheduler` check reading <live>/checks/scheduler.json
(report fresh, workers up, reserved card clean, failed runs in 26 h). The
timer files in checks/jobs/ and support/offsite/jobs/ are left (the
installer supersedes them). Post-merge: the installer re-placed the shipped
worker unit and the worker restarted from the main checkout at 21:05.
