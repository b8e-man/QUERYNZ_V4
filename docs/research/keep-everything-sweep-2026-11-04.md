# Keep everything: the sweep of the lanes (4 November 2026)

Ruling 142 (Arthur, 4 November 2026), with ruling 143's list of what it supersedes: every lane keeps everything its
source gives, whole. A suppression, removal, takedown or correction a source states is a flag beside the row (with a
date and the source's words where the source gives them), never a delete or a NULL. Identifying values (home
addresses, birth dates, emails, phones) live in the lane's `<lane>_private` schema, which `qv4_read` and
`qv4_product` are not granted; a suppressed name is kept there, keyed so the links can join. The checks red on an
address-like column stay on the pub views and the read-login schemas.

Every lane under `registers/` was swept except `registers/linz` (another session) and `links/` (another session).
Counts only; no value is printed here. Each section says where its counts come from.

Reloads queued by the integrator on 4 November 2026 once `qv4-links-build` released its lease (09:45): insolvency
(1453, done), courts (1458, done: 39,680 names kept in `courts_private.withheld_names`, every one flagged `suppressed`), commerce_commission (1459, done), fma (1460, done), worksafe (1461, done),
overseas_investment (1462, done), real_estate_authority (1463, done), building_practitioners (1464, done); the registry lanes queued
their own (councillor_interests 1465 done, charities 1466 done, limited_partnerships 1467 done, gazette 1468 red: the two suppressed `ba` notices now kept were counted "not taken by a
bankruptcy profile"; `registers/gazette/check.py` takes a suppressed notice by its flag, and gazette 1479 published green).

## Insolvency (registers/insolvency)

| File | Dropped before | Kept now | Live |
| --- | --- | --- | --- |
| `capture.py` `call`, `read.py` `strip`/`_DROP`/`strip_bytes` | Every address field and the month and year of birth taken out of each API answer before landing; the bytes as received only hashed | The answer landed whole, as received; the identifying fields also kept by field in `insolvency_private.identifiers` | Every answer from the next capture on (the 4 November 2026 answers and earlier stay stripped: their received bytes were never kept) |
| `capture.py` `apply_removal` | A removals-named estate's row deleted from `insolvency.estates`, its identifying fields deleted from `insolvency_private.identifiers`, its stored answers withdrawn | The row flagged `removed_on` (the API's `removedDate`) and `removal_seen_at`; its identifying fields flagged `removed_at` with the API's words; no answer withdrawn | 1,536 estates named by the removals so far; identifying fields the earlier removals deleted are not recoverable from the store |
| `capture.py` `keep_identifiers` | A detail answer deleted its estate's identifying fields before writing the new ones | A field a later answer no longer gives is flagged `gone_at`, never deleted | from the next capture |
| `load.py` `ledger`/`build`, `read.py` `why_withheld` | Estates withheld: removed after our latest answer, suppressed, annulled, past the display window, no name; answers withdrawn by a removal skipped | Every estate with an answer is read into `insolvency.estates` with `suppressed`, `suppressed_said`, `annulled_on`, `window_unknown`/`shown_until`, `removed_on`, `removal_seen_at`, `absent_since`; a suppressed estate's names kept by key in `insolvency_private.suppressed_names`; `withheld` replaced by `unanswered` (named, nothing to read) | published on live (qv4-insolvency-load, queue 1453): 13,563 estates, 13,556 read; 312 named by the removals after their answer (206 people, 106 companies) and 11 past their window, all withheld before; 0 suppressed; 7 unanswered (404, no answer ever held) |
| `load.py` `publish` | Rows the removals named between build and publish deleted | Flagged (`flag_removals`) | |
| `publish.sql` | `pub.insolvency_people`/`_companies` filtered to `shown_until >= current_date` | No filter; the views carry `suppressed`, `suppressed_said`, `annulled_on`, `past_window` (worked out on the day read), `removed_on`, `removal_seen_at`, `absent_since` | |
| `check.py` | Red on a staged row suppressed, annulled or past its window; red on identifying fields kept after a removal | Red on a suppression flag that is not the register's words, a suppressed row with a name in the row or none kept privately, a removals-named row not flagged, identifying fields from before a removal not flagged. The address-column check stays on the lane's schema and its pub views | |
| Profiles `insolvency-register-estate`/`-search`/`-removals` | v1: "landed with every address field and the month and year of birth taken out" | v2: landed whole, the terms as flags (no extract list; align.py does not hold this lane) | |
| `spec.md`, `pane.md`, `docs/legal/positions/insolvency-register.md` | The strip, the deletes, the window as a filter | The flags, as above | |

