### Reusing the old code

Whether to rebuild a piece or move it depends on where its value sits.

| Treatment | Pieces | Why |
| --- | --- | --- |
| Rebuild, with the old code as reference | The reading of names and addresses, the lane template, the reader contract, the links, the product shapes | Their faults are structural: seven copies of one name function, hand-set weights, one package doing ten jobs. They are also small |
| Move as it is, behind a new contract | The fetch gate, the headed-browser code, the amended-filing rules, the per-form parsers and document profiles, the release pipeline without its deploy step, the scheduler's registry, rules and ledger | This code is edge cases paid for one at a time. A rewrite would relearn them |
| Never rebuild | Decisions, corrections, document profiles, answer sets | They are data. They move across untouched |

Three rules for a rebuild:

1. **Carry the tests first.** The old tests are the lessons in a form that runs. Run them from the reference copy, never from the live old folder. The new module passes them before it replaces anything, except tests that only pin the old structure.
2. **Account for every difference.** Run old and new over the same real rows. Each cause of disagreement gets one card saying which side is right. One card per cause, not per row.
3. **Stop rule.** If a rebuilt module still has unexplained differences after its second full comparison, stop. Card the residue and put the choice in the decision queue.

Four rules for anything reused:

1. **A verdict before use:** take as is, take after a named fix, take the idea and rebuild, or leave. The reference section gives a first verdict for each piece.
2. **Reuse through one imported function, never by copy.**
3. **One check against the outside world** before anything depends on it. The old release pipeline passed eleven gates on a wrong site because every gate read our own output.
4. **No new member of an old debt list:** no fetcher that bypasses the fetch gate, no table without a definition in one place, no writer outside its own lane.

