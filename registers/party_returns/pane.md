# Party returns, on the board

One pane, three lines and a table:

- **Returns read:** `select count(*) from pub.party_return_totals`, with the
  count read from text and from pixels (every row is text until the page
  reader lane exists).
- **Set aside:** `select stage, count(*) from party_returns.set_aside group
  by stage`: how many returns the lane holds but could not take to a row,
  and at which stage (not recognised by the profile; declaration page
  not reconciled). A rising count is the point, not noise.
- **Against the frozen site:** `python -m registers.party_returns.check`:
  equal, differing (each a card), not on the frozen site.
- The table: party, year, declared total, check (`parts-sum` or
  `declared-nil`), document (first twelve characters of the hash,
  linking to the document), read from text or pixels.
