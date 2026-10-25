# board-3: the field search and near matches (rulings 82 and 83; ruling 81 kept)
branch: session/board-3 (pushed, 11962c9; one commit on 73db83c)
session: board-3 (Opus, build, scope products/board/)
raised: 2026-10-25
claims: products/board/ (catalogue.py, search.py, panes.py, server.py, graph.py, check.py, spec.md; new fold.py, near.py;
tests: new test_fields.py, test_near.py, test_fold.py, test_check_vocabulary.py, test_real.py extended);
lessons/a-near-match-must-exclude-the-exact-match-of-its-own-source-not-only-the-search-s.md;
cards/an-address-search-on-the-board-cannot-also-name-the-company.md (finding, open); docs/status/board.md

## What it does

1. **Ruling 82, both tabs.** "narrow by field": a details element in the search form, closed until clicked (open when a
   field is filled), with first, middle and last name, address, organisation, year. Each matches whole words
   (`\m..\M` after the search fold) in the columns `catalogue.FIELDS_OF` declares per view, as data (`Name`, `Fields`;
   a lane adds a line, no code). A view printing name parts is matched part by part; a one-string name is read in its
   places (a first or middle name never its last word, a last or middle name never its first, when it has two words or
   more; a comma reads as Family, Given; an honorific is no word). Organisation: organisation-kind names, the party and
   company columns of other views, and a donor-type name only where it carries a keys.names organisation word. Year:
   year columns and the year of the catalogue's date columns. Address: only `catalogue.ADDRESS_COLUMNS` (company
   registered offices, charities' addresses for service, limited partnerships' registered offices; societies publish
   none). Fields and box combine with "and"; the plain box alone is unchanged (same results as main on four queries).
   Fields ride every href in `search.Boxes` (`first= middle= last= address= org= year=`), with the ticks. The results
   pane says "narrowed by: …", and where a register has no column for a field, says so.
2. **Ruling 83, search tab.** "Near matches", a details element closed by default below the exact results, never in
   their count: names reversed (keys.names' reading; a middle name absent either side; an initial matches the name it
   begins) and close addresses (same street number and street by keys.addresses' fold; unit, level, spelling, suburb
   may differ; a differing town or postcode is not near; a PO box never). 25 per class (`near.NEAR_LIMIT`) with the
   whole count; same fields, citation, marks and panes as exact rows; `panes.shown()` governs suppression and the SQL
   keeps the suppression guard. Rows that are exact, including an address exact in a column the box does not search,
   are ruled out (the lesson).
3. **keys' readings.** Products may not import `keys/`, so `fold.py` is a verbatim copy of the pieces used
   (person_name, honorifics, ORG_WORDS, address_key, …); `tests/test_fold.py` holds each equal to the keys/ source.
4. **Outside check** adds: every field column exists and is typed; last name "Hart" alone finds rows, every one with
   HART a whole name word (never HARTNELL alone); the known reversed donor (MILLS PHILLIP) under Near matches and not
   exact, and rendered below the exact rows; a registered office found as near by its address without its level (the
   street type spelled the other way so the exact search misses it); the address field reads only `ADDRESS_COLUMNS`
   and no person's view declares one; for each word of the comparison's residence vocabulary (held equal by a test),
   no result carries a person's name with a residence after it and the address field finds nothing outside those
   columns.

## Checked

- `QV4_INTEGRATOR=1 bin/fast products/board`: green (41.6 s).
- Whole-repository fast tier (`QV4_INTEGRATOR=1 bin/fast`): one red, `tests/test_generators.py::test_the_committed_records_generate_cleanly`,
  because the committed `docs/board.md` and `lessons/INDEX.md` lag this branch's new card and lesson (the fence refuses
  generated files to a build session). With both regenerated in the working copy the test passes. Everything else green;
  625.6 s, over the 300 s target (recorded).
- `python -m products.board check`: green against live pub (23 s). Each new case shown to fail with its rule broken in
  memory (prefix not whole words: 191 problems; reversal never found; address never near; a person's view declaring
  an address).
- Slow tests (`-m slow`, 7, two new): green. Field search 0.4 s, near 0.4 to 1.1 s on live data.
- The new pure tests shown to fail on their broken rules (loose name positions, prefix matching, any-order names,
  town ignored, initials refused).
- A rendered page looked at (scratch screenshot): the fields, the narrowed line, the near section.
- **Rebuild `docs/board.md` and `lessons/INDEX.md` at the merge** (`bin/board`, `bin/lessons-index`): neither is in
  the branch.

## For the integrator

1. Merge, then **restart `qv4-board`** at the release (new modules `near.py`, `fold.py`). No table, unit or other
   module changes; no `state` run.
2. Lanes, mirror your field line in `pane.md` at your next session (the board already holds them; the form is
   `catalogue.FIELDS_OF`): companies (directors, company_lookup_roles: first_name+middle_names+last_name;
   shareholders, company_lookup_holdings: name, organisation if an organisation word; companies, company_states,
   company_lookups: organisation name; company_addresses: address line_1..line_4+postcode); societies (officers:
   parts; societies, society_states: organisation name); charities (officers: first_name+middle_name+last_name;
   charities: organisation name+other_names, address address_for_service); party_returns (donors: donor, lender;
   party+party_label; year); disclosures (donor_name, contributor; party+party_label); candidate_returns (donor, and
   the candidate's given_names+surname; party; year); party_finance (promoter, people's name; party+party_label;
   year, filed_year); expenses (name, member; party+party_label); house (name, display_name; party,
   party_registered); mp_interests (name, member; party); parties (secretary; name, first_name, label, new_name);
   gazette (celebrants and bankruptcies given_names+surname; prohibitions, liquidators, practitioners, appointments
   name; possessions mortgagee/mortgagor; liquidations, company notices company; notices year); party_boards (name,
   name_as_declared; party); courts (parties' name); limited_partnerships (partners' parts; name;
   registered_office); building_practitioners (name); sanctions (listings' name; dates without renewed_on);
   tenders (business_name); commerce_commission, fma, worksafe, overseas_investment (parties' name); grants
   (recipient; grantor; name_as_published); iwi_directory (name+legal_entity; act_year); contract_disclosures
   (year_ended); councillor_interests (member); local_elections (candidate_as_listed; election_year).
3. The card `an-address-search-on-the-board-cannot-also-name-the-company` is open: an address and an organisation
   together find no company registered office (that view has no name column). One board tranche when wanted.

Lesson filed (above).

## Result (integrator, 25 October 16:20 NZDT)

Merged as 1c431fb: fast tier green (623 s; the one red the session saw,
the committed indexes lagging its card and lesson, cleared by `bin/board`
and `bin/lessons-index` at the merge), gate green, nothing to load.
Working copy and branches retired; release copy moved; `qv4-board`
restarted; the field form, the "narrowed by" line and the Near matches
section answer on the local network. The field lines for each lane's
`pane.md` stand in this request for the lanes' next sessions. Open card:
`an-address-search-on-the-board-cannot-also-name-the-company`.
