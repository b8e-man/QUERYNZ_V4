# trial-3: step 3 halted under ruling 60; the verdict, the profiles, what ran and what did not
branch: session/trial at 6b956dc (on top of main at 71413f1)
session: trial (session 2)
raised: 2026-10-19 19:10
claims: docs/trials/page-readers.md (the verdict at the top; pass two as run; scores; what did not run; the proofs table), support/profiles/profiles.jsonl (eleven new versions: ocr.second_reader null, ocr.trial, the verdict in notes; nothing edited), two tests pointed at the new versions (profiles: 4 green; trials: 37 green; fast tier green for both under the venv), three cards, one lesson, docs/status/trial.md

What it claims: pass two was scored as read (7,896 page readings:
`scratch_trial.page_scores`, `page_agreement`, `level_pairs`). GLM-OCR
Q8_0 under "OCR" stays the page reader, alone; no challenger reached zero
loop or invented-text failures on the pages it shares with the incumbent
(OvisOCR2 on 2,327 pages: 68 loop pages to 27; Infinity-Parser2-Pro
Q4_K_M on 445: 24 to 9; Chandra OCR 2 on 191: 17 to 9), though all three
read amounts on complete keys at least as well. No second reader; carded.
300 dpi over 200 and f16 over Q8_0 change nothing measurable. Step 3 is
not finished: two scheduler proofs, the TeleOCR arm, the rows pass, the
prompt variant and the 111-page repeat are owed to the resumption.

## For the integrator

1. Nothing runs; card 1 is released (`scheduler.swaps` 327). No units,
   no catalogue change, no install.
2. `lessons/INDEX.md` is NOT in the branch: `bin/lessons-index` rewrote
   it in the working copy and the scope hook refuses even restoring it,
   so it sits modified there; regenerate at the merge as usual.
3. Two new cards are outside the trial's fence and go with the TeleOCR
   card to a fix session on `support/scheduler`:
   `the-lease-lapses-while-a-large-model-loads` (the claim's lease is
   not renewed while the card loads; the 35B's 124 s and 202 s loads
   lapsed it twice, one piece each) and
   `the-card-manager-loads-a-profile-for-a-job-no-box-can-claim` (rule 6
   picked the unclaimable TeleOCR row three times and discarded the
   working profile to load a server that is not healthy).
4. The third card, `no-second-reader-qualifies-under-the-trial-s-rules`,
   is the plan's own "card the lack" and closes when the trial resumes.
5. The profile versions are appended lines (56 in the file now); the
   tests that pinned the scan profile at version 4 now read version 5 or
   the current version.

## Result (integrator, 2026-10-19 19:40)

Merged into main as 7608be8 (merged main first: ruling 60 and the probe fix;
lessons index and card board regenerated at the merge as asked). Fast tier
and gate green. Step 3 is closed under ruling 60 with GLM-OCR Q8_0 under
"OCR" the page reader alone and no second reader (carded). The two
scheduler cards go to one fix session on `support/scheduler` with the
TeleOCR card (brief in `docs/briefs/next.md`, `## scheduler-fix`). Step 4
opens: the large-donation disclosures lane first, as the plan says.
