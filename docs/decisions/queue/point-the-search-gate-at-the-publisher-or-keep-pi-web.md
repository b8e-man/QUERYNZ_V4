# Point the release's search gate at the publisher, or keep querynz-pi-web running
default: Keep `querynz-pi-web` running, in the carve-out; no change to the old repository
blocks: Nothing. The carve-out carries one more unit, the product's own instance on port 8300, the same program as the publisher on 8301
recommendation: The default. `ops/pi_search_gate.py` takes `--base`, defaulting to `http://127.0.0.1:8300`, and the release runs it without one. A one-line change to 8301 would let the unit stop, but that is a third commit to the old repository, which the plan does not authorise (1.5 names two), and the gate's author chose the customer-facing instance on purpose. Revisit when the frozen product is retired, or fold it into the second freeze commit only on Arthur's word
raised: 2026-10-18 by founding-f05585e (the 12:36 release by hand, red on `pi_search_gate`; card "The release's search gate reads the product on 8300")
