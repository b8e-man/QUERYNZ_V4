# disclosures: where the lane stands

Step 4.1, the large-donation disclosures lane, `registers/disclosures/`.
Last change: session `reconcile-1`, 21 October 2026, ruling 66 (merge
request `reconcile-1`). Before it: `disclosures-3` (merged).

## Done

- 520 declarations, all three regimes, from the Commission's own table;
  catch log reconciles. Nothing fetched.
- Form check on the 276 linked scans: 245 equal, 1 "equal, a second
  figure in the box", 3 differ (each carded), 27 no total read, set aside
  with hash and pages (stage `form`, ruling 62).
- The received-date rule: a declaration belongs to the year of the gift
  (`given_on`).
- **Ruling 66** (a difference below $100 between the parts and the printed
  total is reconciled with an issue; $100 or more is not). The lane's one
  parts-sum is a declaration's itemised gifts against its printed amount
  (`items_check`). Constant `RECONCILE_TOLERANCE_CENTS = 10000` in
  `reconcile.py`; new `items_check` value `reconciled`; column `issue`
  on `declarations`, last in `pub.disclosures`; `check.py` counts and
  prints the issue rows. Replayed over both held listings (no fetch, no
  model): of 14 that differed, 1 is now reconciled with an issue
  (`ec-listing/2009-01-07/33dc6812f2c6`, +$0.16 over 8 gifts, the largest
  admitted), 13 stay `differs` (the nearest $500.00). Every amount and
  every frozen-site figure unchanged. The form check is two printings of
  one figure, not parts, and stays to the cent.
- Sample: the three cases as `key:` lines; tests either side of and at
  exactly $100. Fast tier green.

## Waiting on others

- The site lane: bucket by `given_on` (`products/published_site/figures.py:84`).
- The comparison: correct two cause rules (owner and side), see the cards.
- Arthur: the Commission's word on three declarations ($42,200 box over
  $27,000 of gifts; the May/February link; the 30 June / 30 July date).
- The board's catalogue (`products/board/catalogue.py:161`) may add
  `issue` beside `items check`.

## Next

- When a page-reader job is allowed: the 27 set-aside scans (stage `form`).
- Take over the old feed only on Arthur's word (step 4.1, step 4.8).
