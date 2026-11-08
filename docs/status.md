# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-07, 10:45 NZDT. **Process:** ruling 131 (31 Oct) ended
the plan's gate process; work runs on Arthur's word. **Boxes:** two, both
take every job (ruling 145); node1 primary on 10.0.0.10 since the drill,
node2 its streaming standby; the voter on 192.168.68.57. **Alarms:** the
old ntfy address.

## Done

- To 2 November: steps 0 to 3; 4.1 to 4.4, 4.9; 5.1 to 5.5; 6.1 to 6.3;
  step 8's parts merged (docs/research/overnight-2026-11-02.md).
- 3 to 5 November: rulings 132 to 144; keep everything, privacy at export
  (142) swept through the lanes; LINZ whole; the ingest MCP's new fields
  read (beehive, parliament, courts, diaries, GETS); a refused host stops
  its lane (141); Papers Past tab on the board.
- 5 and 6 November: node1 returned, rebuilt as a standby by base backup;
  the shared work folder and stores over NFS; worker helpers (fbcff15);
  the takeover machinery: voter, quorum lease, role agents
  (support/takeover/voter.md).
- The drill, 6 to 7 November, all three passed: switchover node2 to node1
  (address gone 2.5 s); node1 crashed, node2 primary in 36 s; node2
  crashed 07:22, node1 primary in about 38 s with nothing lost (promoted
  at replay = received), node2 rewound and standby in 3.2 s. Fixes on the
  way: 16bedb9, 912ef49, 2a26561, 42e3626.
- The frozen site's release, failed safe at 06:29 on the crash, fired
  again: 2026-11-07T0727 live 07:40, every check green.
- node2's takeover scripts reinstalled at 42e3626 (7 November 09:18):
  the box named by agent.conf on both boxes; qv4-roled active.

## Running

- Both workers claim every job; the bulk ingest from the MCP; the nightly
  lanes on their timers.
- Source board 8 Nov 15:15: 5 red, from 8. Fixed 437a98c (pull),
  2ede69b (companies), 79ec372 (linz), 970ed4b (insolvency), 468bb11
  (grants), 409815c (courts-load). Loads re-run now; captures tonight.
  Grants waits on Arthur: communitymatters.govt.nz blocks (403), held.

## Half-done

- 4.5: the comparison daily since 22 October; the switch is open now the
  election hold is lifted (145). 0 clean days of 19: the site build's
  read timed out 4 to 6 November (fixed 39f35e3; 8 November read in
  6 s). 8 November refused at the compare gate: a name fold moved
  $100,000 between two pages of one donor; Arthur's word on --allow-drop.
- The inbox: all 177 merge requests are on main; nothing waits.
- Waits on Arthur: the Insolvency Register API subscription and the PPSR
  account (8.4); letters (Dunedin, TPK, Police); rulings 69, 75; the 15
  unsplittable courts documents. Which box is primary does not matter
  (Arthur, 7 November): no fail-back.
