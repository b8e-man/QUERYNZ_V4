> Part of [LESSONS](../LESSONS.md) — living memory, one section per file
> since 2026-10-04 so that "read the relevant section" is a thing a reader
> can do. The rules of the file, and why it exists, are in LESSONS.md.

## 1. Ops & the estate

- **Two captures of one document are two readings of it, and a
  regenerate-and-purge derive will let them fight.** Where a derived table is
  rebuilt by "write what this pass parsed, delete what it did not", feeding it
  the same document twice in one run makes each pass undo the other. The rows
  come back with NEW ids every run, and any consumer keyed on the row id — a
  graph feed's idempotency DELETE, say — can never find the rows it wrote
  last time. Nothing looks broken: the register is correct, the counts are
  plausible, and the claims quietly accumulate forever.
  *Paid for by:* 2026-09-21. 1,328 gazette notice URLs sat in `articles`
  twice and the derive's read had no DISTINCT, so four purge-carrying
  families tore at each other. Appointment claims for notice `2025-go7375`
  grew by two every night since 2026-08-24. The tell was in the data, not the
  code: a register with 10,662 rows whose id sequence had reached 513,595.

- **A DSN THAT SETS `options=` DISCARDS `PGOPTIONS` WHOLE — so a setting
  shipped in the environment can be silently absent exactly where it matters.**
  libpq does not merge the two: `PGOPTIONS` is the DEFAULT for a connection
  string's `options` parameter. Measured on the primary 2026-10-10: `PGOPTIONS`
  alone gives `statement_timeout` 12345ms, the same `PGOPTIONS` with a DSN
  appending `?options=-csearch_path%3Dv3,public` gives **0**. Four live sites
  appended an `options` for the search path alone and two were inside the
  nightly derive chain, so C558 PF-3's timeout drop-ins would have been absent
  on `gazette-feed` — the one lane whose orphan earned the lesson. The
  separator fails silently too: `+` between two settings put the whole string
  into `search_path` and left the timeout at 0; only `%20` separates. One
  builder now holds it, `estate_dsn.with_options`, which folds the
  environment's settings in, and a repo-wide test refuses a second site.
  Corollary for any unit-level setting: prove it ARRIVED (`SHOW`), never that
  the file exists.
- **When you must choose between two captures, do not choose by size — find
  the signal that says which one is FAITHFUL.** Size is the first thing to
  hand and it is not a fidelity measure. Look for damage that the capture
  path leaves behind: structure lost, whitespace injected, characters
  flattened.
  *Paid for by:* 2026-09-21. Both captures of `2025-go7375` are 626
  characters, so the length tie-break I wrote first would have picked by
  article id — a coin toss. One capture flattened the notice's lines and
  injected a space before punctuation as it went, so it reads "Puamirira
  Parata -Goodall" and the parser takes the name as "Puamirira Parata" and
  loses Mark Kneebone entirely: 3 appointees where the faithful capture
  yields 4. In ALL 1,328 duplicates exactly one capture kept its newlines —
  a clean discriminator, and the only reason a pick could be made on evidence
  rather than luck.

- **A rebuild's DELETE must be as wide as the thing it rebuilds, or the
  residue is invisible.** A feed that owns a family of rows clears the family
  and writes it again, inside one transaction. Anything narrower — per member,
  per edition, per "everything except what I just wrote" — leaves rows nobody
  will ever look for, because they belong to keys the new run no longer
  produces and so never touches.
  *Paid for by:* 2026-09-21, C164. Deleting per (member, category) left 825 of
  4,171 claims — each edition ate the last. Widening to per member left 241
  for 13 members the re-parse no longer produces. Adding a sweep of members
  NOT in the run still left 5: Megan Woods' August trust claims, minted from
  Standing Orders boilerplate, spared because she IS in the run and simply has
  no trust rows any more. Only the family-wide rebuild reached zero.

- **A dry run that counts only what it writes will confirm a wrong number.**
  The count said 4,171 inserts and was correct about inserts; 825 survived,
  because it never mentioned the deletes eating them. Report the destructive
  side beside the constructive one.
  *Paid for by:* 2026-09-21, C164 — the feed now prints `cleared` and
  `editions_folded` next to `claims`.

- **A hand-run command that needs context the reader already has to know is a
  broken command — ship the wrapper, not the incantation.** The repo keeps its
  own interpreter and its credentials outside the tree, so a module path alone
  is never runnable: it dies on an import, or on a DSN that was never
  exported, and the traceback names neither. Anything handed to an operator
  carries its own venv and its own credential file, and anything that CAN
  still be run the wrong way says what the right way is in the error.
  *Paid for by:* 2026-09-21, C164 — the feed was handed over as `python -B
  ops/mp_interests_feed.py --apply` and returned
  `ModuleNotFoundError: No module named 'psycopg'`. The fix is
  `ops/production/mp-interests-feed.sh` plus two guards that print the wrapper
  line instead of a traceback.

- **The thing you changed is not the thing that ran — restart it, and verify
  at the layer that serves.** A code fix does not reach an already-running
  process, a deploy path reports success while serving stale code, and a timer
  that fires between a merge and the unit sync runs the OLD unit. Verify the
  SOURCE's freshness, not the tool's success message; after a unit gains steps,
  run the missed steps once by hand.
  *Paid for by:* 2026-08-20, the sweep's Decimal fix — committed, correct, and
  the relaunched run had already imported the old module and died on the same
  line (previously learned and lost as v2 SCRAPERS.md lesson 17, where a
  backend without `--reload` served a stale catalogue for hours) · v2's
  "Already up to date" from a clone that had not been fed, and the same shape
  when node1's mirror went stale · the 07:45 daily that ran without its new
  steps because the sync landed at 08:17 · 2026-08-23: "push the mirror, then
  pull on node1" followed to the letter for weeks while node1's checkout sat on
  `bringup/node2-factory-2026-07-30` — `git pull --ff-only` fast-forwarded the
  wrong branch and printed success every time; compare the BRANCH and HEAD hash
  to node2's, not the pull's exit code (memory `node1-deploys-via-mirror`) ·
  2026-09-08: `ec-disclosures.timer` sat in `ops/systemd/` with its manifest row
  and watcher and did not exist to systemd until Arthur copied it — a repo unit
  is not an installed unit, and the manifest gate (T7.12) is what says so.

- **Essential work runs under a unit with a restart policy and a watcher, and
  a watcher is proven by stopping something.** Transient means ephemeral
  experiment. Nothing measures the measurers unless you make it — and a board
  that produces no result is not a watcher either. An invariant board asserts
  properties of the RUNNING system, not of the code, which is why T7 queries
  the live database and leaves its unit FAILED on red rather than printing a
  warning (→ ops/systemd/README.md): contracts break in production between
  commits while every log line reads healthy.
  *Paid for by:* 2026-08-20, the embeddings backfill launched with
  `systemd-run` died with the embed server and sat failed for 17 hours (→ plan
  28w, terminal L8) · the same 2026-08-20 services audit: every daemon
  self-restarted and every timer was scheduled, and nothing asserted "no unit
  is in a failed state" (→ watcher doctrine, terminal Layer 8; T7.12) ·
  `Restart=on-failure` masking an OOM kill completely — the kernel killed
  llama-server at 05:11, by 05:12 the unit was active and nothing showed
  failed; both kills that week were silent, and only a memory watcher (kernel
  OOM line, commit ratio, swap) sees them (→ plan B2) · 2026-08-22 (B2): the
  acceptance for "the estate watches itself" was a deliberately stopped timer
  showing RED on the next board run, and the board's own failed state must not
  feed its own unit arm (ruling 39) or every red is counted twice · audit
  2026-09-03: the T7 board produced no result from 2026-08-31 18:53Z through
  both incidents (09-02 killed at the 15-min timeout, 09-03 exit 1), so
  T7.12/21/28/30 were never evaluated while the estate was at its worst and
  every "watcher row" cited in the postmortems was nominal — a
  board-ran-within-26h alarm that survives era pauses · 2026-08-22 (B2b): a
  statutory deadline gets a watcher, not a calendar note — T7.16 goes red two
  weeks before commencement without a seal and stays red while clear rows
  remain.

- **Read the live listeners before touching database networking; a bridge
  rewrites the address the server sees.** node1's Postgres is localhost-only
  behind socat bridges — NEVER set `listen_addresses='*'`. Expose a new address
  with ITS OWN bridge (`querynz-vip-bridge.service`), never by widening
  postgres; `ss -ltnp | grep 5432` first, and reason about EVERY listener. The
  known-good list is `localhost,10.0.0.1`; restore with `ALTER SYSTEM SET
  listen_addresses='localhost'` + restart.
  *Paid for by:* 2026-08-29, exposing the db-primary VIP — postgres tried to
  bind `0.0.0.0:5432`, collided with the `pg-bind-bridge` socat already holding
  `10.0.0.1:5432`, and came up IPv6-only (`[::]`), so every IPv4 path died,
  the factory's `10.0.0.1` included (TWIN_FACTORY_ARCH.md) · 2026-09-06, the
  C051 restart: the same bind failure against the VIP bridge on 10.0.0.10:5432,
  ~13 min off IPv4 · 2026-08-18, the standby rebuild: the socat bridge made
  replication arrive as `127.0.0.1`, so both host lines were required — any
  relay rewrites provenance · and check `uptime` and `ss` before touching a
  node1 service at all: the box idle-suspends and postgres can lose its NIC
  bind on boot (memory: node1-ops-traps).

- **A postgres setting is tested by making postgres run it, in postgres's own
  domain.** A `runuser -u postgres` shell test is UNCONFINED and proves nothing
  about the SELinux domain the server actually runs in; a change bundled into
  "the one restart" is still a change, and each gets its own pre-check and a
  post-check from the OTHER box.
  *Paid for by:* 2026-09-06 (C051): `restore_command`/`archive_command` run
  under `postgresql_t`, which cannot exec ssh — and an exit status above 125
  from `restore_command` is FATAL to recovery, so the standby shuts down. Fetch
  across boxes by a `user`-level mirror timer and let postgres read local
  files; the post-check includes `pg_isready` FROM the other box, not only a
  local `SELECT 1`.

