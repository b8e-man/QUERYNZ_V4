# A company's same-name companies are not set apart as namesakes
kind: finding
state: closed
use-case: links (4.2); 4 agriculture counterparty; 7 construction (phoenix)
session: agriculture
opened: 2026-10-20
closed: 2026-10-20

No link rule joins a company row to another company row by name: pub.links
holds company-to-company links only between person rows (directors,
shareholders). So a counterparty report cannot list the companies that
share its name or nearly do: two FONTERRA CO-OPERATIVE GROUP LIMITED rows
(`companies/9429036748471`, `companies/9429036965915`), or a farm company
and its "(2025) LIMITED" successor. For a credit manager these are the
namesakes to set apart first (the wrong entity on an invoice), and the
phoenix template (use case 7) needs the same pairs. For the links lane: a
near rule on the companies' own names (the shared reading of names), never
confirmed, with its reason; the NZBN stays the only confirmation.

Links, 20 October (links-2). `company-name@1` joins company rows under one
name (the shared reading, `keys.organisation_key`), one star per name,
near, with both registration windows and whether the two were alive
together: 75,184 links; and under one name apart from a year in brackets
(a successor's name, "KAHIKATEA FARMS (2008) LIMITED"), 13,635 more. The
NZBN stays the only confirmation. The two FONTERRA rows and a farm
company's "(2025)" successor are set apart with their reason.
