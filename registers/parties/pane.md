# Registered political parties, on the board

**A registration pane** (`pub.parties`, one row per registration).

- **Title:** the name it carries now, or last carried; under it the status: on the register, cancelled on <day>, or "not on the register page of <day>; no cancellation held".
- **Fields:** registered on (the register's day; the notice's day beside it where they differ), cancelled on, abbreviation (and whether it is on the ballot paper), component parties, statement deadline, audit requirement, website, party rules, the secretary's name. Never the secretary's contact lines.
- **Names:** every name and abbreviation in `pub.party_names`, oldest first, each with its window (`from_on` to `to_on`; an open end says "before the notices begin" or "still carried") and its basis: registered, stated by the Commission, the registration window, the register page.
- **Citation:** each row opens its document: the register page (party <n>) or the notices export (notice <id>, resolution <n>), with the Gazette's own address for the notice. Rows from the export say "taken from the old estate's tables; original not held".
- **Same name:** where another registration carried one of its names (New Zealand Loyal, United Future New Zealand, the Alliance), the other registration's key and both windows (`same_name_as`, `same_name_note`): two registrations, never folded.
- **Links:** every row of another lane whose filed label resolves to the registration on the filing's day or year (`pub.party_labels`: the label, the day or year, the basis, the sources and their row counts).

**A label pane** (`pub.party_labels`, one row per label and day or year).

- **Title:** the label as filed; under it the registration it joins, or "unresolved" and why.
- **Fields:** the day or year, the basis (exact, variant, core, fuzzy, before its bracket, not a party), the lanes and tables that publish it with their row counts, and where two registrations carried the name, both with their windows.
- **Citation:** the name row the registration carried that day (its notice or the register page); an unresolved label cites the register page.
