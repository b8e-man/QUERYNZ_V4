# Rulings

Each answer from Arthur, with the date and his words. Rulings 1 to 54 are from the October discussion that produced the plan, copied here unchanged from `docs/plan/reference/dated-jobs-open-decisions-rulings/rulings-in-force-from-the-october-discussion.md`. New rulings number on from 55.

**Three points that govern everything**

- Follow the Money does not stop, and the build goes toward it first.
- Rebuild the shape, move the scar tissue, and make the cards account for every difference.
- Every use case can be exported whole, without heavy duplication of code or state. Since ruling 47 an export is a shape, a template and the tables it reads.

**10 October**

1. This is a capability build-out. Plan as if customers exist. Billing, accounts and metering are out.
2. Legal work comes after the build and before any service is sold.
3. The partner model is an enhancement, not the frame.
4. Order and parallel work are free. New operating rules replace the old method.
5. The ten August use cases join the plan.
6. Parked and retired work is a resource to draw on.
7. Press is demoted entirely for now.
8. Keyword search is back for journalism other than Papers Past.
9. History search is a use case, with every search tool.
10. The capture rules are abandoned. Collection is judged on legality and politeness.
11. Superseded by 12.
12. NZME is dropped, every masthead.
13. The Papers Past archive is on the boxes. Each ingest catch is identified exactly where it happens.

**11 October**

14. Work is parallelised as far as it can be. The lessons flow and the card board are kept. The backlog is not allowed to pile up, but not at the cost of the work.
15. Follow the Money is the first thing recreated in the new estate. After it the order is the planner's, as set out in this plan.
16. Each product is tested when built. Gaps and failures are carded, not necessarily fixed.
17. The live Follow the Money is frozen and kept as a working, exported product.
18. The held legal sources are in. Research legal document extraction and try newer page readers. Easiest first.
19. Company monitoring goes as deep as the official interface allows: poll on lookup and update from the differences. The monthly import stays.
20. The Papers Past meaning index lives on the hard disks for now.
21. The off-site copy stores changes, with a weekly checkpoint.
22. Four graphics cards, switched between jobs by the scheduler.
23. Papers Past is read whole.
24. The build method for the full meaning index is agreed.
25. A new repository. The old one stays as it is, running the frozen product.
26. The old two-closures rule is dropped. Three kinds of card replace it.
27. One short spec per module, checked at the merge.
28. Stopping the press-graph jobs is a plan step.
29. The three-way delete rule is agreed. The safety hook stays.
30. Build sessions run on node2, each in its own working copy: three plus the integrator to start.
31. The two boxes are peers and one service schedules every job. A third machine makes database takeover automatic. Each box has a hardware profile. The spare memory goes in node2; the primary database role normally stays on node1.
32. The frozen Follow the Money keeps its daily data refresh.
33. The old cards are not carried over. All are read for context, with care.
34. The standing product rules were gone over one by one (see 39 to 43).
35. Arthur starts each build session on node2. The plan gives a short brief for each.
36. The new estate's data lives beside the old at first. The old is deleted once properly consumed.
37. Lanes re-read from documents already captured. Judgments and corrections are copied untouched.
38. The new repository is named QueryNZV4.
39. The Follow the Money money and scope rules belong to that product only.
40. The two confirming rules stay exact for Follow the Money. The wider estate starts with them; they are revisited only after measurement, by Arthur.
41. Arthur is not in the review loop. A suspicious link is reviewed by an agent and split if not trusted. Reports list near connections.
42. A company's registered address is shown. A person's home address is never shown or extractable, and is still used for matching.
43. Papers Past gets a broad name index as a search aid: people, towns, roads, organisations. It never feeds the links.
44. A graphics card runs one model on one kind of job at a time. The scheduler may swap it and records every swap.
45. Re-reads no longer wait for Arthur. The scheduler runs them.
46. The rule-learning process is kept, and the old extraction lessons and rules are captured.
47. The design is simplified: five parts, no stored person, four product shapes.
48. The support design is kept in full, because the work may grow.
49. The four page readers are trialled. Chandra OCR 2 is in.
50. The trial runs first, over the election documents, as the scheduler's live trial, under three conditions: profiles first, readings tied to bytes, text or scan decided per page.

**12 October**

51. Passwords and API keys are rotated as part of this plan, and the long-running security cards are brought into it (track H). This replaces old ruling 270, which deferred every rotation.

52) An interface that shows the connections between registers: one search across all of them, with the results and each followed link shown in panes side by side, like the Miller boards of the earlier estates. It is a fifth product shape, the board (step 4.9).

53. The build starts next week. Follow the Money keeps running as an exported product, and the only feed it still needs is the declared-donations feed, which is carved out to run alongside (step 1.4).

54) The new estate is kept quick to work on: three weights of session, a budget on required reading, nothing that grows read whole, two tiers of checks on a sample database, registers that rebuild in parts, data questions answered from the published tables, and the wait measured ("Keeping the work quick").

**Old rulings this plan still relies on,** by their number in `docs/records/DECISIONS.md`: 172 (no text to a cloud model), 203 (Papers Past is a search corpus), 217 (busy address), 220 (the watch on links; its "on Arthur's word" is replaced by ruling 41), 221 (the two confirming rules), 253 (ownership is a note), 193, 277 and 357 (the return is the record), 321 (fyi.org.nz), 333 and 347 (2019 onward; superseded on the window by 364 and ruling 71: calendar 2017 onward), 349 (a renamed party), 351 and 356 (seven parties), 355 (no press row), 361 (a race is every year since the election before it, cut at the window; it replaced 358 on 16 October), 360 (for telling a person's name from an organisation's, the director register is the authority for given names).

## From 55


**18 October**

55. Node1 is out of the plan. "Forget about node 1 and everything we need it to do." Nothing waits for it: no re-measurement, no second half of a batch, no mirror, no standby, no push to it. Node2 is the estate. If node1 is ever brought back, that is a new decision, not a resumption.

56. A timer is an artificial blocker. "Anytime there is an artificial blocker like a timer, just fire the service or unit or module and keep things moving." Where the next step waits only on a clock (a release, a feed, a board run, a nightly load), start the unit by hand, use its result and record that it was a hand run. The plan's "wait for one scheduled release between batches" is read this way from here. A real blocker (Arthur's hand, a hard limit, a source that has not published) is not a timer. Said after batch 3 was stopped at 16:04 on the strength of the 13:34 release run by hand.

**18 October.** 57. Arthur to the scheduler session, on its queue item about a second worker on node2: "card the node 1 setup". node1 is to be set up as the estate's second box (`cards/node1-setup-as-the-second-box.md`), each line that touches node1 itself on Arthur's word. This narrows ruling 55: node1 is not waited on by anything in step 1, and nothing in the plan is owed to it until the setup card is worked; the two-box proofs of step 2 are owed on it then, not on a second worker on node2.

