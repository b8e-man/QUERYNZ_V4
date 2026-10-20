# The other companies in an amalgamation notice are not reached from the company a report starts from
kind: finding
state: open
use-case: 2 legal counterparty and conflict check; 3 banking; 13 beneficial ownership
session: legal-1
opened: 2026-10-21

An amalgamation proposal is read as one row per company, all under one
notice key (`gazette/2011-ot1330/company/1`, `/2`, …), with `role`
amalgamating or amalgamated. The walk's `POINTING_AT` reaches only the row
whose `register_key` is the company's, so a report on RED CIRCLE WHOLESALE
LIMITED (`companies:companies/9429000072854`, named "amalgamated company"
in 2011-ot1330) cannot list the companies it absorbed, and a report on an
amalgamating company cannot name the company it continues as. For a
conflict check that is the point: a firm that acted against the absorbed
company has a conflict with the one that continues. The legal template's
`amalgamation` flag fires and says the others are not reached. For the
report lane: from a notice row reached by pointing, list its sibling rows
of the same notice (near, with the reason "named in the same Gazette
notice"), with the walk's limits counted.
