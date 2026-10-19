An OData feed's `/$count` obeys its row cap (Charities: 1000 for every set); take the count from `$inlinecount=allpages`, and never trust a set to be small by its name.
area: capture, charities, odata, outside check, counts
paid-for-by: 2026-10-20, charities-capture session, the first probe of the feed

`Organisations/$count`, `Officers/$count` and `AnnualReturn/$count` all
answered `1000`; `$inlinecount` gave 46,132, 589,015 and 430,434. A check
against `/$count` would have passed a copy of 1,000 rows as complete. The
same probe found Activities, Beneficiaries, Sectors and SourceOfFunds, named
like code lists, holding every "Other - ..." entry a charity typed (up to
12,728 rows); fetched whole, each was cut at the cap. The capture now pages
them by key and sets aside any "whole" list that reaches the cap.
