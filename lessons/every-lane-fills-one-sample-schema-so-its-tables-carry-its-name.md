Every module's sample fills one shared scratch schema, so a lane's tables there must carry its name (`load.table(schema, t, shared=True)`): a second lane's `returns` or `files` takes the first's name and its fill, and every other lane's sample fixture, fails.
area: any lane's sample.py and load.py (registers/*), support/sample
paid-for-by: 2026-10-20, candidate-returns session, step 4.1

The candidate-returns lane created `scratch_candidate_returns.returns`
with its own columns; the party-returns lane's fill, run by `bin/fast` in
the same schema, then failed on `column "party" of relation "returns" does
not exist`, and with it thirteen tests of two other lanes. party_finance,
house and disclosures already prefix (`shared=True`); party_returns, the
first lane, does not, which is why its table names are the ones taken.
Run the whole fast tier, not only your module's, before raising the
request: a lane's own tests passed throughout. A stale table in your own
scratch schema cannot be dropped (the hook refuses DROP); rename it aside.
