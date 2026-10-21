# The practitioners on an insolvency notice are not reached from the notice
kind: finding
state: closed
use-case: subject report (5.1); 4 agriculture counterparty; 7 construction
session: agriculture
opened: 2026-10-20
closed: 2026-10-21

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

Closed 2026-10-21 by the report session (report-3). `gazette_liquidators`
now sits on its notice (`entity=("gazette_liquidations", "notice")`,
joined by the notice number, which `entity_col` names since a notice's
company rows do not carry it as their key) and `walk.ROLES_ON` lists the
practitioners as rows on a liquidation notice and on a company notice.
The walk expands every notice it lists on a company (the `pointing`
bucket) into its practitioners, with the notice's grade, via the notice;
the statement reads "… · Liquidator named in the Gazette notice on SAVAGE
MOTORS LIMITED", a business name and a role, never an address. Measured on
`companies:companies/9429052657764` (BENJAMIN FRANCIS, liquidator, via the
notice); `python -m products.report check` takes the latest liquidation
notice with practitioner rows on a company, from the tables at run time,
and fails unless the practitioners are listed via the notice. The
agriculture template's practitioner-repeat reads them (a fix in its
folder). No practitioner row joins a company notice today (the lane's
notice numbers differ); the route is in place for when one does.