Tests: `test_nothing_is_stripped_from_an_answer` and the landed-whole assertion in `test_the_night_the_load_and_the_check` fail on the old code; the removal, suppression and identifying-field mutants are caught.

## registers/courts

Live counts are from the owner login on 4 November 2026, before this load (the courts schema as the 04:40 load left it). Counts only.

| File | Dropped or withheld before | Kept now | Live rows |
| --- | --- | --- | --- |
| `registers/courts/read.py` (`rows`, the people loop, the cases loop, `_suppressed`, `_words_for`, `_kept`) | A name a suppression covers went to `courts_private.withheld_names` as key, name and capacity only: nothing said which table the row was in, which document or citation it came from, or why it was covered | Each covered name is kept whole with `held_in`, `document`, `citation`, the counsel's `for_party`, `suppressed` = true and `suppression_words` (the source's words: the banner or order kinds the judgment printed, or the ledger order's reason). The row in `courts` keeps its role, its place and the `withheld` flag | 34,531 names, each now with its table, document, citation and the source's words: 3,691 party names, 30,350 model-read names, 490 case names |
| `registers/courts/suppress.py` (`withhold`, the lever) | An order set `people.for_party` to NULL and never saved it. Covered names were saved as key, name and capacity only | `for_party` stays in the row (the pub view still hides it on a covered row). The private row carries `held_in`, `document`, `citation`, `for_party`, `suppressed` and the order's reason as `suppression_words` | 0 today: the ledger holds no orders |
| `registers/courts/tables.sql` | `courts_private.withheld_names` (key, name, capacity) | The same table with the six new columns. The header now says what is kept and where | Rebuilt at the next load |
| `registers/courts/private.sql` (new; run by `load.publish` after `publish.sql`) | No row anywhere held a covered name in place | `courts_private.judgment_parties_whole`, `people_whole`, `cases_whole`: the rows with the names back in place, the flag and the words beside them, for the links lane. Not granted to `qv4_read` or `qv4_product`; no pub view reads them | 36,129 parties, 255,370 people, case rows as loaded |
| `registers/courts/model_read.py` (`PROMPT`, `DETAILS`, `parse_answer`, `_details`, `detail_rows`, `key_for`, `piece_key`; reader 3) | The prompt told the text reader to "never add an address, an age or a date of birth" | That rule is gone. The reader is asked for each person's details as printed (address, place of residence, age, date of birth, occupation, employer, email, phone, relationship, other). They are parsed into the closed kinds and written to `courts_private.identifiers` with `person` set to the people row's key. A person found in two parts keeps the details from both. Readings made under the two earlier prompts still stand (`rd.supersede`, both whole-document and piece keys) | 0 model details yet. They come with each document the reader reads under the new prompt: 2,926 documents are waiting on the text reader. The 13,508 documents already read keep their names; they get model details only if they are read again |
| `registers/courts/extracts.py` | No `details` field | `details` (`by: model`, kinds `model_read.DETAIL_KINDS`). `withheld_names.held_in` and `.citation` are housekeeping | — |
| `support/profiles/profiles.jsonl` (15 courts profiles, every one but `courts-scanned-document`) | `parties`, `people`, `for_party`, `suppression` and `case_name` said a covered name "is withheld" or "no ... name is published". There was no model details item | New extract iteration: 5 for the 10 judgment profiles, 4 for the other 5. It adds `details` (model, private, landing in `courts_private.identifiers.kind`, `.value` and `.person`) and rewrites `people`, `for_party`, `suppression`, `parties` and `case_name` as a flag with the name kept privately, landing in `withheld_names.suppressed`, `.suppression_words` and `.for_party`. Reading versions are unchanged, so no stored reading is orphaned | 15 lines appended |
| `registers/courts/check.py` (`_kept_privately`) | Nothing checked that a covered name was kept | Red on any party or model-read row flagged under a suppression whose name is not kept whole, with the source's words, in `withheld_names`. It counts the private names. The checks that a covered name stays out of `pub.court_*`, and that no address-like column appears in a pub view or a reading table, are unchanged | — |
| `registers/courts/spec.md`, `docs/legal/positions/court-judgments.md`, `specialist-court-and-authority-decisions.md`, `professional-disciplinary-tribunal-decisions.md`, `waitangi-tribunal-reports.md` | Said a suppression "withholds" names, a withdrawn decision "is withdrawn here too", and the lane "reads no address" | Facts as built: every name and detail is kept; a suppression or withdrawal is a flag with the source's words; covered names and details live in `courts_private` only | — |

