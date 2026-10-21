# The societies capture dies on one read timeout
kind: finding
state: closed
use-case: 1
session: founding
opened: 2026-10-21
closed: 2026-10-21

The nightly `qv4-societies-capture` run of 21 October (queue row 154,
01:00) ended at 03:58 with exit 1 on an uncaught `TimeoutError: The read
operation timed out` from the socket layer inside `fetch_entity`
(`registers/societies/capture.py` line 257, reached from `night` at 342).
Nearly three hours of landed pages are kept, but the run is recorded as
failed and the checks board went red for it at 07:30.

Recommended: a timed-out read is a failed read like any other: set the
entity aside with the reason, rest, and continue; the run ends green with
its count of set-asides, red only when nothing lands. The lane's fix.

Closed 2026-10-21 by the fix session (fix-registers-societies-1). In
`capture.night` a read that does not finish (a socket `TimeoutError`, a
reset or dropped connection, the gateway's 504 whose page carries no
challenge) sets its society aside: its ledger line carries the reason,
the clock moves, the run rests `REST_S` (60 s) and goes on; five in a row
stop it. `capture.set_asides()` feeds each society whose last ask did not
finish into the catch log (`societies.set_aside`, stage `capture`) at load.
A block or a challenge still stops the run (hard limit 6), and a gate
refusal or an unreachable host stops it in one line, not a traceback. The
run is red only when the register answered nothing; a run stopped early
that landed answers is green and says why. The test with an invented
fetcher that times out on one society fails against the old `capture.py`
with this card's `TimeoutError`. The live capture was not run.
