# support/takeover: the database role moves between the boxes

Ruling 145 (6 November 2026): continuous uptime. The old estate's tested drill (old repository
`docs/runbooks/FAILOVER_DRILL.md`: 24 August, back in 2 minutes 37 seconds, nothing lost) made into
four root jobs, with the lessons of 17 October (`docs/plan/track-a.md`) built in. Takeover is still
started by a person or a session: with two boxes neither can tell "the other died" from "the link
dropped", and the voter that would make it automatic is track A's third machine.

## The jobs (system units, installed by `system/install.sh`, run as root)

| Job | What it does | Refuses when |
| --- | --- | --- |
| `qv4-release` | marks this box not-primary, takes 10.0.0.10 off it, checkpoints and stops a primary cleanly (so the rejoin needs no rewind) | the address will not come off |
| `qv4-takeover` | waits up to 30 s for the standby to replay what it received, promotes, reserves the other box's slot `<peer>_standby` AT promotion, removes the marker, starts `querynz-vip`, announces the address (gratuitous ARP) | the database is down or not a standby; anything on the wire answers for 10.0.0.10 |
| `qv4-rejoin` | marks not-primary, stops the database, `pg_rewind` from 10.0.0.10, writes `primary_conninfo` (host 10.0.0.10) and `primary_slot_name = '<me>_standby'` itself (a "no rewind required" writes none), `standby.signal`, starts and waits for streaming | this box holds the address; nothing answers for it; the rewind refuses (the fallback, a full copy, is never automatic) |
| `qv4-role-guard` | at boot, before the database and the address: a box with no marker whose address answers elsewhere marks itself not-primary and gets `standby.signal`, so it never comes up as a second primary | (never refuses; with no carrier on the link it keeps its role, as the 15 September cold-start drill needs) |

The estate's account may start the first three with no password (`50-qv4-takeover.rules`, polkit:
start only, those three only), so no privileged line is typed during a takeover (track A lesson 1).
Every job writes one line per step to `/var/log/qv4-takeover.log` and the journal.

## A switchover (planned), node2 to node1

    node2:  systemctl start qv4-release
    node1:  systemctl start qv4-takeover
    node2:  systemctl start qv4-rejoin

A failover (node2 gone) is the second line alone, and the third once node2 is back; the role
guard keeps a returning node2 from claiming the address meanwhile.

## What it does not do yet

- **No automatic trigger.** Needs the third machine (track A).
- **The stores and the work folder are served from node2 over NFS.** With node2 gone, node1 holds the
  database but not the documents; the two-way copy is its own piece of work.
- **The standing services** (board, report, scan, site preview, MCP tunnel) run on node2 only; a
  survivor does not start them yet.
- **The old jobs that name a box** (`wal-archive-mirror`, `querynz-residue-mirror`,
  `querynz-deploy-node1`) are not changed; none is on the takeover path.

## Access lines

`install.sh` puts the same five lines in both boxes' `pg_hba.conf` (replication and `pg_rewind`'s
`postgres` login from either box, and `samehost`, which the 17 October standby lacked), and on the
primary grants `replicator` the four file functions `pg_rewind` reads through.

## Tests

`tests/test_takeover_scripts.py` runs every script against stand-in commands; each refusal is
checked by what must not happen. Nine mutations (each guard removed in turn) all fail the suite.
