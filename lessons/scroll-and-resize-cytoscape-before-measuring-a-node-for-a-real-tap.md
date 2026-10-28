In a headless walk, scroll the canvas into view, wait, call cy.resize(), then read a node's rendered position: Cytoscape caches its box, so a tap measured before the scroll lands on the background and a working handler looks broken.
area: board, graph, canvas, headless walk
paid-for-by: board-11, 28 October 2026

Why: the dossier (ruling 110) opens when a node is tapped. The walk's first run reported no dossier after a real tap on both tabs, though the click on a result worked. A tap listener showed the tap reached the canvas as a background tap: the script had scrolled the canvas into view inside the same evaluation that read the node's position, and Cytoscape maps a mouse point through the container box it cached before the scroll. The page's code was right; the instrument was wrong, and it would have sent the session to "fix" graph.js.

How to apply: before any real tap on the canvas, scroll first, sleep a little, `boardGraph.resize()`, then read `renderedPosition()` and the container's box together, and dispatch the mouse event. When a tap seems to do nothing, add a `tap` listener that records the target before changing the page's code.
