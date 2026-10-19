# Five party expense returns are unread against the Commission's figure
kind: finding
state: closed
use-case: 1
session: party-finance
opened: 2026-10-20
closed: 2026-10-20

The party-finance lane reads each current expense return's own total
(`Total (A + B + C)`) and checks it against the Commission's table. Of the
37 party-elections the Commission lists for 2020 and 2023, 30 equal it to
the cent, 2 differ where the Commission printed Part A alone (Advance NZ
and Māori Party 2020, already on record), and 5 are unread:

- No stored page reading for the image pages, so the lane cannot replay
  them: New Zealand First Party 2023 (`072c63d80730`, 22 pages), New
  Conservatives 2023 (`9cf79940a2e1`, pages 2 to 22), Democratic Alliance
  2023 (`cc6f2ef26b69`, 14 pages; the Commission's figure is NIL). Fix: a
  page-reader job that reads every image page (`pages.thin_pages`) under
  the stamp the lane replays (GLM-OCR Q8_0, 300 dots, `OCR`, profile
  `ec-party-expenses-return`). The same job type the card
  `forty-one-party-returns-have-image-pages-with-no-stored-page-reading`
  asks for; the scheduler's module, not this lane. The lane picks the
  readings up on its next load with no change.
- Read but not reconcilable: Vision New Zealand 2020 (`919d4fef5edb`, the
  correction the Commission links; Parts A and C read, Part B not, no
  total) and Aotearoa Legalise Cannabis Party 2023 (`34b97a436d6c`, no
  total and no part read from text or stored pixels). Each needs its
  declaration page looked at; a reading rule changes only if the page
  shows a shape the reader has not met.

The superseded Leighton Baker Party 2023 original (`ef943a1c589a`) is set
aside too (its OCR total disagrees with its parts by 8 cents); it is not
current and blocks nothing.

`party_finance.set_aside` lists them (`stage = 'declaration'`).
Blocks: nothing. `pub.party_expenses` carries the Commission's figure for
these five with `agrees` NULL.

**Closed, 2026-10-20 (party-finance session 2).** All five read, each
equal to the Commission to the cent. NZ First and New Conservatives 2023
replay the page-reader job's readings (row 115) under the contract's
stamp with no change. The other three showed two shapes the reader had
not met, and the reader now takes both: the figure alone on the line
below its label (Democratic Alliance 2023, every box 0; Vision New
Zealand 2020's faint scan, Part B's total read only on the declaration)
and whole dollars with no cents (Aotearoa Legalise Cannabis Party 2023,
$986). A whole number counts only with nothing after it on its line, and
A + B + C = total still gates every one. Six returns read before moved to
that full check with the same totals. On every real file: 35 of 37
equal, 2 explained (Part A alone), 0 differ, 0 unread. Leighton Baker
Party's superseded original stays set aside (8 cents).
