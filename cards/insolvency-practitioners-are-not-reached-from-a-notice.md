# The practitioners on an insolvency notice are not reached from the notice
kind: finding
state: open
use-case: subject report (5.1); 4 agriculture counterparty; 7 construction
session: agriculture
opened: 2026-10-20

pub.gazette_liquidations.liquidators and pub.gazette_company_notices.people
are counts; the practitioners' names are rows of pub.gazette_liquidators,
keyed by notice. The walk has no route from a notice to its practitioners
(`ROLES_ON` has no Gazette entry) and the catalogue's notice statement does
not name them, so the old estate's practitioner-repeat check (the same
practitioner across distinct companies of one group) cannot run: the
agriculture template blocks it whenever a notice is listed. Seen on a
director with 17 insolvency notices on 4 companies
(`companies:companies/9429030552067/director/fd77610deb97`). For the report
lane: add pub.gazette_liquidators as rows on a notice (by notice key) so a
template reads the names; the practitioner is a business name, never an
address.
