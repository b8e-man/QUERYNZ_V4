# board: where it stands

**Date:** 2026-10-25. **Step:** 4.9 second version, rulings 82 and 83
(81 kept), `products/board/`. **Merge request:** `board-3` (raised).

## Done

- Ruling 82, both tabs: "narrow by field", a details element (closed
  until clicked or a field is filled) with first, middle and last name,
  address, organisation, year. Each field matches whole words in the
  columns `catalogue.FIELDS_OF` declares per view (data: a lane adds a
  line). A one-string name is read in its places: a first or middle name
  never its last word, a last or middle name never its first; a comma is
  Family, Given; an honorific is no word. Organisation reads organisation
  names, party and company columns, and a donor-type name only where it
  carries an organisation word. Year reads year columns and the year of
  the catalogue's dates. Address reads only `ADDRESS_COLUMNS` (company
  registered offices, charities' addresses for service, limited
  partnerships' registered offices; societies publish none). Fields and
  box combine with "and"; the box alone is unchanged (identical results
  to the main line on four queries). Fields ride every href in
  `search.Boxes`; the results pane says which narrowed it.
- Ruling 83, search tab: "Near matches" below the exact results, closed,
  never counted with them: names reversed (keys.names' reading; middle
  absent either side; an initial) and close addresses (same street number
  and street by keys.addresses' fold; level, unit, spelling, suburb
  differ; a differing town or postcode is not near). 25 per class with
  the whole count. `near.py`.
- `fold.py`: keys' readings copied verbatim, held equal by a test.
- `bin/fast products/board` green; slow tests green (7); `python -m
  products.board check` green (23 s), its new cases each shown to fail.

## Known limits

- An address and an organisation together find no registered office
  (`company_addresses` has no name column): card
  `an-address-search-on-the-board-cannot-also-name-the-company`.
- 49 directors with no `last_name` part are not found by the name fields.
- From the plain box, a reversed name is already exact (any order), so
  near names from the box show only the forms it misses (an initial).

## Next

1. The integrator merges `board-3` and restarts `qv4-board`.
2. Lanes mirror their `FIELDS_OF` line in `pane.md` (the request lists
   them).
