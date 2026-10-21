# registers/tenders — government procurement award notices

Step 6.2, template 1's register (use cases 9 and 10). The Ministry of
Business, Innovation and Employment's open-data files of award notices from
the Government Electronic Tenders Service (every award since July 2014),
copied verbatim by hash from the old estate's raw acquisition of 14 August
2026 and refreshed quarterly through the fetch gate when the ministry's host
lets the estate read them (on 21 October it answers 403: card
`the-ministry-s-gets-files-answer-403`). Read by profile into one row per
award notice and one per supplier named on a notice, checked against the
files' own record counts and the old estate's 29,874. The licence (CC BY
3.0 NZ) and its attribution travel with every row.

The supplier file's business-number column holds no valid NZBN (card
`the-gets-supplier-file-loses-its-business-numbers`): it is kept as
published with its shape named. No address, website or free text is read.

Built by `tenders-1`: `spec.md` is the five lines; `position/` is the draft
legal position the integrator moves.
