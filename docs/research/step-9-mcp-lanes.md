# Step 9, tranche 5: six lanes read the MCP's copy (10 November 2026, night)

Stream A3 of the integrator session. On 9 November the boxes stopped crawling nine sources the ingest MCP now
gathers (3429166). FMA came back first, reading the MCP's copy (`--from-mcp`, d1e125c). This record covers the
other six lanes that went orange: what each lane's MCP copy holds, the `--from-mcp` mode each capture now has, and
the proof that what the mode takes equals what the old capture landed. Facts come from `mcpsource.files` (the pull's
record of each estate-* file: url, seq, sha256, state), the lanes' own capture tables, and the `corpora` tool. The
reading proofs ran each lane's own reader over both copies' bytes, opened by hash from the store. Every proof can
fail: run on mismatched pairs, it reported every pair as different.

## The pattern

Each capture gets `MCP_CORPORA = ("estate-<lane>",)` and `from_mcp(conn)`. That function returns the run's opener
(`support.mcpsource.replay.opener`, the newest copy of each address, `NotHeld` when there is none), with no pacing
and no off-peak hours. `main` takes `--from-mcp`. Three things go beyond FMA's version:

- **A copy that is a challenge page is a block** (`fg.looks_challenged`), as it would be from the web (hard limit 6).
  `replay.opener` returns every copy as a 200, so without this check a challenge page held by the MCP would be read
  as the page itself. FMA's `--from-mcp` does not have this check (see "For the integrator").
- **An address the copy does not hold yet holds no host and spends nothing.** In council minutes, building
  practitioners and local elections, `NotHeld` used to be treated as a transport failure. That meant a host was held,
  a document was marked failed forever, or the run stopped after three failures in a row. Now the address stays due
  and is asked again on the next run, after the pull may have brought it.
- **The gate is not asked** (councillor interests and local elections, where an injected opener already skips it).
  No request leaves the boxes. A host the *lane itself* holds still stays held (see "For Arthur").

Each lane has `tests/test_<lane>_from_mcp.py`, which runs on invented pages with the web and the gate made to fail
if asked. Its checks fail when the opener is left as the web's, when the corpus is wrong, when the hours bind, when
the challenge check is removed, and (where it applies) when `NotHeld` counts as a failure. Each mutant was tried and
caught. Each file also checks that the job in jobs.toml carries `--from-mcp` and that qv4-mcp-pull takes the corpus.

## Per lane

| Lane | Corpus held in our store | Proof | Job |
| --- | --- | --- | --- |
| commerce_commission | 3,007 of 3,007 records (1,726 copied from our store, 1,281 fetched by the provider 5 to 7 Nov) | 1,686 of our 1,730 entry hashes are in the copy. The 44 missing were captured on 6 Nov, after the handover copy. 18 of 18 listing pages are held. 200 of 200 sampled entries whose newest copy has other bytes read the same (`read_entry`). The bytes differ only in a script nonce and asset stamps. The copy's 18 listing pages carry 1,259 cards: 1,210 are in our last pass and all 1,210 match. A pass from the copy would fetch **0** entries. | **on**, `--from-mcp` |
| councillor_interests | 566 files (450 copied, 116 provider) | 391 of 391 documents: same address, same sha256. Pages: 56 of 57 held; 30 have the same bytes, and all 26 others read the same (`register_links` and `read_register`). The copy has 521 addresses to our 448. | **on**, `--from-mcp` |
| council_minutes | 1,068 of 1,069 | 986 of our 990 minutes PDFs are held, 965 with the same newest bytes. 21 of 21 listings are held. The copy's newest listings name 987 minutes PDFs, all already ours, so a run fetches nothing new. | **on**, `--from-mcp` |
| building_practitioners (decisions) | 81 of 81 list pages | Every page has newer bytes from the provider. Read across all 81 pages: 790 decisions on each side, 788 the same, 1 changed (citation and links: re-published), and 1 swapped for another. The site changed between the two fetches. | **on**, `--from-mcp` |
| building_practitioners (register) | 19,075 of the 20,870 records pulled (the provider adds about 3,000 a day) | 26 of 26 searches are held, all with newer bytes. They list 26,729 practitioners, 26,712 of them ours, and 17 that are new. 198 of 200 sampled practitioner pages read the same; 2 differ in region and contacts (updated). The copy holds 13,213 of our 26,977 practitioner pages. A page it lacks is asked again the next night and does not stop the run. 4 of the 17 new practitioners' pages are held now. | **on**, `--from-mcp` |
| local_elections | 2,887 landed or held, 1,987 waiting | 2,004 of our 2,005 returns: same address, same sha256. 87 of our 89 listing pages are held, and all 87 read the same: 2,339 returns and 29 sub-listings on each side. Of our 97 wanted files, 71 are in the copy, still waiting on the pull. They stay wanted until it lands them. | **on**, both jobs `--from-mcp` |
| worksafe | **0**: all 1,439 files still waiting on the pull | All 665 of our documents' sha256 are in the copy's records (the newest copy of each has other bytes: refetched). 35 of 35 listing pages are in the copy. No reading proof yet: no bytes are in the store. | **set aside**: `--from-mcp` is built and tested, but the job stays off |

