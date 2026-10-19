# The card manager loads a profile for a job no box can claim
kind: finding
state: closed
use-case: the scheduler (step 2, rule 6 and the probe; the trial's TeleOCR row 74)
session: trial
opened: 2026-10-19
closed: 2026-10-19

Queue row 74 (`qv4-trial-read-teleocr`, one piece) requires the program
`qv4-llama-server-teleocr`, which the probe does not list, so the worker
never claims it (attempts 0 at the halt): the proof "a box missing a
program is never given that job" holds at the claim. The policy's rule 6
("a small job never waits for ever", ceiling 1,800 s) does not look at
the probe. Three times on 19 October it picked row 74 as the starved
small job, unloaded the profile that was working and loaded
`trial-teleocr` on the estate's unpatched `built` server, which is not
healthy after 2 s:

- 09:06:17 (`scheduler.swaps` row with action `failed`, "not healthy after 2s")
- 11:35:45 "unloading page-reader: making room for trial-teleocr:
  qv4-trial-read-teleocr has waited 15380s (rule 6 ...): load, discarding
  page-reader"; 11:35:48 "load of trial-teleocr FAILED"; 11:35:53 the
  next bulk job's profile loaded instead.
- 16:02:04 the same, discarding `page-reader` again.

Cost: three swaps, a working profile discarded each time, no piece lost
(the drain finished first). The row would have been picked again every
few hours for as long as it sat in the queue.

Blocks: nothing now (row 74 is cancelled under ruling 60). It returns when
the TeleOCR arm resumes.

Fix (a fix session on `support/scheduler`, with card
`teleocr-needs-a-patched-server-the-scheduler-cannot-choose`): rule 6
chooses only among rows this box can claim (the probe's eligibility), and
a profile whose load fails on a box is not tried again on it until the
probe changes. A policy test: a starved row whose requirement the box
lacks is never the pick.

**Closed 19 October (fix session fix-support-scheduler-1):** `policy.plan`
takes `eligible`, the job types this box can claim at all, and sees no other
demand, so rule 6 (and rule 3's "others waiting") never act for a row no
worker here may take; the card manager passes `Manager.claimable(worker)`:
enabled, every required program present (the probe's test the claim already
applies), and not on a profile whose load failed here while the box's
programs have been as they are now (`failed_loads`, keyed by the probe's
programs; a stray on the port is not held against the profile). The binary
and weights checks now run before the resident profile is unloaded, so a
load that cannot start no longer discards a working profile. Tests:
`test_a_starved_job_this_box_cannot_claim_is_never_the_pick` (policy),
`test_a_profile_whose_load_failed_here_is_not_tried_again_until_the_programs_change`,
`test_a_stray_on_the_port_is_not_held_against_the_profile` and
`test_what_can_be_checked_without_the_card_is_checked_before_the_resident_profile_goes`
(cards); each fails without its change. The profile-names-its-server half is
card `teleocr-needs-a-patched-server-the-scheduler-cannot-choose`.