Tests that fail against the old behaviour:
- `test_courts_caption.py::test_a_suppressed_name_is_kept_whole_with_the_source_s_words_never_lost`
- the added assertions in `test_a_suppressed_judgment_withholds_every_name_but_the_crown_s_and_an_initial` and `test_courts_shapes.py`
- `test_courts_model_read.py::test_the_reader_asks_for_every_detail_and_keeps_them_privately_tied_to_the_person` and `test_a_person_in_two_parts_keeps_the_details_both_parts_print`
- in `test_courts_lane.py::test_the_lever_dry_runs_by_default_and_withholds_on_execute_across_the_case`: every name the order covers is kept with the order's words, and no flagged people row is without its kept name
- `test_courts_extracts.py`: the ruling 142 iteration, field by field

Two `test_courts_lane.py` assertions had expected the sample's 16-page ERA determination (b969c55c2414) to be waiting on the text reader. `qv4-courts-read` has since read it under the previous prompt, so they now accept "read" as well. That change is unrelated to ruling 142.

Commit 784b6a8 is on main; the release is at 09f3688. The live reload has not been queued yet because `qv4-links-build` was leased. `qv4-courts-load` brings in the new columns and the `_whole` views at its next run, either from the queue once links-build has finished or nightly at 04:40. Until then the live `withheld_names` has the old three columns.

## Regulator and decision lanes (fork: commerce_commission, fma, worksafe, overseas_investment, real_estate_authority, building_practitioners, hdc_decisions, tenancy_tribunal, openlaw)

Counts only. Measured on 4 November 2026 by building each lane from the live capture into a scratch schema
(`querynz_v4_sample.scratch_<lane>_full`; REA in `querynz_v4.staging_real_estate_authority_session`), owner login.
The published tables were not reloaded: `qv4-links-build` was leased (queue id 1439, since 07:45) the whole time.