**19 October.** 58. Arthur to the windowed session, on both track E questions: "Decisions held - yes", the defaults are the rulings. Tenancy Tribunal orders are kept after the Ministry takes them down at three years and never shown: held in the document store by hash past their `unpublished_date`, the lane's tables carrying no name or address, nothing published; step 5's reading decides nothing about showing, and a ruling is owed before any product shows one. The lawyer reads the position before anything is sold.

59. No letter to the Real Estate Authority yet. The lane captures and holds its decisions as in-house use, which the Authority's terms allow; nothing is published. Before any product shows them: the lawyer says whether a Complaints Assessment Committee decision is a tribunal judgment under section 27 of the Copyright Act 1994, and if not, one letter to the Authority. `decisions.dotnous.com/robots.txt` says `Disallow: /`; under ruling 10 that is recorded, not obeyed, and it is in the position for the lawyer to weigh.

60. Arthur, 19 October, 18:50: "I would prefer that we halt the ocr test with the results we have and come back to it once the plan is complete." Step 3 halts. The five unfinished pass-two rows (66 to 69, 74) were cancelled at 18:48; every page read so far stays in the stored readings. The trial session closes step 3 with what is scored: GLM-OCR, the incumbent, is the primary reader; the second reader is chosen from the challengers' partial scores, or left open with a card if the scores are too thin to choose; the write-up names what was not run. The trial resumes after the plan is complete (TeleOCR's patched server, the GLM-OCR prompt variant, the rows and compression comparisons). Card 1 goes to the scheduler's other work meanwhile; card 0 stays the carve-out's until the election (hard limit 22).

**20 October.** 61. Arthur, 20 October, 08:05, on hard limit 9: "we dont need the legal positions. we can get that before product" (confirmed). The one-page legal position for a new class of source is written before product, not before capture: the capture itself is still judged on the four questions as the work goes (open page, lawful copying, the terms accepted, what privacy law or the register's statute limits), and every other capture rule stands unchanged (no challenge solved, no block got around, polite, the two named sources out, robots read for a crawl delay only). The lawyer reviews the positions before anything is sold, as before. Charities (the register's own feed) and incorporated-society officers (the per-entity interface) may be captured on this basis; their positions are written before the product that shows them.


62. Arthur, 20 October, 14:30: "let's delay the document reading until everything is built. We need some sample data but not the full tranches." The page-reader jobs (`qv4-read-pages*`, the re-reads) are not queued in bulk until the plan's build is done; a lane that needs readings works from the sample the store already holds and sets the rest aside with hashes and pages, so the queue is one command when the time comes. `qv4-read-pages-candidates` (row 130, 713 pieces) was cancelled at 14:30 with 60 of its 713 returns read; those stay as the sample. Step 3's halt (ruling 60) stands with it.

**21 October.** 63. Arthur, 21 October, 08:15: "let's hold 6 until the end", corrected at 08:30: "I miss typed. i meant step 7"; after step 6 was explained to him, "step 6 can go back as it was". Step 7 (archive search) is held until the end of the plan; step 6 (register scans) keeps its place after step 5. The briefs are ordered step 5 to its close, then step 6, then step 7.

64. Arthur, 21 October, about 12:45, through the integrator's side chat, on
the queue item `whether-a-charity-s-address-for-service-is-shown-when-it-may-be-a-trustee-s-home`:
"1. keep. We will decide to withhold before we have customers." The default
stands: a charity's address for service is shown where the charity is a
body corporate (an incorporated society, a company, a trust board
incorporated under the Charitable Trusts Act) and withheld for the rest
(20,031 of 45,895 on the 21 October copy, 16,507 of them for filing no
legal structure); the final withholding rule is decided before there are
customers, with the legal review (ruling 61). Built so by `charities-3`;
the queue item closes.

65. Arthur, 21 October, about 12:50, on template 7's phoenix window (365
days either side of the failure; the old estate used 90 days after): "2.
for this we want the window to be user configurable, so flag all companies
with shared people or offices." The template flags every company that
shares a person or a registered office with the subject and carries a
failure notice, whatever the gap, showing the gap in days; the window is
the reader's parameter, no cut until set. Built by `construction-2`.

66. Arthur, 21 October, about 13:00, on Part A rounding (a candidate
return's parts against its printed total; the default made a one-cent
difference a set-aside): "4. anything under $100 is considered reconciled
but flaggd as having an issue. anything over $100 is considred
unreconciled. this applies accross political donation documents as
doctrine." Doctrine for every political-donation document (candidate
returns, party returns, disclosures, party finance): a difference under
$100 between a document's parts and its printed total is reconciled and the
row carries an issue flag; $100 or more is unreconciled. Lane work in the
four lanes, briefed as `reconciliation-1`.

67. Arthur, 21 October, about 13:10, on the queue item
`may-the-gazette-lane-read-notices-that-name-people-for-conduct`: "5.
keep". The default stands: vehicle confiscation orders and professional
disciplinary findings stay typed and unread in `pub.gazette_notices`, and
no person is published from them. The queue item closes.

68. Arthur, 21 October, about 13:15, on the queue item
`which-frozen-sections-belong-in-the-follow-the-money-template`: "6. I dont
understand but keep all the sections of course, I dont know why you would
ask". Every section of the frozen site's pages belongs in the Follow the
Money template; the comparison keeps counting a missing section as the new
side short until the template carries it. Not to be asked again. The queue
item closes.

69. Arthur, 21 October, about 13:20, on the queue item
`may-the-review-agent-s-splits-be-applied`: "8. we will review at the end.
Keep as a card for after the build". The switch stays off; the agent's
verdicts are recorded and applied by nobody; the question is a card for
after the build (`cards/the-review-agent-s-splits-are-ruled-on-after-the-build.md`).
The queue item closes.

70. Arthur, 21 October, about 13:25, on the card
`act-new-zealand-2026-a-declaration-filed-after-the-lane-s-capture` (the
disclosures lane's copy of the Commission's table is one declaration behind
the frozen site): "9. keep". The gap stands until the switch; no nightly
capture of the Commission's table is added before it (step 4.8 unchanged).
The card closes as accepted.

71. Arthur, 21 October, about 13:30, on the queue item
`the-template-s-window-2017-or-2019`: "7. no we changed it to 2017". The
Follow the Money window is calendar 2017 onward, whole, as ruling 364 says
and as the template's `settings.window_from` holds; old ruling 347's 2019
is superseded on the window. The queue item closes on its default.

72. Arthur, 21 October, about 13:40, on party boards (card
`party-boards-have-no-lane`): "8. buikld the declared anbchor tier but dont
deploy to the site". A party-boards lane is built from the held
party-website capture (1,061 files, no fetch), the tier the party itself
declares; it is not published on the Follow the Money site and does not
enter the links until he rules; the party page's board stays "not held".
Briefed as `party-boards-1`.

73. Arthur, 21 October, about 13:45, on coupled donor names such as "A & B
Surname" (card `the-two-folds-cut-donor-names-differently`): "9. one row
where the EC files them together. they are in effect a single entity but
joined to each of the individual entities". The donor row stays one row as
the Commission filed it (ruling 253 unchanged); the links join that coupled
donor to each person named in it, so each person's page shows the coupled
donation and the donor page stays one. A fix session on links and keys.