WorkSafe is set aside because the copy is not in our store yet, not because it lacks anything. Switched on now, the
run would read nothing and could go green over nothing. Once qv4-mcp-pull lands estate-worksafe's files, the proof
to run is the commerce_commission one: the reader over each pair (newest copy, our latest capture), then the job
switched on with `--from-mcp`.

## For the integrator

- **To deploy:** the jobs.toml blocks for qv4-commerce-commission-capture, qv4-councillor-interests-capture,
  qv4-council-minutes-capture, qv4-building-practitioners-capture, qv4-building-practitioners-register-capture,
  qv4-local-elections-listings and qv4-local-elections-files are switched on with `--from-mcp`. They need the usual
  catalogue load and timer install. The FMA proof did the same.
- **The lights.** `checks/source_lights.py` gives these lanes `asks=(their capture jobs)`, so a gate hold lights a lane
  whenever its capture is on. With `--from-mcp` the capture asks no host. Unless this changes, a gate hold on a lane's
  hosts will light it again (on 10 November the gate holds dunedin, fndc, gdc, huttcity, kaipara, mdc and selwyn, all council
  hosts that the councillor-interests and local-elections positions name; it holds nothing of comcom, worksafe, lbp or
  infocouncil). Suggested change, in `held_hosts`: count only asking jobs whose command lacks `--from-mcp`. Or, per
  lane, `asks=()` together with `hosts=()`. The corpora lines, should the lanes be watched on the pull's record (the
  survey's caution stands: a pull that runs out of budget before the estate-* corpora turns these red):
  `corpora=("estate-commerce_commission",)`, `corpora=("estate-councillor_interests",)`,
  `corpora=("estate-council_minutes",)`, `corpora=("estate-building_practitioners",)`,
  `corpora=("estate-local_elections",)`, `corpora=("estate-worksafe",)`.
- **`checks/tests/test_source_lights.py::test_the_nine_stopped_sources_on_the_real_lanes` now fails, as it should.**
  It asserts that the six lanes are orange because their captures are switched off. On the real catalogue the
  lanes now come out like this: commerce_commission, building_practitioners and council_minutes green; worksafe
  orange (still off); councillor_interests and local_elections orange on the test's fndc hold, which is the asks
  problem above. The test's `stopped` tuple becomes `("worksafe", "courts")`, the four that run again join FMA's
  green line, and its fndc line holds once the asks change is made.
- **FMA's `--from-mcp` has no challenge check.** The same five lines (`fg.looks_challenged` on the copy's body) would
  close it. This is better done once, in `support.mcpsource.replay.opener`, which this stream does not own.

## For Arthur

- **Hosts the lanes themselves hold.** The councillor-interests lane holds 11 council hosts after blocks or
  challenges in October. The MCP's copy has 75 records on three of them (mpdc 51, dunedin 21, gdc 3). The lane does
  not read them: a hold stays until a person reads why. Whether a copy the provider gathered may fill in a council
  the boxes were blocked from is your decision. No default.
- **The provider's freshness.** Commerce Commission, WorkSafe and councillors' interests have had no arrivals since
  7 November; council minutes and local elections none since 8 November. The lanes now keep pace with the copy, so
  a lane is only as fresh as the provider makes it.
