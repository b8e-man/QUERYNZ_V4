# The database serving role `querynz_serving`

**Done inside the wave-two sitting** (`database-application-role.md`):
Arthur's, after the election by default, rehearsed first. This is the
read-only role the public app (`querynz-pi-web`, in the carve-out) connects
as, so its restart is the one the public site feels; it goes last.

**Reach:** local network only. Its three connection strings were typed
into node2's shell history when the file was made on 5 September 2026
(`docs/security/leaks.md`), so it counts as exposed on the box, though
not usable from outside.

**Where it lives, by path only, node2:**

- The Postgres role itself (`ALTER ROLE querynz_serving PASSWORD`, or re-run `ops/production/c007_serving_role.sh --apply` from the reference copy, which mints the role's password in-process and never prints it).
- `~/.querynz/serving/serving.env`: the role's own `V3_DSN`, `V3_BACKLOG_DSN`, `V3_REGISTER_DSN` lines (and `PI_TRUSTED_PROXIES`, not a secret). It sits in a subdirectory so no fleet launcher's `*.env` glob reads it; keep it there.
- Read by `querynz-pi-web.service` through `~/.config/systemd/user/querynz-pi-web.service.d/30-serving-role.conf`.

**Order in the sitting:** after the application role and the replication
role; rewrite the file; `systemctl --user restart querynz-pi-web.service`
(Arthur or the script: the hook refuses a session this restart, the unit
being in the carve-out); then the proofs.

**The session proves, verdicts only:**

- The product answers on :8300 and the release's search gate is green
  (`ops/pi_release.py --dry-run`, run by the integrator).
- The old password is refused: one connection with the old value, by the
  script, prints "refused".

**Inventory line:** the serving role row, "Last rotated: <date>, in the
sitting".
