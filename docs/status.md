# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-11-10 04:24 NZDT. **Process:** ruling 131 (31 Oct) ended
the plan's gate process; work runs on Arthur's word. **Boxes:** two, both
take every job (ruling 145); node1 primary on 10.0.0.10 since the drill,
node2 its streaming standby; the voter on 192.168.68.57. **Alarms:** the
old ntfy.

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
- The drill, 6 to 7 November, all three passed (switchover 2.5 s; crash
  takeovers 36 s and 38 s, nothing lost); fixes 16bedb9 to 42e3626.
- The frozen site's release, failed safe at 06:29 on the crash, fired
  again: 2026-11-07T0727 live 07:40, every check green.
- node2's takeover scripts reinstalled at 42e3626 (7 November 09:18):
  the box named by agent.conf on both boxes; qv4-roled active.

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

- Step 9 (150-157), 9-10 Nov night: 1, 2, 6, 8 built; 5 going
  (insolvency, grants green; 7 lanes orange till read from the MCP).
  Hops and hub limits: Arthur (docs/research/step-9-stage1-depth.md).
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
