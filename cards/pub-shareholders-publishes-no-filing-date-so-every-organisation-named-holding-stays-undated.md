# pub.shareholders publishes no filing date, so every organisation-named holding stays undated under ruling 125
kind: finding
state: open
use-case: board (4.9, the Rank Group search of ruling 119); 4 counterparty; 7 phoenix; 14 post-settlement
session: links-5
opened: 2026-10-30
owner: companies (registers/companies), with links

Ruling 125 judges a body's "alive" on the row's own date, and names the
shareholding's filing as a holder row's date. `pub.shareholders` carries no
date column (its columns: key, entity_key, nzbn, company_number,
shareholder_type, name, holder_nzbn, shares, allocation_status, in_latest,
first_file, last_file, suppressed, source_note, document, page, place,
read_from, reader, profile, profile_version, loaded_at), so the links lane
reads every holder row with no `started_on`, and the 1,170 organisation-named
holder rows (446 of them naming a body on the four registers; the Rank
Group holders among them) all stay near under `organisation-name@1` with the
reason "undated". Nothing else in the lane can date them: `first_file` and
`last_file` name monthly files, not the shareholding's filing, and the lane
does not reach into `registers/`.

Asked of the companies lane: publish the shareholding's filing date on
`pub.shareholders` (the date the holding was filed, or where the register
gives only the file it first appeared in, that file's month as a dated
column the links can read, said so in the lane's spec). When it lands, the
links lane reads it as `started_on` in `links/rows.py` (`SOURCES`, the
shareholders entry: two `NULL::date` columns) and the holder rows are judged
like every other; no rule changes. Measured today, read-only: 410 holder rows
name exactly one body and 36 several, so about 400 confirmations wait on the
date. Not worked here.
