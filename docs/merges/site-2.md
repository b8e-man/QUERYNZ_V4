# site-2: the frozen sections, electorate money, statements and the interests register on the rebuilt site
branch: session/site-2 (pushed; 4aff450)
session: site-2 (Fable, node2)
raised: 2026-10-20
claims: products/published_site/ (figures, candidate_money, money_sections, render, gates, build, read, tests), products/templates/ftm/ (ftm.json v2, README), docs/status/site.md, cards/ (18 of the comparison's closed, accepted or annotated; 4 new; a line on the candidate-returns card), lessons/ (one, index regenerated)

The shape's second tranche under the queue's default (all frozen sections):
every home-page money section, the parties page's three, the party page's
statements, donations made, top donors, coverage; electorate money from
the candidate-returns lane (370 of 380 returns joined, the rest shown
apart, never guessed); list candidacies and the interests register on the
person page; donor pickers, display names and page keys settled in the
template with why. Two gates re-sum the lanes by SQL and each caught a real
fault on the way. No deploy step, nothing on 8300/8301, no address, no
suppressed name.

Measured by `python -m checks.comparison run` (never edited) against the
frozen 2026-10-20T0620: 43,062 differences fell to 30,447; sections not in
the template 10,651 to 266; candidate returns not held 9,618 to 7,077;
new-side-only sections 1,866 to 209; statements 17 to 0. 610 uncarded, all
the comparison's own readers (carded for it).

Fast tier: `products/published_site products/templates/ftm` 55 passed.
Builds in scratch only; the live `qv4-site-build` picks the code up on merge
and builds version 2 beside the frozen site.
Lesson: a section is matched by its key, so the key takes the other side's name.

Waits on Arthur: the section queue item, the window, party boards, the
coupled donor names, the real-property text.

## Result (integrator, 2026-10-20 15:12 NZDT)

Merged into main as 2431ba3 (merged main first; the generated lessons
index conflicted and was regenerated). Done at the merge: records
regenerated; the party-returns-5 record rode along; `docs/status/site.md`
was 4,504 bytes against the 3,000 limit and the fast tier refused it, so
the integrator cut it to the standing facts (the tranche's detail is
this record and the request above). Fast tier and gate green; nothing to
load. After the merge the integrator fired `qv4-site-build` and
`qv4-site-compare` once each (ruling 56) so version 2 stands beside the
frozen site tonight and the comparison reads it before its 08:45 run.
Arthur's to rule, in the queue: the frozen sections (default all), the
window, party boards, the coupled donor names, the real-property text.
The session ran headless from the integrator as Fable, about 65 minutes.
