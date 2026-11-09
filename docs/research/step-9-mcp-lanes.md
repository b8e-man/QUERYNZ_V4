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

## councillor_interests, ruling 159

Stream H, 10 November 2026. Arthur's ruling 159: the lane takes the provider's copy of councils that blocked the
boxes, since that copy has a different compliance relationship. `capture.from_mcp` now hands the walk
`lane_holds=False`: under `--from-mcp`, `Run.run` starts from no stored holds, and the gate is not asked (as before).
Neither hold is cleared. The 11 rows of `capture_held_hosts` and the gate's holds stay, and the boxes' own walk
(`lane_holds=True`, the default) still asks a held host nothing. A copy that is a challenge page is still a block
(hard limit 6). It holds its host in the table and for the rest of the run.

**What it takes now** (a dry walk of all 78 councils on the real copy, nothing written, compared with the same walk
honouring the holds):

| Council | Copy records | Taken | Through the lane's reader |
| --- | --- | --- | --- |
| Matamata-Piako | 53 (51 on www.mpdc, 2 on mpdc) | 2 pages and 51 documents, 51 distinct sha256, none held before | 21 PDFs have a text layer and name the register: read by the text reader. 30 have no text layer and wait for the page reader. The 2 pages are landing pages that link the documents. The load would call the council "per-member files". |
| Dunedin | 23 (21 on www, 2 on secure) | 1 page: the register page `REGISTERS` names | It prints the register itself, with no document linked. The text reader reads it (`recognise_page` passes), so the load would call it "html register, waiting: text reader". |
| Gisborne | 3 (one address, three copies) | nothing | `REGISTERS` has no address for Gisborne. The copy's one address is the council's "Page Not Found" page. |

The walk's totals went from 53 pages and 391 documents to 56 and 442. That is the 54 above and nothing else. Failed
reads went from 8 to 17: these are the other 8 held councils' addresses, which the copy does not hold. They are
`NotHeld`, so no host is held and each address is asked again next run. The 11 addresses on held sites that are not
taken are all off the walk: Dunedin's dog, premises, road-name and ePathway pages, and its own "Page Not Found" at
governance/elected-members/registers-of-interests, plus Gisborne's page. The 21 readable PDFs and the Dunedin page
make 69 text-reader pieces (412,026 characters). They are read by qv4-councillor-interests-read after the capture
and the load. No model was called here.

**Tests** (`registers/councillor_interests/tests/test_councillor_interests_from_mcp.py`):

- A held council's copy is taken and its hold stands.
- The three councils, as `REGISTERS` has them and held as the live record holds them, are read from the copy.
- A challenge copy on a held council still blocks.
- A challenge copy met in the run holds its site for the rest of the run.
- The boxes' own walk still asks a held host nothing.

Five mutants were tried and each was caught: from_mcp keeping the holds, run reading the holds always, the direct
mode dropping them, no challenge check, and the in-run hold dropped.

**For the integrator:** `support.mcpsource.replay.opener` serves every copy as a 200. Gisborne's and Dunedin's
"Page Not Found" copies are not reached by this walk. A copy of a 404 that a walk does reach would land as a page.
If the pull records the provider's HTTP status, the opener could carry it (stream F's file).

## tenancy_tribunal and real_estate_authority (10 November 2026)

Two more lanes get `--from-mcp`, as above: `MCP_CORPORA`, `from_mcp(conn)` (the replay opener, no pacing, no
off-peak hours), the challenge check, and `NotHeld` kept due. Neither corpus was in qv4-mcp-pull's list, so
`mcpsource.files` holds none of their records. Both are added to the pull's command (`estate-tenancy_tribunal`,
`estate-real_estate_authority`; their cadences were already in `checks/mcp_cadence.toml`). The proofs below
compare our capture tables with the MCP's own `records` (metadata: address, sha256, provenance), and the reading
proof uses bytes taken by `download`. Both corpora were read whole: 20,888 and 8,507 records.

