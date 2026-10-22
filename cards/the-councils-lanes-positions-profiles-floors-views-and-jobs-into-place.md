# The two councils lanes' schemas, positions, profiles, floors, views and jobs into place
kind: blocker
state: closed
closed: 2026-10-23
use-case: none (step 6.3)
session: councils-1
opened: 2026-10-22

For the integrator at the merge of `councils-1` (a session's fence keeps these out):

1. `support/db` `LANES`: add `council_minutes` and `councillor_interests` (neither has a private twin); apply.
2. Positions: move `registers/council_minutes/position/council-meeting-platform-infocouncil.md` and
   `registers/councillor_interests/position/councillors-registers-of-interests.md` to `docs/legal/positions/`, and
   `registers/councillor_interests/position/terms-read.md` beside the second as
   `councillors-registers-of-interests-terms.md` (it has no `hosts:` line; the position cites it); repoint
   `test_the_position_names_every_host_the_lane_asks` and `test_the_position_names_every_instance_host` at the moved files.
3. Profiles: append the lines of each lane's `profiles-proposed.jsonl` (five: two and three, version 1) to
   `support/profiles/profiles.jsonl`; remove the proposed files.
4. Gate floors: 5 s for `infocouncil.biz` and the four council-domain instances; nothing else (each council site's
   stated crawl delay is honoured by the gate).
5. Jobs: the four in the lanes' `jobs-proposed.toml`, with priorities; `support.scheduler check`.
6. Views: `pub.council_meetings`, `pub.councillor_interest_registers`, `pub.councillor_interests` on the board in the
   merge after this one (each lane's `views.md`).
7. Before the first run of either capture job, carry the session's capture record into the live schemas, once:
   `QV4_INTEGRATOR=1 python -m registers.council_minutes.capture --adopt scratch_councils_1` and the same for
   `registers.councillor_interests.capture` (proven into `scratch_councils_1_adopt2`: 948 minutes rows, 485 register
   rows, 1,060 documents re-landed from the store, a second adopt refused, a run after it asks for nothing). Without
   it the first nights fetch about 990 documents a second time.
8. Regenerate the queue, the card board and the lessons index.

## Closed (integrator, 23 October 2026, the councils-1 merge)

Items 1 to 5 and 8 done at the merge; the four jobs enter the catalogue
disabled, because a job new to the catalogue runs at once (card
`the-scheduler-s-worker-runs-the-main-checkout-s-working-tree-so-an-integrate-branch-s-jobs-ran-live-before-the-gate`)
and the adopt runs (item 7) must come first; the integrator runs both adopts
after the merge and enables the jobs in the records commit. Item 6, the three
views, in the merge after.
