# Charity officers and organisation rows are not in the names table
kind: finding
state: open
use-case: 14
session: scan-1
opened: 2026-10-21

`pub.names` carries no row for `pub.charity_officers` (the links lane does
not read the charities register yet) and none for any organisation view
(`companies`, `societies`, `charities`, `parties`). So a scan's person step
cannot land on or start from a charity officer, and a link step lands on
an organisation row by the ref prefix and the key, not through the names
table. The post-settlement template (use case 14: charity officers holding
company roles) needs charity officers in the links. Owner: links (the
charities lane's views are published; `links/spec.md` does not list them).
