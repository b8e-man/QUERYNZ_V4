Rule a near-match row out by the exact match of the text it was found by, not only by the search's own exact clause: an address typed in the box is exact in a column the box never searches, and showed as "near".
area: products, the board, any search with an exact tier and a near tier
paid-for-by: 2026-10-25, board-3 (ruling 83)

The board's near matches (ruling 83) are found by a wide SQL filter, then
decided by keys' own readings, and must never be among the exact results.
The first cut excluded each candidate with the exact search's clause, and
"41 Shortland St" typed in the plain box then listed charities registered
at exactly that address under "Near matches: a close address". The box
searches a charity's name, not its address for service, so the exact
clause never held those rows and the near tier caught them instead. A
near row is "close, not exact" relative to the text it was matched on:
exclude by the exact rule applied to that text in the columns the near
rule reads (here, the address field's whole-word rule over the address
columns), as well as by the search's clause.

Two smaller things the same work showed:

- Under "every field and every word must match" a query naming both a
  person and an address finds nothing, because no published view holds
  both; a test that fills both and expects rows is testing the wrong thing.
- A position rule on a one-string name ("a last name is never the first
  word") costs a regular-expression rewrite of every row; put a cheap
  whole-word test in front of it and the scan went from 5 s to 0.4 s.
