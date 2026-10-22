# The two councils lanes' schemas, positions, profiles, floors, views and jobs into place
kind: blocker
state: open
use-case: none (step 6.3)
session: councils-1
opened: 2026-10-22

For the integrator at the merge of `councils-1` (a session's fence keeps these out):

1. `support/db` `LANES`: add `council_minutes` and `councillor_interests` (neither has a private twin); apply.
2. Positions: move `registers/council_minutes/position/council-meeting-platform-infocouncil.md` and
   `registers/councillor_interests/position/councillors-registers-of-interests.md` to `docs/legal/positions/`, and
   `registers/councillor_interests/position/terms-read.md` beside the second as
   `councillors-registers-of-interests-terms.md` (it has no `hosts:` line; the position cites it); repoint
   `test_each_position_names_every_host_its_lane_asks` at the moved files.
3. Profiles: append the lines of each lane's `profiles-proposed.jsonl` (five: two and three, version 1) to
   `support/profiles/profiles.jsonl`; remove the proposed files.
4. Gate floors: 5 s for `infocouncil.biz` and the four council-domain instances; nothing else (each council site's
   stated crawl delay is honoured by the gate).
5. Jobs: the four in the lanes' `jobs-proposed.toml`, with priorities; `support.scheduler check`.
6. Views: `pub.council_meetings`, `pub.councillor_interest_registers`, `pub.councillor_interests` on the board in the
   merge after this one (each lane's `views.md`).
7. Regenerate the queue, the card board and the lessons index.
