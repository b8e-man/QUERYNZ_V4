A page reader prints one space where the text layer kept a column, so a skip keyed on an item heading misses on a scan: restore the heading shape before any rule runs, and test on real documents rasterised.
area: reading, page reader, scans, council minutes, hard limit 16, skips before readers
paid-for-by: 2026-11-02, council minutes scans fork of integrator-9d788fb (registers/council_minutes)

The council minutes lane skips a public forum item and a public-excluded part
before either reader sees the text, and finds both by the item heading's
shape (a number, two or more spaces, a title in capitals). The page reader
prints `5. Public Forum` with one space and in any case. On a real Western
Bay of Plenty minutes rasterised and given back with its columns collapsed,
the forum item was not skipped and one public-excluded part of two was
missed. minutes.from_pages puts a numbered capitals heading back as
`n  TITLE`, and makes any numbered line naming a forum or a public-excluded
part a heading whatever its case (over-skipping loses only what is kept).
The test rasterises real landed minutes and holds the skip counts equal and
no line the layer's skips drop kept from the scan's text.
