# The links hold a donor key read before party-returns-5 fixed the row, and have not read the rows loaded since
kind: finding
state: open
use-case: 1
session: site-3
opened: 2026-10-20

Two things the links' `pub.names` holds for the donor registers, found
while closing `a-donor-name-key-on-the-rebuilt-site-carries-a-residence-fragment`
and `the-rebuilt-site-writes-two-donor-pages-for-one-name` on the site's side.

One: a key for a party-return Part A row was read before party-returns-5
fixed that row on 20 October (a text cell's name taken from its first
line), so the key carries words after the donor's name that the fixed
display name lacks, a residence among them (hard limit 15; not repeated
here). On version 2026-10-20T1513, 14 donor pages carried a key with words
the name lacks. The site no longer publishes any links key, so nothing
shows; but the links still fold that row under the stale key, apart from
the donor's other rows, and the board shows the key.

Two: rows loaded since the links last ran have no `pub.names` row: on the
same version, 54 of the 58 donors with twin pages had rows under a
filed-spelling stand-in because no reading existed (the 2025 Labour
return's Part A rows, the 2026 declarations). `pub.names` gives no filed
spelling two keys (0 of 1,389 rows in party_returns and disclosures), so
the links' fold itself is consistent; it is behind the lanes.

Which side is right: the lanes' rows; the key must be re-read from them.
Owner: links. What it needs: the links' rows and build run after each lane
load (`qv4-links-build`, proposed in the links' spec), so the fixed row's
key is read again and the new rows get one. Meanwhile the site folds an
unread row by its exact filed spelling and keys every page by its display
name, so no site figure waits on this.
