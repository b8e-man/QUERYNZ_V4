# The memo's header repeats the group rows a section already lists
kind: finding
state: open
use-case: subject report (5.1)
session: recruitment
opened: 2026-10-20

`build.build` sets `report["members"]` to every group row but the start,
though its comment says "the group's members that no section claimed". So
the header lists "same person, by confirmed link: …" for a shareholding and
a prohibition that the companies and Gazette sections list again under the
same citation number (`companies:companies/9429031200745/director/9826f5895450`).
Not wrong, only twice. For the report lane: drop from the header the
members a section took, or drop the comment.