74. Arthur, 21 October, about 13:50, on the Stats NZ service key for the
2025 electorate boundaries (card `stats-nz-2025-electorates-need-arthur-s-key`;
queue item `the-key-for-electorate-boundary-shapes`): "11 not wanted". No
Stats NZ key; `pub.electorates` keeps the 71 for 2026 with `join_basis`
"boundary set not held"; the card closes and the key leaves the queue item.

75. Arthur, 21 October, about 14:20, on links-2's three structure
questions (queue items `may-a-registers-own-structure-confirm-a-politicians-row`,
default yes; `may-a-donation-rows-circumstance-confirm-a-link`, default no;
`may-one-candidate-under-two-printings-be-one-page`, default no): "12.
let's experiment once the build is complete". The three defaults stand as
built; the questions are held, not closed, for an experiment after the
build (card `the-links-structure-questions-are-tried-after-the-build`); no
change to the links now. The queue items close into that card.

76. Arthur, 21 October, about 14:25, on card
`nz-first-2019-the-frozen-site-shows-a-misread-total` (the frozen site's
NZ First 2019 total is $1,000 under its printed parts, Part A $52,325.00
and Part G $317,210.17; the Commission's own by-year figure agrees with the
parts): "15. fix now". An emergency fix to the frozen product under hard
limit 19: one commit to the old repository correcting that published
figure, drafted from the reference copy and applied by Arthur himself in
the live old folder; the next daily release is the proof.

77. Arthur, 21 October, about 14:25, on card
`a-donor-name-key-on-the-rebuilt-site-carries-a-residence-fragment` (the
frozen site's fold of one filed donor name keeps a residence fragment in
the donor page's file name and the picker; the rebuilt side is already
clean by site-3's name-keys gate): "16. fix now". An emergency fix under
hard limit 19, and first of the two because it is a live hard-limit-15
exposure: one commit to the old repository so the fold drops the fragment
and the donor page and picker regenerate clean, drafted from the reference
copy and applied by Arthur himself; the next daily release is the proof.

A note on 76 and 77 (integrator, 22 October, 05:13): applied in the old
repository as aefd8d0b (77: a ledger correction reaches a candidate return's
rows), 6ff4b228 (76: a total correction may set the declared total and Part
G) and 7f4a88c6 (the two ledger lines), by Arthur's run of the integrator's
script. 77's row was a 2020 Manurewa candidate-return row whose donor name
the old reader took from the cell's residence line, not the Labour
party-return row the first draft named; that row was already clean. Proof
is the 06:19 release on 22 October: published 06:29, no donor file or picker entry carries a residence word, and NZ First 2019 reads $369,535.17 (checked by the integrator from the release folder).

78. Arthur, 21 October, about 18:20, while the integrator was gating
sanctions-1, unprompted: "forget about capturing the beehive and hansard
I have a 3rd party source". Neither www.beehive.govt.nz (the ministers'
diary releases, step 6.2 template 4(a)) nor Parliament's Hansard pages is
captured by the estate; the diary register and the Hansard register are
built from a third-party source Arthur supplies. Its name, its terms and
its legal position (ruling 61, the four questions) wait on him naming it;
until then the two registers are not held. Closes diaries-1's queue item
`may-we-ask-the-beehive-to-let-the-diaries-reader-through` with no letter,
its blocker card `the-beehive-s-wall-refuses-the-diaries-reader`, and the
Office of the Clerk letter in the letters queue item; the step 4 line on
Hansard's challenge (held at 23 September) closes the same way: no
permission request is sought.

A note on the clock in 75 to 77 (integrator, 21 October, 20:40): their
"about 14:20" and "about 14:25" are the relaying session's estimate, which
it later said ran slow; the commit that recorded them (02b1cce) is
timestamped 13:41 NZDT. Neither clock is firm; the order of the rulings is.

