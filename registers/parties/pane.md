# Registered political parties, on the board

**A registration pane** (`pub.parties`, one row per registration).

- **Title:** the name it carries now, or last carried; under it the status: on the register, cancelled on <day>, or "not on the register page of <day>; no cancellation held".
- **Fields:** registered on (the register's day; the notice's day beside it where they differ), cancelled on, abbreviation (and whether it is on the ballot paper), component parties, statement deadline, audit requirement, website, party rules, the secretary's name. Never the secretary's contact lines.
- **Names:** every name and abbreviation in `pub.party_names`, oldest first, each with its window (`from_on` to `to_on`; an open end says "before the notices begin" or "still carried") and its basis: registered, stated by the Commission, the registration window, the register page.
- **Citation:** each row opens its document: the register page (party <n>) or the notices export (notice <id>, resolution <n>), with the Gazette's own address for the notice. Rows from the export say "taken from the old estate's tables; original not held".
- **Links:** returns and declarations whose filed label resolves to the registration on the filing's date (through `keys.parties`, once it reads `pub.party_names`).
