# The Gazette lane leaves the other insolvency, bankruptcy and appointment notices unread
kind: finding
state: open
use-case: 1
session: gazette
opened: 2026-10-20

Read so far: celebrant lists, director prohibitions, liquidator
appointments (`al`). Typed by the Gazette's own section code and not read,
in notices on the 20 October export: winding-up applications (`aw`)
30,452; liquidation and removal (`ds`) 29,783; receivership (`ar`) 5,012;
bankruptcy (`ba`) 2,239; public appointments (`go`/`vr` "Appointment of…")
about 7,200 by the old classifier. Bankruptcy notices print home
addresses: their reader keeps the address in `gazette_private` from its
first line, and every look at them is masked by the vocabulary mask
(lesson `a-masked-gazette-sample-still-leaks-through-its-lowercase-words`).

Next sessions, one profile each: `ds` and `aw` (company lists, the same
suffix-cut title rule as `al`), then `ar`, then `ba`, then the public
appointments (status.md "Next" 2 and 3 come first).
