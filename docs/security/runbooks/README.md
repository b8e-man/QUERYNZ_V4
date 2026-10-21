# Rotation runbooks (track H.3)

One short page per secret, for Arthur. Each says where to go at the
provider, exactly which permissions, which file and variable on which
box, what to tell the session when done, the two proofs the session then
runs, and the inventory line that closes it.

The rules on every page, from `docs/plan/track-h.md`:

- **The value never passes through chat, a note, or anything a session can see.** Copy it from the provider's page straight into the credential file at the box.
- **Tell the session one word: "rotated"** (or "removed", "revoked"). It never asks to see the value.
- **The session proves two things and prints verdicts only:** the new value works, the old value is refused. Then it writes the date into `docs/security/inventory.md`.
- **Anything the frozen product uses is rotated well clear of the daily release** (`ftm-release.timer`, 06:19) and followed by a dry-run release.

Writing a value into a file at the box, without a paste buffer a session can see: on node2, in a terminal that is not a session,

```
install -m 600 /dev/null ~/.querynz/<file>.env     # only if the file is new
nano ~/.querynz/<file>.env                        # replace the one line
```

## Wave one: secrets that work from outside the local network

| Runbook | Secret |
| --- | --- |
| `cloudflare-deploy-token.md` | The deploy token for followthemoney.nz. Arthur alone; first |
| `nzbn-api-key.md` | The business-number interface key |
| `linz-api-key.md` | The LINZ Data Service key |
| `offsite-storage-keys.md` | The off-site storage push and read keys |
| `offsite-backup-passphrase.md` | The backup passphrase: the special case |
| `cloud-model-keys.md` | The cloud model keys: revoke and remove |
| `subscriber-logins.md` | NBR, BusinessDesk and Newsroom logins: remove |
| `alarm-address.md` | The ntfy alarm address |
| `github-and-box-keys.md` | The keys the boxes use for GitHub and for each other |

## Wave two: the database passwords, one sitting

| Runbook | Secret |
| --- | --- |
| `database-application-role.md` | The application role every old job connects as |
| `database-replication-role.md` | The replication role |
| `database-serving-role.md` | The read-only role the public app uses |

The sitting is Arthur's, after the election by default (7 November 2026),
rehearsed on scratch instances first. `database-application-role.md`
carries the order of the sitting; the other two are done inside it.

## Carried from H.7

| Runbook | What |
| --- | --- |
| `node1-admin-rights.md` | The admin-rights file on node1, never redone |
