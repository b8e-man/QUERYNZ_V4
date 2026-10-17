# The old querynz-api unit file carries a database password in plain text
kind: finding
state: open
use-case: -
session: founding-2
opened: 2026-10-18

Found measuring node2 (1.3): the user unit `querynz-api.service` in the old
estate sets the database password in an `Environment=` line instead of
reading a credential file. Hard limit 1: it is not repeated here or
anywhere. For track H (rotation): move it into the credential folder's
file for that service, point the unit at it, rotate the password, restart
the job. Each sitting of track H is on Arthur's word; the deploy token is
its first item and this is the second.
