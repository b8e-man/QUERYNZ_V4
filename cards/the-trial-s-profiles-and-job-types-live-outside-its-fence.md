# The trial's model profiles and job types live outside its fence
kind: blocker
state: open
use-case: Follow the Money (step 3, the page-reader trial)
session: trial
opened: 2026-10-18

Step 3.2 says "serve each as a scheduler profile", and the brief points at
`support/scheduler/jobs.toml` and `profiles.toml`; the launcher line in the
plan fences the trial to `support/trials`, `support/profiles` (the DOCUMENT
profiles) and `docs/trials`. The scope hook refuses the edit, rightly. The
plan's table "What is live, and who may touch it" meant the trial to change
model profiles; the file they live in moved into the scheduler's module in
step 2.

What the trial did: its additions are kept beside its code in
`support/trials/scheduler/{profiles,jobs}-additions.toml`, proven against
the registry's own rules on the merged catalogue
(`python -m support.trials.catalogue check`), and `python -m
support.trials.catalogue patch` prints the unified diff. The merge request
carries the patch.

Blocks: every trial pass through the scheduler (3.5 pass one over the page
set, 3.6 the challengers, 3.7 the rows). Until the catalogue holds the
trial's job types nothing can place them; the worker reads the main
checkout's catalogue.

Fix: the integrator applies the patch when merging `session/trial`
(`git apply` of the merge request's patch, then `python -m
support.scheduler check`), and the next trial session queues the passes.
Decision queue: whether the trial's scope should name the two files.
