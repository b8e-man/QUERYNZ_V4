# Party boards have no lane
kind: finding
state: open
use-case: 1
session: comparison
opened: 2026-10-20

The frozen site read party boards from the parties' own websites (the
`party-boards` capture, 1,061 files in the listing) and published 106
board-member pages and a board on each party page. No lane holds party
boards, so the rebuilt site has no board-member kind and every party page's
board is "not held". Today: 123 differences (106 pages, 17 party boards).

Which side is right: the frozen one, until Arthur rules boards out of the
Follow the Money template. The capture is held, so a lane could read it
without fetching. Owner: site (the template), then a boards lane if ruled.

Site-2 (2026-10-20): unchanged; the party page's `board` and the person page's `party_boards` say "not held" and why. Measured against the frozen
2026-10-20T0620, rebuilt in scratch: 123 differences. Still needs: Arthur's ruling (queue: which-frozen-sections-belong-in-the-follow-the-money-
template, boards among the sections the recommendation would move), and a boards lane if ruled in; the capture is held. Owner: site (the
template), then a boards lane.

Ruling 72 (21 October): "build the declared anchor tier but dont deploy to the site". A lane reads the held capture, the tier the party itself declares, no fetch; nothing on the site and nothing into the links until Arthur rules. Briefed as `party-boards-1`. Owner: that lane.

party-boards-1 (2026-10-21): the declared tier is built, not deployed (`registers/party_boards/`, merge request `party-boards-1`): `pub.party_board_roles` 2,876 rows from 440 pages of ten parties, `pub.party_board_pages` every capture; 429 pages are drop-notes with their reasons. Nothing on the site, nothing in the links. The site's 123 differences stand until Arthur rules boards into the template. Labour, the Greens and Vision: card `labour-and-green-boards-are-not-in-the-party-boards-capture`.
