# Step 2 is written for two boxes; node1 is out (ruling 55), so what do its two-box proofs mean now
default: Build the whole design as the plan says (queue, leases, two workers, takeover, the alarm from the other box), and prove the two-box items by running a second worker on node2 under its own name against the same queue, with the proof recorded as a rehearsal. The real two-box proof is owed when a second box exists (the third machine of step 0, or node1 by a later ruling). Nothing in step 2 is cut
blocks: Nothing; the step 2 session starts under the default
recommendation: The default. Ruling 48 keeps the full design because the work may grow; a second worker on one box exercises every line of the takeover but the network
raised: 2026-10-18 by founding-f05585e (at the close of step 1, before the step 2 brief was written)

Five of the eleven done-when items in `docs/plan/step-2.md` name the other
box: a worker on each box registered, a job for a program only one box has,
a worker stopped mid-job finished by the other, the alarm from the other
box, a timetabled job on the survivor. 2.9's reservation on node1 for
`querynz-vision-ocr` is moot while node1 is out; node2's card 0 (the carve-out's
chat model and page reader) is the one fixed reservation, and card 1 is free
since `querynz-llm@1` was stopped in 1.4 batch 2.
