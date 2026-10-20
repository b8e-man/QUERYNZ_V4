# charities_b: the charities lane's reading, built by Opus

Step 4.1: the Charities Register is built twice, once by Opus (this folder)
and once by Fable (`registers/charities_a/`), against the same tests, from the
one capture in `registers/charities/` (plan step-4, "Build this one twice").
The comparison is recorded as a lesson and one build is kept.

Built by session `charities-b` (21 October 2026). `read.py` types the feed's
pages, `load.py` builds the tables (`python -m registers.charities_b.load`
into `scratch_charities_b_full` of the sample database), `check.py` holds the
build to the pages and the register. It publishes nothing until it is the
build kept (`load.KEPT`). The merge request has the figures.
