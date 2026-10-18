# scheduler-2c: the model server built from source, beside the copy (step 2.11, hard limit 23)
branch: session/scheduler
session: scheduler (session 2)
raised: 2026-10-18
claims: support/installer (`build`: clone of /home/user/llama.cpp read-only into <live>/llama/src, cmake for the probed architecture, llama-server into <live>/llama/built/bin with VERSION.json; runpath and self-contained in every record; spec, README); support/scheduler (profiles.toml `[server] binary`, the probe's `qv4-llama-server-built`, cards.server_binary by the setting, the swap ledger naming the server)

What it claims: the estate has its own build of the model server, made
from source on the box, beside the copy of the old build and never over
the program the frozen product's two servers use. Built 18 October: 10276
(6ea215d17), gfx1201 from rocminfo, the old build's flags minus examples
and tests, `$ORIGIN` baked in so the folder is whole on its own (the copy
in `<live>/llama/bin` loads the old build tree's libraries; the card
manager's LD_LIBRARY_PATH covers that, the built one needs no help). Which
one the cards run is one line in `profiles.toml`, now "built"; a missing
one falls back to the other.

Proven live on node2 18 October through the queue: the embedding profile
(2 s) and the text-reader profile (4 s) loaded on card 1 by the built
server, each model read back from the card, the rehearsal calls answered,
every swap in the ledger with `server <path>`.

Nothing to do after the merge; the build is on the box. On a second box
`python -m support.installer build` makes its own.

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
