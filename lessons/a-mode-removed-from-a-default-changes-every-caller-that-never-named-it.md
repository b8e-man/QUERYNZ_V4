When a function loses a mode its callers got by default, find the callers that never named it: a grep for the flag finds those that asked, and the ones that took the default now get the other answer without a word.
area: board, graph, checks, any API with a default mode
paid-for-by: fix-products-board-6, 29 October 2026

Why: ruling 120 removed the graph's rows state. `graph.build(people=False)` was the default, so the grep for `people=` found every caller that asked for a state and none that took the default. Three of those were checks and slow tests holding a rows-graph contract (every node id is a row of a view, the centre is a node, one donor node is a `party_return_donors:` node, the SVG's node link is the JSON's node id); after the change each met `entity:<group>` nodes and turned red only in the slow tier, which the fast tier does not run.

How to apply: before removing or changing a default mode, list the callers that pass nothing for it (grep the function's name, not the flag) and read what each asserts about the shape of the answer. Run the module's slow tests and its outside check, not only the fast tier, before raising the request. Where a node can stand for several rows, give the checks one helper that says which rows it stands for (`check.rows_drawn`).
