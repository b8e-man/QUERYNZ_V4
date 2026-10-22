# procurement: where the step 6.3 procurement lanes stand

Session procurement-1 (Opus), 22 October 2026, node2. Merge request `procurement-1`. Ruling 79: no model reading.

## Outcome per source (positions in each lane's `position/`, to move)

| Source | Open? | Terms | Outcome |
| --- | --- | --- | --- |
| GETS listing of current tenders | yes | 3.2(i)(e) bars any spider or robot | **not captured**; queue (a letter) |
| Agency contract disclosures | catalogue yes; 9 of 24 agency sites 403 or Incapsula | ACC's file CC BY 3.0 NZ; MSD's no licence | **ACC built**; MSD not landed; no agency lists its awards off GETS |
| Council procurement off GETS | TenderLink, QLDC challenged; VendorPanel registration | Clutha, Tauranga non-commercial; Dunedin on request | **not captured**; monthly watch; queue (a letter) |

The collected file for both awards questions is the GETS award notices, already held (76 councils, 278 agencies).

## Done

- `registers/tenders`: the listing's position; its terms landed by hash; 4 tests (citation, quotes, no GETS
  address in the lane's code). Award notices untouched, their tests green.
- `registers/contract_disclosures`: catalogue capture (licence gate, 28-day refresh, copy-by-hash case), stdlib
  workbook reader, one profile by shape, `pub.agency_contract_costs` proven in `scratch_procurement_1_cd`: 80,860
  rows; check green, 837 printed totals compared, 0 wrong; 15 tests (one slow), mutants caught.
- `registers/council_procurement`: survey of 45 councils, a watch of four terms pages, profile, 11 tests.
- 122 requests through the gate (121 survey by day, one file at 22:00), 13 failed reads, none retried.

## Waits on Arthur

- Queue `whether-to-ask-the-ministry-to-read-the-gets-listing` (default: not captured).
- Queue `whether-to-ask-councils-for-their-award-lists` (default: not captured; Dunedin first).
- The existing letter to the ministry (card `the-ministry-s-gets-files-answer-403`) is unchanged.
