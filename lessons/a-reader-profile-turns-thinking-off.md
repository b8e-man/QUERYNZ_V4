A Qwen reader profile turns thinking off with --chat-template-kwargs enable_thinking false; --reasoning-budget 0 alone still thinks, and under a small output budget the answer is all reasoning with an EMPTY content field.
area: model profiles, reading documents, scheduler

Seen 18 October 2026: the first re-read piece answered `declared_total: None` for ACT 2025; with thinking off the same page read 2,445,255.79, equal to the published figure, and every one of ten re-reads was equal. The review-and-questions profile keeps thinking on (budget 2048) by design. A caller that treats empty content as a finding, not a failure, repeats the old "a lane that cannot call the model must not report an empty document" lesson.
