Read a party's board page by its markup (the name's element and the role's element, per site and theme era), never by guessing from a line's words which line is a name.
area: registers/party_boards, reading HTML pages, document profiles
paid-for-by: 2026-10-21, party-boards-1 (ruling 72)

The old derive (`ops/party_boards_derive.py`) flattened every page to text
lines and classified each line as a name or a role by regex, then patched
the misses one site at a time; the frozen site carries the results: "Share
this" and "Remove British Royal Family" as board members, MPs and candidates
read from the same page as the board. The rebuilt lane keeps each line's
element chain (`page.py`) and the profile names, per shape, the opening
heading, the name element and the role element (`h4.card-title` / `div.cont
strong`, `.directory--signup-name` / `.directory--signup-occupation`, a
table's first and second cells). Nineteen shapes read 440 pages of ten
parties with 37 lines set aside and no name guessed. Two more lessons the
pages taught: an archived theme can carry the theme's demo people ("John
Doe", "Enter member description here"), which a refusal marker in the
profile drops; and a two-column layout where the role heading sits over
both columns does not say which name holds which role, so the profile names
that layout and drops it rather than pairing by position.
