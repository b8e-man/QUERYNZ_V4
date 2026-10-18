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

**Old rulings this plan still relies on,** by their number in `docs/records/DECISIONS.md`: 172 (no text to a cloud model), 203 (Papers Past is a search corpus), 217 (busy address), 220 (the watch on links; its "on Arthur's word" is replaced by ruling 41), 221 (the two confirming rules), 253 (ownership is a note), 193, 277 and 357 (the return is the record), 321 (fyi.org.nz), 333 and 347 (2019 onward), 349 (a renamed party), 351 and 356 (seven parties), 355 (no press row), 361 (a race is every year since the election before it, cut at the window; it replaced 358 on 16 October), 360 (for telling a person's name from an organisation's, the director register is the authority for given names).

## From 55


**18 October**

55. Node1 is out of the plan. "Forget about node 1 and everything we need it to do." Nothing waits for it: no re-measurement, no second half of a batch, no mirror, no standby, no push to it. Node2 is the estate. If node1 is ever brought back, that is a new decision, not a resumption.

56. A timer is an artificial blocker. "Anytime there is an artificial blocker like a timer, just fire the service or unit or module and keep things moving." Where the next step waits only on a clock (a release, a feed, a board run, a nightly load), start the unit by hand, use its result and record that it was a hand run. The plan's "wait for one scheduled release between batches" is read this way from here. A real blocker (Arthur's hand, a hard limit, a source that has not published) is not a timer. Said after batch 3 was stopped at 16:04 on the strength of the 13:34 release run by hand.

**18 October.** 57. Arthur to the scheduler session, on its queue item about a second worker on node2: "card the node 1 setup". node1 is to be set up as the estate's second box (`cards/node1-setup-as-the-second-box.md`), each line that touches node1 itself on Arthur's word. This narrows ruling 55: node1 is not waited on by anything in step 1, and nothing in the plan is owed to it until the setup card is worked; the two-box proofs of step 2 are owed on it then, not on a second worker on node2.

**19 October.** 58. Arthur to the windowed session, on both track E questions: "Decisions held - yes", the defaults are the rulings. Tenancy Tribunal orders are kept after the Ministry takes them down at three years and never shown: held in the document store by hash past their `unpublished_date`, the lane's tables carrying no name or address, nothing published; step 5's reading decides nothing about showing, and a ruling is owed before any product shows one. The lawyer reads the position before anything is sold.

59. No letter to the Real Estate Authority yet. The lane captures and holds its decisions as in-house use, which the Authority's terms allow; nothing is published. Before any product shows them: the lawyer says whether a Complaints Assessment Committee decision is a tribunal judgment under section 27 of the Copyright Act 1994, and if not, one letter to the Authority. `decisions.dotnous.com/robots.txt` says `Disallow: /`; under ruling 10 that is recorded, not obeyed, and it is in the position for the lawyer to weigh.
