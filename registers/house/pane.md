# Candidates, electorates and the House, on the board

**A person's pane** (`pub.candidates` and `pub.members`, by `name_key` within the links' person, once the links exist).

- **Candidacies:** one line per election: the electorate and the list place (either may be empty), the party as printed and as registered, the votes at the official count, and "poll cancelled" where it was. A 2026 row joined from the workbook and the list says how it was joined.
- **Seats:** one line per seat: electorate, list or by-election; the window "from <polling day> to, at the latest, <the next poll that filled it>", or "sitting at the last held file". The day a seat actually ended is in no file this lane holds, and the pane says so rather than show a day.
- **Citation:** each line opens its document at its place: the electorate page (row <n>), the successful-candidates page (row <n>), the workbook (sheet row <n>), the list page (party, item <n>).

**An electorate pane** (`pub.electorates`): its name per election, Stats NZ's name and code beside it (or "boundary set not held" for 2026), the page's own totals, which candidates are held (`candidates_held`: Mana and Rongotai 2020 hold the leading two only, from the status page), and its candidates by election with their votes, the member marked.

**An election pane** (`pub.elections`): its polling day, and the Commission's figures in `house.figures` beside the rows' own counts.
