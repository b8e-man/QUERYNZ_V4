A provider's answer that the change is on our side is work owed the same day, not a closed thread: the MCP said on 25 November that seq keeps holes and nobody changed the pull.
area: support/mcpsource, provider threads (asks_get)
paid-for-by: 2026-11-28, integrator, two red pulls and a four-hour re-walk on estate-councillor_interests

**What happened.** On 25 November 2026 the MCP provider withdrew 42 councillor-interests records. Its record
numbers (`seq`) kept their holes; our page check demanded `seq` equal to the place, so every pull of that corpus
went red. We asked (estate-councillor-interests-seq@2026-11-26). The provider answered the same day: seq is a
stable number with holes by design, the cursor counts places, "the change is on your side". The thread showed
"done", and nobody made the change. Two pulls failed on 28 November, a re-walk sat four hours and timed out, and
the morning was spent finding the answer again.

**The rule.** When a provider's reply puts the change on our side, the change goes on the board as a card the same
day, before the thread is filed. A thread marked done on their side is not done on ours.

**The contract now (support/mcpsource).** `seq` is a record's stable arrival number, rising, with holes; a record's
seq is never below its place. Page by `next_cursor`. "Already taken" is `seq` at or below the highest seq taken,
never below the cursor. A caught record is looked for in the window of places that can hold its seq.
