# Who left the House mid-term is not in the results files
kind: finding
state: open
use-case: 1
session: house
opened: 2026-10-20

`pub.members` holds who the official results and the held by-election
returned, with a window from the polling day to, at the latest, the next
poll that filled the seat. A list member who resigned and the list
candidate who replaced them, and the day any seat actually ended
(dissolution, resignation, death), are in no file this lane holds: the
results site prints the result as at the return only. So `ended_on` is
empty on every row, as the dates contract asks, and a list replacement
in the 2020 or 2023 term is absent. The Commission's Gazette notices
declaring a list candidate elected to a vacancy (Electoral Act s 137) are
the source; the Gazette lane holds the notices, and a later tranche (it
would read `pub` Gazette rows, never import that lane) can turn them into
windows. Not a gap to fill by inference.
