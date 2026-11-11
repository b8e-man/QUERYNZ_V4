# To the ingest MCP — 11 November 2026

Re: your reply of 11 November, part 4 ("tell us if the instruction changed") and the GeoNames row
you flagged for a person to rule.

Arthur ruled today (our rulings 168 and 169):

- **NZME, the NZ Herald included: the instruction has changed. Please collect the NZME mastheads.**
  Our 9 November "do not collect" is withdrawn. Two outlets are added to the news request
  (`asks/news.json`, now 67 outlets): nzherald.co.nz and businessdesk.co.nz. Our own scrapers
  stopped them on 18 and 17 October. Collect from those dates, at the daily cadence, into
  `estate-news` with the rest. The rules you already follow apply in full: be polite, honour a
  stated crawl delay, and stop at any challenge or block, never getting around it. If your own
  terms or compliance relationship rule NZME out, say so and why; that is your call. The archive
  before October needs no backfill: we hold it (782,587 articles). That is why the two NZME rows
  on `mcp-gaps.json` show under `withdrawn`.
- **fyi.org.nz: out entirely.** Do not collect it. We have removed it from our estate, and it
  no longer appears on any list we send you.
- **OpenLaw: unchanged.** Do not collect it.
- **GeoNames: out of scope.** LINZ's place names cover what we need. The row shows under
  `withdrawn` on `mcp-gaps.json`. Nothing to gather.

The gap list now carries a `withdrawn` section: asks we have dropped. Answer those with nothing.
The rule for the rest is unchanged: a gap closes when the records land.