| Lane | File | Dropped before | Kept now | Rows (scratch build) |
| --- | --- | --- | --- | --- |
| commerce_commission | `read.py`, `load.py`, `tables.sql`, `publish.sql`, `check.py` | a suppressed party's name; a suppressed case's title; the contact person; a case the register stops listing left the view | suppressed names and cases in `commerce_commission_private.suppressed_names` / `suppressed_cases`; contacts in `.contacts`; a de-listed case stays with `taken_down_on` (ruling 143) | 1,684 cases, 2,446 parties; 235 contacts; 0 suppressed names (the 80 'Commission withholds the name' parties print no name); 335 taken down 29 Oct (of 1,194 listed 21 Oct, 335 absent 29 Oct; only 9 share a card with a new entry: removal or a change of the listing's scope, not established) |
| fma | same set | a suppressed party's name; a suppressed action's title, summary, outcome, url; a warning's address, website, email, phone, bank fields; a de-listed action | `fma_private.suppressed_names`, `suppressed_actions`, `warning_fields`; `taken_down_on` | 802 actions, 612 parties; 3 suppressed names, 3 suppressed actions; 2,102 warning fields; 1 taken down |
| worksafe | same set | the code or word printed in place of a withheld party's name; a withheld action's title/url; every unread label row and h2 section (facts in brief, incident, lessons) | `worksafe_private.suppressed_names`, `suppressed_actions`, `page_sections`; `taken_down_on` | 665 actions, 668 parties; 24 suppressed names; 24 suppressed actions; 4,695 page sections; 0 taken down |
| overseas_investment | `capture.py`, `read.py`, `load.py`, `check.py`, `publish.sql` | the land address in the investment statement (withheld from every view); the rationale's address-bearing text; a withheld party's origin; every unread headed row | the statement published whole with `addresses_named`, rationale whole with `rationale_names_address` (ruling 143: a land address, not a home address); withheld parties' values in `overseas_investment_private.withheld_values`; every headed row in `.page_rows`; `taken_down_on` per decision | 1,295 decisions, 2,911 parties; 28 withheld values; 12,540 page rows; 0 taken down |
| real_estate_authority | `capture.py`, `read.py`, `load.py`, `check.py` | a suppressed party's name and licence number; every abstract field not read (reasoning, complainant, a suppressed decision's penalty) | `real_estate_authority_private.suppressed_parties`, `.abstract_fields` | 3,063 decisions, 1,573 parties; 1,585 abstract fields; 7 suppressed decisions, 0 suppressed parties (those abstracts print no party name; 17 of their fields kept) |
| building_practitioners | `read.py`, `register.py`, `load.py`, `tables.sql`, `publish.sql` | Board decisions past the 3-year window (view WHERE); a suppressed decision's name, number, region, urls; every summary; the register page's postcode, email, phones, fax, website | the view holds every decision with `window_ends_on`, `past_window`, `taken_down_on`; `building_practitioners_private.suppressed`, `.summaries`, `.contacts` | 790 decisions; 7 suppressed; 784 summaries; 51,219 contact values over 8,792 practitioners; 2 taken down |
| hdc_decisions | `read.py`, `load.py`, `tables.sql`, `publish.sql`, `check.py` | the page heading; the parties block; a named practitioner's name; every value the consumer-detail guard refused; a page the Commissioner stops listing | `hdc_decisions_private.page_fields` (heading, party lines, named individuals with role, each guarded value with its kind); `taken_down_on` | held (no authorisation on file): nothing loaded; no count |
| tenancy_tribunal | `capture.py`, `tables.sql` | the listing was asked with a field list: party names, tenancy address and every other field never fetched (ruling 58) | the listing asked whole; each row kept in `tenancy_tribunal_private.listing_rows` (ruling 143); months read with the field list re-listed once (`listings.whole`) | 0 until the next nightly capture (37 months to re-list) |
| openlaw | none | not changed: withheld names and suppressed titles already kept in `openlaw_private.party_names` / `case_titles`; "never expanded" means a court's anonymisation is not invented back; counsel are not asked for, but the lane is dropped (ruling 137) and captures no more, so widening the query buys nothing | — | — |

## Registries lanes (fork of integrator-9d788fb)

### councillor_interests (commit 709b1ef)

| File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- |
| registers/councillor_interests/read.py | a category whose heading named real property, land, a home, an address or a contact, or a spouse's or partner's interests, skipped (counted by heading); an entry shaped like a street address, an email or a phone number dropped | every category a row, flagged `real_property` / `of_partner`; an address-, road-, title-, email- or phone-shaped entry kept in `councillor_interests_private.entries` (key, ordinal), counted in `private_entries` | structured pages: real-property and partner rows now kept (part of the 1,409 below) |
| registers/councillor_interests/model_read.py | prompt 1 told the model to empty real property's entries, copy no address, road, email or phone, and leave out a spouse's, partner's or family's entries; `kept` and `_store_parsed` dropped the same from rows and from the stored reading | prompt 2 asks for every entry as printed; `kept` keeps every category with its flags; the stored reading is the whole answer; a document not yet read under prompt 2 replays its prompt-1 reading | staging build on live (4 Nov): interests 7,538 -> 8,947 (+1,409 rows: 1,364 real property, 45 spouse/partner categories; 53 rows flagged `of_partner` in all); `private_entries` 1; re-read queued (qv4-councillor-interests-read, row 1445, 371 documents) to fill the entries prompt 1 left out |
| registers/councillor_interests/load.py, tables.sql, publish.sql | `read_withheld` (categories never read) | `read_flagged` (flags by heading and count); interests columns `real_property`, `of_partner`, `private_entries`; private twin `councillor_interests_private.entries`; `pub.councillor_interests` carries the three flags | private schema not granted to qv4_read (checked on staging) |
| registers/councillor_interests/check.py | red on any real-property or partner category in `interests` | red on such a row without its flag, on an address-shaped entry in the published entries, and on qv4_read/qv4_product seeing the private twin | staging check green |
| support/profiles/profiles.jsonl | no extract lists | interests-register-pdf-text v2, interests-register-html-text v2, interests-register-html-clause-rows v2, each with an extract list (iteration 1), prompt 2 | |
| spec.md, views.md, pane.md, README.md, docs/legal/positions/councillors-registers-of-interests.md | "never read" wording | facts of what is kept and where | |

