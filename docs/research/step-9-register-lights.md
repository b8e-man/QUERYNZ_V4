# Step 9, tranche 5: the orange and grey registers (9 November 2026, evening)

Stream A of the integrator session. Facts from `scheduler.queue`, `scheduler.runs`, `scheduler.pieces`,
`pub.court_documents`, qv4-mcp-pull's run record, the ingest MCP's `corpora` tool and the lights computed live
(`python -m checks.source_lights --print`, 08:43 UTC). The three reds (insolvency, LINZ, grants) are the
integrator's and are not covered here.

Classes: (a) ours, fixable now; (b) ours, running (a reader or pull catching up); (c) the MCP provider's;
(d) needs a person (a host the fetch gate holds: ruling 141).

## For Arthur

- **Seven registers stopped updating on 9 November, and four of them showed green.** The boxes stopped their
  captures (3429166). Their loads kept running on their clocks over what had already landed, so the board said
  "up to date". The lights now show orange for them: Commerce Commission, WorkSafe, building practitioners,
  council minutes, councillors' interests, local elections, and the JDO/ERA part of courts. Each goes green
  when its collector reads the MCP's copy, as FMA does now (the copying plan, steps 2 and 3).
- **The MCP provider has not refreshed six of those sources since 7 or 8 November.** `corpora` shows no
  arrivals in 24 hours for WorkSafe, Commerce Commission, councillors' interests (newest 7 Nov), and local
  elections, council minutes, building practitioners (newest 8 Nov). Only FMA, JDO and ERA are fresh. That is
  for the provider.
- **The Tenancy Tribunal still needs a person** to clear forms.justice.govt.nz at the fetch gate, or the
  provider to resume collecting it (copying plan, step 5). 13,069 orders are still waiting.
- The council hosts the gate holds (Dunedin, Gisborne, Kaipara, Far North and others) no longer stop anything.
  The boxes stopped asking them on 9 November, so clearing them now would change nothing. Whether the MCP's copy
  holds those councils will be known once the lanes read it.

## The oranges

| Register | Cause (from the facts) | Class | Done | Owed, by whom |
| --- | --- | --- | --- | --- |
| parliament | Declared gap: what the MCP lacks (bill texts, most select committee reports and evidence, SOP and submission files, file hashes, written questions outside 2003 to 1 Oct 2026). Pull and load run well. `corpora`: no written question has arrived since 23 Oct. | c | Nothing; the gap stands. | Provider (request 5 of the 9 Nov letter) |
| hansard | Declared gap: the MCP has nothing before 11 Feb 2003, misses 35 corrected days, and has no sitting after 23 Sep 2026. Re-measured: `parliament-hansard-debates` still runs to 2026-09-23, newest arrival 26 Oct. | c | Nothing | Provider |
| ministers_diaries | Declared gap: PDFs come without their capture hash, Sep and Oct 2026 are missing, and 119 releases have no address. Re-measured: `parliament-diaries` still runs to 2026-08-31. | c | Nothing | Provider |
| tenders | Declared gap: GETS awards only for 1,102 tenders, with no supplier or award date. The award files from data.govt.nz stay on the boxes, and their jobs run well. | c | Nothing | Provider |
| courts | (1) 14,403 waiting on the text reader and 218 on the page reader. (2) The JDO and ERA captures were switched off on 9 Nov. The pull copies `estate-courts-jdo` and `estate-courts-era`, but the courts load does not read them. (3) The MCP lacks part of the back catalogue (declared). | b + a + c | (1) The reader ran 11:37 to 20:20 and finished all 14,403 pieces, about 1,650 an hour. The light only changes when the next load replays them (qv4-courts-load, 04:40 NZDT 10 Nov, about 3 h): the text-reader wait should be near 0 by about 08:00. (2) The light now names the switched-off captures. The stale gap line ("walking the back catalogue, 10 to 12 nights") is rewritten. | Integrator: an adapter so the courts load reads the estate-courts-jdo/era copies (copying plan step 3). Integrator: qv4-courts-pages has no clock and is not chained (last run 30 Oct), so the 218 scanned documents never drain. They need a `then` or an enqueue, which uses a page-reader profile swap. Provider: back catalogue. |
| councillor_interests | Was orange on 4 to 5 gate holds (fndc, huttcity, mdc, selwyn) for a capture switched off on 9 Nov: a stale light. In truth the capture is off and the register stands at 9 Nov 00:30. | a (light) + c | Lane gets `asks`, so holds no longer light it. It is orange on the switched-off capture. The declared gap is reworded (the MCP gathers the source now). | Integrator: wire `--from-mcp` replay (copying plan step 2). Provider: refresh estate-councillor_interests (newest 7 Nov). |
| local_elections | The same: stale hold lines (4 hosts) plus 2,005 of 2,147 files held (31 failed), and the listings and files captures off since 9 Nov. | a (light) + c | As above: `asks`, switched-off line, gap reworded. | Integrator: an adapter (copying plan step 3). Provider: refresh estate-local_elections (newest 8 Nov; 4,680 files waiting in our pull). |
| tenancy_tribunal | The gate holds forms.justice.govt.nz (4 Nov). The capture is still on but asks nothing. The MCP holds only the 5 Nov copy. | d | Nothing (never cleared, never retried) | A person clears the hold, or the provider resumes collecting it (copying plan step 5) |

