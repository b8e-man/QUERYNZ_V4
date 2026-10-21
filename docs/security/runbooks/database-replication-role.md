# The database replication role `replicator`

**Done inside the wave-two sitting** (`database-application-role.md`):
Arthur's, after the election by default, rehearsed on scratch instances
first. Rotating this one in August forced the standby to be rebuilt from
scratch; the rehearsal is for exactly that.

**Reach:** local network only (the access file allows replication from
the other box's address).

**Where it lives, by path only:**

- The Postgres role itself (`ALTER ROLE replicator PASSWORD`, run as the postgres user at the primary).
- The standby's `primary_conninfo` in its data directory's `postgresql.auto.conf`, or the postgres user's `~/.pgpass` on the standby (the 5 September rotation put it there).
- `~/.querynz/replication.env` on both boxes: the record file, lines `REPLICATION_USER=` and `REPLICATION_PASSWORD=`. Nothing reads it; it exists so the password manager and the boxes agree.
- The shell history on node2 carries the August value in three lines (`docs/security/leaks.md`); that history is cleaned as part of H.2.

**Order in the sitting:** change the role at the primary; write the
standby's connection setting; restart the standby's receiver; confirm
streaming; then the record file; then the password manager.

**The session proves, verdicts only:**

- The standby is streaming (`pg_stat_replication` on the primary shows the
  standby's slot active; the standby's lag returns to zero).
- The old password is refused: one replication connection with the old
  value, made by the script before it forgets it, prints "refused".

**Inventory line:** the replication role row, "Last rotated: <date>, in
the sitting; standby streaming".
