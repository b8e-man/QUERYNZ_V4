# Forty-one party returns have image pages with no stored page reading
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19

The lane reads a scanned return by replaying the page reader's stored
readings (GLM-OCR Q8_0, 300 dots, `OCR`) and never calls the model. Step
3's trial read every 2019+ party return it held then; 41 of the 152
landed returns were not in its page set and are set aside at stage `read`
with "ask for a re-read of <hash>": 23 cover 2017 and 2018 (outside
Follow the Money's window, ruling 347, but the lane holds the whole
source) and 18 were filed for 2024 and 2025 (and one in 2026's folder).
The 2025 returns are why National, Labour, NZ First, Green, Opportunity,
Conservative, Te Pāti Māori and Vision NZ 2025 do not yet equal the
frozen site.

Fix: queue a page-reader job over those documents' image pages through
the scheduler (step 2.14), the in-window 18 first; the lane picks the
readings up on its next load with no change. `party_returns.set_aside`
lists the hashes (`stage = 'read'`). A build session does not queue live
jobs, so this is the integrator's after the merge, or a scheduler
session's.
