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
