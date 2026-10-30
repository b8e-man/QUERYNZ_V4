# The page backlog runs on one card: a second page reader cannot stand beside the OCR server on card 0
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed:

30 October 15:50, Arthur: why is one card idle? During the night window card 0 is held for the frozen product's
OCR server (:8032, 4.7 GB; hard limit 23) and the page reader (GLM-OCR, 4.8 GB) runs on card 1 alone, while
card 0 has 20 GB free. Unholding card 0 by hand did not help: the planner serves a job type from one card and
`_env` takes the first card serving the profile, so a second page reader is never loaded and the pieces are
never spread. The hour's remedy was three slots on the one reader (`profiles.toml` page-reader `slots = 3`,
`qv4-read-pages-candidates` `concurrency = 3`, 6038992), which lifted the pace from 1.0 to about 1.6 documents a
minute, not 3.

Owed (`bin/fix support/scheduler`): inside the window a page profile may load on card 0 beside the OCR server
when the card's free memory covers it (a card holds one model profile at a time: the OCR server is the frozen
product's, not a profile of ours; say what rule 25 means for it), and a pieced job's rows may be served from two
cards. Whether three slots on GLM-OCR help at all is a measurement for the fix (1.6 a minute from 3 slots).

19:25 to 21:14, 30 October, on Arthur's word ("fuck that rule ... give the card to the scheduler"): a second GLM-OCR
server by hand on card 0 (port 8110, -np 3, HIP_VISIBLE_DEVICES=0) BESIDE the frozen OCR server (the safety hook
refuses to stop that unit; the card had 21 GB free, so nothing needed stopping), fed by a shell loop running
`python -m support.scheduler read-pages` with the worker's QV4_MODEL_* environment over the todo pieces of rows 861,
860 and 854 from the tail, three at once. Both cards at 100%; 207 + 20 documents read there, 0 failures; the
scheduler's rows replayed the stored readings in seconds. The backlog that would have ended near 02:00 ended 21:14.
The fix owed stands: the planner should do this itself (a page profile on card 0 beside the OCR server when memory
covers it; pieces of one job across two cards).