### charities (commit 7b9e4fd)

| File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- |
| registers/charities/publish.sql | `pub.charities.address_for_service` NULL unless the charity is an incorporated society, a company or a Charitable Trusts Act board (ruling 64's default) | the address for every charity, `address_not_body_corporate` beside it (ruling 143) | 20,017 addresses newly on the view (of 45,903 held) |
| registers/charities/read.py, load.py, tables.sql | an address part holding an email address dropped (counted) | kept whole in `charities_private.address_parts` | 3 |
| registers/charities/read.py, load.py, tables.sql | an officer's name field holding a date or reading as an address withheld (NULL, counted); an officer with no other name part set aside | kept whole in `charities_private.officer_name_fields`, `name_note` on the row; the officer kept with an empty name | 26 fields (19 officers); 0 officers had been set aside |
| registers/charities/read.py (`pages`, `absent_since`), load.py, check.py, publish.sql | a build read the newest full copy only, so a row the register later withdrew or restricted left the tables | every full copy read; a row only an older copy holds is kept with `absent_since` (the newer copy's day); the register-count check counts only rows it still holds | 0 today (one full copy per set so far; the next is due about 17 November) |
| spec.md, pane.md, docs/legal/positions/charities-register.md | "withheld", "shown only for a body corporate" | facts of what is kept and where | |

Staging build on live (`staging_charities_sweep`): check green.

### limited_partnerships (commit a67bc6f)

| File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- |
| registers/limited_partnerships/read.py, load.py, tables.sql, publish.sql | a role other than `Partner` (a person authorised for service) counted, not read | every role a row in `partners`, `role_type` and `general` beside it | 26 roles |
| same | the answer's e-mail addresses, phone numbers and websites never read | `limited_partnerships_private.contacts` | 11 |
| same | a partnership's name the register withholds left NULL and not kept; a suppressed partner's name kept on a row in a schema the session login reads | both kept in `limited_partnerships_private.withheld_names` by the row's key; the row carries `name_withheld` / `suppressed` | 0 (none withheld today) |
| spec.md, docs/legal/positions/limited-partnerships-register.md | "never read", "blanked" | facts | |

Staging build on live (`staging_limited_partnerships_sweep`): check green.

### companies (commit f01e5cb)

| File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- |
| registers/companies/monthly.py, load.py, tables.sql | the monthly package's shareholder address columns and a retirement village's statutory supervisor's, registered office, premises and operator's address blocks never read | `monthly.package_addresses` reads each block as filed into `companies_private.package_addresses` (document, place, nzbn, number, kind, address jsonb) | measured on the companies-2026-10 package without a load: 207,462 blocks (205,434 shareholder, 493 statutory supervisor, 514 village registered office, 514 premises, 507 operator); filled at the next qv4-companies-load (not reloaded: a full load is large and nothing published changes) |
| registers/companies/monitor.py, tables.sql | a name the NZBN register withholds (namePrivateInformation) left out; an answer's e-mail, phone and website lists never read | both kept in `companies_private.lookup_withheld` (key, owner_key, kind, value jsonb, document); `ensure_private` makes the table on the next rebuild | fills as the monitor's answers are applied |
| spec.md, docs/legal/positions/nzbn-register-entities.md | "never read", "stays withheld" | facts | |

Left alone: the register's own published filters (what the Companies Office leaves out of its export).

### gazette (commit cb825e3; profiles aa3d690)

| File | Dropped before | Kept now | Live rows (staging_gazette_sweep, 4 Nov) |
| --- | --- | --- | --- |
| registers/gazette/read.py, load.py, tables.sql | a notice the Gazette's robots file disallows by number (a suppression request) set aside, never read | every line held kept whole in `gazette_private.suppressed_notices`; a `notices` row with status `suppressed`, title ''; no typed row read; never fetched from the Gazette | 2 notices |
| appointments.py | where an appointee lives (", of <town>"); an item not taken as a name | `gazette_private.kept_text` | 611; 470 |
| offices.py | a JP entry's address; a JP entry not taken; a judge's former description | `kept_text` | 5,680; 265; 464 |
| windingup.py, entries.py | the plaintiff's address for service; a plaintiff whose name runs into an address | `kept_text` | 30,394; 570 |
| restorations.py | each company's applicant and address | `kept_text` (place `company <n>`) | 31,581 |
| liquidations.py | the liquidators' contact lines after the signature | `kept_text` | 32,226 |
| bankruptcies.py | a record the reader cannot cut (its text never kept) | `kept_text` | 523 |
| prohibitions.py, publish.sql | a revocation's words, incl. the person it says was wrongly identified | `kept_text`; `in_error` on the reading, `superseded_in_error` on the revoked rows and `pub.gazette_prohibitions` | 1 revocation; 1 row flagged |
| support/profiles/profiles.jsonl | no extract lists | v2 of ten gazette profiles with extract lists landing in gazette_private | |
| spec.md, pane.md, docs/legal/positions/new-zealand-gazette.md | "never read" | facts | |

Left alone: an annulled bankrupt's and a revoked prohibition's name stay blanked on the pub views (the row and the name are kept in `gazette`, flagged by `withheld_by` / `superseded_how`); possessions' "part set aside" has no text to keep (the part is not found). Reload queued: qv4-gazette-load row 1468.

### iwi_directory (commit 154e720)

| File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- |
| read.py, load.py, tables.sql | every label of an organisation's entry outside the allowlist (people, phone, mobile, email, postal and physical address) counted by name, value never read; a contact paragraph; a kept label holding a contact value nulled | each value whole in `iwi_directory_private.entry_fields` (key, entity_key, label, value, document, place); not granted to qv4_read | published 4 Nov from staging: 1,804 values; check green |
| spec.md, README.md, docs/legal/positions/iwi-and-hapu-directory.md | "never read" | facts | |

Note: the lane's job skips a load when the walk is the one published (`unchanged`), so this was published from staging by `load.publish` directly.

## The remaining lanes (fork: sanctions, mp_interests, party_*, parties, candidate_returns, council_*, hansard, beehive, parliament, contract_disclosures, tenders, grants, disclosures, expenses, house, local_elections, settlement_commitments, papers_past)

Counts only. "Live" is the count on querynz_v4 after each lane was reloaded and published on 4 November 2026 (09:45 to 10:10 NZDT, after qv4-links-build released its lease). The new private tables are not visible to qv4_read or qv4_product (checked).

| Lane | File | Dropped before | Kept now | Live rows |
| --- | --- | --- | --- | --- |
| mp_interests | `registers/mp_interests/read.py`, `tables.sql`, `publish.sql` | a real-property declaration's text: NULL in `mp_interests.declarations` and `pub.mp_interests` (a copy in `mp_interests_private.declaration_text`) | the text whole in its row, `withheld` true beside it (the flag a product applies hard limit 15 by); the private copy stays | 5,452 declarations of 24,931 |
| sanctions | `registers/sanctions/read.py`, `load.py`, `tables.sql`, `check.py` | every address part but the country, passport and identity numbers, the lists' narrative comments; passport phrases cut out of names, aliases and positions with nothing kept | every element (UN XML) and every cell (Police, MFAT workbooks) of each listed record whole in `sanctions_private.details`, keyed by the listing; the views unchanged; the check red on a listing with no record kept | 107,612 values for all 3,736 listings: 4,914 address values, 3,840 identity-document values, 918 comments |
| tenders | `registers/tenders/read.py`, `load.py`, `tables.sql` | the supplier file's `Full Address` and website; the notices' overview, comments and tender-box address: never read | every column a notice's or a supplier's row does not carry, whole, in `tenders_private.fields`, keyed by the row; the views unchanged | 122,421 values: 29,880 supplier addresses, 25,190 websites, 29,303 overviews, 13,455 comments, 24,593 tender-box addresses |
| party_boards | `registers/party_boards/read.py`, `load.py`, `tables.sql` | contact lines (email, telephone) and the text of every set-aside line of a board section: never kept | every line of each page's board section whole in `party_boards_private.section_lines`, contact lines flagged `contact`; role rows unchanged | 12,999 lines, 462 of them contact lines; 2,876 role rows unchanged |
| council_minutes | `registers/council_minutes/minutes.py`, `load.py`, `read.py`, `tables.sql`, `publish.sql` | a public-excluded part and a public forum item: skipped before any reading, counted only; a meeting's venue: never read | every line of both parts whole in `council_minutes_private.part_lines` (part and part number beside); the standard template reads their resolutions and declarations, `part` beside each row (`pub.council_resolutions`, `pub.council_meeting_declarations` carry `part`); each meeting's venue in `council_minutes_private.venues` with `venue_names_address` | skipped before: 37,167 public-excluded lines (15,898 standard, 21,269 text profile) in 460 parts, 6,425 forum lines (4,093 standard, 2,332 text) in 427 items, all now in `part_lines`; 273 resolutions from public-excluded parts, 7 from forum items, 2 declarations from excluded parts now rows (5,883 open resolutions unchanged); 786 venues kept, 597 address-shaped |
| party_returns | `registers/party_returns/loans.py`, `load.py`, `private.sql` | a Part H lender block's guarantor (name and address), security and terms: read past, kept nowhere (the module said private; the code dropped it) | each lender block whole in `party_returns_private.loan_blocks`, keyed by the loan | 10 loan blocks (every loan row) |

Profiles (new versions, `support/profiles/profiles.jsonl`): `un-sc-consolidated-list-xml` v2, `nz-police-designated-entities-workbook` v2, `mfat-russia-sanctions-register-workbook` v3, `gets-award-notices-current` v2, `gets-award-notices-historic` v2, `gets-supplier-data` v2, `party-website-board-page` v2, `council-minutes-standard` v2. None of these profiles has an `extract` list; each new version restates its "never read" lines as kept. `council-minutes-text` and `council-minutes-scanned` were not given a new version: their version is in the key of every stored text and page reading (model_read.key_for, scans.page_key), so a new version orphans 629 stored text readings and every stored page.

Legal position pages changed (facts only): `docs/legal/positions/sanctions-lists.md`, `government-procurement-award-notices.md`, `council-meeting-platform-infocouncil.md`.

### Checked and found clean (they already keep the value, or the hit is parsing, not privacy)

- party_returns, candidate_returns, disclosures: donor and lender addresses already in `<lane>_private.addresses` (with the whole cell).
- party_finance: a promoter's email, address and every unknown label already in its private twin.
- parties: the secretary's contact lines already in `parties_private.secretary_contacts`.
- beehive: a release's body and text already in `beehive_private.texts`.
- contract_disclosures: `suppressed` is ACC's own "<4" / "<$100" statistical cells, kept as printed with a flag.
- parliament: text kept whole with address-shape flags (ruling 102); `text` of a record not kept is the provider's concatenation of fields already held.
- hansard, expenses, house, grants, local_elections, settlement_commitments, council_procurement, papers_past: no privacy or suppression withholding (grants' `ADDRESSISH` and house's "no home address" are checks on pub columns; papers_past's search-only rules are hard limit 17, left alone).

### Not changed, and why

- The name passes' prompts in `registers/hansard/model_read.py`, `beehive/model_read.py`, `parliament/model_read.py` say "never add an address, an age or a date of birth". Their output has no field for one; the texts they read are held whole (hansard sections, `beehive_private.texts`, parliament's text). An address or birth-date field means a new prompt and a fresh reading of every document of three corpora on the boxes; left for a re-read decision.
- `council-minutes-text` (model) reads the open meeting only; the public-excluded and forum lines of the 629 text-profile minutes are kept whole in `council_minutes_private.part_lines` but are not read into rows until the text reader re-reads them.
- candidate_returns (12 parts on live) and party_returns (2): a Part A or H whose name cut cannot be vouched for (a digit or street word left in the name) is set aside whole. That is a correctness gate on the name (rulings 190 to 193), not a privacy cut; the document is held and the set-aside line says why.
