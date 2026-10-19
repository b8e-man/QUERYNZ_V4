A lane read from an old loader's tables reconciles against that loader's own run counts: rows short of the count were folded by it, and the catch log carries the difference as one counted line per file.
area: lanes, catch log, exports from old tables, companies
paid-for-by: 2026-10-20, companies session 1, step 4.1

When only the loaded tables survive, "items in" is not the export's line
count: the old loader may have folded lines before they reached its table.
`nzbn_canonical.import_runs` recorded each file's lines (directors 1,176,923
in August) while the table held 1,176,751: 172 lines folded on equal
content, and 20,688 shareholder lines the same way. Comparing only export
lines to rows would have reconciled perfectly and hidden the loss.

How to apply: export the loader's run counts in the export's header, count
the rows each file contributed, and write `stated - got` as one catch-log
line with a `count`; raise when a file gives more rows than it had lines.
Also: `keys.dates.filed_date` reads only years 19xx and 20xx; an ISO date
column copied from an old table (companies registered in the 1860s) is
taken as stored.