79. Arthur, 22 October, about 08:40, in three sentences while working
through the integrator's list: "let's hold this to after the build" (the
track H sittings, the deploy token's rotation first: the runbooks from
security-1 stand, no rotation before the build closes); "2 can wait till we
have the other box" (the diaries source under ruling 78: template 4 stays
not held until node1 is in service); and "no document reading proceeds
until we have both boxes up". So: every lane may survey, write its
position and capture; no reading of documents by a model (the read stages,
the trials, the Waitangi Tribunal reports' question) starts until node1
is in service beside node2.

80. Arthur, 25 October, about 12:00, on how the board shows connections,
after the integrator proposed a connection graph as a further pane: "if
we make it a pane the board will get cluttered. Let's do this. Let's make
the current pane the basis of the 'search' tab. Let's give each register
a check box, and searching searches all checked registers. Let's have a
'search all' check box at the top. Search results appear in an adjacent
pane in the same tab. This pane should be wider and show all information
that comes up under each register entry, grouped by register with the
search term highlighted. Let's make the graph search tab show connections
between register entries, with register entries as nodes and the
connections, or edges colour coded with a key below the display." Earlier
in the same talk: "this is just for the querynz board" (not the public
site), and the whole thing is a change of mind about how links are shown,
not about how they are made. So: the board gets two tabs, search and
graph; a register row is a node; a connection is an edge typed and
coloured by what the register says (money, role, candidacy, declaration,
dealing, the links' same-person verdicts); the key sits below the
picture. Recorded under step 4.9 as its second version; built by
`board-2` in `products/board/` only.

81. Arthur, 25 October, about 14:10, after seeing the board's two tabs:
"default in the search all pane should be all unchecked with search all
checked. This means that a user can uncheck search all and then check
individual registers. they can check and uncheck search all without
losing their checked register selections". So, on both tabs: the first
view shows "search all" ticked and every register unticked; a search runs
over every held register while "search all" is ticked, whatever register
boxes are ticked, and over the ticked registers alone when it is not;
the ticked registers are carried through every search and every pane
opened, so turning "search all" off and on loses none of them; "search
all" unticked with no register ticked searches nothing and says so.
Replaces board-2's rule that nothing ticked means all. Built by
`fix-products-board-1`.

82. Arthur, 25 October, about 14:30, after a search for "graham hart"
found John Graham HARTNELL (each typed word begins a word in the row):
"I think what you are trying to do is different to what we are really
trying to achieve ... Let's make the search expandable and add some field
options that can be used to narrow a search. let's start with first name,
middle name, last name, address. you can choose 2 more fields that you
would like to add". The integrator chose organisation (a company, party,
charity or society name) and year. So, on both tabs: the search box gains
an expand control; open, it shows those six fields; each field matches
whole words in the columns that hold that thing (a surname column where
the register prints one, else a whole word of the name string); the plain
box is unchanged when the fields are closed; address searches the
registered addresses organisations publish, since no published table
holds a person's home address (hard limit 15). Built by the board fix
session after `fix-products-board-1`.

83. Arthur, 25 October, about 13:05, to the explainer agent (relayed to
the integrator 14:45): "I just made a request for a change and dont want
to interrupr the work. I want situations where fists and last name might
be reversed and addresses might only be a close match to be expandable at
the bottom of the search". So, on the board's search tab: below the exact
results a section "Near matches", closed until clicked, with two labelled
classes, a person name whose given name and surname are reversed against
the query, and an address that is a close but not exact match by the
estate's own address fold; never mixed with or counted in the exact
results; only addresses the published views already show, never a home
address (hard limit 15); nothing written. Rulings 82 and 83 are built
together by `board-3` in `products/board/` after `fix-products-board-1`
(ruling 81) merges.

84. Arthur, 25 October, about 16:30, on the board after board-3: "the
graph display is cluttered with overlapping text. 'name-only@1' what does
this mean? Let's list rather than overlap multi-cause edges". The label
was the links lane's rule id and version as `pub.links` carries it. So:
an edge never shows a rule id; the links' rules read in plain words from
a table in the board's catalogue (name-only@1 reads "same name, nothing
else"); two rows joined by more than one connection get one line, and the
causes are listed, not drawn over each other; no label is drawn over
another: each edge carries a number on the picture and the edges are
listed by number under the key, each with its kind, its words and a link
to the row that asserts it. Built by the board fix session after
board-3.

85. Arthur, 25 October, about 16:45, on the field search's reading of a
one-string name: "where the registers do not have clearly defined first
and last name conventions, let both be eligible for a match under that
search field. there are some basic ingestion rules that may have bearing,
for example, mills phillip and phillip mills on a donation return should
be considered ambiguous about ordering, however, 'mills, phillip' on the
same form is not ambiguous because the comma indicates that 'mills' is
the last name. Many registers will have clear conventions, and normal
text will use normal ordering, except in the case of the indicative
comma". So: a comma reads family name then given names everywhere; a
view with a convention (a surname column, or a form that fixes the order)
is matched by it, stated once per view in the board's catalogue as data;
a one-string name with no comma in a view with no convention is
ambiguous, and the first-name and last-name fields each match any of its
words, so "Mills Phillip" and "Phillip Mills" are both exact for last
name Mills, first name Phillip and neither is near; ordinary text reads
given name first. The near-matches reversed-name class applies only where
a convention exists and the row contradicts it. Replaces board-3's rule
(a first name never the last word, a last name never the first). Built by
the board fix session after ruling 84's.

86. Arthur, 26 October, about 05:50, four lines on the board: "switch
the interface to a night mode colour scheme"; "the numbered edges are
confusing"; "let's group the donations so that all donations to a
specific party are aggregated into a single node and a total given";
"Let's make it easier to find the originating document of a record". So:
(1) the board's pages take a dark scheme throughout, the edge colours of
the key re-chosen to read on it; (2) edges carry no numbers: an edge's
words are drawn only where they fit without touching another, every edge
still has its hover title, and the list under the key is grouped by the
far row's name, not by number (ruling 84's "listed, not overlapped"
stands; its numbering goes); (3) in the graph a donor's donations to one
party, across returns and years, are one edge to one party node labelled
with the total and the count, the returns listed under it; the same for
a candidate's donors to that candidate; (4) every row, in the results
pane and its own pane, carries a "source" link that opens the captured
document it cites (served by the board from the document store on the
local network, read only, with the page named) beside the publisher's
own address where the view holds one. Built by `board-4` in
`products/board/` after ruling 85's fix.

87. Arthur, 26 October, about 06:40: "let's also add a tab that lists the
use cases". So: a third tab on the board, "use cases", listing the plan's
use cases from the plan's own table
(docs/plan/reference/registers-and-use-cases/the-sixteen-use-cases.md,
seventeen rows, read at render time from the copy the board runs from):
number, name, who it serves, the question it answers, the shape and the
step, in the plan's order; each row says which templates built for it
exist on the scan and which registers it needs are held or not held,
read from the published views. Nothing written. Built by `board-4` with
ruling 86.

88. Arthur, 26 October, about 07:20, on the queue item
`which-captured-documents-the-board-may-open-whole` (no default; board-4
opened only the House and expenses documents under hard limit 15):
"because the interface we are building here with the Querynz board is
internal only we can display the addresses". So: on the board, and on the
board alone, the "source" link opens every captured document the store
holds, whole, the addresses it prints included. This is an exception to
hard limit 15 and is written into the limit's own text in
docs/plan/limits.md and CLAUDE.md. What does not change: the board stays
on the local network (hard limit 13); no published table and no export
carries a home address; a session, card, lesson or log never prints one
(hard limit 11); the public site and every other product are untouched.
The queue item closes. Built by the board fix session after board-4.

89. Arthur, 26 October, about 08:10, on the use-cases tab: "let's build
out the use cases that we have all the required records for. Let's make
the name a link that opens the usecase interface in a new tab in the
browser so we can isolate use case interfaces from the querynz board
interface". The integrator's finding at the time: every use-case
interface the plan has built already exists as a template on its shape
(ten subject-report templates in products/templates/, use cases 2 to 8,
11 to 13, on the report server at port 8440; three scan templates for 9,
10 and 14 on port 8450; Follow the Money as the site preview on port
8430), but the tab saw only the scan's templates, and by the plan's own
reference no subject-report use case has every named source held (OpenLaw
and the tribunals wait on letters and lanes). So: each use-case name on
the tab is a link opening that use case's interface on its own server in
a new browser tab (the report template's page, the scan's page, the site
preview), the tab counts the report templates as built, and a use case
with no interface yet says what holds it (ruling 79 for 15, ruling 63 for
16 and 17). "Build out" beyond the links waits on the sources each use
case still lacks, which the tab names. Built by the board fix session
after ruling 88's.

90. Arthur, 26 October, about 08:25, told the product reader login is
capped at 10 connections of the database's 100: "allow the full 100
database connections. for my diagnostic use please put a database
connection counter in the querynz board nav bar". So: the new estate's
logins carry no connection limit of their own (qv4_product and qv4_read
set to no limit by Arthur as the database's superuser; the database's
max_connections of 100 stands as the only cap); and the board's nav bar
shows on every page the connections in use over the maximum, with the
count by login on hover, read from pg_stat_activity on the board's own
connection. Built by the board fix session with ruling 89.
Done 26 October 10:05: Arthur set qv4_product and qv4_read to no limit;
confirmed from pg_roles. qv4_owner keeps 20 (the jobs' own cap) and
qv4_oldread 5.

91. Arthur, 26 October, about 10:05, after the integrator flagged that the
explainer agent had proposed an SSH alias in his ssh config pointing at a
deploy key in the credential directory, so that its commands never name
the directory: "I am comfortable with the explainers actions but will
speak to you going forward about these things. I was just looking for
parallelism and didnt want to interrupt your work". So: an SSH alias
whose IdentityFile is a key in the credential directory, written by
Arthur himself, is an accepted pattern under hard limit 1 (the key never
leaves the directory, nothing secret passes through a session); the
explainer's read-only clone of the ingest repository (its name struck under
ruling 92) and its reading on the MCP queue item stand; instructions for the estate come to
the integrator directly, and a message never interrupts running work.

