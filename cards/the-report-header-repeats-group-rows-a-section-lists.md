# The memo's header repeats the group rows a section already lists
kind: finding
state: closed
use-case: subject report (5.1)
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

`build.build` sets `report["members"]` to every group row but the start,
though its comment says "the group's members that no section claimed". So
the header lists "same person, by confirmed link: …" for a shareholding and
a prohibition that the companies and Gazette sections list again under the
same citation number (`companies:companies/9429031200745/director/9826f5895450`).
Not wrong, only twice. For the report lane: drop from the header the
members a section took, or drop the comment.

Closed 2026-10-20 by the report session (report-2), the comment's way: the
header keeps only the group rows no section claimed, and the group line
says how many of its rows the sections list ("3 rows, not contested; 2 of
its rows are listed in the sections below, marked confirmed"). The card's
own row `companies:companies/9429031200745/director/9826f5895450` prints each
of its two group rows once. Measured: `python -m products.report check`
builds a report on a director row in a group of two to six, taken from the
tables at run time, and fails if the header repeats a row a section lists.
