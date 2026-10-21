# Court judgments, on the board

One pane, counts only (never a party's name, never a judgment's text):

- **Held and read:** `select status, count(*) from courts.judgments group by 1`: parsed, partial, unparsed.
- **Against the listing:** `python -m registers.courts.check`: listed, read, set aside, not held, per source; the
  per-field missing counts; roles the counsel lines name that no party holds.
- **Suppression:** `select count(*) filter (where suppression), count(*) filter (where withheld is not null) from courts.judgments`
  and `select count(*) from courts.suppression_orders`: judgments flagged, judgments with names withheld, orders in the ledger.
- **Parties:** `select count(*), count(*) filter (where withheld), count(*) filter (where anonymised), count(*) filter (where confidence = 'low') from courts.judgment_parties`.
- **Capture:** `select count(*), count(document) from courts.captures` and the newest `qv4-courts-capture` run record:
  found, landed, why it stopped. Above zero found-not-landed for a week is the number that matters.
- **Set aside:** `select stage, count(*) from courts.set_aside group by stage`.
