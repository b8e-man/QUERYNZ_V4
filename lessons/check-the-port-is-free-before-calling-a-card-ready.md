Before a swap starts a model server, ask the card's port: a stray server from an earlier worker answers there, the new one fails to bind, and a readiness check that only reads back the model name calls the stray ready.
area: scheduler, model serving, swaps

Seen 18 October 2026: after a worker restart a stray text-reader answered on :8111; the next six swaps were ledgered as loads of 0 seconds and the embedding and page-reader loads "failed: the card answered with qwen". The fix is two-fold: a busy port is a refused load with the stray's model in the ledger, and a stopping worker unloads every server it started so nothing is left behind.
