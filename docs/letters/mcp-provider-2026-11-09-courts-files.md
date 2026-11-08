# A second note for the ingest MCP (9 November 2026)

From QueryNZ. Thank you for the download fix: the test record and all 159 waiting FMA files arrived and
every one matched.

## 107 files in the `courts` corpus come back different from their record

In the `courts` corpus, 107 of 62,891 records hand over a file whose sha256 is not the one the record
promises. Your own `delivered_sha256` agrees with what we receive, so the bytes are sent faithfully. They
are just not the bytes the record says were captured. We take none of them, because we cannot tell which is
the real capture.

They are all www.courtsofnz.govt.nz HTML pages, seq 399 to 8534. Examples:

| seq | address | the record promises |
| --- | --- | --- |
| 399 | https://www.courtsofnz.govt.nz/cases/r-v-l | e62535957782… |
| 518 | …/cases/a-person-or-person-unknown-and-ngai-tupango-hapu-inc-v-tea-custodians-bluestone-limited/++resource++courts-contenttypes.css | ca8efbe69305… |
| 519 | …/same case/sendto_form | ca8efbe69305… |

Records 518 and 519 promise the same hash for two different addresses, which suggests the record's hash and
the stored file have come apart. That could happen if a page was fetched again and the new copy overwrote
the old one, or if a file was re-saved after capture.

Please either serve the bytes that match each record's hash, or, if the file has changed, issue a new
record with the new file's own hash. Then tell us and we will fetch them again.
