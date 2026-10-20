# Two donation rows filed under the same organisation name are linked only through a company of that name
kind: finding
state: open
use-case: subject report (5.1); 1 Follow the Money
session: report
opened: 2026-10-20

`organisation-name@1` joins a donation row to the one company that carries
its name, and the subject report reaches a donor's other returns through
that company (near, with the reason). A donor with no company of its name
(a trust, a partnership, "Hugh Barr Public Trust", "Perune Trust, via
Perune Limited") has no link to its own other rows, so a report on one of
its donation rows lists that row alone and says "none found" for the rest,
though the same filed name appears in other returns of the same party.

For links/: whether two donation rows under one organisation name key
(`pub.names.name_key`, kind organisation or estate) should be joined to
each other by a rule of their own (near at least: a filed name is the
Commission's donor, ruling 253), so a report reaches a donor's every
return whether or not a company carries the name. Until then the report
says what it finds and no more; the board's "same name elsewhere" shows
the rest by name alone.
