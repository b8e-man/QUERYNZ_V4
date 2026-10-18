# The model client has no embedding call, so the embedding profile is proven by read-back only
kind: finding
state: closed
use-case: search
session: scheduler
opened: 2026-10-18
closed: 2026-10-18

`support.modelclient` offers `chat` only. The embedding profile (bge-m3,
step 2.15) loads and advertises `bge-m3-q8` (read back from the card, 8
slots), but no embedding was made through the client because the contract
says every model call goes through it. Add `embed(url, lane, model, texts)`
to the client (a contract change: the integrator, on a merge request that
says why), then give `qv4-embed` a real piece command.

Closed 18 October 2026 by scheduler (session 2): `embed()` is written and
tested as a patch to the contract (merge request scheduler-2b carries it;
the integrator applies it, a contract change), proven live against the
embedding profile on card 1 (3 texts, 1,024 dims, served model read back).
The first draft checked the answer's `model` field and accepted a wrong
name: an embeddings answer echoes the request (lesson filed); the patch
reads the served model from `/v1/models`. `qv4-embed` has its piece command
(`embed-piece`: one reading per page in the reader store, vectors as rows,
replayed when stored) and is enabled; its first queued run waits on the
patch landing.
