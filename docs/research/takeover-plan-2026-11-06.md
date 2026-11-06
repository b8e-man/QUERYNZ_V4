# Takeover and two-box work: the plan, aligned with the v4 build (6 November 2026)

Integrator-9d788fb, for Arthur. Sources: `docs/plan/step-2.md`, `docs/plan/track-a.md`, `docs/plan/step-0.md`,
rulings 31 and 145, `docs/DESIGN.md`, the cards named below, and the old repository
(`docs/runbooks/FAILOVER_DRILL.md`, `docs/records/DECISIONS.md` rulings 130 and 365,
`docs/doctrine/lessons/1-ops-the-estate.md` lines 1158-1227, `V4_ideation/DISCUSSION_RECORD.md` line 184).

## What the old estate had, and what the v4 build adds

**Worked and tested, by hand:**
- **Failover:** the 24 August drill (2 min 37 s, nothing lost) and the real one on 17 October, about
  45 minutes with Arthur typing.
- **The floating address 10.0.0.10:** every writer follows it, so no writer was edited on 17 October.
- **The no-touch reboot drill** (15 September, node1 only).
- **Fencing by the `not-primary` marker.**
- **Board arms:**
  - T7.28: replication lag;
  - T7.29: no box address in a unit;
  - T7.30: one holder of the floating address.

**Never built:**
- automatic takeover;
- a promote that needs no password;
- an `arping` check before the address is claimed;
- any watcher of the other box;
- a third machine. Arthur parked it on 11 October. The recorded fallback: "takeover stays a single command a person runs, with everything else automatic".
- the fail-back after 17 October;
- a planned move of the address between the boxes;
- node1 streaming from a node2 primary (done today for the first time).

The v4 build ports this and adds two things:
1. **Step 2, the scheduler's two-box half:** either box takes over the other's work, in either direction.
2. **Track A:** the five rules of 17 October, then automatic takeover once the voter exists.

## Where things stand against the plan

