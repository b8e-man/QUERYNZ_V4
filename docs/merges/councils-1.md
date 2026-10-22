# councils-1: step 6.3, council minutes (InfoCouncil) held unread, and councillors' registers of interests, council by council
branch: session/councils-1 (pushed; head 0201902)
session: councils-1 (Opus)
raised: 2026-10-23
claims: registers/council_minutes/ and registers/councillor_interests/ (capture, read, load, check, tables.sql, publish.sql, spec, pane, README, sample, sample.list, profiles-proposed.jsonl, jobs-proposed.toml, views.md, position/, tests); docs/status/councils.md; cards the-councils-lanes-positions-profiles-floors-views-and-jobs-into-place (blocker, for this merge), christchurch-s-infocouncil-listing-trips-the-gate-s-challenge-check, the-old-estate-s-council-minutes-pdfs-are-on-its-other-box, infocouncil-past-years-and-two-moved-instances, councillors-registers-held-as-pdfs-wait-for-a-reader, councillors-registers-the-capture-could-not-reach (findings); queue may-a-councillor-s-spouse-s-or-partner-s-declared-interests-be-shown (default applied), whether-to-capture-councils-whose-terms-bar-automated-access (no default); three lessons

## What each lane is

- **Council minutes** (`registers/council_minutes`; `pub.council_meetings`). The 24 InfoCouncil instances of the old
  estate's verified list. Each instance's listing (the year's meetings) is read by its grid's shape: council, body,
  date, time, kind, the council's code, and every document linked; the venue is never read. Minutes PDFs are landed
  by hash and never read (plan 6.3; ruling 79). Case 1 of 1.10: the old estate's listing of its 351 InfoCouncil PDFs is
  pinned (`2264a857…`); none of the files is on node2 (they are on node1), so the 347 that today's listings name are
  recorded with the old hash and never fetched again; `--copy-old` lands them when the box is back. The old estate's
  other 1,159 minutes were stripped text, not bytes, so they were fetched. Proven in
  `querynz_v4_sample.scratch_councils_1`: 21 listings, 1,347 meetings, 4,130 documents listed; the night of 22
  October 600 PDFs landed (601 requests, 5 s apart, 22:00 to 22:49, no block), 1 404; all 948 listed minutes
  accounted. Held: Christchurch (the gate's challenge check on a page that is not one: card for a fetchgate fix),
  Kāpiti and Hawke's Bay (404: moved). Check green: rows held against each grid's own row count.
- **Councillors' interests** (`registers/councillor_interests`; `pub.councillor_interest_registers`,
  `pub.councillor_interests`). No collected file exists. The 78 councils from DIA's list (data.govt.nz, `b6a3c710…`);
  each register's address found by web search (councils' names only), each page read through the gate; 47 terms
  pages read and cited by sha256. The night of 22 October: 387 register documents held for 42 councils, never read;
  Invercargill's structured register read (15 members, 56 category rows). Never read: real property (the queue's
  answer), homes, addresses, contacts, and a spouse's or partner's interests (new queue item, default no); an entry
  shaped like an address, email or phone is dropped. Held: 10 sites that blocked the survey; Auckland, South Waikato
  and Waimakariri, whose terms bar automated access (no default). Check green: all 78 councils, nothing withheld
  published.

Survey honesty: six asks in the survey went to a site already blocked, before the survey script learned to skip
them (lesson); the two that answered are held and nothing they returned is used. No challenge was solved, no login.

## For the integrator (the blocker card has the detail)

1. `support/db` `LANES`: add `council_minutes`, `councillor_interests` (no private twins); apply.
2. Move the two positions from each lane's `position/` to `docs/legal/positions/`, and
   `registers/councillor_interests/position/terms-read.md` beside its position; repoint each lane's position test.
3. Append the five profiles (`profiles-proposed.jsonl`: two and three, version 1); remove the proposed files.
4. Gate floors 5 s for `infocouncil.biz` and the four council-domain instances.
5. Jobs from each lane's `jobs-proposed.toml` (four; priorities yours).
6. **Before the first capture job**: `QV4_INTEGRATOR=1 python -m registers.council_minutes.capture --adopt
   scratch_councils_1`, and the same for `registers.councillor_interests.capture`, once: carries the session's capture
   record into the live schemas and re-lands the 1,060 documents from the store, so nothing is fetched twice (proven
   into `scratch_councils_1_adopt2`; a second adopt refuses).
7. The three views on the board in the merge after this one (`views.md` in each lane). `pub.councillor_interests`
   names elected members: off the public site unless Arthur says (hard limit 14).
8. Regenerate the queue, the card board and the lessons index.

## Fast tier

Each lane folder green (39 s with the fill). Whole repository, before the last fixes: red only on
`tests/test_generators.py` (generated files stale from the new cards, queue items and lessons; step 8) and on a
one-way import in my test, since fixed and rerun green. `docs/board.md` shows modified in the working copy
(rewritten by the fast tier; the hook refuses any touch of it); it is not committed. Target 300 s missed (585.9 s,
recorded).

## Result (integrator, 23 October 2026 00:25 NZDT)

Merged into main as 71cd2a6 (`merge integrate/councils-1: gate green`). Branch `integrate/councils-1` from `session/councils-1` (0201902), main merged, the integrator's commits through 5c7c6a7. Card `the-councils-lanes-positions-profiles-floors-views-and-jobs-into-place`, now closed: `council_minutes` and `councillor_interests` in the lane list, schemas applied on both databases; the two positions and the terms file (as `councillors-registers-of-interests-terms.md`) in `docs/legal/positions/`, both position tests repointed; the five profiles appended as version 1 (133 slugs), the proposed files removed; floors 5 s for `infocouncil.biz` and the four council-domain instances; four jobs at priorities 77 to 80, `support.scheduler check` green (74 job types). The jobs entered the catalogue disabled, because a job new to the catalogue runs at once from the main checkout's working tree (the worker finding card), and the adopt runs had to come first; after the merge the integrator ran both adopts (minutes: 948 capture rows, 3 held hosts, 4 set aside, 621 documents re-landed from the store; interests: 485 rows, 10 held hosts, 13 set aside, 439 documents re-landed; no request to any host) and enabled the jobs in the records commit. The council procurement lane's position test changed at this merge: the councillors' interests position names the same council hosts and the gate's host map takes the later file, so the test now checks its own hosts line. Fast tier: RED in 618 s only on that test, fixed and the lane rerun green; the gate's full tier is the whole-repository proof. The three views go on the board in the merge after this one; `pub.councillor_interests` names elected members and stays off the public site (hard limit 14). Arthur's to drop in the sample database: `scratch_councils_1`, `scratch_councils_1_adopt2`, and the lanes' test scratch schemas. Branches and worktree retired.