- **Postgres's own traps, each paid for once: read them before a DB
  operation.** `pg_hba` is first-match-wins — read it top-down as postgres
  does, don't append and hope (2026-08-18 standby rebuild: an existing ident
  rule silently shadowed the scram line below it). `ALTER SYSTEM` cannot run in
  a multi-statement `psql -c` string — all statements go as ONE simple-query
  transaction, ALTER SYSTEM errors and rolls back the WHOLE string, silently to
  a hurried reader; one `-c` per statement and VERIFY the effect (2026-09-02,
  where it took the slot drop with it). A replication slot reserves nothing
  until told to — create the peer's slot AT promotion with `reserve=true`, or a
  2-minute rewind becomes a 257 GB basebackup (2026-08-24 failover drill; same
  run: pg_rewind's "no rewind required" writes NO recovery conf on some paths,
  basebackups do not copy slots, hba's `replication` keyword does not cover
  pg_rewind's ordinary login, and long-lived services must restart with the API
  on every DB endpoint flip). An INACTIVE slot with
  `max_slot_wal_keep_size=-1` is an unbounded disk claim on the PRIMARY —
  every slot needs a retention cap and a watcher row on `pg_replication_slots`
  (2026-09-02: node2's standby died of disk-full while the `node2_standby` slot
  kept 2,197 GB of WAL distance on node1 with the era mid-drain; a standby can
  stream WITHOUT a slot, so a leftover slot from a rebuild is pure liability —
  and user-level `du` CANNOT see root-owned PGDATA, so a "missing terabyte" on
  a box with postgres on it is pg_wal until proven otherwise). `CREATE OR
  REPLACE VIEW` can only APPEND columns — new columns go at the end or the view
  is dropped and recreated in the same migration (2026-08-22 B2b,
  `registers.colocations`). And `psycopg` dict_row silently collapses duplicate
  unaliased column names, so `.values()` comes back one short and the
  IndexError fires at serving time, far from the SQL — ALIAS every aggregate
  column (2026-09-02, PI coverage 500).

