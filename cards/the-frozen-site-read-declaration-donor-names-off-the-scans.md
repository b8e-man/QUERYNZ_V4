# The frozen site read declaration donor names off the scans
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

The frozen site took a large declaration's donor name from its own OCR of
the scan, and some are mangled: five Toorak Chambers pages under five
spellings, "Charles Dave" with no party, three Warwick and Averil Norman
pages. The disclosures lane takes the name from the Commission's table, so
a declaration-only donor sits under another name on each side (16 frozen
pages with no rebuilt match, and new rebuilt pages such as "Rank Group
Limited via Graeme Hart" as the Commission files it). Today: 30
differences.

Which side is right: the rebuilt one; the Commission's table is the
record. Owner: disclosures (until 2026-10-20; see below).

## Measured 2026-10-20 (disclosures-3): the names are the Commission's; the pages are not the lane's

On the frozen site's 2,399 donor pages there are 282 distinct
large-declaration lines. 275 of them are a row of the Commission's table
(the same scan, the same amount) under the name the table prints, folded
by `keys.names`. Seven are not, and only these were read off scans:

- 3 OCR rows from `Vision_New_Zealand_25_July_2023.pdf`, which no row of
  the Commission's table links ($37,063.35, $9,989.18, $2,472.85);
- 1 "Charles DAVE" row, $36,066.60, from
  `Vision_New_Zealand_23_October_2023-v3.pdf`, the superseded version of
  the struck-out Freedoms New Zealand declaration, also unlinked;
- 2 "Wal IEF Limited" rows and the IEF Limited row filed against the
  Maritime Union's scan: card `national-2023-the-frozen-site-counts-one-declaration-twice`.

The disclosures lane takes the donor from the Commission's table on all
520 declarations (ruling 253), so for these seven the rebuilt side is
right and nothing in the lane changes.

The rest of the 41 differences the comparison counts under this card on
day one are donor pages present on one side only whose lines carry the
same Commission name on both: the frozen site titles a page from its fold
over candidate-return and party-return spellings (five "Toorak Chambers"
pages each carrying the one $34,000 declaration; "Warwick and Averil
Norman" and "Warwick & Averil Norman" as the Commission itself prints
them); of the 40 the day record samples, 20 are `pickers.json` entries. Page names are chosen by the site
and the links, not by this lane.

What it still needs: the site lane (with links) to say which page title is
right for each of those pages; the cause text in `checks/comparison.py`
("read the donor's name off the scan") should be corrected to page titling,
owner site. Left open for that.
