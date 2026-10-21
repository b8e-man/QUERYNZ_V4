# tenders: where the lane stands

Session tenders-1 (Opus), 21 October 2026, node2. Step 6.2, template 1's
register: `registers/tenders`, the ministry's GETS award notices.

## The four questions (position: `registers/tenders/position/`)

1. **Open?** The catalogue is. The files are not: the ministry's host
   answers 403 to our User-Agent and `www.data.govt.nz` shows an Incapsula
   challenge (21 October). Failed reads, logged, not got around.
2. **Lawful copying?** CC BY 3.0 NZ (the catalogue's statement), Crown
   copyright: copying and reuse with attribution. The attribution is on
   every row and view.
3. **Terms accepted?** None by click; the site terms sit behind the
   challenge, unread. Lawyer to confirm.
4. **Privacy?** Suppliers include sole traders. The address and website
   columns, and the notices' free text, are never read: a name and nothing
   finer.

## Done (merge request `tenders-1`)

- Lane: capture (case 1, the old raw files of 14 August by hash; case 3,
  the gated quarterly refresh), six profiles proposed, `read.py`,
  `load.py`, `check.py`, `publish.sql` (`pub.award_notices`,
  `pub.award_suppliers`), sample, pane, spec, position.
- Landed in `querynz_v4`: 10 documents, copy run 1, 3 failed reads logged.
- Full build: 29,874 notices (7,314 historic, 22,560 current, report date
  15 July 2026) = the old estate's figure; 31,264 suppliers; 3 set aside
  (one historic RFx ID the notices lack); 2.4 s. check.py green.
- Tests: 43 (3 slow), a mutant check (11 reading, 3 capture mutants).

## Open

- Card `the-ministry-s-gets-files-answer-403`: the refresh is blocked;
  Arthur's letter. The done-line's "refreshed on a schedule" waits on it.
- Card `the-gets-supplier-file-loses-its-business-numbers`: no NZBN in the
  file; template 2 joins by name.
- Card `the-tenders-jobs-into-the-catalogue`: the integrator's part.
- Queue `whether-the-old-gets-copy-is-kept`: default kept.
