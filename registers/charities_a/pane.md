# Charities, on the board (the Fable build)

One pane per charity, from `pub.charities`: its name and charity number, its
NZBN where it has one, status with the registration and deregistration dates
and the coded reason, legal structure, the main sector, activity and
beneficiary, the register's lists beside them (activities, sectors,
beneficiaries, areas of operation, sources of funds), the charitable purpose,
the address for service and the postal address as the register publishes
them (the organisation's, like a company's registered office), and its group
where it reports in one. Then its officers, from `pub.charity_officers`:
current first (status Qualified or Proposed), then past, each with the role
and the register's own appointment day and last day; a disqualified officer
is marked, with the grounds the register flags, by the register's own words.
A suppressed name shows as "name suppressed"; the row stays. No officer
address, birth date or contact detail exists to show. Then its annual
returns, from `pub.charity_returns`, newest first: the period end, tier,
currency, whether audited and any modified opinion, and the financial fields
(income, expenditure, surplus, assets, liabilities, equity, grants and
donations in and out, people), with every other figure the return carries
under `figures`.

A person pane lists every charity officer role a name holds, each cited to
the feed page it came from (the page's sha256 and `OfficerId=<n>`). A group
pane (`pub.charity_groups`) lists the group's members and the group's own
returns.

The lane's own line on the board: the outside check (the register's count
against the build's, with the rows that moved during the pass), the last load
(pages, rows in, typed, set aside, replaced, seconds) and the catch log's
count by reason.
