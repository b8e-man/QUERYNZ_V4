# Candidacies the frozen site shows and the house lane lacks
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

A candidacy on a frozen person page, an electorate contest of 2020, 2023
or 2026, that no rebuilt person page carries under any name form (Ala
Al-Bustanji, Taupō 2023), or a candidate on a frozen electorate page the
rebuilt race lacks (Mana 2020's candidates, where the result is not held),
or a frozen person page whose 2026 candidacy has no rebuilt page at all
(Adrian Graamans, Waitaki 2026, Independent). Today: 139 figures and 20
whole pages. The full list is in the day record under
`<live>/checks/comparison/days/`.

Which side is right: the frozen one; the house lane has no row for these.
Owner: house.

House, 20 October (house-2), measured on the day's differences against the
rebuilt races. Of the 139 figures, only 35 are rows the house lane lacks:
Mana and Rongotai 2020. The old estate holds their result pages (20 and 43
of the 2020 results site) only as its job's fetch-error stubs, so "the file
is in the listing" is true of the error, not of the result. The other 104
are rows the lane holds under another name form: 93 under the same first
given name (card `the-rebuilt-site-splits-one-candidate-across-two-name-forms`)
and 11 under another given name, Dave/David KENNEDY, Jack/Jacobus GIELEN
(card `a-candidate-s-given-name-differs-between-the-return-summary-and-the-results`).
None of the 20 whole pages is a row the lane lacks: 4 are the frozen site's
second page for one person (Menendez March, van Velden, Van de Molen,
MacLeod; card `the-frozen-site-has-two-pages-for-one-person`), 7 are under
another given name and 9 under another name form. The comparison's rule
order files them here; moving them is the comparison's job.

house-2 reads the leading and second candidates of Mana and Rongotai from
the held status page (Edmonds and Hayes; Eagle and Crossen), and joins each
winner to the seat. On a scratch build from the listing of 2026-10-20T0620,
this card's figures fall from 139 to 128.

Still open, and the frozen side is right: 9 Mana and 8 Rongotai candidates,
and every vote in both races. Needs those two pages (card
`three-by-elections-and-two-2020-electorate-pages-are-not-held`). No job may
fetch them before the switch (plan 4.1: the old capture jobs stay the only
fetchers), and the four questions for that fetch are answered in
`docs/status/house.md`.