**Beyond the six.** In both lanes `get` answers `NOT_HELD` for an address the copy lacks. That writes no set-aside
line, counts no failure, needs no rest, and three in a row do not stop the run. A month or year that is not held
stays unlisted. An order, or a case whose abstract or one of whose PDFs is not held, stays due. The Tenancy Tribunal
walk had no record of what it had tried in a run, so a not-held order would have come back in every batch. It now
keeps one, as the REA walk already did. Its challenge check reads the decoded body, because the listing service
answers gzip. The soonest-to-be-taken-down order (the Committee's oldest first, for REA) is kept for what the copy
holds.

| Lane | The copy | Proof | Job |
| --- | --- | --- | --- |
| tenancy_tribunal | 20,888 records: 20,777 order PDFs and 61 field-list listings from our store; 50 whole listings (ruling 143's shape) the provider fetched 4 to 8 November | All 20,778 of our order documents: same address, same sha256. The copy holds no order PDF we lack: the provider has fetched none. Our 69 listings are all in it, same sha256. Its 50 whole listings cover the window (November 2023 to November 2026) at our addresses, so a run lists every month whole from the copy. They name 33,444 orders. 181 are not in our table (earliest take-down 6 October 2029). 584 of ours are not named: 411 were published before the window, 157 of November 2023 have been taken down since, and 16 others are no longer listed. | **on**, `--from-mcp` |
| real_estate_authority | 8,507 records: 8,110 from our store, 397 listing pages the provider fetched 5 to 9 November | 3,063 of our 3,065 abstracts and 4,438 of our 4,442 PDF rows: same address, same sha256. The 2 cases missing (4 PDF rows) were captured on 9 November at 23:02, after the copy. All 319 listing addresses are held, and each newest copy has other bytes. Read by `parse_listing`, all 319 read the same (count, pages and rows). Across them they name 3,092 cases, all ours. On mismatched pairs, 0 of 319 read the same. A pass from the copy would fetch **0** cases. | **on**, `--from-mcp` |

**Orders neither side holds (Tenancy Tribunal).** 13,069 listed orders are not held by us or by the copy, and
another 181 are named only by the copy's listings: 13,250 in all. The earliest take-down date among them is
23 June 2028. Every order due to be taken down before that is held.

**Tests.** `registers/<lane>/tests/test_<lane>_from_mcp.py` run on invented pages, with the web, the gate and
`time.sleep` made to fail if asked. Each file checks that the job carries `--from-mcp` and that qv4-mcp-pull takes
the corpus. These mutants were tried in both lanes and each was caught: the opener left as the web's, the wrong
corpus, the hours binding, pacing kept, the challenge check removed, and `NotHeld` as a failure. Two more were tried
in the Tenancy Tribunal lane: the challenge check made on the gzip bytes, and no record of what was tried (caught
as the run never ending).

**Lights.** `checks/source_lights.py` gives both lanes `asks=(capture)` and their corpus. The gate's hold on
forms.justice.govt.nz (since 4 November) no longer lights the Tenancy Tribunal red, because the capture asks it
nothing. The hold is not cleared (ruling 141), and the boxes' own walk would still be red on it.
`test_the_tenancy_tribunal_held_host_is_red_on_the_real_lanes` now asserts both. The declared gap in
`checks/source_gaps.toml` still holds (13,069 wait), so the lane stays orange.

**For the integrator.** Deploy the pull's new corpora first. Until it lands their files, a `--from-mcp` run reads
nothing: every address is `NotHeld`, and the run goes green over nothing (WorkSafe's case). No `--from-mcp` run
was made here, because neither lane has a dry mode and the store holds no copy yet. The REA load job reads landed
abstracts only, so it is unchanged.

**For Arthur.** Under `--from-mcp`, the Tenancy Tribunal takes the provider's whole listings, which were fetched
after our gate held the host (because of connection resets, not a challenge). Ruling 159 settled this for the
councils that blocked the boxes. Whether it reaches this host is your call; no default. The provider has listed
but fetched no order PDF, so the 13,069 orders wait on it.
