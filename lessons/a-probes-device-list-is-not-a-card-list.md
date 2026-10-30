A probe's device list is not a card list: keep a device only when it is a discrete card (not a processor by name, memory at or above a floor), and reserve any card row the probe no longer lists.
area: scheduler, probe, graphics cards, card rows

Seen 30 October 2026 on node2 at 13:49, the first tick after the night-window merge: rocm-smi listed a third device
for one tick, index 2, "AMD Ryzen 9 9950X 16-Core Processor", 2.0 GB, the processor's own graphics. The probe passed
it as a card, the row was written, the planner saw a cold card and loaded the page reader on it, and the server ran
on the processor for four minutes with two pieces on it. A minute later the probe listed the two R9700s only, but
the row stayed, and a row is what the planner plans from.

Two rules follow. A listing from the box is filtered by what a card is before anything is written from it: a name
that says processor, or memory under 8 GB, is not a card, and the log line says what was dropped. And a row that
outlives its device is reserved with a reason naming this, cleared only when the probe lists the card again, so a
one-tick device never leaves a plannable row behind. The same shape as the one-filter lesson beside this: a model
server on the processor answers with the right model name, so only the card's memory and the probe tell the truth.
