# links-2: every published register in the rows, two rules from a register's own structure, six near rules with their reasons, the links no longer behind the lanes
branch: session/links-2 (pushed; 5b7b501)
session: links-2 (Fable, node2)
raised: 2026-10-20
claims: links/ (rows, rules, build, check, measure, tables.sql, __init__, spec, README, measurements.md; tests test_rules); cards (5 closed, 3 annotated and handed on, 1 new for keys); docs/decisions/queue/ (3); lessons (2); docs/status/links.md

Built and measured in `scratch_links_2` on the real published tables (the
live `links` schema untouched; nothing here must run live). `check.py` 29
of 29 green there (`--pub scratch_links_2_pub`); `bin/fast links` green (35
tests, 36 s); the whole-repository fast tier was run too (see the end).

**(1) Every row the links had not read.** `links.rows` reads nineteen
views (2.88 M rows): Gazette bankruptcies (64,741; a withheld name is no
row) and appointments, MPs' and ministers' expense lines (40,156, under the
member's name), the companies a member's interests declare (4,208 entries
read out of the entry's text, 3,593 organisations), the filing candidates
and candidate donors, and the rows the lanes loaded since the morning: 454
Part A rows, 560 candidate-return rows; 18 Part A keys re-read, the one
with the residence fragment among them (site-3's card; it is on your side
of the merge, not on this branch: please close it with the note in
`docs/status/links.md`'s "closed" line or leave it to me). A catch log per
view (`links.rows_catch`, read = written + set aside) and a new check that
counts every view again and fails when a lane has loaded rows the links
have not read. Rule 10: `python -m links.rows --register <lane>` refills
one register's rows alone (2 s for expenses); the links are still built
whole. `tables.sql` adds `rows_catch` and an index on `rows (register,
view)`; `links.ddl` is idempotent, so the live reload needs nothing by hand.

**The given name.** The shared reading took every given name into the
first-and-last key when a lane files them in one field (candidate returns,
Gazette bankrupts): 385 filing candidates and 52,939 bankrupts were keyed
apart from every other register. Fixed in `rows.read_name` (first given
name, the rest middle), and a director whose first-name field held two
names now carries a middle name (26,294 rows), so rule 1 reaches further:
1,257,095 → 1,289,139. Lesson filed.

**(2) A member and the House's rows.** `seat-and-window@1`: an interests
return or an expense line joined to the seat whose term covers its date,
same first and last name, the printed electorate agreeing ('List' to a list
seat); confirmed when every seat that fits is one member (one party, no two
middle names), near otherwise: 23,042 confirmed, 0 near; 685 returns and
22,357 expense lines joined. 19,196 House rows are dated before the first
seat row the house lane holds (ge-2020) and 1,091 in the window are
list-vacancy members with no seat row or a name the House prints two ways
(`who-left-the-house-mid-term…`). A member to a donor row: near only, under
`member-and-party-donor@1` (106, the member's own party in the term) and
`own-return@1` (1), each naming its evidence.

**(3) Same-name donor rows.** `filed-name@1`, near: 172 links across one
organisation name key, with whether both rows name one party. **(4)**
`company-name@1`, near: 75,184 under one name, 13,635 under one name apart
from a bracketed year. **(5)** Declared interests anchored:
`organisation-name@1` for every declared company (2,917 links; 64% to
exactly one company alive on the return's date), `official-number@1` where
the member printed the number (8), and `declared-directorship@1`: a member's
return to a director row of the member's name on the declared company,
confirmed (434 links, 86 returns; the design's own supporting link). 172
groups hold a seat, 40 of them reach a company. **(6)** `candidate-name-form@1`,
near: 402 links, 37 a middle name on one printing only.

**Measured** (`links/measurements.md`, second run): 2,815,624 links (was
2,613,986); 681,618 groups over 2,315,026 rows; watch 152,771 flagged, a new
flag `bankrupt-yet-appointing` (149); error on two-people pairs rare 38.5%,
middling 22.0%, common 35.5% on a redrawn pool (754 pairs available, was
430), not comparable with the first run's; measurement 6 had counted groups
twice, fixed. Test pairs redrawn; the review agent should be scored again
on them (its job, track C; `review.py` untouched).

**For the integrator:** reload `links` from this branch with `links.build_all`
(about 55 minutes: rows 3 min, links 20, watch, groups, pairs,
measurements), then `python -m links.check`; the old ledgers are already
in the live schema. Drop `scratch_links_2` and `scratch_links_2_pub`
afterwards. No job change. Regenerate the board and the lessons index. The
working copy's `docs/board.md` was touched by the fast tier and is not on
the branch.

**Waits on Arthur** (defaults built as settings): may a register's own
structure confirm a politician's row (default yes, as built); may a
donation row's circumstance confirm (default no; recommend confirming the
filed organisation name within one party); may one candidate under two
printings be one page (default no). One new card for keys: a judge's title
read as a given name, a surname particle dropped, a bare post-nominal kept.

**Whole-repository fast tier, 21:50:** red on one test only,
`tests/test_generators.py::test_the_committed_records_generate_cleanly`:
`docs/board.md` is stale because five cards changed state on this branch,
and the scope hook refuses a session that file. Every other test is green
(293 s). The board is yours to regenerate at the merge, as for every branch
that closes a card.

## Result (integrator, 2026-10-21 07:48 NZDT)

Merged to main at 6246340, gate green on the second run (the first was red
on the board's outside check: gazette-5's possessions view had no board
entry; added in this branch with the pane paragraphs' other fixes). The
stale-key card closed at the merge; two lessons' rules cut to the limit.
The live `links` schema reloads from main now (`links.build_all`, about
55 minutes), then publish and `links.check`; the board restarted. The
review agent is to be scored again on the redrawn pairs once the reload
lands. The three structure questions are in the queue for Arthur.
`scratch_links_2` and `scratch_links_2_pub` are Arthur's to drop. Worktree
and branch retired.
