# Companies, directors and shareholders, on the board

One pane per entity (`companies/<NZBN>`, or `companies/retirement_village/<number>`): its name, type and status as
filed, its registration and removal dates, the monthly files it is in, its earlier state where a later file changed it,
and its registered office (a company's registered address is shown). Every row says "taken from the old estate's tables;
original not held" and cites the export part's hash and line.

Directors and shareholders are listed with their window as the files give it: appointed on the filed start date, and
"in the files from <first> to <last>". A role that has left the latest file says so and carries no end date, because
the file states none. A holding whose shares changed shows as one holding leaving and one starting. A suppressed name
reads "name suppressed"; the row stays.

A person pane lists every role filed under a name, never linked across companies here: that is the links' work. No
residential address is ever shown; the monthly files carry none.

An entity a product has looked up or watches also shows the interface's last answer (`pub.company_lookups`): its kind
(a sole trader, partnership or trust has a pane of its own kind, which the monthly files lack), its status and the day
it was asked; its roles with the register's own start and end dates; and its changes (`pub.company_changes`), newest
first, each dated by the register's own date where it states one, else "seen on <day>", and citing the answer. A role
the monthly file stopped listing shows the end the interface gives it. A sole trader whose name the register
withholds reads "name withheld by the register". No address of a sole trader, partnership, trust, director or
shareholder is shown.
