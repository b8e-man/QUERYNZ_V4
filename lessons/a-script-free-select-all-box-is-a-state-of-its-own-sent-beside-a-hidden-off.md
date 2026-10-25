In a script-free form, keep a "select all" box as a state of its own, never a tick of every other box: send a constant hidden `all=0` before the box's `all=1`, carry both on every href, and an address with neither is the first view.
area: products, the board, any page served with no script
paid-for-by: 2026-10-25, board-2 (ruling 80); corrected by fix-products-board-1 (ruling 81)

Board-2 drew "search all" as every register ticked, so a GET form (which
sends only the ticked boxes) could not tell "unticked one under search
all" from "just ticked search all", and it needed a hidden mark of the
state the page had been showing (`was_all`) and a rule that nothing
ticked means all. Ruling 81 made the two states independent: "search all"
ticked searches everything whatever is ticked below it, and the register
ticks are shown and carried as the user left them, so turning it off and
on loses none. Then no mark of the previous state is needed. One thing
is: an unticked box sends nothing, so without the hidden `all=0` the form
with "search all" off and nothing ticked looks like an old address, and
an old address must open as the first view. `search.boxes_of` reads it:
`all` present, "1" among its values; `all` absent, all only when no `r`.
Test each case by rendering the form and reading the boxes and hrefs
back through the parser the server uses. The same rule for the
highlight: mark text with the search's own fold, one character for one
character, or "Maori" typed never marks "Māori" filed.
