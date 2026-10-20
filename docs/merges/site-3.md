# site-3: a page's key is the display name's own; one donor, one page; a declaration's year is the gift's
branch: session/site-3 (pushed; 56ee30f)
session: site-3 (Fable, node2)
raised: 2026-10-20
claims: products/published_site/ (paths, figures, render, read, gates, spec, tests), products/templates/ftm/ (ftm.json v3, README), docs/status/site.md, cards/ (3 closed, 1 accepted, 4 annotated, 1 new for links), lessons/ (one)

**(1) The blocker, hard limit 15.** A donor's published `name_key` is now
derived from the settled display name alone (`paths.name_key`); the links'
readings fold rows inside the build and no published field repeats one. A
ninth gate, `name-keys`, fails a build on any key with a word the name
beside it lacks, or a residence word in a name field or a file path (the
comparison's vocabulary, a test holds the two equal); on version
2026-10-20T1513 it fails with 43 faults, naming files and fields, never
text. Measured by code on a scratch rebuild from the same listing: keys
with a word the name lacks 28 → 0; residence words in name fields and
paths 9 → 0. Card closed on the site's side; the links' half is the new
card `the-links-hold-a-donor-key-read-before-party-returns-5-fixed-the-row`
(one stale key; 54 of 58 twinned donors had rows the links have never read).

**(2) Two donor pages for one name.** 58 display names with two pages on
1513. A row the links have not read takes the links' reading of its exact
filed spelling in any register (before, candidate returns only); donors
left with one display name fold (`figures.fold_by_display`); the twin-path
rule is gone and the build refuses rather than invent one. Donor pages 990
→ 928; the cause `rebuilt-splits-a-donor-across-two-pages` 198 → 0.

**(3) The money year of a declaration** is `given_on`'s, `received_on`'s
only where no gift date is printed (2008–2022 itemised declarations); both
dates and the year's basis are on every row (`figures.disclosure_year`,
`read.py`'s window filter, the commission gate's SQL). Home-page party-years
from 2023 against the frozen: NZ First 2023 $888,141.69 and Labour 2023
$744,672.35 now equal; the 2024 rows are gone; National 2023 stays $23,000
apart under its own card. `declaration-dated-by-the-day-received` 8 → 0.
**For the integrator, in `checks/comparison.py`:** the causes for
`two-declarations-sit-in-2023-on-the-frozen-site-and-2024-on-the-rebuilt-one`
and disclosures-3's `one-2026-declaration-is-dated-by-the-commission-before-its-gift`
want `owner="site"`, `right="frozen"`. The two-declarations card is appended
on both `session/disclosures-3` and this branch: merge disclosures-3 first
and keep both sections.

**(4) The comparison-2 cards.** `the-party-page-lists-statements-by-period-
the-frozen-listed-files` accepted (the shape's rule; a known-limits line;
7 figures stay). Annotated with the figure that moved and left with their
lanes: promoter people (2), expense-return reconciliation (4), interests
counts (335), the aggregate card (1,890 → 1,920, the merged pages carry
more parts).

**Measured** with `checks.comparison.run` into scratch (the live ledger
untouched), frozen 2026-10-20T0620 against two builds from its listing on
the same tables, main's code and this branch's: 29,511 → 29,336
differences, 0 uncarded, new-side-wrong 7,946 → 7,752. Fast tier
`products/published_site products/templates/ftm` 61 green (28 s with the
fill); `python -m products.published_site check` green in scratch, 9 gates.
Lesson: a key published beside a name is derived from that name.

For the integrator: no new job; `qv4-site-build` picks the code up and
builds template version 3 beside the frozen site; `qv4-site-compare` reads
it. The board and lessons index want regenerating (cards: 3 closed, 1
accepted, 1 new).

Waits on Arthur: nothing new. Standing: the section queue item, the
window, party boards, the coupled donor names, the real-property text; and
the frozen site's own copy of the residence fragment (hard limit 19).

## Result (integrator, 2026-10-20 20:04 NZDT)

Merged to main at 20336d9, gate green. The two-declarations card keeps
disclosures-3's measurement and this branch's closing; the comparison's
cause `declaration-dated-by-the-day-received` now says owner site, right
frozen (`checks/comparison.py`). `qv4-site-build` queued at 20:05 to build
template version 3 beside the frozen site; `qv4-site-compare` reads it
tomorrow 08:45, or tonight by hand once the build lands. The links half
(the stale key) is in links-2's brief, launched 19:48. Worktree and branch
retired.