| Plan item | State |
| --- | --- |
| 2.2 a worker on each box | Both run (node1 since 6 Nov, reading only) |
| 2.8 leases; a stopped worker's job finished by the other | Built; never proven across boxes |
| Helpers (ruling 145, pooled capability) | Built and live: one courts row read by both boxes |
| 2.10 alarm from the other box | Built (`queue.silent_workers`), but the alarm goes through the database, so it is silent when the box that dies holds the primary |
| 2.11 one installer, both boxes | Release copy on both; credentials not copied box to box; old folder shared read only (Arthur's script pending) |
| 2.12 the clock is the queue's | Built; the "survivor runs a timetabled job" proof never run on two boxes |
| 2.13 standing services are jobs | The `wanted` count exists; the real standing services (board, report, scan, site preview, MCP tunnel, Radiance) are still per-box units on node2, so a survivor starts none of them |
| Track A, rule 1: promote with no password | Built in `support/takeover` (root job, polkit); not installed |
| Rule 2: ask the wire before claiming the address | In `qv4-takeover` only; the address unit itself (`querynz-vip`, old) does not ask |
| Rule 3: a returning box never a second primary, no static marker deciding | `qv4-role-guard` asks the wire at boot, but still writes and reads the marker |
| Rule 4: access rules from one source, diffed nightly | Not met: the install appends lines |
| Rule 5: no job names the other box | The new jobs meet it. Of the four old ones: `wal-archive-mirror` still runs, copying node1's dead archive, and should stop; `querynz-residue-mirror` is superseded by the read-only mount; `querynz-deploy-node1` is still useful; `querynz-verdict-sync` is disabled |
| Every rule a board check | None yet; T7.28/29/30 not ported |
| Rehearse on a scratch pair, then drill live both ways on Arthur's word | Not started (I proposed a live drill first: withdrawn) |
| The primary normally on node1 | node2 is primary; the fail-back is owed |
| The scheduler reserves memory for the primary role | Not built |
| The survivor's set within 62 GB | Not met: Radiance alone holds 85 GB on each box (n-gram table 47.7 GiB in RAM, host pool 26 GiB) |
| Two-way copy of the files | Not started; node2 serves the stores and the work folder over NFS |
| Watchers ping a box's own address | Not built |
| Third machine (step 0) | Arthur's; not set up |
| Cable card: ignore-carrier and static hostname on both boxes, a board check | node2 done by hand 21 Oct; node1 unchecked; no board check |
| Archive card: `archive_mode` is off on the primary | Open, Arthur's call |

## The plan, in order. Each tranche is verified against something that can fail

1. **Bring `support/takeover` into line with track A, rehearsed off the live pair.**
   - (a) A `qv4-vip` unit replaces `querynz-vip` in the jobs. It asks the wire, refuses if anything answers, and announces the address. `querynz-vip` is left as it is (hard limit 23) and disabled at the switch.
   - (b) The role guard decides from the wire every boot. The marker becomes its output, never its input.
   - (c) `pg_hba` is generated from one file in the repository; `install.sh` writes it whole on both boxes.
   - (d) A rehearsal runs the real scripts against two scratch PostgreSQL 18 instances on node2 (own ports, own data folders, a stand-in address). It covers a real promote, a diverged timeline, a real `pg_rewind`, a reserved slot, a returning old primary held in recovery, and the "no rewind required" case.
   - Done when the rehearsal passes both directions and the mutation checks still catch every guard.
2. **Board checks** for the rules and the old arms:
   - the standby streams and lag is under a bound;
   - exactly one box holds 10.0.0.10;
   - both boxes' `pg_hba` match the source;
   - no `qv4-` unit names a box address;
   - each box has the cable drop-in and a static hostname;
   - the takeover jobs are installed on both boxes.

   Each check is first seen red against a broken state.
3. **Arthur's sitting (one script per box).**
   - Install the takeover jobs.
   - Put the cable drop-in on node1.
   - Stop `wal-archive-mirror`.
   - Turn `archive_mode` on, if he rules it (a restart of the primary).
4. **Live drill, on Arthur's word.**
   - (a) A switchover node2 → node1, measured: when writes stop and start, and every scheduler worker reconnecting through the address. This also restores the plan's normal state, primary on node1.
   - (b) An unplanned one: node1's database stopped hard, node2 takes over, node1 rejoins.
   - (c) Back to node1.
   - Each step is logged with its time in the setup card.
5. **The scheduler's two-box proofs (step 2's done-when list, on node1 and node2):**
   - a worker stopped mid-job loses at most one piece;
   - a timetabled job runs on the survivor;
   - the silent worker is alarmed by the other box;
   - a job needing a program one box lacks is never placed there.

   The alarm for a dead primary box gets a path that does not need the database (the alarm channel straight from the surviving worker).
6. **Standing services as queue jobs (2.13).**
   - The board, report, scan, site preview, MCP tunnel and Radiance get wanted counts and priorities, so a survivor starts what is missing within its memory.
   - The primary role's memory reserve goes into the worker.
   - This needs the Radiance decision below.
7. **The two-way file copy.** The stores and the work folder are held on both boxes, so the box that takes over has the documents as well as the database. This needs a design pass of its own (sizes, which disk on node1, how a writer on each side is fenced).
8. **Automatic takeover.** Once the third machine is on the network, the voter's word triggers `qv4-takeover`. Until then takeover stays the single command a person (or a session) runs, as recorded 11 October.

## Decisions for Arthur

1. **Radiance's memory on the box that holds the primary.** Track A sizes the survivor at 62 GB; Radiance alone is 85 GB. Choices:
   - put the n-gram table back on disk on the primary box only (slower steps there);
   - one Radiance per estate, not per box, placed by the scheduler;
   - accept a survivor that drops Radiance until the other box returns.
2. **The third machine.** Any always-on computer with its own path to each box. The home Wi-Fi network (both boxes are on it) is a path independent of the cable. The cloud server is reachable only through outbound tunnels, so it sees the internet link, not the boxes.
3. **`archive_mode` on the primary** (the open card): a restart, and point-in-time recovery from then on.
4. **The live drill's time**, when tranches 1 to 3 are done.
