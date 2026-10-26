Split a JSON-lines file on "\n", never with str.splitlines(): a text holding U+2028 is cut mid-line, and a count taken before the last stage hides it (the Beehive export read 55,344 of 55,358 lines, none set aside).
area: export, json-lines, reading, counts, registers
paid-for-by: 2026-10-26, mcp-1, the old estate's Beehive export

`json.dumps(..., ensure_ascii=False)` writes U+2028, U+2029, U+0085 and
control characters raw, and `str.splitlines()` treats every one of them as a
line end. Each split line then fails to parse, or two halves are dropped as
blank, and the export reads short. The loss stayed invisible because the
reader's `set aside` figure was computed before the export's lines were read.

How to apply: iterate `data.decode("utf-8").split("\n")` (or bytes split
on b"\n"); compute every count after the last stage that can add to it; and
hold the reader's line count to the export's own line count (the export
prints it) before trusting a zero.
