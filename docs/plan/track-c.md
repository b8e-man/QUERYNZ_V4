### Track C: the review agent

**Starts** with the links in step 4. **Model:** Fable.

- **Its job:** read each watched link's evidence and split the link if it cannot trust it. Arthur is not in this loop.
- **Three verdicts, matching the decisions table.** *Not the same:* that decision is added and the groups rebuild. *Contested:* the agent cannot trust the link; it drops to near, and products show it as a possible namesake. *No reason to doubt:* the link stays confirmed and the review is recorded.
- **It runs on the boxes,** as a bulk job through the scheduler, on the review-and-questions model profile (the local Qwen model). Nothing it reads is sent to a model off the boxes.
- **It may search the web only to find evidence that two rows are different people.** A query carries a name and a public role at most (hard limit 12), goes through the fetch gate, and every web citation must be a page it actually fetched in that run.
- **Build on what exists:** `data-layer/research/research/merge_refuter.py` (the refute-only agent with web search), `data-layer/research/research/webtools.py`, and the timed screen-then-re-read pattern in `data-layer/healer/healer/crawler.py` and `reread.py`.
- **It must be measured before it acts alone.** The old one was tested on 13 hand-labelled cases, where about 196 "different" cases are needed to measure it to within 0.05. Use the test pairs from step 4.3, which need no labelling.
- **The pass mark, as a default until Arthur rules:** on the pairs known to be one person, it wrongly splits fewer than 1 in 100. Splitting is the safe direction, so no minimum is set on how many of the known-different pairs it catches; report that figure. Until it passes, its verdicts are recorded and not applied.