92. Arthur, 26 October, about 10:10, eight lines handed to the integrator
to run "as parallel as possible", with "a report at the end that answers
all questions and give a status update": (1) "for the graph, I see we
have the returned search matches as yellow nodes with edges showing the
connections that these have. Let's put the search match nodes in a
horizontal line so they dont have so many intersecting edges in the graph
display. Let's expand it more like a family tree both up and down to
reduce clutter, using right angle intersections." (2) "in the search
result's companies display like this: companies/9429050975815. We want a
company name" (3) "are we showing removed companies as removed still? Are
we surfacing results for removed companies?" (4) "The search bar needs a
new button that offers a 'near match list that includes colloquialisms'.
this means that 'garry payinda' can show options like garreth payinda.
These can be added as search terms" (5) "Let's make the name of a
register clickable to open a table of the register. 100 rows to start
with with additional rows expandible. Each row should be one line.
searching open a new pane with the results in between the search and
table display." (6) "Let's make a selector in the search pane that allows
the extra fields to be restrictive or permissive. ie 'and' fields or 'or'
fields" (7) "the subject reports ask for a 'register:key, as the board
names a row' i dont understand what this means" (8) "delete and remove
all references to [the explainer's ingest repository on GitHub],
including credentials". So: items 1, 2, 4, 5 and 6 are board builds
(sessions board-5 for the graph, board-6 for the search, in parallel from
the same main); item 7 is a report fix (the start page searches a name
and never asks for a row reference; the reference stays in the address
for the board's link); items 3 and 7 are answered in the integrator's
report; item 8 withdraws the part of ruling 91 that let the explainer's
clone stand: the clone is deleted, the repository's name and address are
struck from ruling 91 and from the MCP queue item's 26 October update
(the reading itself stays, unverified, as the queue item's record of what
was seen), the deploy key and its SSH alias are removed by Arthur (they
are his, in the credential directory and his ssh config), and the key is
revoked on GitHub by him. Two merged commits of 26 October still carry
the name in their messages and diffs; rewriting them is a force push,
which the integrator does not do without Arthur's word, so they stand as
history.

93. Arthur, 26 October, about 14:55, on ruling 92's item 3 (the
integrator's report that the board returns every removed company with "status Removed" among its
fields and nothing in the title): "let's add a check button to show
removed companies. Dont display them by default". So: the board's search
pane gets a check box "show removed companies", unticked on the first
view and riding every href like the register ticks; unticked, a company
whose status reads as removed (the status words declared as data in the
catalogue: removed, deregistered, dissolved, closed, case folded) is
left out of the search results, the near matches, the register table and
the graph's matched nodes, and the companies count says how many were
hidden; ticked, every row returns as before. A row pane opened by its
own link still opens whatever its status, since the link names the row.

94. Arthur, 26 October, about 15:50 to 16:00, setting up the ingest MCP
(the Hermes VPS's `query-nz-ingest` server, version 0.2.0, corpora of
beehive.govt.nz and parliament.nz captured and read on that box, outside
the estate) on node2: "i am setting up the mcp on this machine … This
needs to be set up on node 1 when we get it back"; "this is a source
that you will regularly call to get its content"; then the four steps
(an SSH tunnel to the VPS forwarding 8642, 8644 and 8646 to the inner
box; a user unit for it; `claude mcp add --transport http query-nz
http://127.0.0.1:8646/mcp`; verify through the MCP). So: the MCP is a
source lane of the estate, third-party (ruling 78): a `qv4-` job will
call it on a schedule, land what it serves in the document store by
hash and load tables from it; no estate job calls its extraction (hard
limit 10); a legal position from the four questions is written before
any product shows its content (ruling 61), recording that the capture
happened off-estate and, for parliament.nz, through a challenge the
estate's own capture may not pass (hard limit 6). Done on node2 by the
integrator: the tunnel unit installed as `qv4-mcp-tunnel.service` (hard
limit 23) in the user systemd folder, Arthur's three forwards with
keep-alives, enabled, lingering; Arthur put this box's key on the VPS
(`ssh-copy-id`) after the unit was refused with the password login the
test tunnel had used; the MCP registered for Claude Code in the project
directory only (local scope; nothing in the repository). Proven: health
`{"status":"ok","corpora":6}` through the tunnel; the MCP's handshake
and tools/list answer (corpora, records, search, get, measure). At 16:10
Claude Code's own client connected (3 s, after one timed-out try), and
the tools answer: `search` for one word in 45 s, `records` for one
beehive record (of 45,418) in 34 s, `measure` at once; `corpora` gave
only keep-alive pings for 40 s. The server's calls are slow on its own
side; handed to Arthur for the VPS. The same setup is owed on node1 when it returns, after
the fence (the unit, the key on the VPS, the registration); the queue
item `an-mcp-for-the-parliament-and-beehive-sites` is closed by this
ruling once the lane is briefed.

95. Arthur, 26 October, about 16:25, after the MCP came up: "what I want
you to do is get new records from it when they arrive. It should tell
you. you are going to need to categorise these as sources. they come from
parliament.nz and also beehive.nz. we already hold many of them. they
have done some processing on them so we might want to capture this.
There might be more there than we have in our records. you should let me
know before we decide on an ingestion strategy". So: no lane is built
until Arthur has seen the survey and ruled the strategy. The integrator's
survey, 16:40 (through the tunnel; the slow calls of 16:10 were the
server under 13,495 arrivals in a day, and answered in a second at
16:40): six corpora, 737,190 records. beehive 45,705 (releases, speeches,
features; 1999 to 2026; per record the ministers and portfolios as the
site tags them, the body text, and two fields their model made, topics
and quotes). parliament-written-questions 683,770 (the Parliament API's
own fields: question, reply, member, minister; October 2024 to October
2026; no model). parliament-bills 92 (the API, most fields empty).
parliament-diaries 5,000 rows (minister, date, time, meeting, location,
attendees, portfolio, read from the monthly PDFs; May to August 2026
only: template 4(a)'s register, which the Beehive's wall refused this
estate, ruling 79's diaries lane). parliament-hansard-index 371 (a
sitemap of Hansard pages with dates; no text). parliament-wayback 2,539
(archived parliament.nz pages, 2006 on, text only). Arrival: there is no
push; `corpora` reports each corpus's cursor, the arrivals in the last
day and the newest arrival, and `records` pages from any cursor in
arrival order, so a lane polls and pulls from its last cursor. What the
estate holds: no Beehive document (the diaries lane was blocked at the
wall) and 21 parliament.nz documents (MPs' interests); the old estate's
database holds claims read from 54,826 Beehive pages (52,954 releases)
and 137 parliament.nz pages, September to October 2026, which stay
there (hard limit 18) and are not a source for the new lane. The
decision Arthur owes is in the queue item
`an-mcp-for-the-parliament-and-beehive-sites`.

96. Arthur, 26 October, about 18:30, on the survey of ruling 95: "I want
to ingest everything they have. we should add their fields to our
registers. we are going to abandon the claims from the old estate. We just
want the records. We should ingest the hansard records we currently have
and add the fields from the MCP and use the MCP for updates. I dont care
what comes in first. I want everything". So: every corpus of the MCP is
taken, in no order, each record landed whole as a captured document (its
JSON by sha256, named by corpus and record id and by the page's own URL;
a record the MCP later returns changed is a second document under the
same names: one frozen reading each). The lanes, one per site as Arthur
categorises them: `registers/beehive` (the beehive corpus: releases,
speeches, features, the site's ministers and portfolios, and the topics
and quotes their model made, kept as the source's own annotation, cited
as such, never a claim or a link); `registers/parliament` (written
questions, bills, wayback); `registers/ministers_diaries` (the
parliament-diaries corpus, template 4(a)'s register; its PDFs are the
Beehive's monthly releases); `registers/hansard`. The shared piece is
`support/mcpsource`: the client over the tunnel, a cursor per corpus, and
the job `qv4-mcp-pull` (hard limit 23) that polls `corpora` and pulls
`records` from each cursor, 200 a page, one request at a time, nightly
off-peak after the first pull. Hansard: the old estate's register is
exported once by hash the way the Gazette's was (the news database's
`hansard_sections`, 3,923 sections of 137 sitting days, 20 November 2024
to 23 September 2026, 47,243 speech turns, with `hansard_members`, 394;
and the canonical database's `registers.hansard_speeches`, 11,627 rows,
128 speakers), and the MCP's `parliament-hansard-index` fields (url,
lastmod, fetched) are joined to it by URL; updates come from the MCP.
Said plainly to Arthur: that corpus carries no text yet, only which
Hansard page changed and when, so the speeches stay held at 23 September
until the MCP carries text. The old estate's claims read from the Beehive
and parliament.nz pages (ruling 95) are abandoned: the new estate never
consumes them; they are not deleted (hard limit 18 is a separate word).
The old estate also holds the text of 55,358 Beehive pages and 3,012
parliament.nz pages in its news database, which Arthur did not name; the
integrator's default, from "we just want the records", is to export those
once by hash too, as the beehive and parliament lanes' last tranche,
MCP fields joined by URL where the MCP holds the same page; Arthur may
strike it. Ruling 79 is untouched: no model reads anything here, the
records arrive structured. Hard limit 11: the pull is a job, never a
session; a session sees samples. A one-page legal position per site
before any product shows them (hard limit 9, ruling 61), recording that
the capture was done off-estate (ruling 78) and, for parliament.nz,
through a challenge the estate's own capture may not pass (hard limit 6).
Sessions: `mcp-1` (support/mcpsource, registers/beehive) and `hansard-1`
(the export) launched together at 18:40; `parliament-1`, `diaries-2` and
`hansard-2` (the index join) after mcp-1 merges. The queue item
`an-mcp-for-the-parliament-and-beehive-sites` closes with this ruling.

97. Arthur, 26 October, about 18:55, while mcp-1 and hansard-1 ran:
"let's start ingesting the old estates beehive and parliment pages. We
will just add the unheld fields and records from the MCP". This turns
ruling 96's last tranche into the base: the old estate's pages are the
record, the MCP adds the fields they lack and the records the old estate
never held. What the old news database holds: 55,358 Beehive pages
(53,459 releases, 1996 to 22 October 2026; 1,853 `node` pages, 2000 to
2016; 35 speeches; 11 files) and 3,012 parliament.nz pages, of which
2,892 are the Hansard transcripts hansard-1 already exported (the same
pages, read into sections) and 120 are Ombudsman PDFs under
ombudsman.parliament.nz, left for a lane of their own if wanted. So the
parliament half is done by hansard-1's export; the Beehive half is the
beehive lane's first tranche, exported once by hash the way the Hansard
and Gazette were, with the MCP's beehive fields (ministers, portfolios,
topics, quotes) joined by URL and the MCP's records loaded only where the
old estate holds no page. mcp-1 was mid-build and cannot be redirected;
`beehive-2` is briefed so at its merge. The fetch gate now holds
hansard.parliament.nz and parliament.nz (ruling 78) so that the hansard
position's hosts line opens nothing.
    Provider's reply, 26 October about 20:25, verified by the integrator
    through the tunnel at 20:31 (seven corpora; the tools now `corpora`,
    `records`, `changes`, `search`, `get`, `measure`): (1) a corpus
    `parliament-hansard-debates`, one record per sitting day, the daily
    PDF's URL, sha256 and capture block, the sitting date, the whole day's
    text as pdftotext -layout gives it, the page count; no split, nothing
    derived; back run from 20 November 2024 filling (127 of about 250
    days at 20:31), then a daily tick; (2) `changes(corpus, since,
    cursor, limit)`: every record arrived or changed in place after a
    stamp, ordered by updated_at then seq, paged; (3) a uniform `capture`
    block on the API corpora with whatever was recorded (written
    questions and bills have none: pure API mirrors). For the estate: the
    client's re-walk for changed records is replaced by `changes`, and
    the seventh corpus is pulled, in a fix of support/mcpsource after
    mcp-1 merges; hansard-2 then reads the debates documents into the
    hansard lane beside the old transcripts, and the register grows past
    23 September when the House sits again.

