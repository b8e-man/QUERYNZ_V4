# A shareholder that is a company carries no business number
kind: finding
state: open
use-case: companies (4.1); 4 agriculture counterparty; 13 beneficial ownership
session: agriculture
opened: 2026-10-20

pub.shareholders has 204,156 rows of shareholder_type "company" and
`holder_nzbn` is empty on every one of its 1.58 M rows; company holders are
not in pub.names either. So nothing joins a corporate holder of record to
its own row in pub.companies, and a report cannot follow a farm company's
holding company to its directors and holders (MACKENZIE IRRIGATION COMPANY
LIMITED has 75 company holders; a name lookup finds two FLETCHER RESIDENTIAL
LIMITED rows, so name alone is not enough). The agriculture template flags
company holders as not followed (company-holders, info). For the companies
lane: fill `holder_nzbn` where the source gives it, or say in the pane that
the bulk file does not; then a link rule (official number) can join them.
