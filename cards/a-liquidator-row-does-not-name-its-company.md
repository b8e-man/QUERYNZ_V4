# A liquidator's row in pub.gazette_liquidators does not name the company it was appointed to
kind: finding
state: open
use-case: 2 legal counterparty; 7 construction and phoenix detection
session: legal-1
opened: 2026-10-21

The link rules join 10,467 director rows to liquidator rows by full name
(confirmed), so a report from a practitioner reaches their appointments,
and the legal template's `practitioner-roles` flag lists them. But a
liquidator row carries `companies` as a count, and the catalogue gives the
view no `entity`, so the memo says "named in a Gazette notice" and cannot
say which company: the reader opens the notice. The company is the
liquidation row of the same notice (`gazette/<notice>/company/<n>`). For the
report lane: an entity pointer from a liquidator row to the liquidation
rows of its notice; for a notice naming several companies, each listed.
