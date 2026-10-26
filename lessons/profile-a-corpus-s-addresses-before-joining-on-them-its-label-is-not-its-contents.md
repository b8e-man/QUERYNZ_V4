Count a corpus's addresses by host and path before building a join on them; the MCP's "Hansard PDF index" held no transcript or PDF address, so the url join matched none, and one day's PDF is not one sitting.
area: registers/* over the ingest MCP, any join by url or by day across two sources; registers/hansard, registers/parliament
paid-for-by: 2026-10-27, hansard-2

Ruling 96 and the brief planned to join `parliament-hansard-index` (url,
lastmod, fetched) to the old transcripts by url. Counted by host and first
path segments before any code: all 383 records were www.parliament.nz pages
(select committees 293, order paper 54, Hansard's information pages 28,
bills 8); the transcripts are at hansard.parliament.nz. The join is built
and loads, and matches 0 of 137; the check counts it rather than failing,
and the card asks the provider what the corpus is meant to hold.

The same habit found the second shape: the old page for a sitting carried
the whole sitting, the provider's PDF is one calendar day, and an urgency
sitting that runs past midnight has later days the corpus lacks. Measuring
the old subjects in the day's PDF text gave 95.0%; bucketing the misses
(continuation note, in a neighbouring day's PDF, on an urgency sitting,
broken by layout) before setting a floor is what made 90% a justified
number and not a guess. A mutation that hands each day the next day's PDF
gives 37.6%, which the floor catches.
