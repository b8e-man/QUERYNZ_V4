# Instructions for the ingest MCP (9 November 2026)

From QueryNZ. Five requests, most urgent first.

## 1. Fix `download` for the `estate-*` corpora (urgent)

`download` fails on every record in every `estate-*` corpus, with "Error executing tool download". It works
on the `courts` corpus.

The cause looks like the `file` field. Its path is doubled:

    /opt/data/querynz-estate/sources/fma/opt/data/querynz-estate/store/9b/9b027b6a…

It should probably be `/opt/data/querynz-estate/store/9b/9b027b6a…`. We saw the same doubling on
estate-fma, estate-courts-era, estate-council_minutes, estate-building_practitioners and estate-worksafe.

To test: `download(record_id="9b027b6a799e1fdf435f18062905872951c37febbf74885cb9c8c07d9a53daa6",
corpus="estate-fma")` should return the page's bytes.

We are waiting on 159 FMA files now, and thousands across the other corpora. Please tell us when it is
fixed. We will fetch everything that waited.

## 2. Keep these nine sources collecting

We stopped collecting these ourselves on 9 November because you are collecting them. Please keep them
running every night:

estate-fma, estate-worksafe, estate-commerce_commission, estate-councillor_interests,
estate-building_practitioners, estate-local_elections, estate-council_minutes, estate-courts-jdo,
estate-courts-era.

If one stops, or a site starts blocking you, please tell us. We still collect it if you don't.

## 3. Start collecting these five again

You hold only the copy we handed over on 5 November. Nothing new has arrived since. We are still
collecting them ourselves and will stop once yours are current:

| Corpus | Source | Note |
| --- | --- | --- |
| estate-charities | Charities Register (www.odata.charities.govt.nz) | an open OData service |
| estate-real_estate_authority | REA decisions (decisions.dotnous.com, www.rea.govt.nz) | |
| estate-tenancy_tribunal | Tenancy Tribunal orders (forms.justice.govt.nz) | the site reset our connections on every order PDF from 25 October; 13,069 of 33,847 orders still to get |
| estate-iwi_directory | Te Kāhui Māngai (www.tkm.govt.nz) | a weekly walk is enough |
| estate-settlement_commitments | Te Haeata (tehaeata.govt.nz) | behind a login: watch the public pages only, never log in |

## 4. Take on these sources (nobody collects them now)

Each was loaded once from the old system and nothing keeps it current:

- Party donation and loan returns, party expenses, statements and broadcasting allocations, the register of
  parties (Electoral Commission, elections.nz)
- Candidates, electorates and the results (elections.nz)
- MPs' register of pecuniary and other specified interests (parliament.nz)
- MPs' and ministers' expenses (parliament.nz, ministerial expenses releases)
- Party boards as each party's website states them: walk each registered party's whole site from its
  homepage; do not hand-pick pages

Also: confirm whether estate-grants includes the Lottery Grants Board "record of grants" pages on
www.communitymatters.govt.nz. That site blocks us (HTTP 403).

Do not collect: fyi.org.nz, any NZME masthead (the NZ Herald included), or OpenLaw.

## 5. Fill these gaps in what you already serve

**Parliament**
- bill texts, and bills before the 43rd Parliament
- select committee reports: you hold 2,500 of the 10,970 the source lists
- select committee evidence and submissions: 16,931 of about 1.1 million
- written questions before 2003 and after 1 October 2026, with their 44,584 attachments
- SOP and submission files
- the hash each report and paper file was captured by. About 4,800 come without one, so we cannot check
  them and take none.
- tabled papers: page 40 of the API answers HTTP 500 on every route

**Hansard**
- everything before 11 February 2003
- the corrected version of the 35 sitting days from 28 April 2026
- sittings after 23 September 2026

**Ministers' diaries**
- September and October 2026
- the PDF address of 119 releases
- the hash each release PDF was captured by

**GETS**
- awards for tenders before August 2026, with supplier and award date
- the future and late lists

**Beehive**
- the 67,527 page bodies your pipeline shows as queued

## Rules that apply to all of it

- Be polite: one request at a time, off-peak where you can, nothing fetched twice.
- robots.txt is read for one thing only: a stated crawl delay, which is honoured.
- Never solve a challenge or CAPTCHA, never use a login that is not ours, never get around a block. A site
  that blocks or throttles you is left alone; tell us.
- A publisher who asks you to stop is obeyed.
- Every file carries the sha256 of the bytes as captured, and `download` returns exactly those bytes.
