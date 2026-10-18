# The model client has no embedding call, so the embedding profile is proven by read-back only
kind: finding
state: open
use-case: search
session: scheduler
opened: 2026-10-18

`support.modelclient` offers `chat` only. The embedding profile (bge-m3,
step 2.15) loads and advertises `bge-m3-q8` (read back from the card, 8
slots), but no embedding was made through the client because the contract
says every model call goes through it. Add `embed(url, lane, model, texts)`
to the client (a contract change: the integrator, on a merge request that
says why), then give `qv4-embed` a real piece command.