- **Every mutation is bounded, audited and reversible BEFORE it runs — and the
  audit row is written first.** Compute the blast radius; default to dry-run;
  make the reversible primitive the only delete. Reversible-by-design is not
  enough — the REVERT path needs per-row savepoints and dead-row skips, because
  a silent revert failure looks exactly like an undo that ran. A judgment table
  is never hand-DELETEd, even to withdraw a defective run: quarantine covers
  our own judgments as much as the graph.
  *Paid for by:* thirteen junk null-pollution rows that turned out to own
  ~6,000 dependents · 154,880 entities renamed with a bare UPDATE and no log,
  so the old names are simply gone — merges write `entity_merges`, retypes
  write `entity_type_changes`, renames wrote nothing (still open:
  reconciliation's wave writer is exempted by its own boundary test) · a silent
  revert failure that poisoned nodes for days · 2026-09-03: the first
  donor-anchor-1.3 pass read dict rows as tuples and wrote 4,324 rows carrying
  no new information, "withdrawn" by a DELETE from a scratchpad script,
  recorded in the PI plan and nowhere else, against a table with no withdrawal
  column — a defective run gets a `withdrawn_at`/reason flip and the serving
  join excludes it; same class as
  `fetch_wikipedia_candidates_2026.py --reparse`, which DELETEs a revision's
  rows while its docstring promises snapshots are kept (both carded, DECISIONS
  157) · a clear-then-promote cutover run as four committed steps, so an
  identical-content rebuild EMPTIED the live register for the window and a
  crash mid-way would have made that permanent.

- **DDL on a live graph: pause the writers, apply statement by statement under
  a lock_timeout, and VERIFY the schema stamp afterwards.** A migration can
  roll back silently and still exit 0. A schema file applied to a LIVE graph
  carries `ADD CONSTRAINT … NOT VALID` + `VALIDATE CONSTRAINT` pairs, never
  validating adds. DDL belongs with the package that owns the table.
  *Paid for by:* a mis-ordered statement that made every upgrade roll back
  silently while the spine's continuous tick deadlocked against `ALTER TABLE` ·
  2026-09-04 (Muster 2 B0, ruling 164): the idempotent `apply-schema` is a
  drop-and-recreate of every CHECK executed as ONE statement; on the primary it
  hit a 10 s lock_timeout because 16 judge workers sat "idle in transaction"
  holding AccessShare on `claims` for the length of each LLM call (22 s – 4 min,
  rolling), and a longer timeout would have queued the ACCESS EXCLUSIVE behind
  them and stalled every reader. What worked in 2.4 s: stop the crawler cycle,
  apply only the differing statements as NOT VALID then VALIDATE (SHARE UPDATE
  EXCLUSIVE — reads and writes continue). The 08-30 "verified on a scratch
  schema" closure is the same lesson from the other side: a fresh schema never
  meets a lock · 2026-09-07: write the DDL where the table's DDL lives
  (`ops/register_indexes.sql` for bulk/public tables, the registers package
  `DDL` strings for `registers.*`), measure the scan count that justifies it,
  and hand Arthur one psql line — amended by ruling 317 (2026-09-20), a
  statement Arthur has already approved may be run by Claude.

- **Share-mint (`V3_SHARE_MINT=1`) is the RULED exception to the
  no-advisory-lock rule — do not re-flag it as a regression.** With share-mint
  on, a worker has no mint side connection, so a NEW-form miss takes the entity
  advisory lock on the article connection — deliberately reverting the
  2026-08-23 split to buy one connection per worker (3→2), which bought +6
  workers inside `max_connections=100`. A/B-tested, adopted into
  RULED_DEFAULTS, cost stated in `v3/cli.py`. Measured on the 26-worker
  light-tier fleet (2026-09-01): 2.3% of non-idle backend time, waits 0.0–1.1s,
  cheap because the fast path skips the lock. REVISIT TRIGGER: a sampled waiter
  fraction over ~10% means the connection headroom no longer pays for the
  serialisation — re-run the A/B before believing either answer.

- **A unit with a deadline needs a writer that can be interrupted, and where
  the transaction BEGINS is a design decision that belongs beside the
  choice.** Atomicity is decided by the CALLER and documented in the CALLEE, so
  the module that understands the boundary does not choose it and the module
  that chooses it does not mention it.
  *Paid for by:* 2026-09-20 — Muster 3's goal G2 required every essential unit
  to have a bounded start, and `docpipe-daily` duly carries
  `TimeoutStartSec=4h`. On the first genuinely busy night (417 documents
  materialised where 0–13 was normal, 77,226 mentions, the resolver's working
  set up from 61,791 forms to 63,051) `resolve auto` ran 2 h 49 m inside ONE
  transaction and systemd killed it at the bound. Every merge rolled back: zero
  `auto:variant-identical` rows that day against 609 the day before. The bound
  did what it was asked; the goal never asked the other half — and it repeats
  deterministically, because the extraction committed and the merges did not.
  `claim_graph.merge.merge_entities` ends its docstring "Caller commits" — the
  only place a reader is told anything about transactions — while the caller,
  `v3/cli.py`, wraps a whole wave in one `with db.graph_conn()` and says
  nothing; when it cost a night's merges the filed defect named the callee, the
  module behaving correctly.

- **A resource setting measured while the rest of the estate was idle is not a
  setting — and more concurrency can be slower.** Measure under CONCURRENT
  load, and size a fleet on Pss, not RSS.
  *Paid for by:* `--cache-ram 20480`, measured-good on 2026-08-18 and
  OOM-killing the agent lane on 2026-08-22 once the era backfill put extraction
  back to work (→ mode 8; plan B3b's batch rule) · sixteen workers taking 653s
  where eight took 186s · the 12 extraction shards showing 2.8 GB each in `ps`
  (33 GB summed) against 8.0 GB true Pss from smaps_rollup — a top-of-head
  reading wrong by 4× · swap at 100% on a 7 GB swap sitting permanently inside
  systemd-oomd's 90% kill condition, unfired only because pressure stayed under
  the second threshold · 2026-08-23: the 62 GB box holds the 10-shard fleet
  (31 GB resident), the agent llama (8.8 GB) and the fleet llama (4 GB), so
  loading the dense 27B on top with zram at 100% got it OOM-killed three hours
  in and lost the whole R3a pass, which writes only at the end — any extra model
  run stops v3-extract first and checks MemAvailable, and long passes write
  partial results (`ops/r3a_run.sh`; runsheet B, the swapfile) · 2026-09-03:
  resuming both era arms (16 + 13 shards) into the 100-slot budget put node1 at
  97/97 and querynz-api went 503 for six minutes — the workers were fine
  (persistent connections), only NEW connections were refused; nothing reserves
  slots for serving and the earlier 89/100 margin was luck. Before widening a
  fleet, check `ss`/pg_stat_activity headroom and hit /api/health after;
  structural fix = reserved serving slots or a pool (era-6).

- **The operator's shell is never the truth — a hand run reproduces the UNIT's
  environment, whole.** Sourcing an env file rewires every later command in
  that terminal; an env file's key can mean a different database on each box; a
  writer that lands on the read-only standby reports success. Anything that
  must run FLAGS-OFF sanitises inherited env
  (`era_cutover._clean_operator_env`); anything needing the FLEET's env reads
  the systemd unit, files overlaid on inline (`parse_unit_env`, offsite_push
  `_fleet_env`). Never put a `source` and a later env-sensitive command in the
  same runsheet terminal without saying "fresh shell".
  *Paid for by:* THREE bites — 2026-08-23, the first era-4.1 `--fire`
  inherited the operator's DSN and seeded the READ-ONLY standby (the fleet UNIT
  is the truth for where the canonical is; preflight now refuses a graph in
  recovery); 2026-08-30, offsite_push read `show -p Environment`, blind to the
  EnvironmentFile= the fleet env had moved into; 2026-08-31, the era-5 fire
  terminal still carried `V3_EXTRACTOR_ERA3=1` + `V3_VAR_DIR` from the §Z
  one-shots — two preflight halts · 2026-08-22 (B2): moving a unit from an
  inline DSN to EnvironmentFile looked like pure hygiene, and the env file's
  `INCOMING_NEWS_URL` points at node2's read-only standby, so the era backfill
  died on its first INSERT at 08:44 — a unit that WRITES names the canonical
  store by the factory's own name for it (`V3_BACKLOG_DSN`), never by a key
  whose meaning is per-box, and a unit change is verified by firing the unit ·
  2026-08-23: `scrapers.run --source enforcement` reported "discovered 142,
  enqueued 0 new" because every INSERT failed on the standby and `enqueue_url`
  swallowed the exception (`pdfpipe/store.py` logs now) · 2026-09-15: a
  backwalk proof that took the embed unit's variables failed authentication on
  every lander call ("streak 1/3 → transient" looked like life); the second,
  applying `fleet_env('newsscrapers.service')` in full, landed 85 articles ·
  2026-09-13: the node1 embed keepers exported `EMBED_URL` per shard and the
  worker module had it hard-coded, so both shards queued on one server for 13
  hours at 4.3/s — and that server had been started without a GPU pin, running
  3.6/s across two cards while the pinned one did 60/s. Neither fact was
  visible from the launcher script or the log; what found it in minutes was the
  worker's own environment, the server's `/slots`, task counts from the server
  logs and `gpu_busy_percent` per card. A burst's first check is throughput PER
  SERVER, measured (queue 1, 2026-09-14).

- **A cold boot is no-touch only when every actor waits for the thing it needs
  — the address AND the disk — and a oneshot with `RemainAfterExit` will not
  notice when it loses either.**
  *Paid for by:* 2026-09-14 — node1's VIP unit waited for `network-online`,
  satisfied by the wifi, and added 10.0.0.10 to a card whose link to node2 had
  no carrier yet; NetworkManager adopted the card as external and never applied
  the LAN profile, postgres bound localhost only, and the standby fell back to
  the WAL archive. Fix (C380): the LAN profile outranks, postgres binds `*`,
  the VIP unit waits for the PROFILE to be active, `ip addr replace` — proof is
  a reboot drill, not a reading. Trap on the way: `pg_stat_wal_receiver` /
  `pg_stat_replication` show a row of NULLs to a non-superuser role, so count
  rows and compare `pg_last_wal_receive_lsn()` · 2026-09-17, the power cut:
  node2's standby keeps pg_wal on the HDD, `/mnt/hdd` is a `nofail` mount with
  a 10 s device timeout, and the stock unit orders itself only after the
  network — postgres started at 20:39:54, the disk mounted at 20:40:08, `FATAL:
  required WAL directory "pg_wal" does not exist`, and the standby stayed down
  for 8 minutes until a person started it. A unit whose data sits on a `nofail`
  mount carries `RequiresMountsFor=<the path>`, homed in the repo and pinned by
  a test (`ops/production/system/postgresql-wal-on-hdd.conf`, runsheet 68);
  grep every unit for `/mnt/`. The OnFailure ledger RECORDS and nothing ACTS —
  a boot-time failure needs a boot-time actor (C390). Both boxes kept the RTC
  in local time, so every boot's journal starts 12 h ahead until chrony steps
  it and a Persistent timer can fire into the wrong day. The power came back
  unstable — node1 booted twice in two minutes with no shutdown lines, C380
  held both times, and a UPS is the only cure for that class. The standby's log
  is root-only but the sudoers psql line reads it via `pg_read_file`, and `sudo
  -n systemctl start postgresql` is allowed, so the recovery needs no password
  · 2026-09-03: after an unclean reboot, `systemctl --user --failed` FIRST,
  then the VIP by `ip addr`, never by the unit's state — every timer whose
  first tick landed before the network/VIP was up failed (offsite-push's
  pg_dump, whose `var` half still uploaded a PARTIAL 4.9 GB object into
  undeletable Object-Lock; crawler, mint-lane, embed-backfill, v3-audit,
  v3-extract; newsscrapers-daily at 07:56 was the unrecorded seventh), while
  the oneshot VIP unit with `RemainAfterExit` reported active with the address
  gone. Units the era has paused do NOT self-retry — their timers are inactive
  until RECORD restores them (Postmortem §9/§9a) · 2026-09-15 06:28 (runsheet
  51): the C380 script's `nmcli con up ethernet-10g` dropped the VIP that
  `querynz-vip` had added two days earlier, the unit stayed "active", node2
  lost the primary for five minutes — a script that touches the profile re-adds
  every address it does not own and ends by proving the wire · the first look
  after a cut is ruling 249's board command plus `systemctl --failed` on both
  boxes and `pg_stat_wal_receiver` on the standby, in that order
  · 2026-10-06 (C317), the same rule one layer up: `After=`/`Wants=` on a
  `Type=simple` server waits for FORKED, never for ANSWERING, so the era-5.1
  restore started the embed backfill in the same breath as the embed server
  (`--no-block`), got a 503 off a loading model and exited 1 — a phone push for
  a deliberate restore. A dependent of a server PROBES it, and the probe's
  load-bearing flag is `--retry-connrefused`: a server that has not opened its
  port REFUSES the connection, and `curl --retry` alone retries only transient
  HTTP statuses, so without it the guard fails on its first attempt in exactly
  the race it exists for. The window had shrunk to 0.9 s (the lane moved to CPU
  with a 700 MB model, ruling 329) — and 0.9 s early fails as hard as a minute
  early.

- **Ingests write the CANONICAL box, never the replica — and a drift "repair"
  can be the thing that destroys the data.** The canonical side flipped at
  cutover; the rule did not.
  *Paid for by:* an ingest that ran on the wrong box, after which the next
  morning's drift repair dropped those tables and synced stale copies over
  them, destroying the only database copy of a month's corpus — recovered only
  because the source CSVs survived.

- **Grep the estate for a path before you move it, and nothing a running unit
  reads goes behind a `noauto` mount.**
  *Paid for by:* 2026-09-02/03 — the disk-full offload moved
  `/home/user/var-era3` (`settings.VAR_DIR`: gazetteer.pkl, a live fleet
  dependency) to the HDD under a `noauto` fstab line, and the 06:17 unclean
  reboot left it unmounted while four v3-extract ticks died on
  FileNotFoundError. `grep -r <path>` over units, settings and env files is the
  pre-offload step; archive mounts carry `nofail` (Postmortem §9a) · the same
  discipline, in code: don't name a script after a stdlib module — a scratch
  `inspect.py` on the path shadowed the module bs4 imports and produced a
  circular-import error nowhere near the cause.

- **Profile the hot path before running a bulk wave for hours, and measure the
  scans before touching a query.** `pg_stat_user_tables` seq_scan /
  seq_tup_read names every hot path in one read; without pg_stat_statements
  (absent on every cluster), that is the instrument.
  *Paid for by:* the merge fold running 11 hours at ~70/min because three
  tables lacked an entity_id-leading index and every merge rescanned keeper
  attachments against 201M rows — ~16,000/min after the fixes, a 230× miss an
  hour of profiling would have caught (claim_graph/SPEC.md) · 2026-09-07:
  director_roles at 287k full scans on a `coalesce()` key the partial index
  cannot serve; `entities` at 1.18 T tuples read through `name = %s` beside a
  `lower(name)` index; the embedder's per-batch anti-join over 15 GB. cProfile
  with a round-trip counter then showed the donor page's 4.8 s was ONE query
  aggregating all 1.56 M shareholdings twice, not the 158 round-trips ·
  2026-08-24: `resolve auto` loaded all 22.6M entities as dict rows to group
  identical name-forms — 15.7 GB, and docpipe-daily's nightly peak had climbed
  4.7 → 15 GB in five days before the kernel OOM-killed it at 05:00 beside the
  extract tick. Streaming but keeping one tuple per form still peaked at 8.4 GB
  — almost every form is unique, so the "compact" dict IS the graph; the
  grouping belongs in Postgres (stream `(id, type, form)` into a temp table,
  bring back only the forms that occur twice: 130 MB peak, 4 min). Any pass
  that keys on "every entity" must be bounded by the DUPLICATE set
  (`reconciliation/waves.py auto_wave`, measured with `/usr/bin/time -v`).

- **A transport failure is not a content failure, and any fetch loop needs a
  circuit-breaker.** Only content-shaped failures count toward poison or retry
  caps.
  *Paid for by:* a ~90-minute DNS outage that charged 47 innocent articles
  three strikes each while IP-addressed traffic kept working — ingestion
  healthy, extraction dead is a shape worth recognising on sight · a 401-storm
  that ingested ~11k bad articles at full speed, looking exactly like success.

- **Assume nothing about an exception hierarchy, a contract in a docstring, or
  a step wrapped in `|| true`.** Pin the hierarchy in a test; encode an
  inter-stage contract as a staleness watchdog that alarms; gate on the real
  exit status.
  *Paid for by:* a deadlock retry that caught `TransactionRollback`, which
  reads like the parent of `DeadlockDetected` — in psycopg 3.3 they are flat
  siblings, so the fix imported cleanly, passed every existing test, and would
  have retried NOTHING · a rewrite that dropped the "mark the ledger processed"
  step, freezing the backwalk at its target for two days while every surface
  looked healthy — every NEW write path must stamp the shared ledger too, or
  its work is invisible to gates · a first-run launcher that showed a green
  registers stage while 5 of 7 syncs crashed on missing modules and absent
  arguments, 4 of the 7 never having run once.

- **Model weights are RECORDS, not teardown targets.** Anything expensive to
  reacquire is a record — the bench CSV, the weights, the sealed captures.
  *Paid for by:* 2026-08-18, a benchmark cleanup that deleted a candidate model
  and had to re-download it.

- **Local llama-server lore:** set client timeouts above the worst observed
  case, restart the server after killing requests (ghost requests spiral),
  remember `--parallel` × ctx-size are coupled for VRAM, and know that q8 KV
  cache costs 13× slower prefill than fp16 KV for identical generation (which
  is why the agent lane runs fp16 KV at 3×50k slots;
  lessons-2026-08-18-era3-close). Under WAYLAND_DISPLAY, Chromium auto-picks
  Wayland and Playwright's launch hangs at the DevTools pipe —
  `--ozone-platform=x11` on the XWayland DISPLAY works, a profile left by a
  killed run crashes the next launch (SIGTRAP), so use a fresh profile per run.

- **Never `pkill -f` / `pgrep -f`: they see the ssh command line that carries
  them.** A pattern that appears in the remote command string kills or counts
  the ssh session itself. Kill by pid (`ss -ltnp` for the port holder) or
  anchor on the executable (`pgrep -x llama-server`).
  *Paid for by:* twice, 2026-09-14/15 · and again on 2026-09-20 by the author
  of this line — see "a standing rule with no gate" in §3.

- **With two remotes, "the push failed" is per-remote, and the combined output
  hides which one got through.** A push to origin and a push to mirror in one
  command line print one stream; origin's pre-push gate failed loudly, the
  mirror's push succeeded quietly underneath it, and the commit was read as
  unpushed. It was then `--amend`ed — which is exactly what the standing rule
  forbids, and the reason the rule says *any push ATTEMPT*, not *any successful
  push*. The divergence was repaired by MERGING the mirror's copy, never by
  force-pushing: two identical-content commits with different hashes are a
  merge, not a mistake to erase. **Check `git ls-remote <remote> main` against
  `git rev-parse HEAD` before concluding a commit is local.**
  *Paid for by:* 2026-09-20, C231's close.

- **Before moving a directory, grep for what names it — and grep the UNITS,
  not just the code.** A directory that looks like old data is a live
  dependency until something has asked. The check is cheap and has three
  parts, because a path can be written in any of them: the repo
  (`grep -rn "<dir>" .`), the unit files and their EnvironmentFiles
  (`systemctl --user show <unit> -p Environment`, `grep -rn "<dir>"
  ops/systemd/`), and the settings module, where a path reached through a
  constant will not match a grep for the path at all — so grep the CONSTANT
  too. Then, if it moves, mount the destination `nofail` and check that the
  first timer tick after the move still passes: a `noauto` mount means the
  move survives exactly until the next reboot.
  *Paid for by:* 2026-09-02/03. `/home/user/var-era3` was offloaded to the
  HDD as part of clearing a full disk. It is `settings.VAR_DIR` — the
  fleet's gazetteer lives in it — so a grep for "var-era3" in the code found
  nothing worth stopping for. node2 then rebooted uncleanly, the HDD was
  `noauto` and did not remount, and the 07:15 tick died on
  FileNotFoundError. Six services failed their first post-boot run, THAT
  DAY'S OFFSITE BACKUP WAS MISSED, and T7.21 stayed red until 01:38.

- **In this estate a commit is PUBLISHED within the minute, so "nothing is
  pushed yet" is never a reason to rewrite it.** `querynz-deploy-node1.timer`
  runs `ops/production/sync-node1.sh` on a clock, and that pushes `main` to
  node1's mirror whether or not anyone typed `git push`. The window between
  committing and being unable to rewrite is the timer's period, not the time
  until you push. Fix a bad commit message the way it is fixed after a push:
  a new commit, or a merge that says what happened.
  *Paid for by:* 2026-09-24. A commit was split thirty seconds after it was
  made, to put the C433 reader fix under its own message. The timer had fired
  three seconds after the commit. The mirror then held a commit that was no
  longer an ancestor of `main`, could not fast-forward, and could not be
  force-pushed — the standing rule, and correct — so main carries a merge of
  two identical trees to get past it.

- **A run history must not change which service a unit belongs to.** Wrapping
  five units with `ops.fleet.runjob` to give their runs a history made the
  first `-m` in every ExecStart `ops.fleet.runjob`, and the census names a
  unit's service from exactly that — so healer and research would have gone
  unowned the day their runs started being recorded, and the SPEC gate would
  have demanded they stop declaring units they still own. **When you wrap a
  command, check what reads the command.** (2026-09-26, C416.)

- **"A database answered" is not "the right database answered" — and
  unpacking a `dict_row` POSITIONALLY yields its keys.** Both health endpoints
  reported `{"database": "current_database", "server": "?column?"}` — the
  column NAMES, served as values, for however long nobody read the payload
  closely. The mechanism is the third occurrence of one mistake in this repo:
  a `psycopg` row factory returning a mapping, unpacked as a sequence. The
  content matters as much as the bug: on a box whose localhost postgres is a
  read-only standby, "something answered" is precisely the hazard
  `estate_dsn`'s own docstring names, so identity has to be `system_identifier`
  (unique per cluster) **and** `current_database()` **and**
  `pg_is_in_recovery()`, every column aliased and read BY NAME. (2026-10-05,
  C061; earlier occurrences 2026-09-02 PI coverage 500 and the duplicate
  unaliased-column collapse above.)

- **A unit with no `Restart=` has no recovery, and the thing it protects is
  measured in days.** The nightly offsite push carried no restart directive at
  all: one transient failure at 02:00 and the next copy offsite was 48 hours
  old, which is an RPO nobody had agreed to and no board arm asked about.
  Every unit's restart policy is part of the thing it is for — state the RPO
  the unit implies, then read its `Restart=`, `RestartSec=` and
  `StartLimitBurst=` (the limit fields live in `[Unit]`, not `[Service]`, and
  a burst limit silently converts "restarts forever" into "gives up by
  breakfast"). `RestartPreventExitStatus=` is the other half: a lane that
  exits because a host CHALLENGED it must not be restarted into the same
  challenge. (2026-10-05, C059 and C501.)

- **A unit edited on the box it does not run on is drift until the manifest
  says otherwise.** T7.54 found `hansard-forward` and `offsite-push` changed
  on node2 and never copied to node1 — and the right answer was not to copy
  them but to record that both node1 copies are DELIBERATELY disabled, kept so
  either box can take the work. Ruling 348 put the units in my hands and the
  judgment came with them: which box a unit is enabled on belongs in
  `ops/systemd/MANIFEST.json` **in the same commit as the unit**, because
  "installed but disabled" and "forgotten" are the same bytes on disk.
  (2026-10-05.)

- **"Regenerable" is a claim about code that exists, not about theory.**
  Classifying the 368 GB dumped offsite nightly: 175 GB genuinely rebuildable
  and safe to drop, and **146 GB with NO rebuild path** — not because the data
  is raw capture, but because nothing in the estate builds an `Emission` from
  stored claims. A view is only regenerable while its regenerator runs; the
  day the pipeline that produced it is retired, the "derived" copy becomes the
  only copy, and a backup policy written from the architecture rather than
  from the code will throw it away. Name the script that rebuilds each class,
  or treat it as irreplaceable. (2026-10-05, `ops/backup_classes.py`.)

- **A unit file is not a line-oriented format — join the backslash
  continuations before you read a directive.** `querynz-embed.service` writes
  its llama-server arguments across six continued lines, so a reader taking one
  line at a time sees `ExecStart=.../llama-server \` and none of the flags. Two
  instruments had the bug: a C317 test looked for `--port` and found nothing,
  and `ops/units_manifest._kv` — which feeds BOTH the published FLEET.md units
  table and the pre-push units gate — would have turned any continued argument
  containing `=` into a phantom directive, and because it used `setdefault` the
  phantom would have SHADOWED the real directive further down the file. Nothing
  in the fleet trips it today (every continuation is `-flag value`), which is
  exactly why it was worth fixing before it cost anything; the proof is that
  FLEET.md came back byte-identical. (2026-10-06, C317/C347.)

- **Measure a card's premise before you build its fix — half of this one was
  already repaired.** C317 recorded two phone pushes from an era pause: a
  deliberate `stop` leaving the unit `failed`, and a restore racing a loading
  server. Measured on the live unit before anything was written, the stop took
  **0.6 s** and recorded `inactive / success` — C074 had fixed it a fortnight
  earlier with `FinalKillSignal=SIGKILL`, and the only work left was a test so
  the next editor cannot remove the line and re-buy the lesson. The other half
  was still live but its window had shrunk from minutes to 0.9 s, which changed
  the fix from urgent to cheap. A card is a claim with a date on it, and the
  estate moves underneath it: re-measure, then build what is left.
  (2026-10-06, C317.)

- **A DROP-IN DIRECTORY IS PART OF A UNIT AND DOES NOT MOVE WITH A SPLIT.**
  C347 split ten ExecStart lines out of `gazette-derive.service` into two new
  units and copied the unit file's own directives faithfully — the
  EnvironmentFile, the two `PAGE_IMAGE_*` variables, the WorkingDirectory, the
  oneshot type. The 04:10 run then ordered perfectly (`gazette-derive`
  04:10:10→04:20:00, `registers-derive` starting at exactly 04:20:00) and
  failed in **one second**: `INCOMING_NEWS_URL is not set (also tried
  V3_BACKLOG_DSN)`. Ruling 130 keeps the DSNs in
  `<unit>.service.d/20-era3-cutover.conf`, and `gazette-derive` needs BOTH
  sources — the fleet env in its own file for the era flags, factory-db.env
  from the drop-in. The unit file looked complete because it WAS complete;
  what was missing sat in a directory beside it, and `systemctl cat` is the
  only view that shows both. **When you move or split a unit, list
  `<name>.service.d/` before you believe you have copied it** — and the gate
  is that every link of a chain must see at least the environment SOURCES of
  the unit that pulls it (`ops/tests/test_registers_derive_chain.py`, checked
  on the sources because the variables live in the credential directory and
  must not be readable from a test). The guard that caught it is the right
  one and worth keeping in mind: the estate carries no default DSN precisely
  because node2's localhost is the read-only standby, so a guessed host would
  have answered instead of failing. (2026-10-06, C347.)

- **A HARD STOP LOOKS IDENTICAL FROM THE BOOT THAT FOLLOWS IT — ASK THE BOOT IT
  ENDED.** No arm in this estate mentioned reboots, so nothing would have
  noticed the next one, and writing the watcher found one nobody had: **node2
  went down hard on 2026-10-02 at 09:24:35** and sat undiscovered for four
  days. Its journal ends mid-inference — two llama-servers printing token
  timings, then nothing — while node1 had been up since 2026-09-18. The new
  boot carries no trace of how the last one ended; a deliberate reboot writes
  `systemd-shutdown` / `Reached target Shutdown` into the boot it is ENDING,
  and a box that loses power writes nothing at all. **One box or both is the
  only question the journals can answer alone**, and it is the one that
  separates the classes: both inside three minutes is site power (2026-09-17,
  28 s apart, already in this file as the power cut); one box with a kernel
  trace is that trace; one box with none is narrowed to its supply or its
  hardware and **not diagnosed further** — an unstable mains that trips only
  the more sensitive box looks the same from here. Validated by making the
  detector agree with the known cases before trusting it: node1's two C380
  drill reboots read CLEAN, the power cut reads UNCLEAN on both boxes.
  (2026-10-06, C058, `ops/reboot_watch.py` + T7.61.)

- **A SHELL METACHARACTER IN AN ARGV LIST WORKS OVER SSH AND FAILS LOCALLY —
  and the failure reads as good news.** `reboot_watch` ran
  `["journalctl", "-b", "-1", "|", "tail", "-60"]`. Over ssh the words are
  joined into a string a remote shell interprets, so node1 answered correctly.
  Run locally the list is exec'd directly, so journalctl received `|` as an
  argument, failed, returned empty — and the survey reported node2 as having NO
  unclean reboots. **The box with the actual defect was the one the instrument
  could not see.** Two rules fall out: never put `| ; & < >` in an argv list
  (`_run` now asserts), and an empty read is UNKNOWN and must be reported as
  such — the survey returns an `unreadable` list and the arm reds on it, because
  "no instrument" and "no faults" are opposite findings that render the same.
  (2026-10-06, C058.)

- **A RECOVERY RUNBOOK THAT POINTS AT A SCRATCHPAD POINTS AT NOTHING.** The
  disk-full postmortem's Phase B said *"run `scratchpad/offload_node1.sh`"* —
  and the script does not exist. The one moment anybody follows a recovery step
  is the moment they are under pressure, and what they would have found is a
  missing file and no account of what it did. Two more holes in the same
  procedure: the base-backup command read `-U <replication_role>` (the role is
  `replicator`, verified on the primary), and **the password was not mentioned
  at all** although `.pgpass` exists on neither box, so the command prompts —
  as `postgres`, under `sudo`, with none of your environment. **A procedure is
  only as good as its least-specified step, and placeholders survive because
  the person who wrote them knew the answer.** Gate: a document that says
  **run** `X` must have X — the imperative is the signal, and it is what makes
  the gate narrow enough to keep. Measured estate-wide: 1,325 script references
  in docs, 87 pointing at files that no longer exist, but nearly all are
  RECORDS correctly describing one-off scripts deleted after use; the
  imperative form had exactly one violation, which was this one.
  (2026-10-06, C279.)

- **EDITING A SHELL SCRIPT WHILE IT IS RUNNING CORRUPTS THE RUNNING INSTANCE —
  AND THE ERROR WILL NOT LOOK LIKE AN EDIT.** `bash` reads a script
  INCREMENTALLY, by byte offset, not into memory. Rewrite the file in place and
  the running shell resumes at an offset that now points into different text.
  2026-10-06: the 11:15 extraction tick ran its fleet for 295 seconds, I edited
  `extract-tick.sh` for C002 while it ran, and at 11:20:41 — the moment bash
  reached the next line — it died with
  `line 65: unexpected EOF while looking for matching \`` and
  `status=2/INVALIDARGUMENT`. The unit failed, T7.35 went red, and
  **`bash -n` passed on the file before the edit AND after it**, because the
  file was never invalid: only the interleaving was. The fleet's own work had
  completed (`fleet done in 295s (rc=0)`), so the failure was pure collateral.
  **The fix is atomic replacement**: write a temp file and `rename()` it over,
  which gives the running shell an untouched inode. Python's
  `Path.write_text()` truncates and rewrites the SAME inode, which is exactly
  the corrupting case — so a script that any timer might be running right now
  is not an ordinary file to edit. Check `systemctl is-active` first, or make
  the write atomic. (2026-10-06, C002.)

- **TWO BUNDLES, TWO PROCESSES: `npm run build` IS NOT THE PI BUILD.** The GUI
  tree has two vite configs. `npm run build` builds `index.html` → `gui/dist`
  (the factory app); the PI product is `npm run build:pi` → **`gui/dist-pi`**,
  from `pi.html`, and `gui/src/pi/HomePage.tsx` is in that second build ONLY. I
  edited the PI home page, ran `npm run build`, and grepped the output for my
  own new strings: absent — and so was every OLD string from the panel, which is
  the tell that the file was not in that build at all. Then the same lesson one
  layer up: the PI product is its own process (`querynz-pi-web` on :8300), so
  restarting the factory API served the old payload with `as_at: null`.
  **Verify at the port the reader uses, and check that a string you just wrote
  is in the artifact you just built.** (2026-10-06, C514.)

- **AN EXIT CODE THAT MEANS THREE THINGS WILL BE SWALLOWED BY THE SHELL ABOVE
  IT.** `registers.donations` exited 1 for `CorrectionsDoNotReconcile` and
  `DoubleCountedDocuments` — which write NOTHING and want a person the same night
  — and also for `SumCheckFailed`, which WROTE the registers and reported 34
  counted reading problems, the ordinary state of that derive. Propagating 1
  would have turned the ordinary state into a nightly red, so the chain above it
  swallowed the code instead: `ec_pageread_disclosures.sh` ended on an `echo`
  (a script's status is its last command's, so it printed `derive exit=1` and
  exited 0) and `ec_disclosures_feed.sh` then ran it unchecked and did
  `exit "$rc"` with the code captured before the page-read had run. The unit
  reported SUCCESS through a failing derive for weeks. **The swallow was not
  laziness, it was the only way to keep the unit usable** — so the fix is the
  vocabulary first (0 clean, 3 wrote-with-problems, 1 nothing-written) and the
  propagation second. Two guards in series are one guard if the first one's
  failure is swallowed; and where a code is swallowed, look for the ambiguity
  that made swallowing it reasonable. (2026-10-06, C516.)

- **A SHELL EXIT DECISION IS TESTED BY EXECUTING IT, NOT BY GREPPING FOR IT.**
  The `case` block that decides this lane's exit status is fenced with
  `# >>> exit decision` markers and `ops/tests/test_disclosure_feed_exit_codes.py`
  extracts it and runs it under `bash` with injected codes. A text assertion on
  a shell script proves the characters are present, never that a systemd unit
  will see the status you intend — which is precisely the gap that hid this
  defect. (2026-10-06, C516.)

- **AN EXIT CODE THAT MEANS "I FOUND SOMETHING" IS NOT A FAILURE, AND THE LEDGER
  CANNOT TELL.** Three of the five units failing on 2026-10-07 had not failed:
  `robots-audit` read all 139 hosts successfully and exits non-zero to force the
  session to address what it found (ruling 288); both hansard lanes correctly
  refused a CHALLENGED read — `200 text/html` where JSON was promised — and
  stopped rather than sweeping with no roster. Only two were defects. So a
  failure ledger counting six units is mostly counting correct behaviour, and an
  estate that reads it weekly learns to discount it. **Every lane that can
  finish with something to say needs the vocabulary before it needs the alarm**:
  found-something, upstream-refused and I-broke are three states, and one code
  cannot carry them. (2026-10-07, C523 · the third sighting after C516 and C520.)

- **SYSTEMD SPLITS `ExecStart` ON WHITESPACE, AND THIS REPO'S PATH HAS A SPACE.**
  `ExecStart=/usr/bin/bash /home/user/Git Repos/QueryNZ_V3/ops/x.sh` execs
  `/home/user/Git` and exits **127**, once a minute, until somebody looks. Every
  other unit in `ops/systemd/` quotes the path; the one I wrote did not, and it
  failed on its first firing. Quote every path in a unit, and when installing a
  unit, FIRE IT ONCE and read its Result rather than trusting the daemon-reload.
  (2026-10-07, C520.)

- **A QUARTERLY TIMER TURNS A NETWORK BLIP INTO A QUARTER-LONG GAP.**
  `querynz-ref-wikidata` hit a `ConnectTimeout` on 2026-10-05; its next firing is
  2027-01-05. Nothing retries, nothing is red about it after the board's window,
  and the reference corpus simply stays three months old. **The rarer a timer,
  the more it needs a retry** — the cost of a missed firing scales with the gap,
  and an idempotent lane has no reason to wait for the calendar.
  (2026-10-07, C525.)

- **`RestartPreventExitStatus` WITH NO TIMER MEANS "NEVER AGAIN".** `hansard-forward`
  carries `Restart=on-failure` AND `RestartPreventExitStatus=3`, and exit 3 is the
  lane correctly refusing to sweep with no member roster when parliament.nz
  challenges it. Both directives are right on their own. Together they stopped the
  daemon on 2026-10-05 13:40 and the journal held **zero** `Starting` entries for
  two days — two sitting days of capture that never happened, with T7.12 reporting
  `FAILED (exit-code)`, which reads like a crash rather than like a lane that has
  given up for good. **A deliberate refusal to continue needs a slower way back,
  not a faster one**: a daily timer, because `systemctl start` on an active
  `Type=simple` unit is a no-op, so the timer only acts when the lane is down.
  Pick that cadence from what it is waiting for — a five-minute retry against a
  government host behind a CAPTCHA is churn, once a day recovers within a day.
  (2026-10-07, C527.)

- **A RED THAT SAYS "THIS LANE IS NOT CAPTURING" IS NOT NOISE — IT IS THE POINT.**
  Having given hansard-forward a daily timer, it now exits 3 daily and the failure
  ledger records it daily, and the instinct from C520 and C523 is to admit the code
  as success. **That instinct is wrong here, and the difference is worth holding:**
  in C520 the WAL mirror was doing its job and reporting failure; in C523
  `robots-audit` had SUCCEEDED and was shouting about a finding. Hansard capture is
  genuinely not happening. A daily red is the true state and must stay until the
  lane is moved off the CAPTCHA'd API (C524). Before silencing a repeated failure,
  ask whether the work is being done — if it is not, the alarm is correct and the
  fix is the work. (2026-10-07, C527.)

- **A PERSISTENT BROWSER PROFILE IS STATE, AND STATE LEFT BY AN UNCLEAN EXIT
  BLOCKS EVERY LATER RUN.** C501 gave the hansard browser a persistent profile so
  Radware clearance survives between polls — right, and it introduced a new way to
  be down. Chromium writes `SingletonLock` as a symlink to `<host>-<pid>` and
  leaves it behind when it dies badly; every later launch then fails with
  `TargetClosedError` and NOTHING clears it. Measured 2026-10-07: three launches
  failed on a lock pointing at a pid gone for minutes, and the profile turned out
  to be broken beyond the lock as well — moving the whole 60 MB aside let the home
  page clear on the first try. **A LIVE OWNER IS NEVER STOMPED**, though: if the
  pid is alive, two Chromiums on one profile is what corrupts it, so that case
  raises rather than "recovers". The pattern generalises past browsers — whenever
  a lane gains durable local state to look less like a stranger, ask what the
  state looks like after a kill -9. (2026-10-07, C528.)

- **A LAZY `CREATE TABLE IF NOT EXISTS` ON A TAKEDOWN PATH HIDES AN INCOMPLETE
  PROVISIONING.** `remediate.py` created `claim_suppressions` and
  `document_quarantine` on first use, beside schema.sql's own copies — belt and
  braces, kept by audit #23 "until that lazy path is retired under a coordinated
  apply-schema". The cost is not the duplication: it is that a graph provisioned
  WITHOUT the ledger still accepts a legal suppression, writing the tombstone into
  a table it invented on the spot, in a transaction the caller commits. **That is
  how `claim_suppressions` came to be absent on the live graph in the first
  place** — nothing could ever report the gap, because every reader created it.
  Retired 2026-10-07 after measuring both tables present in `v3` (0 and 9,589
  rows), and replaced by a refusal that names the consequence and the remedy:
  absence is now a `RuntimeError` saying the suppression would be UNAUDITABLE and
  to run apply-schema. Proven by renaming the table inside a rolled-back
  transaction and watching it refuse. **Where a path is allowed to create what it
  audits into, it cannot audit.** (2026-10-07, C080.)

- **`MemoryMax` KILLS AND `MemoryHigh` RECLAIMS — WHICH ONE A JOB WANTS DEPENDS ON
  WHETHER ITS FOOTPRINT IS RECLAIMABLE, AND "BOUND IT" IS NOT THE SAME
  INSTRUCTION AS "CAP IT".** C435 was raised on one unbounded nightly job sharing
  node1 with the canonical primary: `querynz-embed-index`, peak **33.2 GiB** on a
  62.3 GB box, both limits infinity, OOM-killed on 2026-09-23 at 97.6% of an
  hour's atomic pass. Writing the gate for it found **four** units over 8 GB and
  three on node2 — and then nearly broke one of them. `querynz-agent-llm` was not
  unbounded: a tracked drop-in from B2 (2026-08-22, after an OOM kill at 05:11
  that morning) sets `MemoryHigh=16G` and says in writing that `MemoryMax` is
  *"deliberately unset"*. It is right. A model lane's footprint is largely
  reclaimable — the host prompt cache and the weight file's page cache — so a hard
  cap kills a serving lane mid-request to free memory the kernel would have
  reclaimed on its own. A batch oneshot is the opposite: it should fail loudly at
  a cap rather than reclaim against the primary for an hour.
  **Two traps underneath that, both cheap and both mine on the day.** First, a
  DROP-IN OWNS THE DIRECTIVE: the `MemoryHigh=20G` added to the `.service` file was
  dead config that systemd ignored while reading 16G from
  `querynz-agent-llm.service.d/memory.conf` — a line that looks effective and is
  not (see #f74eff for the other half of "read what systemd reads"). Second, a cap
  sized once against today's peak becomes a NIGHTLY KILL as the corpus grows,
  because `init_index(max_elements=total)` scales with it — and a oneshot dying at
  97% is the failure nobody notices. So the headroom is watched (T7.65) against the
  ceiling that kills, and a peak sitting ON a soft ceiling is that ceiling WORKING,
  never a finding.
  *Paid for by:* 2026-09-23 (the kill) and 2026-10-07 (C435), where the gate found
  three more and the near-miss was reversing a decision somebody had already made
  correctly and written down.

- **QUIETENING AN ALARM MOVES A SIGNAL, AND THE INSTRUMENT THAT KEEPS IT MUST
  WIDEN IN THE SAME COMMIT.** C523's fix was obviously right: `robots-audit` read
  all 139 hosts, found a changed robots.txt and exited non-zero, so the OnFailure
  ledger filed correct behaviour as breakage. Giving it an exit vocabulary (0 ok ·
  2 changed · 3 stricter · 4 unread · 1 broke) and `SuccessExitStatus=2 3 4` stops
  that. But the unit's exit code WAS the alarm for a changed-but-not-stricter
  host: T7.45 only reddened on a tightening, so the same commit that quietened the
  unit would have turned "we are aware of all changes" — Arthur 2026-09-18, *"for
  changes I need to be aware of all changes as this is core to the health of the
  corpus"* — into silence. Before you downgrade a signal, name what currently
  carries it and check the thing you are leaving it to actually carries it; the
  noisy channel is often load-bearing precisely because it is noisy. The tell is
  that the fix feels like pure subtraction.
  **And the host that could not be read at all was counted nowhere**: an exception
  out of `check` was `continue`d with a print, so a Monday on which thirty hosts
  timed out produced a clean report over the hundred that answered. Permission for
  an unread host is UNKNOWN, which is a refusal (ruling 78), so it is now a state
  of its own in both the report and the vocabulary.
  *Paid for by:* 2026-10-08 (C523), caught while writing the arm's test rather
  than after a silent Monday.

- **A SECRET REACHES A TRANSCRIPT AT THE MOMENT SOMEBODY CONFIRMS IT, NOT AT THE MOMENT
  SOMEBODY SETS IT.** The Cloudflare token was pasted into a transcript at the first
  publish. It was rolled and narrowed to a handful of permissions, and **the replacement
  reached a transcript too** — so the exposure was unchanged and only the blast radius
  shrank. The path for setting one without chat already existed and was written down in
  the runsheet (create the file mode 600 in the credential directory, then paste at the
  box); what did NOT exist was a way to CONFIRM the new value afterwards, so the
  confirming was done by showing it to the agent, which is the one thing the path exists
  to prevent. **Pair every write-it-at-the-box procedure with a verifier that prints
  verdicts only** — not the value, not a prefix, not a length: four characters of a
  secret are four published characters, and a length narrows a brute force. Then
  "rotated" is the whole message.
  **And the verifier must prove the NARROWING, not just the grants**, or it certifies a
  credential that works and says nothing about what else it can reach. The sharpest probe
  turned out to be positive and scoped: not *"can it see zones"* but *"does it see exactly
  `followthemoney.nz` and no other"* — which is also how the record was found to be
  incomplete, because that fourth grant had never been written down.
  **The verifier cried wolf twice first.** `/user/tokens/verify` answers `401 Invalid API
  Token` for an ACCOUNT-owned token with no user scope, and `/accounts/{id}/pages/projects`
  answers 403 because Cloudflare folded Pages into Workers and `wrangler` deploys through
  `/workers/scripts`. Both false alarms were about a credential that works perfectly. A
  checker that reports a working secret as broken gets switched off, so both wrong
  endpoints are recorded in the file beside the right ones.
  *Paid for by:* 2026-10-08 (C470), six days after the roll that did not close it.

- **A FIX THIRTY LINES AWAY IN A MODULE THE OTHER LANE CANNOT IMPORT IS A FIX THAT WILL
  BE PAID FOR TWICE.** C528 gave the hansard browser a stale-lock clearance on
  2026-10-07, measured and documented, with a closing line saying *"the pattern
  generalises past browsers"*. Nine days later `querynz-ec-results` — the only OTHER lane
  in the estate with a DURABLE browser profile — had failed **35 consecutive firings** on
  exactly that lock, because the helper lived inside `ingestion/hansard/scraper.py` and
  an ops script cannot import a hansard scraper. The generalisation was WRITTEN DOWN and
  not ACTED ON, which is the expensive half: when a fix's own note says it generalises,
  the next step is the census, not the sentence. Four modules launch a persistent
  context; two build a fresh profile per run and cannot inherit a lock, so the hazard was
  exactly two lanes wide and one of them was already down.
  **Where a shared fix goes matters as much as what it does.** It is now a leaf
  (`ingestion/browser_profile.py`, importing `os` and `pathlib` and nothing else), for
  the same reason `estate_dsn` sits at the bottom: no package below the others means a
  thing both layers need belongs under both, never inside one of them.
  **AND THE SECOND HALF OF THE ORIGINAL FINDING WAS THE LOAD-BEARING ONE.** C528 recorded
  that the lock was not the whole story — *"the profile turned out to be broken beyond the
  lock as well — moving the whole 60 MB aside let the home page clear on the first try"*.
  Reading only its headline gave a fix that cleared the lock and still failed in 632 ms.
  The remedy is retire-and-retry-ONCE: move the profile aside (229 MB here), rebuild,
  try again, and let a second failure raise, because a retry loop would thrash a quarter
  of a gigabyte against a host that is merely refusing us. Proven by breaking the profile
  deliberately and watching the unit report the retirement and then read two pages.
  *Paid for by:* 2026-10-08 (C537), 35 firings after the fix existed.

- **A SLICE'S CLOCK CANNOT BE THE TABLE THAT ONLY RECORDS SUCCESSES — AND THE
  ORDER IS THE COVERAGE GUARANTEE, NOT A NICETY.** The incorporated-society
  officer register had no clock at all: 130,475 rows over 22,766 societies, every
  one `imported_at` 2026-08-26 — one hand-run sweep, 42 days stale, no unit, no
  timer, no watcher — and it is what the PI product reads for the Green,
  Labour-vehicle, Te Pāti Māori and TOP party boards. On the first slice after
  the clock was built, **TOP had gone from 15 officers to 16.** Officers change;
  nothing was looking.
  **TWO THINGS WOULD HAVE BROKEN THE OBVIOUS NIGHTLY SLICE.** The sweep selected
  `ORDER BY entity_name`, which is fine for one 6.3-hour pass and useless as a
  slice: `--limit N` re-reads the same alphabetically-first N every night and
  never reaches the end of the alphabet. (The identical defect was found in
  `source_policy.weekly` the same day, #f08599 — two lanes, one shape, neither
  author thinking about `--limit` as a cursor.) And **the clock cannot be the
  officer table**, because officers are written only when some were PARSED: an
  empty answer is deliberately a no-op so a transient 200 cannot wipe a good load.
  So a society that answers with no officers never gets an `imported_at`, and a
  stalest-first order over that column parks it at the head of the queue FOREVER
  — the slice never advances past the officer-less, which are exactly the rows
  that would stall it. An ASK is a fact separately from what it found, and it
  needs its own ledger. **A failed ask counts too**, or a permanently-failing id
  pins itself to the front every night.
  **ASK THE REGISTER FOR WHAT ITS ROWS CAN CARRY.** The population looked like
  26,901 "registered societies". Measured by `entity_type`: 22,787 Incorporated
  Societies of which **22,766 have officers (99.9%)**, and 4,114 NZ/Overseas
  Limited Partnerships of which **0 do** — because a limited partnership has no
  officers. A 150-sample had already found none among "the other 4,135" and been
  read as a statistical result; the population was 99.5% partnerships and the
  answer was structural. 4,114 requests a cycle saved by asking a type question
  instead of trusting a sample.
  **AND THE RED CONDITIONS BELONG TO THE CLOCK, NOT THE BACKLOG.** On the night a
  sweep is installed every row is unasked and a seven-night cycle drains it. An
  arm red for those seven nights teaches a reader to ignore it, which is F7's
  lesson about a unit that is always red. So the arm goes red on what the clock
  is responsible for — the sweep has stopped, the priority pin is not working, or
  the cycle has had time to finish and did not — and REPORTS the draining backlog
  every run with a countdown. The watcher was then proven the only way a watcher
  can be: the timer was disabled, T7.12 said
  `society-officers.timer: is-enabled=disabled (intent enabled)`, and re-enabling
  cleared it.
  **HALF THE CARD WAS ALREADY ANSWERED, IN A DOC, BY ARTHUR.** It asked for "a
  cadence for the bulk import and for the officer sweep". The bulk feed has one:
  `nzbn_canonical/docs/bulk-import.md` records it as monthly and MANUAL because
  the Companies Office publishes via Box.com, the timer is deliberately not
  installed, a missed month fully recovers, and his 2026-09-19 word is that *"it
  is his, it is scheduled, and it is not a card; nothing should re-raise it as
  outstanding"*. Reading the runbook before planning the work removed half the
  card and told the new arm which number to print without judging (#BEFORE
  PLANNING WORK ON A BLOCKED SOURCE, READ THE RUNSHEET).
  *Paid for by:* 2026-10-08 (C531), 42 days of an unwatched party-board register
  and a TOP board that had moved while nobody asked.

- **A KILLED RUN'S PEAK IS WHERE IT GOT TO, NOT WHERE IT WAS GOING — AND A CAP
  ABOVE WHAT THE BOX CAN SPARE IS A COMMENT, NOT A CONTROL.** C435 bounded node1's
  one unbounded job from the peak of the last clean pass, 33.2 GiB. systemd had
  recorded **21 dated passes**: 30.3–38.4 GiB normally and **57.1 GiB on 09-21**,
  on a 62.3 GiB box. Two things in that series are traps.
  **THE KILL NIGHTS READ LOWEST.** The three global OOMs (09-23, 09-27, 09-28)
  record 30.3, 30.3 and 31.0 GiB — the smallest numbers in the whole series —
  because each died 60–75 minutes into an atomic pass, so `MemoryPeak` captured
  the climb and not the summit. A ceiling derived from a set that mixes completed
  and killed runs is therefore wrong in the comfortable direction, and the nights
  that look safest are the nights the box died.
  **AND THE CAP COULD NOT BITE.** `MemoryMax=44G` against `MemAvailable=40.7 GiB`
  means the box runs dry before the cgroup does: the kernel's global OOM picks a
  victim by score, which is why all three kills are `global_oom`,
  `CONSTRAINT_NONE` rather than a cgroup kill. `OOMScoreAdjust=200` chose this
  job every time and is the only reason the canonical primary survived. The test
  for a killing cap is not "is it above the measured peak" but **"is it below
  what the box can spare"** — otherwise the thing that fails is the box.
  **A GATE THAT READS A RESET COUNTER SEES ONE SAMPLE FOREVER.** `MemoryPeak` is
  reset per invocation, so T7.65 judged the headroom of whichever run happened to
  be most recent and never saw the 37.7 GiB pass that was over its own 85% line.
  systemd prints the peak in its `Consumed …` line at the end of every run, so
  the history was always there — the counter was a witness nobody called. Reading
  it needs a WINDOW, though: history is immutable, so an arm comparing a current
  ceiling to an all-time peak goes red for ever the moment a ceiling is lowered.
  Fourteen days is long enough to show a trend and short enough that a config
  change ages out.
  **AND WHEN THE ARM THEN SAYS YOUR OWN NUMBER IS WRONG, THAT IS THE ANSWER.**
  With the history wired in, T7.65 reported the new 39G cap at 97% of the worst
  pass. 85% headroom would need 44.4 GiB and the box can spare 40.7: there is no
  value that is both reachable and roomy, which is the measurement saying *the
  index no longer fits this box* — exactly the signal C435 predicted a tripped
  ceiling would be. The cap stays at the largest reachable value so the cgroup
  rather than the kernel chooses, and the red keeps a verdict pointing at the
  footprint. A verdict per red, never fewer reds.
  **MEASURE THE SUSPECT BEFORE NAMING IT.** The card observed that each kill
  landed 2–5 minutes after `wal-archive-prune` and implied contention. The prune
  peaks at **32.4 MiB**. It is innocent, the timing was coincidence, and the
  squeeze is this one job against postgres — which also means C435 bounded the
  victim rather than the pressure: 20 of node1's units are still
  `MemoryMax=infinity` and most report no peak at all.
  *Paid for by:* 2026-10-08 (C533), three global OOM kills on the box that holds
  the canonical primary, and a first re-measurement of mine that took a `tail` of
  the journal and reported 11 passes topping at 37.7 when there were 21 topping
  at 57.1.

- **A PRE-PUSH HOOK THAT TAKES MINUTES CAN IDLE OUT THE PUSH IT IS GUARDING, AND THE
  ERROR NAMES THE TRANSPORT RATHER THAN THE CAUSE.** Two pushes to GitHub failed on
  2026-10-09 with `client_loop: send disconnect: Broken pipe` and
  `send-pack: unexpected disconnect while reading sideband packet`, while the MIRROR
  push succeeded — so the estate had the commit and GitHub was one behind, the
  inverse of the stale-mirror trap. Everything about the diagnosis pointed away from
  the cause: the push was **1 commit, 18 objects, 345 insertions** (not a size
  limit), `ssh -T git@github.com` authenticated cleanly (not credentials or
  reachability), and earlier pushes the same session over the same transport had
  worked.
  **What changed was the HOOK, not the network.** The pre-push gate runs the doc
  drift and invariant suites, and I had spent the day adding arms and tests to them;
  it now holds the SSH connection open for ~2.5 minutes before a byte of pack moves,
  which is long enough for the path to drop an idle connection.
  `GIT_SSH_COMMAND="ssh -o ServerAliveInterval=15 -o ServerAliveCountMax=8"` pushed
  first time.
  **The general shape: when a transport error appears in work that used to succeed,
  ask what got SLOWER, not what got bigger.** And a verification that reads both
  remotes is what caught it — the first report of "pushed" was true of the mirror and
  false of origin, because the task was killed between the two.
  *Paid for by:* 2026-10-09, after C411. The keepalive belongs in the repo's git
  config rather than in a one-off environment variable, which is the owed follow-up.

- **`--query-port` IS A FALSE NEGATIVE FOR A RICH-RULED PORT, AND A GREP OVER A
  TOOL'S OUTPUT CAN DISCARD THE ANSWER.** Measuring C085's exposure I built a case
  for a real security finding and it was wrong twice over. `:8100` and `:8300` bind
  `0.0.0.0`, which looks alarming; `firewall-cmd --zone=querynz-lan --list-all |
  grep -E "target|interfaces|services|ports|rich"` showed `ports:` empty and
  `rich rules:` with nothing after it; and
  `firewall-cmd --zone=querynz-lan --query-port=8100/tcp` answered **`no`** for every
  zone. An off-box probe then got **HTTP 200** from node1, so I had "firewalld
  running, config closed, port open" — which would have been a genuine finding if
  either measurement had been sound.
  **Both were mine.** The permission is a RICH RULE, and `--query-port` reports only
  port ENTRIES, so it answers "no" about a port that is explicitly allowed. And my
  grep filtered out the rich-rule lines themselves, because `--list-all` prints them
  on following lines beginning `rule family="ipv4" …` — which contains neither
  "rich" nor any other word in my pattern. The evidence was in the output I threw
  away. `--list-rich-rules` shows seven rules admitting 8100, 8300, 8090, 8020,
  8002, 8001 and 5432 **only from `10.0.0.0/24`**, and the default zone's port list
  is empty, so ruling 173's narrowing (`ops/production/firewalld-lan.sh`) is
  installed and in force.
  **Two rules out of it.** When a tool has a query verb AND a list verb, the query
  verb usually answers about one KIND of rule — ask the list. And a grep written to
  keep a summary readable will drop a multi-line answer, so when the output and the
  behaviour disagree, re-read the output UNFILTERED before believing the
  disagreement.
  *Paid for by:* 2026-10-09 (C085). The off-box probe was right and necessary — a
  curl from the box itself to its own addresses goes via `lo` and proves nothing
  about a zone, which was a third thing I had to correct on the way.

- **THE SURFACE WITH THE LIMITER WAS NOT THE SURFACE THAT NEEDED ONE — AND MOVING
  THE BUCKET IS CHEAPER THAN COPYING IT.** C085's measurement (2026-10-09) found the
  estate's exposure LAN-scoped and the PRODUCT on `:8300` already running a token
  bucket with 429 + `Retry-After`, then said the remaining gap exactly:
  *"so the gap is `:8100` alone"*. The conductor API — the factory's own app,
  reachable from loopback, the LAN twin and the tailnet — had no limiter at all, so
  one loop on one tailnet device was a GPU and a database with no brake. **The
  hardening was measured on the surface that had it and the conclusion drawn about
  the estate.**
  **WHERE IT WENT IS THE WHOLE DESIGN.** `pi` already imports
  `query.influence.base` and `v3.api` already mounts `query`'s router, so `query`
  is the one package BOTH surfaces reach — a new editable package for a hundred
  lines of arithmetic is a deployment step on two boxes, and a second copy is what
  this estate had just paid for twice in one night (a POSIX restatement that had
  drifted by the arm worth $60,000, #8a634c; a finder's glob stated in three
  modules, #3603e8). **Check which package the two callers already share before
  inventing a home for a shared rule.**
  **THREE THINGS THE MOVE FIXED THAT COPYING WOULD HAVE DUPLICATED.** The knobs are
  read at CALL time, not at import — the old module-level constants are why PI's own
  fixture has to `importlib.reload` after setting the environment, which works only
  because the fixture remembers and a later surface would not. A bucket key is
  namespaced by its surface (`pi:` / `v3:`), because one process has served the
  factory GUI and the product together for a year and an IP-only key makes one
  surface's budget the other's. And a non-positive rate is clamped to 1 rather than
  read as "no limit": zero divides by zero computing the wait and a negative hands
  out tokens for ever, and both read as "the limiter is off" to whoever typed them.
  **The health probe keeps its own budget** — a probe the limiter starves takes the
  box down in the monitoring rather than in the serving.
  *Paid for by:* 2026-10-10 (C085). Verified on the running unit, not in a test
  client: 60 requests to `:8100` → **40 served, 20 refused with `Retry-After: 1`**,
  `/api/health` still 200 while limited, and normal service after the refill.

- **AN UNQUALIFIED `ALTER … IF EXISTS` OUTSIDE THE SEARCH PATH IS A SILENT
  NO-OP, AND THE `CREATE` BESIDE IT THEN MAKES THE DUPLICATE THE RENAME EXISTED
  TO PREVENT.** Moving `registers.candidates_announced`'s DDL into the service
  that owns it meant renaming two indexes into the package's `ix_register_*`
  convention — the prefix a guard uses to tell which objects the service owns.
  Written as `ALTER INDEX IF EXISTS ix_cand_announced_rev RENAME TO
  ix_register_cand_announced_rev`, the bare name resolved against a
  `search_path` with no `registers` in it, found nothing, and `IF EXISTS` turned
  the miss into a NOTICE. The `CREATE INDEX IF NOT EXISTS` on the line below
  names its table in full, so it succeeded. **Four indexes where there should be
  two, and not one error** — the rename and the create are only idempotent
  TOGETHER if they resolve the same name, and one of them did not. Two further
  teeth: once the target name exists a plain rename ERRORS, so the corrected
  DDL has to be conditional (`to_regclass` on both names) or it fails on the
  very database it was meant to repair; and the repair itself needs an index
  deleted on a live register, which is not mine to run — so the cost of a
  missing schema qualifier is a row on Arthur's runsheet.
  *Paid for by:* 2026-10-10 (C151). Same family as the `%` in a SQL comment and
  the `--` that swallows an appended line: the statement ran, exited clean, and
  did nothing. `IF EXISTS` is a promise not to fail, never a promise to act.

- **`systemctl show -p A -p B -p C --value` PRINTS SYSTEMD'S ORDER, NOT YOURS —
  AND A POSITIONAL READ OF IT MISLABELLED 1,733 LEDGER ROWS FOR FIVE WEEKS.**
  The estate's one failure-delivery path, `ops/production/unit-failed.sh`, did:

      read -r RESULT STATUS INVOC < <(systemctl --user show "$UNIT" \
          -p Result -p ExecMainStatus -p InvocationID --value)

  Measured on this box, systemd prints those three as **InvocationID, Result,
  ExecMainStatus** — its own internal order. So since 2026-09-04 every row in
  `var/audits/unit_failures.jsonl` has carried `result` = a hex invocation id,
  `status` = the result word, and the NUMERIC EXIT CODE under `invocation`. The
  ntfy alert, where configured, said *"exit exit-code"* and named an invocation
  id as the result, and nobody noticed because every field was populated with
  something plausible-looking.
  **The lost field was the one that mattered most.** `hansard/forward.py` sets
  `CHALLENGED_EXIT = 3` with the comment *"systemd reads this one"*, and its
  unit carries `RestartPreventExitStatus=3`, precisely so a lane can say *the
  SOURCE refused me, I am not broken* — and no consumer could reach it.
  *Paid for by:* 2026-10-10 (T7.35, found while working the board's reds).
  Parse `KEY=value` — one call, and order cannot matter. The history is a
  RECORD and was not rewritten: the board normalises on read, and detects the
  old shape BY SHAPE (a non-numeric `status` beside a numeric `invocation`),
  never by date, because a date cut-off silently mislabels rows written by a
  box that has not pulled the fix. Same family as the `dict_row` positional
  unpacking that made a guard report success while doing nothing: **when a
  tool's output order is not part of its contract, reading it positionally is a
  guess that looks like a value.**

- **A CHALLENGED READ IS A FAILED READ — AND THE BOARD MUST BE ABLE TO SEE
  WHOSE FAILURE IT IS.** `hansard-forward` had failed **292 times since
  2026-09-14**, reported by T7.12 and T7.35 exactly as if our code were broken.
  Measured: hansard.parliament.nz sits behind Radware, which serves its
  **captcha page to the `/api/` endpoints** — to a browser NAVIGATION as well
  as to a `page.request` call, body text *"your activity and behavior on this
  site made us think that you are a bot"* — after the home page itself cleared.
  So the lane is CORRECT: it raises `Challenged`, exits 3, and its unit
  declines to retry, because retrying is 288 requests a day against a site
  already refusing us and it hardens the block. There is no permitted
  workaround: solving a captcha is barred anywhere, for any source, including a
  governmental one (ruling 242 lifts ROBOTS, never a challenge).
  Two things follow. **The convention has to be complete:** `forward` exited 3
  and its sibling `reprocess` let the exception propagate and exited 1 — 21
  refusals reading as crashes — so it now imports the same constant rather than
  restating it, and both units carry `RestartPreventExitStatus=3`. **And the
  board has to report it as a refusal**, named and counted, still red, because a
  month of un-collected Hansard is a real outage whose owner is at the other
  end. A red that cannot say whose failure it is gets read as noise.
  *Paid for by:* 2026-10-10. **And a caution measured the same night:** two
  probes minutes apart and the home page stopped clearing on the second. A
  refused source is not a thing to keep testing by hand — record the
  measurement so the next session spends no requests re-learning it.

- **A FAILOVER THAT NEEDS A HUMAN TO TYPE IS NOT A FAILOVER — IT IS A RUNBOOK,
  AND A RUNBOOK IS ONLY AS GOOD AS ITS LAST REHEARSAL.** 2026-10-17: node1
  died after a RAM install (no POST, no screen, the link at 10 Mb/s). The VIP
  model itself HELD — every writer resolves `db-primary`, nothing was edited —
  but everything around it was manual, and five things the runbook assumed
  were not true. Each is a rule:
  1. **A runbook prerequisite that no gate holds is not done.** "Install the VIP
     units on node2 before run 2" sat in prose for six weeks; run 2 never ran;
     the unit was absent on the night. Every "one-time" prerequisite is a board
     check (the file exists on both boxes, the marker is where it should be),
     red until it is true.
  2. **The standby must already carry every access line the primary has — for
     every writer's SOURCE address as seen from the standby.** node2's
     `pg_hba.conf` had no entry for node2 reaching ITSELF through the VIP
     (`querynz_serving` → nzbn_canonical from 10.0.0.2 refused). The fix is one
     line, `host all all samehost scram-sha-256`; the rule is that `pg_hba` is
     generated from one source for both boxes and diffed nightly, never two
     hand-kept files.
  3. **Promotion has to be possible without a password.** The NOPASSWD set
     allowed `systemctl`, `ip addr`, the marker and `pg_ctl` — but `pg_ctl`
     refuses to run as root and nothing allowed the postgres user, so the one
     step that matters needed Arthur. A root-owned `querynz-promote.service`
     that runs `pg_ctl promote` as postgres, startable without a password, is
     the smallest fix; the real one is track A's voter.
  4. **A box that boots believing it is primary will claim the VIP.** The
     `not-primary` marker is static per box: node1 will return with no marker
     and its VIP unit enabled, and nothing on it asks the wire first. The VIP
     unit's `ExecStartPre` must `arping` the VIP and refuse if anything
     answers; and postgres on a box whose marker is absent must not start as a
     primary while the VIP is answered elsewhere. Fencing by a human after the
     fact is the wrong direction.
  5. **"Never a box IP" was ruled for the database and nowhere else.** Four
     timers and the git mirror name `10.0.0.1` outright (`wal-archive-mirror`,
     `querynz-residue-mirror`, `querynz-verdict-sync`, `querynz-deploy-node1`)
     and had to be stopped by hand. Anything that names the other box names a
     ROLE (`db-standby`, `db-primary`) or carries its own "is the peer up"
     check and a clean skip.
  *Paid for by:* 2026-10-17 22:00–22:45, about 45 minutes of Arthur typing
  lines he should never have had to, on a Saturday night.

- **A WATCHER THAT PINGS THE FLOATING ADDRESS SEES ITSELF.** The moment the
  VIP landed on node2, my watcher reported "node1 UP at 22:21:14": it was
  pinging 10.0.0.10, now a local address. Watch the peer's OWN address
  (10.0.0.1); the VIP tells you who holds the role, never whether the other
  box is alive. *Paid for by:* 2026-10-17, one false alarm mid-failover.

- **THE LINK SPEED IS A DIAGNOSTIC: 10 Mb/s ON A 10G PAIR MEANS THE PEER IS ON
  STANDBY POWER AND HAS NOT BOOTED.** A NIC links at 10/100 from auxiliary
  power before POST (Wake-on-LAN state) and negotiates up only when the OS
  driver loads. `ethtool enp13s0 | grep Speed` says whether the other box
  booted before anyone looks for a screen. *Measured:* 2026-10-17 21:48–22:45,
  10 Mb/s the whole time node1 was dark.

- **A BOX WITH NO WORKING CONSOLE CANNOT BE RECOVERED FROM A FIRMWARE PROMPT,
  AND A RAM CHANGE IS THE COMMONEST WAY TO REACH ONE.** node1's display
  output has never worked; after the RAM install it may have sat at "memory
  configuration changed — press F1" with nobody able to see it. Two
  requirements for any box that holds a role: a way to see firmware (onboard
  video, serial, or a management interface), and firmware set to continue
  without a keypress after a hardware change. *Paid for by:* 2026-10-17, the
  whole night.

- **DO NOT TAKE THE STANDBY DOWN AND THEN TOUCH THE PRIMARY.** Both boxes got
  RAM in one sitting: node2 (the standby) was shut at 15:20, node1 was opened
  while it was off, and node1 did not return — so the only copy of node1's
  last hours was node1. The standby had been consistent to 15:17; the loss was
  bounded only because the lanes were off. One box at a time; the standby
  streams again, measured (`pg_stat_replication`, lag 0), before the primary is
  touched. *Paid for by:* 2026-10-17 — RPO was the shutdown window instead of
  zero.
