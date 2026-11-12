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
- 11 Nov (166-168): old API jobs moved to the new lanes; old backups
  stopped; consumed READY (154 copied, 53 held, 58 let go). fyi removed
  (171: quarantine deleted); NZME asked of the provider (169); GeoNames
  out, tables dropped. Courts load past
  its 4.5 h limit 10 and 11 Nov: text layers now cached (58970db), 91,942
  filled. 170: the gap list asks only what we lack (0 backlog asks, 282
  withdrawn); asks/collect.json: EC, legislation, Hansard, 73 sites.
- 12 Nov (171): model server at 10 requests x 32k, 11.5 GiB pool a
  rank, both boxes; node2 reads the n-gram table from the spare
  drive (/mnt/ssd2), node1 from RAM. fyi quarantine removed on
  Arthur's word, ledger stamped; the 4 store files stay withdrawn.
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
