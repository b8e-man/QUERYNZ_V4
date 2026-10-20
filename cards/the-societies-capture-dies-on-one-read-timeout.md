# The societies capture dies on one read timeout
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-21

The nightly `qv4-societies-capture` run of 21 October (queue row 154,
01:00) ended at 03:58 with exit 1 on an uncaught `TimeoutError: The read
operation timed out` from the socket layer inside `fetch_entity`
(`registers/societies/capture.py` line 257, reached from `night` at 342).
Nearly three hours of landed pages are kept, but the run is recorded as
failed and the checks board went red for it at 07:30.

Recommended: a timed-out read is a failed read like any other: set the
entity aside with the reason, rest, and continue; the run ends green with
its count of set-asides, red only when nothing lands. The lane's fix.
