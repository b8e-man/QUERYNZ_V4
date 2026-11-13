# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-12 23:20 NZDT. **Process:** ruling 131 (31 Oct) ended
the plan's gate process; work runs on Arthur's word. **Boxes:** two, both
take every job (ruling 145); node1 primary on 10.0.0.10 since the drill,
node2 its streaming standby; the voter on 192.168.68.57. **Alarms:** the
old ntfy.

## Done

- To 7 November: steps 0 to 3; 4.1 to 4.4, 4.9; 5.1 to 5.5; 6.1 to 6.3;
  step 8 merged; rulings 132 to 145; node1 back as standby; the takeover
  drill passed (2.5 s switchover, 36 to 38 s takeovers, nothing lost).

## Running

- Both workers claim every job; the bulk ingest from the MCP; the nightly
  lanes on their timers.
- Source board 9 Nov 09:10: 4 red. Insolvency check fixed 5bfd50b,
  waits on the walk (13,495 of 14,089). Linz: one 502, resumes tonight.
  Courts-load running. Grants: our capture takes the DIA file only
  (5 Nov split); the Lottery records are the MCP provider's to add.
- 9 Nov: MCP download fixed; the pull copies 11 estate-* corpora.
  Candidate returns read from the MCP (proven equal); disclosures wait
  on its files. Diagnostic report on :8440, findings in
  docs/research/diagnostic-findings-2026-11-09.md.

## Half-done

- Step 9 (150-162), 10 Nov: 1, 2, 6, 8, pane built; 7 waits on news;
  5: 6 lanes on the MCP, stale list lit. Old estate copied in nightly
  (oldcopy on); handover/mcp-gaps.md for the provider, daily.
- 11 Nov (166-170): old API jobs on the new lanes; consumed READY;
  fyi out; NZME asked; GeoNames dropped; courts text layers cached.
- 12 Nov (171-172): model server 10 x 32k both boxes, node2's n-gram
  table on /mnt/ssd2; the provider asked for the courts finder.
- 13 Nov (173-175): provider talks through the MCP's asks tools; 13b
  and the answers sent. Courts: IPT, Waitangi record and reports,
  early ERA, ARLA/NZTDT/HPDT, Environment Court, old HC numbers
  recognised (~20,000 more read). Tenancy takes the courts corpus
  (5,479 orders). Charities groups whole each run. WorkSafe on, MCP.
- 14 Nov: asks for directories, councils, NZME, 87 media sources sent;
  fixes: charities group rename, WorkSafe MCP gaps, courts publish
  locks, LINZ transport stops (2103819).
- 4.5: the comparison daily since 22 October; the switch is open now the
  election hold is lifted (145). 0 clean days of 19: the site build's
  read timed out 4 to 6 November (fixed 39f35e3; 8 November read in
  6 s). 9 November 09:00 built, every gate green, --allow-drop on
  Arthur's word: a name fold, and 5ac0ea5 (an amended EC form beside the
  one it amends was added twice; one Opportunity donor, $75,000).
- The inbox: all 177 merge requests are on main; nothing waits.
- Waits on Arthur: the Insolvency Register API subscription and the PPSR
  account (8.4); letters (Dunedin, TPK, Police); rulings 69, 75; the 15
  unsplittable courts documents. Which box is primary does not matter
  (Arthur, 7 November): no fail-back.
