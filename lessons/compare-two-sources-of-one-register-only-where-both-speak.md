Before storing differences between two sources of one register, strip each source's furniture from the values and compare a category only where both list it: one real run gave four false changes in five companies.
area: companies, monitoring, change detection, step 5.5, NZBN interface, registers
paid-for-by: 2026-10-21, companies-2 session, step 5.5

The monitor compares the NZBN interface's answer with the monthly file's
rows. On the five sample companies the first draft found nine changes; one
was real (a company in liquidation in August, removed since). Two holdings
"left and started" because the interface files a body's name as
"7559576 - X LIMITED" while the file has "X LIMITED"; four came from a
removed company whose August rows are all `in_latest` false, so every
director and holding in the answer read as "appointed". The fixes: strip
the prefix in the reading; give each held state the categories it can speak
for (an answer speaks for all; the monthly file only for what it lists
current); and pin it with a test per false change and a slow test that the
five real answers against the real lane give the one change. Run a
difference engine on a handful of real rows before trusting any change it
reports: invented fixtures share the shape you assumed.
