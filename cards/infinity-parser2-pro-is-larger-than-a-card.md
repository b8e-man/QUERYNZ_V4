# Infinity-Parser2-Pro's only conversion is larger than a card
kind: finding
state: open
use-case: Follow the Money (step 3, the page-reader trial: the 35B arm)
session: trial
opened: 2026-10-18

The hub holds one GGUF conversion of Infinity-Parser2-Pro
(glebkudr/Infinity-Parser2-Pro-Q8-GGUF): Q8_0, 36.9 GB, against 31.9 GB on
node2's card 1. Step 3.1's "two levels of compression" cannot both come
from the hub. The trial fetches the Q8_0 and makes the second level itself
with the quantiser (`python -m support.trials.models quantise`: Q4_K_M from
the Q8_0, so twice-quantised, recorded as such in the downloads ledger);
the Q4_K_M (about 20 GB) is the arm on the card, and the Q8_0 is served
only for the twenty-page comparison with the experts on the processor
(`--cpu-moe`, slow). If the Q4_K_M reads differently from the Q8_0 on the
twenty pages, the 35B's trial figure carries that caveat, and a conversion
from the safetensors at Q6_K or Q5_K_M (a larger download and a
conversion on this box) is the next step, carded then.

Blocks: nothing; the arm runs on the Q4_K_M. Accepted onto the trial's
record when the twenty-page comparison has run.
