# Where the build stands

Overwritten at every close; under 3 KB.

**Date:** 2026-10-31, 14:10 NZDT. **Step:** 4 built through 4.4 and 4.9;
4.5 comparing daily, no clean day yet; 5.1 done; 5.2 closed
(ten templates); 5.3 eight lanes merged (OpenLaw, HDC held on terms;
sanctions lists held); 5.4, 5.5 merged; 6.1 merged (the scan on port
8450); 6.2 `tenders-1` and templates 1 to 3 merged; 6.3's four source
lines have lanes. Track C measured; B and E closed. **Boxes:** node2 is the
estate; node1 offline indefinitely (Arthur, 25 Oct); model reading
runs on node2 alone (ruling 128). **Alarms:** the old ntfy address.

## Done

- Steps 0 to 3 closed (60); 1.4's positive half seen (70).
- 4.1, fifteen lanes merged: donations (66), parties, party finance,
  gazette, house, companies (1.92 M), expenses and interests, societies,
  candidate returns, charities (64), party boards, OpenLaw (HELD), courts.
- 4.2/4.3 links: 3.07 M confirmed, 725 K groups (fix-links-5, 29 Oct);
  the agent applies nothing (ruling 69). 4.4 site version 3. 4.9 board
  87 views, chat pane (122). 5.1 the report shape, tranche 3.
- Rulings 64 to 130 (102: limit 15 binds products, not the board; 123:
  pub.entities; 126 to 129: MCP courts, reading, night; 130: the bulk
  ingest, the common reader rules, no excerpts).

## Running (the bulk ingest of the MCP, ruling 130)

- 31 October merges: `fix-registers-courts-1` 10:5x (one keep rule;
  `pub.court_people` 57,096 names), `readers-1` 12:50 (beehive-2,
  hansard-3, parliament-2: the names readers; Radiance at 32,768
  tokens, 200 tok/s a request). Released.
- Readers queued 13:44: hansard row 940 (1,857 days), parliament 941
  (65,809 pieces), beehive 942 (66,399 releases); courts row 936
  (511) done 12:26. Views catalogued in the merge after.
- Gating `integrate/courts-2`: fix-registers-courts-2 (whole documents
  in pieces, ERA/HRRT/tribunal/NZDC kinds, every courts document read
  again: 10,600 calls), fix-links-6 (an all-zero NZBN is none; one
  body per NZBN; the pull every six hours), the four views. Then
  `fix-support-scheduler-5` (8 rows in parallel; worker restart).
- Missing from the MCP: parliament papers' attachments (sc-submissions
  1,335, sc-reports 1,000, bills, SOPs) are metadata only until the
  provider captures them; courts outside NZSC/NZCA/NZHC only as the
  provider began (ERA 292, HRRT 389, tribunals 71, NZDC 10).

## Half-done

- 4.5: the comparison runs daily since 22 October, 0 uncarded every day
  but 23 October. 30 October: 29,186 differences, 7,216 the new side
  wrong (candidate returns not held 5,133). The switch after 7 November.
- Waits on Arthur: letters (Dunedin, TPK, Police); rulings 69, 75;
  sample-schema drops (`scratch_hansard_3_full`); the 15 unsplittable
  courts documents (courts-2 item 5); remote branch deletions. node1's
  return: fence first (10.0.0.1, never the VIP), ruling 57, 94.
