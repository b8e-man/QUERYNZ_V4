# Labour's and the Greens' boards are not in the party-boards capture
kind: finding
state: open
use-case: 1
session: party-boards-1
opened: 2026-10-21

The party-boards lane (ruling 72) reads the old `party-boards` capture, 2017
onward: 869 distinct pages of 13 parties. It holds no board page for Labour
(its 2017 New Zealand Council page lists no one; its other pages are the
caucus and a 2017 news item on a new president) or the Greens (`about`,
`our_people` and the governance policy: no officers listed), and none for
Vision New Zealand in the window. So `pub.party_board_roles` has 0 rows for
the three. The frozen site shows Labour's 27-seat New Zealand Council read
from `labour.org.nz/party-information` and ACT's officers from
`action.act.org.nz/contact`: both in the whole-site capture `party-sites`
(46,843 files), which this lane does not read.

Which side is right: the frozen one holds more, from pages this capture
lacks. Still needs: Arthur's word on reading the whole-site capture's
governance pages through this lane (the same profile, new shapes per page),
and for the Greens whether any captured page lists the party's officers.
Owner: party-boards.
