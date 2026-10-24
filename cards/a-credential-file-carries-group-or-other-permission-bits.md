# A credential file carries group or other permission bits
kind: finding
state: closed
use-case: machinery; track H (hard limit 1)
session: integrator
opened: 2026-10-23
closed: 2026-10-25
module: support/security

`python -m support.installer plan` on node2, 23 October 2026 13:50, reports
`credentials: {present: 18, mode_ok: false}`: at least one `*.env` file in
the credential directory the plan names has group or other permission bits
set (`support/installer/__init__.py: cred_dir_state`). The integrator may not
read that directory (the session's hooks refuse it, as the plan intends), so
which file is not known here and no value was seen. The fix is Arthur's, one
line on node2 that reads no content: the directory to mode 700 and every
`.env` file in it to mode 600; then `python -m support.installer plan` reads
`mode_ok: true` and this card closes. Track H's inventory
(`docs/security/inventory.md`) should carry the expected mode beside each
file.

Closed 25 October 2026 10:20: Arthur set the directory to 700 and every
`*.env` file to 600; `support.installer plan` reports `mode_ok: true`.
