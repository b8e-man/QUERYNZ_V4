# group-standing calls a filed row with no group an organisation
kind: finding
state: open
use-case: subject report (5.1); every template
session: banking-1
opened: 2026-10-20

Started from a party donor row that no confirmed link names a person for
(`party_returns:f1504cb1933382d0ccc3ed675c2492b377a631232501b95227ee4a58972f11ae/A/1`),
the common rule `group-standing` clears with "an organisation: its official
number is the link", because it tests `subject["kind"] != "person"`. The row
is a filing, not an organisation. For the report lane: a filed row with no
`via` says it has no group (the walk's own `NO_GROUP_FOR_FILED` text).
