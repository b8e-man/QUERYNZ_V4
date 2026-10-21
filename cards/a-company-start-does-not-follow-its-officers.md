# A report started from a company does not follow its officers
kind: finding
state: closed
use-case: subject report (5.1); 4 agriculture counterparty; also 2, 3, 5, 7, 13
session: agriculture
opened: 2026-10-20
closed: 2026-10-21

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

Closed 2026-10-21 by the report session (report-3). From an organisation
start the walk follows each officer on it one step (`walk.follow_officers`,
the `officers` bucket, run when a section of the template names it in its
`sources`): the rows of the officer's group (confirmed links) the template
allows, a role row only when current (in the latest file, no end filed),
the companies and societies they sit on and the Gazette notices pointing
at those; every row near by the through-people default, with the reason
naming the officer ("reached through a person on the subject (…): an
officer's other role is the officer's connection, not the subject's"), via
the officer's row on the start, which a template reads as `through`.
Twelve officers and forty rows each are followed, the rest counted in the
memo. Measured on NIRVANA FARM LIMITED (`companies:companies/9429041725702`):
the director's other current companies (ANGIWA CARBON NO 1 LIMITED and
others, each marked "one step through" the director's row) are listed,
where the report listed one director's name and stopped. The shape's own
`prohibition` rule now clears on a company start only when every officer
was followed, and blocks otherwise (lesson: a company start lists people
the walk never follows). `python -m products.report check` builds a report
on a company whose director's group holds another current directorship,
taken from the tables at run time, and fails unless the other company is
reached, near, through the director's row. The agriculture template (and
2, 3, 5, 7, 13) names `officers` in the sources of the sections that want
it and unblocks the five people checks (a fix in each folder).
