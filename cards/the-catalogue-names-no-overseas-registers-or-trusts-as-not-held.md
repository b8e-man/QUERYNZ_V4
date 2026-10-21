# The catalogue names no overseas registers and no trusts as not held
kind: finding
state: closed
use-case: subject report (5.1); 13 beneficial ownership and AML
session: ownership-1
opened: 2026-10-21
closed: 2026-10-21

`catalogue.NOT_HELD` lists sanctions, limited partnerships and securities,
but not overseas company registers or trusts, so the ownership template
names them only in its section's text, and the memo's "not held" list and
a blank cannot. Trusts are not a register NZ keeps; the entry would say so.
For the report lane: add `overseas` ("Overseas company registers") and
`trusts` ("Trusts: no NZ register exists") to NOT_HELD; the template then
lists them in its not-held section's `not_held`.

Closed 2026-10-21 by the report session (report-3). `catalogue.NOT_HELD`
is now one list of every register a template must say it cannot see, each
with a key: `overseas` ("Overseas company registers") and `trusts`
("Trusts: no New Zealand register exists") among fourteen added (see
`the-not-held-list-has-no-key-for-the-safety-registers`). A fixture test
holds the keys. The ownership template lists both in its not-held section
(a fix in its folder).
