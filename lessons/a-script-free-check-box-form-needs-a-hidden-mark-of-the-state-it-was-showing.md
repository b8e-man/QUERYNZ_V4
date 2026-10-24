A script-free form with a "select all" box cannot tell "unticked one under select all" from "just ticked select all" without a hidden mark of the state the page was showing; decide from both and test each case.
area: products, the board, any page served with no script
paid-for-by: 2026-10-25, board-2, step 4.9 second version (ruling 80)

A GET form sends only the boxes that are ticked. With "search all" ticked
and every register shown ticked, a user who unticks one register sends
`all=1` and the rest; a user who had narrowed to two registers and then
ticks "search all" sends `all=1` and those two. The two submissions differ
only in what the page was showing before, so the board writes
`was_all=1` into the form while "search all" is in force, and
`search.selection` decides from the boxes and that mark (nothing ticked
still means all). The same rule for the highlight: mark text with the
search's own fold, one character for one character, or "Maori" typed never
marks "Māori" filed.