98. Arthur, 26 October, about 21:50, after the integrator listed the jobs
that need a card: "I want to replce qwen with
ornith-ai/Ornith-1.5-35B-A3B-GGUF at q4_K_M". So: the text-reader and
review profiles (step 2.15) serve Ornith 1.5 35B-A3B at Q4_K_M in place
of Qwen 3.6 35B-A3B; the embedding and page-reader profiles are
untouched. What the hub says (read 21:58): MIT licence; a mixture of
experts, about 35B with 3B active, the Ornith family built on Qwen 3.5
and Gemma 4; Q4_K_M 21.7 GB and a 903 MB image projector; a reasoning
model whose turn opens with a think block, served with the qwen3
reasoning parser and a modified Qwen chat template, no documented way to
turn thinking off; recommended temperature 0.6, top_p 0.95, top_k 20;
native context 262,144; its claims are coding-agent benchmarks against
Qwen 3.6 35B-A3B, vendor-reported. Said to Arthur: the text-reader
profile runs with thinking off and temperature 0, and whether this
model's template honours that is measured at the swap, not assumed. Done
by the integrator: the Q4_K_M weights fetched once through
support.trials.models' downloader to /mnt/hdd2/qv4-models/ornith/ (hash
checked against the hub, one line in downloads.jsonl); a fix session on
support/scheduler swaps the two profiles (absolute weight paths, served
name `ornith-1.5-35b-a3b-q4km`, memory re-measured at 50000x2 on card 1,
the thinking switch measured, the probe jobs' one real call each), the
plan's model table and map follow at the merge. Every swap is recorded
(hard limit 25). Ruling 79 is untouched: a probe is one call, not a
reading.

99. Arthur, 26 October, about 22:05, ten minutes after ruling 98: "hmm.
maybe i've changed my mind forget about ornith". Ruling 98 is withdrawn
before anything landed: the download stopped at 15 MB (no line in
downloads.jsonl; the scope hook refuses the integrator a delete outside
the repository, so the partial file under /mnt/hdd2/qv4-models/ornith/ is
Arthur's to remove), the fix session
fix-support-scheduler-1 stopped before it edited anything and its copy
and branch retired, card 1 untouched, profiles.toml unchanged. The
text-reader and review profiles stay on Qwen 3.6 35B-A3B Q4_K_M as step
2.15 names them.

100. Arthur, 26 October, about 23:05, after the integrator compared the
board's graph with the old estate's ("in v3 we had a more attractive
looking graph"; the old one was Cytoscape with the cola force layout in
the browser, round nodes coloured by type, soft curved edges, tap to grow
a neighbourhood, drag, zoom): "abandon ruling 80." The integrator's
reading: what is abandoned is the rule the board carried from ruling 80
that it runs with no script ("still no script", step 4.9's second
version). Ruling 80's two tabs, the register check boxes, the results
pane and the graph tab itself stand, since rulings 81 to 93 were built on
them; Arthur says so if he meant more. So: the board may run script, on
the local network only (hard limit 13), served by the board itself from
its own folder, a vendored library at a pinned version with its licence
file beside it, never a request from the page to anything off the box
(hard limit 10's spirit: nothing of the estate's leaves). The graph tab
takes the old estate's interaction model and look (Cytoscape and cola as
v3 used them, read from the reference copy): round nodes coloured by
register with the label beneath, soft curved edges in the key's colours,
tap a node to grow its one hop and tap again to fold it, drag, zoom and
pan, the centre ringed; the rows and edges from a JSON answer built by the
same `graph.build` (published tables only, every edge cited by its
asserting row, never an address edge, suppression as before). The
server-written SVG stays as the picture for a browser without script and
the layered layout (ruling 92 (1)) gives every node its first position,
with a control that lets the force layout spread it; the key and the
cited edge list under the picture stay (rulings 84, 86); the dark scheme
(86 (1)) stays and the contrast test covers the node colours. Session
`board-7`.

101. Arthur, 27 October, about 08:35, on parliament-1's default that its
published views carry no question or reply text: "its published views
carry no question or reply text - isnt this the whole point?" So: the
text is published. `pub.parliament_written_questions` carries the
question and the reply whole; the lane runs an address-shape check over
both at the load (the street, legal-description and numbered shapes the
Gazette lane cuts on, hard limit 15) and a row the check hits has its
text withheld in the view with the reason, the whole text kept in the
lane's table, the count reported by key. The same for the archived
pages' and committee papers' text where the API gives it. Closes the
queue item `publish-the-written-questions-question-and-reply-text`.
Built by fix-registers-parliament-1 on parliament-1's branch before it
merges.

102. Arthur, 27 October, about 08:40, on the integrator's reading that
hard limit 15 bars a written question's text from a published view:
"Hard limit 15 is only for use cases, not for the querynz board". So the
limit's reach is restated in CLAUDE.md and docs/plan/limits.md: it binds
the products (the use cases), the public site and every export, not the
board and not the published views. A published view may carry a text or
location column whole, with a flag beside it where the value's shape
names an address (the Gazette lane's three shapes), and each product
applies the limit at its own surface by that flag; the board shows the
text whole. Ruling 101's withholding in the view is withdrawn: the
parliament lane publishes the question and reply whole with the flag
(fix-registers-parliament-1 relaunched); the ministers' diaries lane
publishes the 3,211 held-back locations whole with flags for "names a
home" and "a street address with no place of business" (a fix on
diaries-2's branch before it merges), and its queue item
`may-a-diary-entry-show-a-bare-street-address` closes: on the board yes,
in a product by the flag. The diaries corpus begins on 1 October 2017
because that is where the Beehive's releases begin: Cabinet's policy of
December 2018 made the monthly releases from January 2019 and some
ministers released earlier months back to October 2017; the provider
holds what the site published, and the lane holds everything its source
holds.

103. Arthur, 28 October, 07:05, on the scope hook's refusal of the
integrator's memory file (Claude Code's per-folder notes under
`~/.claude/projects/-home-user-querynzv4/memory/`, outside the repository
and so outside the fence): asked why, offered the lesson instead, took it,
then on learning the folder exists and holds the old estate's 80 notes:
"I want you to be using that memory". So the fence opens that one folder
to a founding or integrator session, the folder Claude Code keeps for the
checkout the session runs in (`fence.MEMORY`); a build, fix or question
session is unchanged. The morning's lesson stands with its last paragraph
reworded. Making the V3 and V4 folders one is Arthur's own line in his
terminal, handed the same morning.

104. Arthur, 28 October, 07:55, on the line that would make the V3 and
V4 memory folders one: "we dont need any notes from v3 we have those.
that is deprecated". The line is withdrawn. The V4 memory folder is the
only one a session keeps; the V3 folder is left as it is and never
merged, linked or read for the new estate.

105. Arthur, 28 October, 09:20, on the board's graph: an entity state,
switchable and separate from the rows graph, that collapses a search's
rows into entities by the links lane's own groups ("collapse all rows
using the rules in the links lane. At least all rows we are able to
collapse. We also want to see where near-links exist"). The integrator's
design agreed: one node per `pub.groups` group, a lone row shown as a
lone row, record relations lifted to the group, near links as dashed
edges with their reason, contested groups marked, tap to open a group as
a compound node of its rows; the board reads `pub.groups` and `pub.links`
and makes no link by looking. Two decisions taken with it: (1) the group's
label is the fullest filed name among its rows, a display choice the pane
says is not a link, until the lane publishes a name; (2) near links reach
one hop from the entities in view. Built by board-8.

106. Arthur, 28 October, 10:05, on the first three links rules developed
from the near pairs ("let's develop some links rules as we go"): "1.
confirm. 2. confirm. 3. confirm, make a new link rule to cover this".
(1) A donation row's organisation name matching exactly one company on
the register, live in the donation's year: confirmed to that company.
(2) Two companies under one name where one carries a year in brackets,
with at least one person confirmed on both: a "succeeded by" relation
between the two companies, not an identity; the companies stay separate
entities and separate groups, and the board shows the lineage as a frame
around them, the companies in date order, the shared people drawn once.
The name pattern alone stays near. (3) One candidate name under one
party in two elections: confirmed as one person, with the seats and years
as evidence; a new rule, not the near printing rule. The method stands:
a rule is proposed from a measured gap with its count and twenty pairs
read on the board, Arthur rules, the lane implements it versioned with
tests, the groups rebuild. Built by links-3.

107. Arthur, 28 October, 12:03, on the gap links-3 measured and queued
(`one-company-of-several-live-in-the-donation-s-year`: thirty donor rows
whose organisation name matches several companies, exactly one of them
live in the donation's year): "do this". A fourth rule: where several
companies carry the name and exactly one was live in the donation's year,
the donation row is confirmed to that company; where none or more than
one was live, the pair stays near with the reason. Built by a links fix
after links-3 merges; the queue item closes with it.

108. Arthur, 28 October, 12:10, on the board's results pane: "let's bring
the rows and entities to the results pane. Also, for the general search
lets have tabs in the pane that allows us to see row entries for each
search field ie. rows that match first name, rows that match address, etc.
Let's group these by register, collapsed with a number of results
displayed, and expandible so the rows can be seen. Same for the 'any field
may match' setting of the narrow by field fields. For 'all fields must
match' we dont need to be able to select between field match tabs in the
results because it is redundant. Let's also enable entity search and when
the results appear in the results pane let's allow clicking a result to
open the graph pane to the right". So: the rows and entities switch of
ruling 105 governs the results pane as well as the graph; the results of
the search box, and of the fields under "any field may match", are shown
under one tab per matching field, each tab grouping its rows by register,
collapsed to a count and expandable; "all fields must match" keeps the
one list; a search finds entities (the links lane's groups) as well as
rows; and clicking a result opens the graph beside the results, to the
right, centred on it, which extends ruling 100's script from the graph
tab to the results page. Built by board-9.

109. Arthur, 28 October, 16:20, on the fifth rule proposed from the
Christopher & Banks case (two companies under one name with no year in
brackets, one removed in December 2024 and the other registered in March
2025, the same people on both): "name the companies with your current
convention with '(delisted/refiled same year)'". The integrator's reading:
the pair is a succession like the year-in-brackets pattern (ruling 106
(2)), and its relation is labelled in Arthur's words, "delisted/refiled
same year", where the board and the report print the relation; "same year"
read as within twelve months of each other, either order of removal and
registration, so that the case that raised it falls in. The rule needs a
person confirmed on both companies, as successor-name@1 does; the name
alone stays near. Built by a links fix.

110. Arthur, 28 October, 16:35, on the entities results of ruling 108:
"'matching here: Arthur William YOUNG, Arthur William YOUNG, Arthur William
YOUNG, Arthur William YOUNG, Arthur William YOUNG and 5 more' listing the
matches isnt helpful because they are all the same name. remove this from
the entities result display. Let's bring back the dossier and open this
under the graph". So the "matching here" line leaves an entity result; and
the dossier of the old estate (gui/src/components/DossierView.tsx in the
reference copy: one page for one entity, its names as seen, its claims with
their sentences, its roles and companies, its money as a time series, its
namesakes, its enterprise members) comes back on the board as the board's
own pane for an entity, built from the published views and the links
lane's tables alone, and opens under the graph when a result or a node is
chosen. Built by board-11.

111. Arthur, 28 October, 16:39, on the results pane after ruling 108 and
the dossier of ruling 110: "we dont need the rows section in the results
pane because your handling of the entities section was so elegant. All
rows will be visible in the dossier. We also no longer need the graph tab
at the top navigation". So the results pane lists entities only (groups,
then lone rows as single-row entities), in every state; the rows and
entities switch governs the graph alone; a row is reached through its
entity's dossier; and the graph tab leaves the top navigation, the graph
living beside the results (108) with the dossier under it (110). The graph
tab's address still answers, redirected to the search page with the graph
open, so a saved path keeps working. Built by board-12, after board-11.

112. Arthur, 28 October, 16:43, on the results pane: "at the top of
results, let's have an expandable 'collapse' section that opens collapse
options. These let us collapse rows based on criteria like shared names".
So the results pane carries, above the entities, a closed section
"collapse" that opens to a fixed list of criteria a reader may tick to
fold the entities further for this view: a shared first and last name, a
shared full name, a shared registered address, a shared official number,
and the links lane's groups (the default, always on). A collapse chosen
here is a display choice for this page, said as such on every folded
entry, never a link and never written: the links lane's rules alone make
links (plan 4.9), and the dossier of a folded entry shows its members as
the entities they are. The address carries the chosen criteria. Built by
board-12 with ruling 111.

113. Arthur, 28 October, 18:12, on the merge gate's twenty-five minutes
("why does it take so long?"): "the idea of the service architecture was
to enable things to be changed in isolation without the need to test
everything". So the gate at a merge runs the fast tier for the whole
repository (the contract tests, the one-way import test, the spec and
reading-limit checks), then the slow tests of the modules the branch
touches and of the modules that read what they publish (a change to a
lane's publish.sql, pane.md, tables.sql or profiles runs the slow tests of
links/, checks/ and every product), then the staging load. A branch that
touches support/, bin/, .claude/, the root tests, the plan or the test
configuration still runs every slow test, because everything imports or
runs through those. Every other slow test runs in the nightly full tier,
as the plan's table already has it. The plan's row for the gate is
reworded to say this.

114. Arthur, 28 October, 20:07, shown that the links lane reads 21 of
the published views and the ones it does not ("are there any other
registers that are not in the links lane?"): "do the links fix for the
people views and organisation registers. Card the mixed views rule". So
one links fix reads into the lane's rows the eight people views it left
out (charity officers, Gazette celebrants, Gazette receivers and
administrators, limited partnership partners, party board roles, local
election candidates, building practitioner decisions, councillor
interests) and the three organisation registers (charities, societies,
limited partnerships) as bodies the organisation rules may confirm a
donor's organisation name to, by the same one-body-live-in-the-year test
the company rules apply; the measurements are run again and the review
agent's switch stays off until it is scored on the charities officer
pairs (links/measurements.md). The views that name people and bodies in
one column with no split (court judgment, FMA, WorkSafe, Commerce
Commission and Overseas Investment parties) wait on a rule for telling a
person from a body, carded, not built.

115. Arthur, 28 October, 20:20, told that three jobs died overnight for
guessed memory figures and were measured and corrected by hand the next
morning: "we should be doing this at the time of failure and then
rerunning the job if the failure is trivial". So a job stopped at its
memory ceiling is not left failed for a session to repair: the worker
records the peak it measured, raises the job's working memory figure from
it (the raise and the measurement logged, kept outside the repository so
the next run uses it, and shown by the scheduler report until the
integrator folds it into jobs.toml), and queues the job again at once, as
long as the raised figure fits the box's budget and the job has not been
raised twice already for one failure; past that, or for any other failure,
the job stays failed and red as now. A trivial failure is one the
scheduler itself caused by a figure it holds; a job's own error is never
re-run by this.

116. Arthur, 28 October, 20:33, told that no MCP-fed view (Hansard
speeches, written questions, Beehive releases, ministers' diary releases)
joins a member row, and offered a links rule of the seat-and-window kind:
"add this to the other links lane work and do it". So the links lane gains
a rule confirming a speech turn's, a written question's asker's and
answering minister's, a Beehive release's tagged minister's and a diary
release's minister's printed name, honorific stripped, to the one member
sitting in the House on that day (`pub.members` by its from and ended
dates); several or none stays near with the reason. Measured first as
ruling 106's method asks and built in the links fix that follows
fix-links-3 (ruling 114) in the same copy. The list members who filled a
vacancy after an election are missing from `pub.members` (card of 28
October) and are the expected abstentions until the house lane carries
them.
