# Limited partnerships, on the board

One pane per partnership (`pub.limited_partnerships`, kind organisation, key `key`), its general partners beneath it.
The board views the integrator adds to the catalogue (products/board):

- **Limited partnerships** (`pub.limited_partnerships`): title `name` ("name withheld by the register" where
  `name_withheld`), `number`, `nzbn`, `kind` (`nz` or `overseas`), `status`, `registered_on`, `country_of_origin`;
  `registered_office` with `office_since` (a partnership's registered office is shown, as a company's is). An NZBN
  opens the companies lane's pane for the same entity.
- **General partners** (`pub.limited_partnership_partners`, joined on `partnership_key`, kind person or body by
  `kind`, names in `full_name`, `first_name`, `middle_names`, `last_name`, blanked by `suppressed`): `current` and
  `status`; `body_nzbn` opens the body's company pane. Dates: `started_on`/`ended_on` only where the register states
  them; otherwise the pane says "dates not stated by the register" (`dates_stated` false) and shows `asked_on` as
  "as the register stood on". Past partners after current ones. No address of any kind.
- **Citation** on every row: the answer's sha256 (`document`), `page`, `place` (`entity`, `roles[2]`), `reader`,
  `profile` and `profile_version`.

Limited partners are not public under the Limited Partnerships Act 2008 and the pane never offers them.
