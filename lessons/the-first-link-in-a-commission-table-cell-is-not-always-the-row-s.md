The first link in an Electoral Commission table cell is not always the row's own: three 2023 rows carry a stray empty anchor to another declaration in front of their own, so take the anchor that carries text, and check any cell with two links.
area: registers/disclosures, any lane reading an elections.nz table (promoters, party expenses, candidate returns)
paid-for-by: 2026-10-19, disclosures session, step 4.1

The over-$20,000 table's cell for IEF Limited (National, $23,000, 2023)
holds `<a href=".../Maritime_Union_of_New_Zealand_25_August_2023.pdf"></a>`
before its own link; so do the Mark James Todd and Rail Maritime Transport
Union rows. The old `ec_disclosure_index` took the first `href`, filed the
three rows against the Maritime Union's scan (and explained it as "the
Maritime Union has four rows against one declaration"), left the three real
scans "unlinked", and read them by OCR as extra rows. National 2023 on the
frozen site is $23,000 high for it (card
`national-2023-the-frozen-site-counts-one-declaration-twice`).

How it was found: a per-party-year comparison with the frozen site left one
party-year $23,000 apart; the old table's rows, diffed amount by amount
against the Commission's, showed the table's row present on both sides and
two OCR rows only on the old side. A count of cells with more than one
anchor then found all three. When one figure differs, diff the rows, not
the totals: the totals said "the new side is missing $23,000", the rows said
"the old side has it twice".