### Greens that were stale, now orange (same cause, 3429166)

| Register | Cause | Class | Done | Owed |
| --- | --- | --- | --- | --- |
| commerce_commission | Capture off 9 Nov; the load runs over the last capture (8 Nov 22:30) | a (light) + c | Orange via the new rule | Integrator: replay (step 2). Provider: no arrivals since 7 Nov |
| worksafe | Capture off; last capture 8 Nov 23:30 | a + c | Same | Same; the pull has 1,439 files still to fetch |
| building_practitioners | Both captures off; last capture 9 Nov 00:12 | a + c | Same | Integrator: replay for decisions and an adapter for the register |
| council_minutes | Capture off; last capture 8 Nov 22:15 | a + c | Same | Integrator: replay (step 2) |

FMA stays green. Its capture runs again from the MCP's copy (`--from-mcp`, d1e125c).

qv4-mcp-pull: the 13:00 run ended failed at 16:30, its 12,600 s budget used up. Every corpus was reached, with 0
caught and 0 drift. The 19:00 run is still leased, working through the estate-* files (JDO 14,634, local elections
4,680, ERA 6,634 waiting). Class b.

## The greys

All eleven are correct; none is stale from 3429166.

| Register | Cause | Class |
| --- | --- | --- |
| party_returns, parties, party_finance, house, mp_interests, expenses | Loaded by the merge gate's staging step; no update job on a clock | grey, right |
| party_boards | qv4-party-boards-load has no clock and nothing queues it (on demand) | grey, right |
| papers_past | ingest and index on demand (limit 17: searched, not mined) | grey, right |
| openlaw | No job (ruling 137) | grey, right |
| hdc_decisions | No job (a ruling on the Commissioner's terms is owed: Arthur) | grey, right |
| council_procurement | qv4-council-procurement-watch switched off (ruling 136) | grey, right |

## What changed

- `checks/source_lights.py`:
  - A new orange rule, `orange_switched_off`: when a lane has one update job switched off and another still running, the light is orange and says when the switched-off job last gathered anything. It clears by itself once the job runs again (as FMA's did).
  - A new `Lane.asks` field: the jobs that ask the lane's hosts. A gate hold lights the lane only while one of them is on. It is set for commerce_commission, worksafe, building_practitioners, courts, council_minutes, councillor_interests and local_elections.
- `checks/source_gaps.toml`: the courts walk gap and the two council gaps are reworded for 9 November.
- `checks/tests/test_source_lights.py`: three tests, plus the new rule added to the mutant scenarios. Two of the tests fail when the `asks` clause is removed; this was tried and seen.
- Not done: the estate-* corpora are not yet added to the lanes' `corpora`. Their files sit at the end of the pull's corpus list. A pull that hits its budget before reaching them would turn those lanes red as "failed before it reached". Better done with the replay wiring (copying plan step 4).
