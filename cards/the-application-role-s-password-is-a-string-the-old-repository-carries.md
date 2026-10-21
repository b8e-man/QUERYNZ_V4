# The application role's password is a string the old repository carries
kind: finding
state: open
use-case: track H
session: security
opened: 2026-10-22

The leak search (H.2) compares each place it finds against the current
values by hash. One place in the old repository's history, a test's
example alarm address at `tests/test_dsn_import_shape.py:325` (commit
b91feac2990f, 20 September 2026), matches the current password of the
database application role `querynz`. So that password is a word that
sits in a tracked file, not a random value, and it is also in the 6.7 GB
transcript of the old project at least fifty times, current.

Its reach is the local network only (the database's access file), which
is why wave two waits for the election by default. Owner: wave two
(`docs/security/runbooks/database-application-role.md`); the new password
is minted at random by the sitting's script. Nothing to do before then
except not repeat the value anywhere.
