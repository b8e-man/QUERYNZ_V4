# Award notices, on the board

One pane per award notice (`pub.award_notices`), its suppliers beneath it (`pub.award_suppliers`, joined on
`notice_key`). The board views the integrator adds to the catalogue (products/board):

- **Award notices** (`pub.award_notices`, kind record, key `key`): title `title`, `posting_agency` and `awarded_on`;
  fields `rfx_id` (GETS's own identifier) and `era` (`historic`: July 2014 to June 2019; `current`: July 2019 on),
  `department`, `rfx_type`, `competition_type`, `tender_coverage`, `prequalification_required`, `reference_number`,
  `opened_on`, `closed_on`, `award_type`, `value_nzd` with `value_note` beside it (an amount of `0` is shown as "no
  value given", never as $0; the historic file has no amount), `regions`, `categories` (code and description),
  `suppliers_named`, `report_date` (the file's).
- **Award suppliers** (`pub.award_suppliers`, kind organisation, joined on `notice_key`): `business_name` as
  published, `nzbn` where it is one (it opens the company) else `nzbn_as_published` with `nzbn_form` beside it
  ("exponent form: digits lost" says the ministry's own file lost the number), `country`. No address and no website:
  a supplier may be a sole trader.
- **Licence** on every pane and export: `attribution` ("Source: Ministry of Business, Innovation and Employment, …
  licensed under CC BY 3.0 NZ"), from the row.
- **Citation** on every row: the file's sha256 (`document`), `page` 1, `place` (`record N`, the record after the
  header), `reader`, `profile` and `profile_version`.

Shown with care: 'Not Awarded' is also how an agency marks a tender awarded off the system (the ministry's schema
workbook); 279 current notices carry an award date after the file's report date, as published. A notice lists who
won what and when; it never says why.
