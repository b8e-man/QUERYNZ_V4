# The MCP's courts corpus lacks 80 judgments the old listing names
kind: finding
state: open
use-case: 2
session: courts-2
opened: 2026-10-30

Of the old estate's 151 courtsofnz judgments (148 held by hash, 3 gone),
80 are pointed at by no record of the MCP's courts corpus, by hash or by
url: NZCA 37, NZHC 43, all of 2025 and 2026; 78 held, 2 gone. Under ruling
127 the corpus is the lane's one source, so each is a line in the catch log
(`courts.set_aside`, stage `listing`), never a row. The line names the
citation and the hash. The first live load counts them (`old_listing_gap`
in the load's counts); report the list to the corpus's provider, and
drop the card when the corpus carries them or the provider says why not.
Nothing is fetched to fill the gap.
