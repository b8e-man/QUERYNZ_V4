# The MCP holds no PDF for an urgency sitting's later days, and its Hansard index names no transcript
kind: finding
state: open
use-case: -
session: hansard-2
opened: 2026-10-27

Two gaps in the ingest MCP's Hansard corpora, measured on mcp-1's pull (27
October, all 1,862 debates records and 383 index records). Both are the
provider's to fill; nothing in the estate is wrong.

1. **Urgency sittings.** When the House sits under urgency past midnight,
   Parliament publishes one daily PDF per calendar day; the old estate's
   transcript page carried the whole sitting. The MCP's
   `parliament-hansard-debates` holds the first day's PDF only for eight
   such sittings: 2024-12-10 (continued 11 to 13 December), 2025-03-25
   (26th), 2025-05-06 (7th, 8th), 2025-05-22 (23rd, 24th), 2025-06-24
   (25th), 2025-09-16 (17th), 2025-11-18 (19th to 21st) and 2025-12-09
   (10th to 12th); every other continuation the old pages note is held.
   119 of the 153 old section subjects found in no held PDF are on these
   eight sittings, and so are the seven lowest days (57% to 74%); the
   lane's check passes at 95.0% (floor 90%) with them out. Whether a
   continuation day has a PDF of its own at another address is not known
   here (the estate fetches nothing from parliament.nz, ruling 78).
2. **The index.** `parliament-hansard-index`, labelled "Hansard PDF index
   (parliament.nz)", holds www.parliament.nz pages: select committees 293,
   order paper 54, Hansard's information pages 28, bills 8. None is a
   hansard.parliament.nz transcript page or a daily PDF, so the url join
   of ruling 96 matches 0 of the 137 sitting days and "the held text may
   be older than the page" is never said. The lane loads the index whole
   (`hansard.index_pages`) and the join stands ready.

Next: Arthur asks the provider (a) whether the continuation days' PDFs
exist and can be added to the debates corpus, and (b) whether the index is
meant to list the transcript pages or the daily PDFs. The lane takes either
the night it arrives (`qv4-hansard-load`), with no change.
