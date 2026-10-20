# A report started from a company does not follow its officers
kind: finding
state: open
use-case: subject report (5.1); 4 agriculture counterparty; also 2, 3, 5, 7, 13
session: agriculture
opened: 2026-10-20

From a company row the walk lists the company's directors, holders of
record and registered office (the `roles` bucket) and the Gazette notices
on it, but goes no further: `walk.py` reads the group and links only of the
start's own rows, and the `second` step runs only when the start is a
person. So the people behind the company are names, not records: their
other companies and what became of them, a prohibition joined to a
director's row, their society roles and their donations are not reached.
Use case 4 asks exactly this ("the people behind a rural trading company";
the old estate's group-receivership read the officer web). The agriculture
template blocks five checks on a company start (officer-group-insolvency,
prohibition, other-companies, charity-officer-roles, practitioner-repeat)
and tells the reader to start a report from each person listed; and its
"people's other companies" section prints "none found in Companies, …",
which reads as a clear and is not one (the section's text says so). Seen on
NIRVANA FARM LIMITED (`companies:companies/9429041725702`, in receivership,
one director with a full name the walk never follows). For the report
lane: from an organisation start, walk each person row on it one step (its
group, its confirmed links, the entities those sit on and the notices on
them), graded near by the through-people default, with the walk's limits
counted; or let a template ask for it as a setting. The template then
unblocks those checks (a fix in its folder).
