Before declaring a board pointer or graph edge, check the far view publishes the column the join needs: `pub.members` carries no Parliament member id, so every Hansard turn would have read "(row not held)", a false absence, and the only join left was a name match.
area: board, catalogue, pointers, relations, hansard, house
paid-for-by: 2026-10-27, fix-products-board-1 (the Hansard views)

A brief asked for a speech turn's member to point at the House's member row
"where pub.members holds it, else (row not held)". `catalogue.pointers`
resolves a column against a far column, and `pub.members` has no member
id (its key is election/seat; `name_key` is a folded name). Declaring the
pointer against any of its columns would have matched nothing and shown
"(row not held)" on all 40,098 member turns, which reads as "this member is
not in the House register" when the truth is "the two registers share no
identifier". Check with one query that a far column holds the values
(`count(*) where exists ...`) before declaring it; if none does, declare
nothing, say so in the view's note, and raise the shared id as the lane's
work.
