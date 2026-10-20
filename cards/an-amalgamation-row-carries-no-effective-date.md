# An amalgamation row carries no date of its own: only the day it was published
kind: finding
state: open
use-case: 2 legal counterparty; 3 banking
session: legal-1
opened: 2026-10-21

Read against the Gazette source file at the legal checkpoint: notice
2011-ot1330 (RED CIRCLE WHOLESALE LIMITED, amalgamated company) prints two
dates, 28 February 2011 and 1 April 2011 (only the dates were extracted,
so which is the proposal's and which the day it takes effect is for the
reader to establish), and the row's `event_on` is empty, so the report can date it only "published 3
March 2011". A conflict check wants the day the absorbed company ceased.
For the gazette lane: read the proposed amalgamation date into `event_on`
with an `event_basis` ("effective"), measured on every amalgamation notice.
