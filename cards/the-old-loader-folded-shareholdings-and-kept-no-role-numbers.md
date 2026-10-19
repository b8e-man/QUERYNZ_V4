# The old loader folded 1.3% of shareholdings and lost the file's own role numbers
kind: finding
state: open
use-case: companies lane; links (4.2, 4.3)
session: companies
opened: 2026-10-20

The monthly CSVs were deleted after loading, so the lane reads the old
tables. The old loader keyed a director on company, names and start, and a
shareholder on company, holder, shares and status, and folded equal lines
into one: by its own run counts 168 (July) and 172 (August) director lines
and 20,725 and 20,688 shareholder lines (1.3%: the same holder with two
allocations of the same size). It read no allocation number, no
shareholder address and none of the ASIC director fields. Each fold is one
counted catch-log line; the lines cannot be recovered from its tables.

So, for the test pairs of step 4.3 ("the same role carried from one monthly
file to the next under the source's own role identifier"), the lane's key
is filed content, not a source identifier: the file gives none for a role.

To close: a reader for the package's own CSVs (`companies_director.csv`,
`companies_shareholder.csv`) for whenever a package is held as a file,
keeping every line and the allocation number; until then accepted as a
known limit of the export.
