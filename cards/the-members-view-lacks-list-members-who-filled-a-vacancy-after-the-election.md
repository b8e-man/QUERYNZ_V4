# The members view lacks list members who filled a vacancy after the election
kind: finding
state: open
use-case: 1
session: integrator
opened: 2026-10-28

`pub.members` (house lane) holds the members an election returned and the
by-election winners (ruling 252's join). A list member who entered the
House after the election, when a member resigned or died and the next on
the party list was declared elected, is not there. Found by the Hansard
lane's check on 28 October: ten speakers of the 2023 Parliament matched no
member (Dansey, Doyle, Hernandez, Lu, McClure, Rosewarne, Wade-Brown,
Wilson, Xu-Nan, Davidson), every one a list replacement; the diaries lane's
check finds 11 of its 78 ministers' titles in no member for the like reason
in part. Both lanes pass their floors with these out, so nothing is red
for it, but the links lane's seat-and-window and member rules never see
these members, and a speech or a diary by one joins nobody.

Wanted: the house lane reads the Electoral Commission's or the Clerk's list
of members declared elected to fill a vacancy (the Gazette prints each
declaration, section `pa`; the Gazette lane holds the notices) and adds a
row per member with the declaration date as `from_on`, the election as the
Parliament's. Then the Hansard check's matched share and the diaries'
ministers-found count rise, and the three Hansard and diaries floors can
be raised.
