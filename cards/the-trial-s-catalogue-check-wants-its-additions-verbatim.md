# The trial's catalogue check wants its additions verbatim, so the shipped profiles cannot change
kind: finding
state: open
use-case: Follow the Money (step 3, the page-reader trial: its additions to the scheduler's catalogue)
session: fix-support-scheduler-1
opened: 2026-10-19

`support.trials.catalogue.merged_text` decides whether the shipped
`support/scheduler/profiles.toml` and `jobs.toml` already hold the trial's
additions by looking for the whole additions file as one verbatim string
(`add.strip() in base`). When it is not found the additions are appended,
the merged file declares every trial table twice, and `tomllib` raises
(`Cannot declare ('jobs', 'qv4-trial-read-glm-ocr') twice`), which fails
`support/trials/tests/test_readers_catalogue.py::test_the_merged_catalogue_passes`
and so the merge gate.

Any edit to a trial block in the shipped file trips it. Seen 19 October in
the fix session for `support/scheduler`: adding `binary =
"qv4-llama-server-teleocr"` to the two TeleOCR profiles (card
`teleocr-needs-a-patched-server-the-scheduler-cannot-choose`) and dropping
their `requires` line both failed the check, and the additions file is outside
that fence. It will trip again by itself: `profiles.toml` says `memory_gb`
and `load_seconds` are written back by the first swap that measures them,
and the trial profiles have neither yet.

Blocks: the last two lines of the TeleOCR card (done by the integrator in
both files at once, this time). Nothing else.

Fix (the trial session, or a fix session on `support/trials`): hold the
additions by their table names, not their text: `merged_text` appends only
the `[profiles.x]` / `[jobs.x]` blocks whose table the shipped file does not
declare, and `patch()` follows. A test: a shipped file holding a trial
profile with one extra key still merges clean.
