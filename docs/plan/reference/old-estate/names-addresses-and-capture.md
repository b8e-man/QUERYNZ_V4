### Names, addresses and capture

| Piece | Where | Faults on record | Verdict |
| --- | --- | --- | --- |
| Name functions | Copies in `registers`, `query`, the graph writer and the document reader | Seven divergent copies. One drops macrons, so Rāwiri and Rawiri differ. The two party-name functions disagree on 6 of 78 labels; a fuzzy rule folds New Labour into Labour. One page never called its fold, so 104 donors were published under more than one name | Take the rules and tests. Write one function |
| Address keys | In `registers` | The street key returns nothing for PO boxes. An older key dropped street numbers under three digits; 160 folds were withdrawn for it. One address holds 1,060 companies | Rebuild. Address never confirms alone |
| Fetch gate | `ingestion/fetchgate.py` | 35 older fetchers bypass it. The standard robots reader in Python is over-permissive and must not make permission decisions | Take. No new lane bypasses it |
| Landing | `ingestion/landing.py` | Five older entry points register a document before landing it, so a failed landing is never retried. Five of thirteen writers bypassed the wrapper | Take the one wrapper only |
| Headed browser | `ingestion/newsscrapers/browserfetch.py, ingestion/hansard/scraper.py; the lock helper is ingestion/browser_profile.py` | A challenged page is dropped. After an unclean exit the browser leaves a lock that blocks every later launch; clear it only if its owner is dead | Take. A challenged read stays a failed read |
| Coverage scan | The `querynz-coverage` job | For 86 of 222 source-and-weekday pairs the test reduces to "published at all". When half the sources are thin on one day, it is our outage, not theirs | Take as is |
| Charities lane | `ingestion/charities` | Client not on the fetch gate; its documented host no longer resolves; officers land with no person key; its timer had never fired at one audit | Take the idea, not the code |
| Award notices | `ingestion/gets`; tables `bulk.gets_*` in `nzbn_canonical` | Loaded by wipe and reload, refreshed by hand each quarter, no scheduled job, never read | Take the data |
| Gazette register | `data-layer/gazette_register` | Its schema file has drifted from the real tables. Its gate records a failure and still exits clean. 35,938 notices unread | Take after fixing the gate |
| Courts register | `data-layer/courts_register`, `ingestion/courts` | Fed by nothing; about 67 documents quarantined; suppress lever points at the old graph | Take in step 5 |
| Disqualified directors | `ingestion/companies_office` | The derive writes three tables that have no definition anywhere | Rebuild the tables, take the derive |
| Regulator actions | `ingestion/comcom`, `ingestion/fma`, `ingestion/worksafe` | 128 records parsed and read by nothing; the Act section is empty on all | Build the read |
| Amended filings | `registers/supersede.py` | "Prefer the amendment" is wrong in at least one case; unmatched pairs are reported | Take as is |
| Table definitions | `schema/nzbn_canonical.sql` and code | Tables were created piecemeal with no replayable chain; seven writers sat outside the package | New estate: every table defined in one place |

