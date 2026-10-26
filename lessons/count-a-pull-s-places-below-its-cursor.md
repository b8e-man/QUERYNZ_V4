Count a pull's places below its cursor: after a source removes records and the re-walk brings the cursor back, the places past the new count keep their old arrival rows, and `count(DISTINCT seq)` overshoots.
area: registers over support/mcpsource, lane checks, mcpsource arrivals
paid-for-by: 2026-10-27, parliament-1, the first full build of registers/parliament

The written questions' cursor is 683,524 and their arrivals hold 683,770
places: the 246 the MCP removed on 26 October left the top 246 places with
the arrivals taken before the removal. The same arrivals answer which
records the MCP still serves: a record is served when it is the last
record landed at some place below the cursor (capture.arrivals). Two more
real-data faults the made records never showed: an id served with a trailing
space (compare ids stripped on both sides), and NUL characters in two
archived pages' text, which no Postgres text or jsonb column holds (kept as
U+FFFD, the document keeps the bytes).
