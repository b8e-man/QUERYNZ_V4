Check a no-overlap rule on the crowded picture it was made for, not only on the known row's small graph: with placement switched off, the donor's 13-node graph still drew nothing over anything and the check stayed green.
area: products, the board's graph tab, any layout or collision check
paid-for-by: 2026-10-25, fix-products-board-1c (ruling 84)

The board's live check drew the known donor's graph and a name-only donor's
graph and found no two labels or numbers meeting. Breaking `graph.place` so
it accepted the first spot for every label and number left the check green:
those graphs have a dozen nodes spread round a circle, so nothing collides
whether or not anything is placed. Only the graph of a name search
("smith": 16 matched rows, 87 nodes) turned it red, with 111 meetings. The
pure tests had the same shape of trap and were given a 110-neighbour fan.
Break the rule in memory and run the check before trusting it; if it stays
green, the case is too easy.
