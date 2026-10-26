Count the categories and search for the palette before promising each its own colour at a contrast and distance floor: the board's dark picture holds about 22 colours at 3:1 and 15 apart, not 28, so graph nodes take one colour per family.

area: products/board, any picture coloured by category (graph nodes, the key, charts)

How it was found (board-7, ruling 100): the brief asked for register colours
"each at 3:1 on the picture's surface and 15 apart in OKLab like the edge
colours". The key has six colours; the catalogue has 28 registers. A
max-min search over every sRGB colour 3:1 on #161a20 gave 16.2 apart for 20
colours, 14.4 for 24, 13.5 for 28. Families of registers sharing a colour
(as the two same-person kinds share a hue in the key) kept 14 colours 17.5
apart; the choice is in the decision queue.

Also from board-7: a script the board serves is checked on the instrument
that runs it. Headless Chrome driven over the DevTools protocol by node's
own WebSocket (no driver installed) gave real taps, folds, the console and
every request the page made; the unit tests could not have shown that the
canvas drew, or that cytoscape-cola looks for `webcola` where WebCola names
itself `cola`.
