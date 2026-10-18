# windowed-2: the two windowed lanes run one at a time and stop on an answer from another host
branch: session/windowed (pushed; 70ff303, on top of windowed-1)
session: windowed (session 2)
raised: 2026-10-19
claims: registers/tenancy_tribunal/capture.py and registers/real_estate_authority/capture.py (`Tables.try_lock`, the redirect guard in `Run.get`, the skip in `main`), their tests; a note on card `open-url-follows-a-redirect-to-another-host-unchecked`

Merge with or after windowed-1 (same branch).

1. **One run of a lane at a time.** `main` takes a session advisory lock
   keyed by the job name (`pg_try_advisory_lock(hashtext('qv4-…-capture'))`)
   after creating the tables; if another run holds it, it asks for nothing,
   records a skipped run (ok) and exits 0. The lock holds no row and no
   snapshot and goes with the connection. Why: until the catalogue lines are
   installed this session runs tonight's capture by hand (ruling 56); a hand
   run and the scheduled run must never double the rate on one host. Proven
   on `querynz_v4`: a second connection is refused while the first holds
   it, and granted once the first closes.
2. **An answer from another host is a stop.** The gate decides for the URL
   asked, not the URL answered (the card). Each lane now compares
   `Fetched.final_url`'s host with its own: if they differ, a catch-log line,
   nothing landed, and the run stops. The gate fix is still owed: this keeps
   the page out of the store, not out of the read.

Fast tier: `registers/tenancy_tribunal` 19 passed, `registers/real_estate_authority`
17 passed (two new tests each). Nothing new for the integrator beyond windowed-1.
Lesson: nothing new.

## Result (integrator, founding session, 19 October 07:45)

Merged into main as 82b169d with windowed-1 (see its result).
