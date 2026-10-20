# The links have not read the expenses registers or joined a member to a donor
kind: finding
state: open
use-case: 1
session: site-2
opened: 2026-10-20

Two person-page sections wait on the links. `pub.names` carries no row for the MPs' and ministers' expenses registers, so no expense row can be
attached to a person under the shared reading, and the page says "not held". And no group in `pub.groups` spans the house register and a donor
register (party returns, candidate returns or declarations): the links' rule 1 needs a full name with a middle name on both rows and rule 2 a
shared office, which a member or candidate row never carries; the house lane's own join (142 groups) stays inside the house. So `donations_made`
on every person page is empty with its basis, and the frozen site's name-matched figures (nine people with declarations sighted) have no rebuilt
counterpart. The site never joins by name alone.

Which side is right: the rebuilt one is not wrong, it is waiting. Owner: links (the expenses registers' names; a confirming rule a member's row
can meet), then site.

Links, 20 October (links-2). The expenses half is done: `pub.names` carries
every `mp_expenses` (26,689) and `minister_expenses` (13,467) line under the
member's name, and `seat-and-window@1` joins 22,357 of them to the seat
whose term covers the period (confirmed); the 17,403 before ge-2020 and the
list-vacancy members' lines have no seat row (the house lane's). The donor
half is built as near, never confirmed: `member-and-party-donor@1` (106: a
member's name on a Part A or declaration row to the member's own party in
the term) and `own-return@1` (1), each with its evidence. The site's
`donations_made` stays empty with its basis until Arthur rules
(`may-a-donation-rows-circumstance-confirm-a-link`, default no; the
recommendation keeps these two near). Owner from here: Arthur's ruling,
then site.
