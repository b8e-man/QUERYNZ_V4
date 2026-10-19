# Loans are set aside on six read returns
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19

Part H (loans over the threshold) publishes one row per lender block when
the blocks add to Part H on the declaration page. Of the 99 returns with a
row: 6 published (9 loans, NZ First 2020 to 2024 and ONE Party 2020), 87
nil, 6 set aside:

- **3 at stage `loans`, the declared figures:** Opportunity 2018 (Part I
  read as the 2018 form's threshold), Vision NZ 2020 (Part I not read),
  NZ Outdoors and Freedom 2022 (no figures read).
- **3 at stage `part-h`:** NZ First 2021 and 2023 originals (both
  replaced by amendments whose loans are published), and ALCP 2019, where
  a $50 figure was read in a blank lender block of a nil Part H.

`select * from party_returns.set_aside where stage in ('loans', 'part-h')`.
