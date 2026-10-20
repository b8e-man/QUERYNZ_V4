# Charities, on the board (the charities_b build)

One pane per charity (`pub.charities`).

- **Title:** the charity's name, its register number (`CC12345`) and status.
- **Fields:** registered on, deregistered on with the register's reason, legal structure, main sector, activity
  and beneficiary, its purpose, its group, its NZBN and incorporation number, its address for service as the
  register publishes it (the charity's, never an officer's), its other names.
- **Officers** (`pub.charity_officers` on `charity_key`): name, role, from and to as the register states them,
  status; "disqualified" only where the register's own status says so. Past officers after current ones.
- **Returns** (`pub.charity_returns` on `charity_key`): one line per return, newest period first: period end,
  tier, gross income, expenditure, surplus, assets, liabilities, the audit opinion where modified.
- **Citation:** each row's page of the register's feed, by sha256, and the row's key in it
  (`OrganisationId=…`, `OfficerId=…`, `AnnualReturnId=…`), with the reader and profile.
- **Links:** an NZBN or incorporation number opens the company or society; an officer opens the person's group.
