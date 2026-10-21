# Two credential files nothing reads: delete `sync.env`, and strike `x.env` from the inventory
default: yes. `sync.env` on node2 holds no assignment (it is the stub `ops/production/factory-bootstrap.sh` writes with a commented example); `querynz-verdict-sync` is inactive and the server it was for never existed. `x.env` is absent on node2 and its only references are example commands in the old hook's docstring. Both rows go in `docs/security/inventory.md` as struck, and Arthur removes `sync.env` at the box if he agrees (a session may not touch the credential directory).
blocks: nothing. Track H's "done when" asks that every inventory row has a rotation date or a reason it has none; these two have their reason.
recommendation: delete `sync.env` on both boxes (and `x.env` wherever it exists, if node1 has one); say "deleted" and the session strikes the rows.
raised: 2026-10-22 by security-1
