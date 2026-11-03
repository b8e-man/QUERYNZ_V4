# The Insolvency Register, on the board

One pane, counts only (no names):

- **Asked:** `select why, status, count(*) from insolvency.calls group by 1, 2`; the cursor:
  `select what, value, at from insolvency.cursor`.
- **Against the source:** `python -m registers.insolvency.check`: per register, the API's own `totalItems` over the months
  walked against the estates seen; the removals' age.
- **Removed:** `select count(distinct estate) from insolvency.removals`.
- **Read:** `select kind, register, count(*) from insolvency.estates group by 1, 2`; flagged:
  `select suppressed, removal_seen_at is not null, window_unknown or shown_until < current_date, count(*) from
  insolvency.estates group by 1, 2, 3`; unanswered by reason: `select reason, count(*) from insolvency.unanswered group by 1`.
