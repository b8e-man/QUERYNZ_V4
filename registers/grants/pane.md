# Grants, on the board

- **Grants** (`pub.grants`, kind grant, key `key`): `grantor` (the society, or the Lottery Grants Board with its
  `committee`) and `recipient_as_published` exactly as printed; `status` as published (Accepted, Declined,
  Refunded); `amount_nzd` for an accepted grant, with `amount_requested_as_published` and
  `amount_granted_as_published` beside it; `period` (the year of decision, or the Lottery's financial year) and
  `round`; `decided_on` where the file dates it; `category_1` and `category_2` (the Department's categories: the
  national file prints no purpose); `territorial_authority` and `region` as published; `multi_year` with the page's
  own footnote. A declined application is shown as declined, never as money received.
- **Recipients** (`pub.grant_recipients`, under their grantor): `name_as_published`, `nzbn` and `charity_number`
  where the publisher printed a valid one, the count of grants, accepted and declined, and the amount accepted.
  `kind` "not shown to be an organisation" means only that: never "a person", and the lane never looks one up.
  A recipient is per grantor: the same name under two societies is two rows here.
- **Publishers** (`pub.grant_publishers`): the Department, the Lottery Grants Board and every society, with its
  website, whether the Department's own list of 21 October 2026 carries it, and the licence and attribution.
- **Citation** on every grant and recipient: the document's sha256 (`document`), `page`, `place` (`record N` of the
  national file, `table row N` of a record of grants), `reader`, `profile`, `profile_version`, and the licence and
  attribution owed (CC BY 4.0, to the Department of Internal Affairs).

No address of any kind.
