To drop a form's printed example row, match the hash of its folded cell text (measured identical on every return), never its words or a fixed date: the text is an address, and the dates change with every edition of the form.
area: registers/candidate_returns, registers/party_returns, any lane reading a Commission schedule with an example line
paid-for-by: 2026-10-20, candidate-returns session, step 4.1

The candidate return prints one example donor row (a three-line name and
address, two dates, "Yes", $5,000.00). Matching its dates missed the 2022
by-election's edition, and grouping lines by the nearest amount pulled the
next real donor's name into the example on five returns, so that donor
lost their name and the part was set aside. `donors.EXAMPLE_CELL` is the
first 16 hex characters of the sha256 of the three lines folded; it was
the same on 336 of 336 returns, and its lines are blanked before rows are
grouped. The hash says nothing about the text; a test patches it to a
synthetic cell's.
