"None chosen" for a party-year with two unreplaced returns belongs to the year, not the headline: every surface that sums rows skips that year too, or the headline is silent while the rows count twice.
area: products, the published-site shape, figures that sum rows across returns
paid-for-by: 2026-10-20, site session, step 4.4

The first build of the shape set the declared figure for National 2022 to
null with "2 returns held and none replaced; none chosen", and summed the
Part A rows of both returns into the named figure: $5,233,211.80 where the
frozen site showed $2,616,605.90 (one return). The check that caught it
was the first one that could fail: seven parties' party-year figures
against the frozen home file. The fix is one set, `ambiguous_years()`, on
the party's series, read by every summing surface, and the donor pages
show those rows as "shown and not counted" so the money is visible and
never added. The compare gate then refused the next build (42 totals fell
by the same $5.2 M) until the drop was allowed and recorded: the gate did
its job on a correction the build itself had made.
