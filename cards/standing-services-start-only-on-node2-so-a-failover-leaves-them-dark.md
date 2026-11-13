# Standing services start only on node2, so a failover leaves them dark
kind: finding
state: open
use-case: all
session: integrator-40ea495e
opened: 2026-11-14

The takeover moves the database to the surviving box, but the services that run all the time are per-box
units installed on node2 alone: the board (`qv4-board`, :8420), the report server, the scan service, the site
preview, the MCP tunnel (`qv4-mcp-tunnel`) and node2's model server. If node2 dies, node1 holds the primary
and starts none of them. This is item 2.13 of docs/research/takeover-plan-2026-11-06.md ("a survivor starts
none of them"), still unbuilt.

Found on 14 November 2026 from the nightly full tier: it runs on node1, where nothing serves the board, so
`products/board/tests/test_retired_templates.py::test_live_board_opens_on_the_diagnostic_template` and the
board's real-data tests fail there. node2's firewall zone for the cable (`querynz-lan`) admits only ssh and
nfs, so node1 cannot reach node2's board either.

Owner: support/scheduler (2.13). Next, one service at a time, the board first:
- run each as a scheduler job with `wanted = 1`, placed on whichever box is alive and taken over by the other
  when its worker goes silent; the per-box unit retired at the switch;
- each proven by stopping it on node2 and watching node1 start it, then back;
- the nightly tests find the board where it runs (or the full tier runs on the box that holds it);
- whether the cable's firewall zone opens the board's port to the other box is Arthur's call (admin rights).
