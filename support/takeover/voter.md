# The voter: automatic takeover by a quorum lease (design, 6 November 2026)

Track A's build ("automatic promotion on the voter's word"), on the third machine `voter`
(192.168.68.57, home Wi-Fi). Status: DESIGN, for Arthur. Nothing installed.

## The one rule

**A box may hold the primary role only while two of the three machines agree.** The box itself is one.
The second is either the voter or the other box:

- **The primary keeps the role** while it holds an unexpired lease from the voter OR from the standby.
- **The standby takes the role** only with a lease from the voter, and only once every promise it gave the
  primary has run out.

Any two majorities of three share a member, and each member grants to one box at a time, so two
primaries cannot both hold a majority. This is what the old estate could not do with two boxes (ruling
130 refused keepalived for exactly this), and what the third machine was for.

## Leases, not clocks

- **What a lease is.** It is a promise for a duration: "I will not grant the role to anyone else for
  30 s from when I answered". Each machine counts durations on its own monotonic clock. No two clocks are
  compared, so their skew does not matter; only their rate (drift) does, and that is parts per million.
- **How long the grantee may count on it.** From when it SENT the request, plus 30 s, less a 5 s safety
  margin. The grantor counts from when it answered. So the grantee always believes the lease ends before the
  grantor does.

| Setting | Value | Why |
| --- | --- | --- |
| Renew every | 2 s | many tries inside one lease |
| Lease | 30 s | node2's Wi-Fi stalled 4.5 s and lost 3.8% in a 2-minute test (6 November); a lease must outlive a dozen lost renewals |
| Primary fences at | 25 s without a lease from anyone | 5 s before any grantor could hand the role on |
| Takeover after the primary dies | about 30 to 40 s | the lease runs out, then the promote, then the address |

## What each machine runs

**`qv4-voter` on the voter.** A user unit (lingering on), Python standard library only, about 150 lines,
one port on the home network.
- It holds `{holder, epoch, granted_until}`, written to disk with fsync before every answer.
- **Grant:** to the holder at any time (a renewal); to the other box only after `granted_until` has
  passed. Every change of holder raises the epoch.
- **Release:** a holder may give the lease up at once (a planned switchover).
- **After its own restart** it grants no NEW holder for 30 s (a lease it gave before the restart may still
  be running); renewals by the stored holder go on.
- It holds no data and never touches a box.

**`qv4-roled` on each box.** A root unit. It drives the jobs already built in `support/takeover`
(takeover, release, rejoin), which stay the only code that promotes, moves the address or rewinds.
- **As primary:**
  - every 2 s it renews with the voter and with the standby (over the cable and over Wi-Fi);
  - at 25 s with neither renewed, it **fences**: the address off, the database stopped fast;
  - it then rejoins as a standby once a new primary exists.
- **As standby:**
  - it answers the primary's renewals: "I will not take over for 30 s";
  - when it has heard nothing from the primary for 30 s, and its last promise has run out, it asks the voter;
  - with the voter's grant it runs `qv4-takeover`.
- **At boot**, replacing the static marker (lesson 3):
  - it asks the voter who holds the role;
  - if the other box holds it, the box comes up as the standby and runs `qv4-rejoin` itself;
  - if the voter is unreachable, and so is the other box, it waits: no role is taken on one vote.
- **Watchdog.** The agent feeds the box's hardware watchdog (`/dev/watchdog`, present on both boxes). If the
  agent hangs for 15 s while primary, the box restarts. A restart stops the database, so a hung agent can
  never keep a primary running without a lease. This is what Patroni does.

**Authentication.** Every message carries the box's name, the epoch and a nonce, signed with a key per
box (HMAC-SHA256). The keys live in `~/.querynz/voter.env` on the box concerned and on the voter, and
nowhere else (hard limit 1). The voter never trusts an address, so a box's Wi-Fi address may change.

## What happens when

| Event | Result |
| --- | --- |
| The primary box dies | Its lease lapses in 30 s; the standby's promise lapses; the voter grants; the standby promotes and takes 10.0.0.10. Writers follow the address; the scheduler's workers reconnect |
| The direct cable is pulled | The primary keeps the role on the voter's lease. The standby asks the voter and is refused (the lease is held). Replication stops until the cable is back; the board shows the lag |
| The primary loses Wi-Fi only | The primary keeps the role on the standby's promise over the cable |
| The voter is down | The primary keeps the role on the standby's promise. No automatic takeover until the voter is back; a person can still run `qv4-takeover` (the 11 October fallback) |
| The primary is cut off from both | At 25 s it fences itself; at 30 s the voter can grant the standby. Never two primaries |
| The agent on the primary hangs | The watchdog restarts the box within 15 s |
| A planned switchover | The primary releases at the voter and stops cleanly; the standby is granted at once; the old primary rejoins. Seconds, not 30 |
| A box returns | At boot it asks the voter, rejoins as the standby (rewind), and its worker starts pulling again |

**What is lost on an unplanned takeover:** the last moments of writes the standby had not yet received.
The standing decision is that writes do not wait for the standby, because everything above capture can
be rebuilt. The takeover logs the last LSN the standby received, so the gap is known.

## What it leaves for later tranches

- The standing services a survivor starts (plan tranche 6).
- The two-way file copy (tranche 7). Until then, a node1 that takes over has the database but reads
  documents from node2's disk, which is gone with node2.

## How it is proven before the live pair

1. **The quorum logic, in a test, with a fault-injecting clock and network:**
   - drop, delay and duplicate messages;
   - partition every pair;
   - restart the voter;
   - hang an agent.

   The invariant is checked at every step: never two holders. Each guard is mutation-checked.
2. **The real agents and voter on two scratch PostgreSQL instances on node2,** with a stand-in address:
   - kill the primary;
   - pull the "cable" (drop that path in the agent);
   - stop the voter;
   - switch over and back.

   It is timed against the 30 to 40 s.
3. **The live pair, on Arthur's word.** First a planned switchover node2 → node1 (the plan's normal
   state), then one unplanned stop each way.
