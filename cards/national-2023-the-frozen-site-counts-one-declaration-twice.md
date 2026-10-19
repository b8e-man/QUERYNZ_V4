# National 2023: the frozen site counts one large declaration twice ($23,000)
kind: finding
state: open
use-case: 1
session: disclosures
opened: 2026-10-19

The New Zealand National Party 2023: the frozen site shows $2,602,816.50 in
large donations; the disclosures lane holds $2,579,816.50, the Commission's
own table summed by the day the party received each gift. The difference is
one declaration, IEF Limited, $23,000 received 31 August 2023
(`IEF_Limited_4_September_2023.pdf`, sha256
d325a2d5e28d8f5fa1a006603da8a9d4cae6d07af52a975b31dff9e7be6b4e29), counted
twice by the old estate.

Why. In the Commission's table that row's cell holds an empty link to the
Maritime Union's declaration in front of its own link. The old
`ec_disclosure_index` took the first link, so the table's $23,000 row was
filed against the Maritime Union's scan, and the IEF scan, now "unlinked",
was read by OCR as two more rows ($20,000 and $3,000) and added. Two other
2023 rows carry the same stray link (Mark James Todd, $5,000 OCR row with an
unreadable date, party unresolved; Rail Maritime Transport Union, a $0
"unreadable" OCR row): they add no money to a front-page party, so this is
the one figure the site shows wrong. The old table's other 276 rows equal
the Commission's 276, to the cent ($14,714,081.38).

The same cause moves two counts on the frozen site: National's disclosures
84 against the lane's 82 (the two IEF OCR rows) and Labour's 32 against 31
(the Rail Maritime Transport Union's $0 OCR row).

Which side is right: the new one. The Commission lists IEF Limited once, at
$23,000, for National. The lane takes the link that carries the row's text
(`listing.link`), and the IEF scan joins its own row.

Not fixed in the frozen product (hard limit 19: a wrong published figure is
an emergency fix only on Arthur's word). Arthur's call whether $23,000 on
National's 2023 disclosures is worth one.
