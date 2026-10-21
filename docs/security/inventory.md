# The credential inventory (track H.1)

Every secret the two boxes hold, by name and never by value. Walked on
22 October 2026 by `security-1` against: the old inventory
(`/home/user/qnz3-ref/docs/runbooks/CREDENTIALS_INVENTORY.md`), the installed
job files on node2 (`~/.config/systemd/user/`), the old code in the
reference copy, and the new estate's code and `qv4-` units. Presence on
node2 was checked one named variable at a time, verdict only (present or
absent), never a value; the credential directory was never listed. Node1
was not walked: it answers on 10.0.0.10 but a login there needs Arthur's
approval in this session's mode, and node1 waits on its setup card
(ruling 57). Its column repeats what the old inventory recorded.

The checker: `python -m support.security.inventory` (the test
`support/security/tests/test_inventory.py` runs it in the fast tier). It
fails when the new estate's code or a `qv4-` unit reads a name this file
lacks, or when any file under `docs/security/` carries a value-shaped
string. Where each secret has leaked is in `leaks.md`; how each is
rotated is in `runbooks/`.

Reach: **outside** means the value is accepted by a service on the public
internet, so a copy anywhere in the world is usable; **local** means the
database or box accepts it only from the local network (the database's
access file is scoped to 10.0.0.0/24).

## Secrets, by wave

