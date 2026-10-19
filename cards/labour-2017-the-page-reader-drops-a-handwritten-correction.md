# Labour 2017: the page reader drops a handwritten correction
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-20

The lane says Labour 2017 declared $1,599,673.77; the frozen site and the
Commission's by-year table both say $1,611,073.77. **The lane is wrong.**
On the declaration page
(`ebe8a89c467c7c15f9f49ddf0718312998233080bd1730052d409663bd0b4b7e`,
page 1) the typed Part A ($867,324.41) and the typed total are struck
through and corrected by hand, initialled: Part A $878,724.41, total
$1,611,073.77. The page reader's stored reading (GLM-OCR, `OCR`) carries
the typed figures only and no trace of the ink, and the typed figures
still add up, so the return's own arithmetic passes it.

No check inside the lane can see this. The Commission's table can: the
outside check (`commission.py`) is what caught it, with the frozen site.
2017 is outside Follow the Money's window, so nothing published moves.

Fix, when it is worked: a re-read of the declaration's figure cells at
cell scale (a job for the scheduler's page reader, not this lane), or a
rule that a declared total the Commission's table contradicts, where the
page shows ink, is set aside. The second thins the register on the
Commission's own slips (card `the-commission-s-table-differs-from-four-returns-that-are-right`),
so it waits for the first.
