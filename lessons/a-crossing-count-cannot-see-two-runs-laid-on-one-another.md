A crossing count cannot see two edge runs laid on top of one another, and a comparison of two layouts on a fixture where both score zero proves nothing: test the channel rule by overlap, on a fixture shaped like a real busy graph.
area: products, the board's graph tab, any layout, routing or "fewer crossings" check
paid-for-by: 2026-10-26, board-5 (ruling 92 (1))

The layered graph routes every edge with right angles and counts crossings
(a horizontal and a vertical segment meeting inside both). Two things passed
that should not have. First, the hand-made fixture (five matched rows, a
shared company, a shared party) scored 0 crossings under the old sector
layout and 0 under the new one, so "new <= old" held whatever the new layout
did. The fixture was rebuilt from the shape of the live "hart" search's graph
(28 nodes, invented names): sector 7, layered 2, the same as the live graph.
Second, with every bar forced onto one channel, the crossing count fell and
every test stayed green: two runs on one y are collinear, never a crossing,
and the picture becomes unreadable without any count noticing. Only a test
that reads the runs on each channel and fails when two bars share an x span
caught it, and only on the busier fixture. Break the rule in memory before
trusting the test; if it stays green, the fixture or the measure is blind.
