A placement rule is written on the level, not the edge: rule 9 took the idle cards only on the tick its job was first placed, so a card freed later sat idle all evening beside a 663-piece backlog.
area: scheduler, policy, cards, night window
paid-for-by: 30 October 2026, the page backlog on one card (card one-page-reader-at-a-time-while-card-0-holds-the-ocr-server)

"A bulk job takes every free card" was coded as "a job type taken THIS tick also takes the idle cards": true on the
tick the page reader was placed, false on every later one. When card 0 was unreserved by hand at 15:50 the planner
saw an idle card and a job already resident and did nothing, because the rule keyed on the event of placing, not on
the state of holding one card while another is idle and nobody waits. The fix asks the state each tick (`kept` job
types with depth above one spread while `waiting_now()` is empty and nothing is served by sharing), and the test
holds a card already held plus a free card, not two free cards. The same shape in the same fix: the measure that a
card has released a model compared its memory to "total less the model", which is a figure a card another server
sits on never reaches; the honest measure is against what the card held before the stop, read just before.