| Secret | File (box) | Variables | Read by | Reach | Last rotated | Wave |
| --- | --- | --- | --- | --- | --- | --- |
| Deploy token for the public site (Cloudflare) | `cloudflare.env` (node2) | `CF_API_TOKEN`; `CF_ACCOUNT_ID` beside it (an account id, not a secret) | Old: `ftm-release.service` (nightly, `ops/pi_release.py` → `ops/pi_cloudflare.py`), `ftm-feedback-drain.service` (`ops/feedback_pull.py`), `ops/cloudflare_token_check.py`. New estate: nothing (hard limit 2) | Outside | Rolled 2026-10-03; that replacement reached a transcript too (C470, closed 2026-10-08 with the no-chat path). No roll recorded since | One, first. Arthur alone |
| Business-number interface key (NZBN, MBIE API gateway) | `nzbn.env` (both boxes) | `NZBN_API_KEY` | Old: `society-officers.service` (`ops/backfill_society_officers.py`), `nzbn_canonical` settings and `api/delta.py`, `ops/settle_mp_orgs.py`, `ops/backfill_bic.py`, `ops/director_addresses.py`. New: `registers/companies/monitor.py` (`qv4-companies-monitor`), `registers/limited_partnerships/capture.py`, `registers/societies/capture.py` | Outside | Never. Supplied 2026-08-26 through chat | One |
| LINZ Data Service key | `linz.env` (both boxes) | `LINZ_API_KEY` | Old: `linz-titles-pull.service` (weekly, `ops/linz_titles_pull.py`). New: nothing yet (the `linz` lane is in `support/db`'s schema list only) | Outside | Never. Issued 2026-09-15 | One |
| Off-site storage push key (AWS IAM user `querynz-offsite-push`) | `offsite.env` (node2) | `OFFSITE_KEY_ID`, `OFFSITE_SECRET`; beside them, not secrets: `OFFSITE_ENDPOINT`, `OFFSITE_REGION`, `OFFSITE_BUCKET` | Old: `offsite-push.service` (nightly, `ops/offsite_push.py`). New: `support/offsite` (the nightly `qv4-offsite-dump` on the scheduler's clock; `QV4_OFFSITE_ENV` overrides the file in tests) | Outside | Never. Created 2026-08-23 | One |
| Off-site storage read key (IAM user `querynz-offsite-read`) | `offsite-read.env` (node2) | `OFFSITE_READ_ACCESS_KEY_ID`, `OFFSITE_READ_SECRET_ACCESS_KEY` | Old: `ops/offsite_restore.py`. New: `support/offsite/restore.py` (the restore rehearsal) | Outside | Never. Created 2026-09-15 | One, with the push key |
| Off-site backup passphrase (symmetric, encrypts every dump) | `offsite.env` (node2) | `OFFSITE_PASSPHRASE` | Old push and restore; new `support/offsite` copy and restore | Not a login: whoever has it and the bucket's contents can read every backup. Needed to restore every existing backup | Never. Created 2026-08-23 | One, special case: old and new both kept in the password manager with dates; a restore of an old backup rehearsed before the old one is forgotten |
| Cloud model keys | `llm.env` (`LLM_API_KEY`); `api.env` and `remedial.env` (`NOUS_API_KEY`). Not in `factory-db.env` or `era3-node2-fleet.env` on node2 (checked) | `LLM_API_KEY`, `NOUS_API_KEY` | Old: `querynz-research.service` and `querynz-sweep.service` (both stopped, on the stop list), `extraction/settings.py`, `query/agent.py`, `reconciliation` judges, `ingestion/explore`, `ingestion/ec_pageread/read.py`. New: nothing, by design (hard limit 10) | Outside | Never | One: revoke at the providers, remove the lines |
| Subscriber logins (NBR, BusinessDesk, Newsroom) | `newsscrapers.env` (node2; node1 per the old inventory) | `NBR_ACCOUNT_EMAIL`, `NBR_ACCOUNT_PASSWORD`, `BUSINESSDESK_EMAIL`, `BUSINESSDESK_PASSWORD`, `NEWSROOM_EMAIL`, `NEWSROOM_PASSWORD` (Newsroom was not in the old inventory; present). Absent on node2: `NBR_PROXY`, `SCRAPER_PROXIES`, `SCRAPER_PROXY`. Beside it: `nbr_cookies.json`, a session-cookie cache | Old: `newsscrapers.service`, `newsscrapers-daily.service` (on the stop list; their timers were still active on node2 on 22 October), `courts-capture.service` (optional). New: nothing; none of the three outlets is captured | Outside | Never | One: remove from the boxes, with the cookie file |
| Alarm address (ntfy) | `ops/config/alert-channel.env` in the live old folder, not the credential directory (the plan's map accepts this; see the queue) | `ALERT_NTFY_URL` | Old: `ops/production/unit-failed.sh` (`querynz-failed@`). New: `support/alarm` (every `qv4-` job; `QV4_ALARM_FILE` overrides the path in tests) | Outside: anyone with the address reads and sends the alarms | Never. Created 2026-09-04 | One |
| Keys the boxes use for GitHub, and between boxes | `~/.ssh/id_ed25519` (node2; node1 has its own pair). Not in the credential directory | The key file; `authorized_keys` on each box | node2's `origin` remotes for both repositories (`git@github.com:b8e-man/QUERYNZ_V4`, `…/QueryNZ_V3`); node2 → node1: the mirror push, `querynz-residue-mirror`, `wal-archive-mirror`, `querynz-deploy-node1` (all inactive on 22 October), the new installer's credential copy | Outside (GitHub) and local | Never. Created 2026-07-30 | One: a key for the new repository; review the old ones |
| Database application role `querynz` | `factory-db.env` (51 old units name it), `era3-node2-fleet.env` (8 old units and hand runs), `api.env` (its `V3_DSN` line is absent on node2), `v3.env` (absent on node2). Two installed drop-ins set connection strings inline: `querynz-api.service.d/10-era3-review.conf`, `querynz-research.service.d/20-era3-cutover.conf` | `V3_DSN`, `V3_BACKLOG_DSN`, `V3_REGISTER_DSN`, `EXTRACTIONS_URL`, `INCOMING_NEWS_URL`, `NZBN_CANONICAL_URL`; `GRAPH_DSN` (absent from `factory-db.env` on node2), `REVIEW_*_DSN` | Every old job, the old API, hand runs. New: nothing (the new estate has its own roles) | Local | Never | Two: the stop-the-world sitting |
| Database replication role `replicator` | `replication.env` (a record file; nothing reads it), the postgres user's `.pgpass` on the standby, and `primary_conninfo` in the standby's `postgresql.auto.conf` | `REPLICATION_USER`, `REPLICATION_PASSWORD` | Streaming replication between the boxes; `pg_rewind` in a fail-back | Local | 2026-08-24, then 2026-09-05 (minted in-process) | Two |
| Database serving role `querynz_serving` | `serving/serving.env` (node2; a subdirectory so the fleet's `*.env` glob never reads it) | The role's own `V3_DSN`, `V3_BACKLOG_DSN`, `V3_REGISTER_DSN`, and `PI_TRUSTED_PROXIES` (per `ops/production/c007_serving_role.sh`; the file's own lines could not be confirmed in this session's mode) | `querynz-pi-web.service` through its drop-in `30-serving-role.conf` (the carve-out) | Local | Minted 2026-09-05 | Two |
| The new estate's own logins (`qv4_owner`, `qv4_read`, `qv4_product`, and the old-estate reader) | `v4.env` and `v4-read.env` (node2; node1's copies when that box is set up) | `QV4_OWNER_URL`, `QV4_OLD_READ_URL` in `v4.env`; `QV4_READ_URL`, `QV4_PRODUCT_URL` in `v4-read.env` | `support/db` (every `qv4-` job and product, `bin/q`, the fast tier's sample fill); the installer copies the files box to box | Local | Created 2026-10-18 | None now (fresh, step 0); yearly under H.6 |
| Sealed-store key | `sealed.key` (node2); `SEALED_KEY_PATH` overrides the path | A key file | `data-layer/registers/registers/sealed.py` (old estate) | Local: a file, no service accepts it | Created 2026-08-22; custody under ruling 80 (one live copy, the other in Arthur's password manager) | None: replaced only under ruling 80's one-sitting rule |
| Postgres superuser | No file: OS peer authentication (`sudo -u postgres`) | — | Bring-up, promotion, rewind, role changes (Arthur) | Local | n/a | None |
| Admin rights on node1 (the sudoers file) | `/etc/sudoers.d/` on node1, never redone | — | Commands that need no password on node2 still ask on node1 | Local | n/a | H.7, Arthur at the box (`runbooks/node1-admin-rights.md`) |

Not on any box, Arthur's alone: the AWS console login, the Cloudflare
account login, the GitHub account login, the ntfy account if any, the
password manager.

## Files in the credential directory that hold no secret

| File | Variables | What it is |
| --- | --- | --- |
| `gpu-gateway.env` | `GATEWAY_BACKENDS` | Fleet topology, ignored by the gateway since C414; never a secret |
| `sync.env` | none: the file holds no assignment (the stub `ops/production/factory-bootstrap.sh` writes). `SYNC_SSH` is absent | Nothing active reads it (`querynz-verdict-sync` is inactive). Arthur to confirm or delete: default delete (queue) |
| `x.env` | — | Absent on node2. Its only references are example commands in the old hook's docstring. Default: struck from the inventory (queue) |
| `statsnz.env` | — | Absent on node2; no reader in either code base (card C135 said the key need not be secret). Struck |
| `v3.env` | — | Absent on node2; the old inventory listed it for the application role. Struck for node2; node1 unknown |

Settings that point at these files, not secrets: `QV4_CRED_DIR` (the
directory; tests point it at a temporary one), `QV4_OFFSITE_ENV`,
`QV4_ALARM_FILE`, `SEALED_KEY_PATH`. Transient: `PGPASSWORD`, which
`support/offsite/restore.py` removes from the environment it hands the
Postgres tools, and never sets.

## Rules this file carries

- A new secret is added here in the same merge as the code that reads it; the test fails otherwise.
- A rotation is a date in the "Last rotated" column, written when both proofs are green.
- A secret that stops being used is struck through, not deleted, for one release.
- Every secret is rotated at least once a year and at once when exposed (H.6).
