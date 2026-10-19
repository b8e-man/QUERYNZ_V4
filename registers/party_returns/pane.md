# Party returns, on the board

One pane, four lines and three tables:

- **Returns read:** `select count(*) from pub.party_return_totals`, with the
  count read from text and from pixels (a pixels row is weaker evidence
  and the pane says so), and the count with `replaced_by` set (an
  amendment the Commission lists replaces it; never summed).
- **Schedules:** per return, `donors_check` and `loans_check`: `parts-sum`
  (every row published, adding to the printed figure), `declared-nil`, or
  empty (the part is set aside; its reason is in the catch log).
- **Set aside:** `select stage, count(*) from party_returns.set_aside group
  by stage`: returns the lane holds but could not take to a row
  (`recognise`, `read`, `declaration`), parts of a published return it
  could not publish whole (`part-a`, `loans`, `part-h`), and amended
  returns the Commission lists that the lane does not hold (`amendment`).
  A rising count is the point, not noise.
- **Against the frozen site:** `python -m registers.party_returns.check`:
  equal, differing (each a card), not on the frozen site.
- The tables: returns (party, linking to its registration by `party_key`; the label as filed when it resolves to none; year, declared total, check, loans, replaced
  by, document's first twelve characters linking to it, text or pixels);
  a return's donors (name, amount, dates, page, how the row was paired);
  its lenders (name, amount, dates, interest). No address is shown or
  held in any table this pane reads.
