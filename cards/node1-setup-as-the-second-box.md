# node1 set up as the second box of the estate
kind: blocker
state: open
use-case: -
session: scheduler
opened: 2026-10-18

Arthur, 18 October, on the queue item about a second worker on node2:
"card the node 1 setup". This reopens what ruling 55 closed: node1 comes
back as the second box, and the two-box items of step 2 are proven on it
for real instead of on the one-box rehearsal. The order, each line on
Arthur's word where it touches node1 itself (hardware, the rewind):

1. Arthur: node1 powered and on the network (10.0.0.1); fence it first,
   then the rewind as the failover note says (track A). The old estate's
   half of the carve-out there (the standby, the mirrors) is track A's.
2. A founding or integrator session re-measures node1 and fills the
   baseline's node1 column (cards, memory, disks, programs; the page
   reader's absence there was the 17-day fault).
3. The installer, from node2: `python -m support.installer apply --units --box node1`
   (code at the same commit, the environment, the qv4- units, the model
   server copy, the weights, the credential files box to box). It needs
   ssh from node2 to node1 for the user; the session asks before each ssh.
4. `qv4-worker@node1` enabled there; it registers its probed profile. The
   reservation for `querynz-vision-ocr` on node1 (step 2.9) goes into
   `jobs.toml` once the baseline says which card it holds.
5. The two-box proofs, with the rehearsal record as the script: a worker
   stopped mid-job finished by the other box; the alarm from the other
   box; the timetable on the survivor; a job needing a program only one
   box has never given to the other.

Blocks: the real two-box done-when items of step 2 (ticked today on the
rehearsal only). The queue item `a-second-worker-on-node2-after-the-rehearsal`
stands: its answer is node1, not a second worker on node2.

## Readiness, 5 November 2026 (integrator-9d788fb)

Measured from node2 at 22:4x:

- node1 does not answer 10.0.0.1; node2's 10 GbE card (enp13s0) shows no
  link (carrier off), so the cable or node1 itself is down. The floating
  address 10.0.0.10 sits on node2, timeline 4, node2 primary.
- The slot `node1_standby` is `lost`: the 100 GB cap
  (`max_slot_wal_keep_size`) dropped the WAL long ago and `archive_mode`
  is off. **A rewind cannot catch node1 up.** Line 1 becomes: fence, then
  move node1's old data directory aside (kept, not deleted) and take a
  fresh base backup from node2 (about 510 GB of databases: extractions
  257 GB, querynz_v4 150 GB, incoming_news 63 GB, nzbn_canonical 26 GB,
  the rest small), then a new slot. At 10 Gb/s that is under an hour
  of copying; the NVMe on node1 must hold it (to be measured at line 2).
- The base backup, the new slot, dropping the lost one and the four old
  node1-bound timers stopped on 17 October (`wal-archive-mirror`,
  `querynz-residue-mirror`, `querynz-verdict-sync`, `querynz-deploy-node1`)
  all touch the live database server or the old jobs: hard limit 22, on
  Arthur's word and not before the election (7 November). The qv4- half
  (lines 2 to 5) does not, and may run as soon as node1 answers.
- From node2: the ssh key and three known_hosts lines for 10.0.0.1 are in
  place; `python -m support.installer plan --box node1` is the first
  command once it answers.

Arthur's half, in order, at node1's console:
1. Power, the 10 GbE cable to node2; check `ip -br addr` shows 10.0.0.1.
2. Fence before anything else: `sudo systemctl disable --now postgresql querynz-vip`
   and `sudo touch /etc/querynz/not-primary`. It must never hold 10.0.0.10.
3. Tell the session; it pings 10.0.0.1 (never the VIP) and starts line 2.
