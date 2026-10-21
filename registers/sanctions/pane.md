# Sanctions lists, on the board

- **Sanctions lists** (`pub.sanctions_lists`, one line per list read): `name`, `publisher`, `law`, `version`, `stated`
  (the publisher's own count, `stated_where`), `listings` current, `ended`. A list held on its publisher's terms has no
  line, and the pane says "not held: <list> is held on its publisher's terms".
- **Sanctions listings** (`pub.sanctions_listings`, kind person or organisation by `kind`, key `key`): title `name`,
  `list_id` and `list_ref` (the list's own identifier; `other_ref` is the UN's where Police give it), `status`
  (designated, revoked, expired) with `designated_on`, `renewed_on`, `expires_on`, `ended_on`, `updated_on`; `aliases`,
  `original_script`, `titles`, `positions`; `nationalities`, `birth_dates`, `birth_countries`, `countries` (the
  countries the list names, nothing finer); `regime` and `basis`; `list_version`.
- **A listing is never matched to a person by name alone.** The pane shows a register row and a listing side by side
  only as "same name", with the birth dates and nationalities next to each, and never joins them with "is". A person
  with the same name is not the listed person until the list's own identifiers and particulars agree.
- **Citation** on every row: the list document's sha256 (`document`), `page`, `place` (`REFERENCE_NUMBER=QDi.001`,
  `Individuals!row 7`), `reader`, `profile` and `profile_version`.

No street, city or address of any kind, no passport or identity number, no narrative comment.
