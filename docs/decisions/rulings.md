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
