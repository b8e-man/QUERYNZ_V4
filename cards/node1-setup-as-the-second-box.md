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
1. Boot node1 with the 10 GbE cable to node2 UNPLUGGED: on boot its
   postgresql and querynz-vip would start, and with the cable in it could
   claim 10.0.0.10 while node2 holds it.
2. Fence: `sudo systemctl disable --now postgresql querynz-vip` and
   `sudo touch /etc/querynz/not-primary`. It must never hold 10.0.0.10.
3. Plug the cable in; check `ip -br addr` shows 10.0.0.1.
4. Tell the session; it pings 10.0.0.1 (never the VIP) and starts line 2.

## Tonight, 5 November 2026 (integrator-9d788fb, on Arthur's "charge ahead")

- 22:51 fenced at node1's console by Arthur (`/etc/querynz` had to be made
  first); postgresql and querynz-vip inactive and disabled, checked from
  node2 over ssh; only node2 holds 10.0.0.10.
- Line 2, the baseline: 32 threads, 125 GB memory, two Radeon AI PRO R9700
  (32 GB each), nvme 1.8 TB (1.2 TB free; the old data directory 365 GB),
  sdb 3.6 TB at /mnt/hdd1 (the old estate's backups, 618 GB), sdc 3.6 TB at
  /mnt/hdd2, an unused 447 GB SATA SSD (NTFS; node2's spare 512 GB nvme is
  NTFS too). querynz-vision-ocr (carve-out) running, 8032 healthy, left as is.
- 1.4 stops, node1's half of batch 2 on the stop list: `gazette-derive.timer`
  and `feed-parties.timer` disabled at 23:00. Arthur approved
  `querynz-embed-index.timer` too; it is not on the stop list (only a
  founding session writes it), so the hook refused it: Arthur stops it at
  the console. Proof: none of the three ran from 17 October to tonight, and
  the site released green throughout.
- Code: node1 has no GitHub key, so its checkout and release copy were
  cloned by git from node2's main checkout (origin
  `ssh://10.0.0.2/home/user/querynzv4`): main at b919605, release detached
  at 8391be6, node2's release. Both venvs built (Python 3.14.7; node2 3.14.8).
- Disks: the qv4- folders of node2's /mnt/hdd2 made on node1's /mnt/hdd2;
  qv4-models copied whole. The stores (qv4-docs, qv4-papers-past, dumps,
  offsite, restore) are not copied: how they stay in step is open.
- Models: every weights file the profiles name, and the Radiance folder,
  rsynced to the same paths (189 GB, 21 files, sizes match); image loaded.
- Credential files: the safety hook refuses a session copying them; Arthur
  copies the ten node1 lacks (it has 10 of node2's 20).
- qv4-radiance, its watchdog service and timer placed in node1's user unit
  folder from the repository; qv4-radiance enabled and started.
- 23:4x, Arthur ran the two scripts (scratch node1/exports.sh, mounts.sh):
  node2 exports /mnt/hdd2/qv4-{docs,papers-past,dumps,offsite,restore} to
  10.0.0.1 (nfs open in zone querynz-lan); node1 mounts each from 10.0.0.2
  (node2's own address, not the VIP: the stores sit on node2's disk) at the
  same path, nfs4, automount, nofail. A document read across matched its
  hash. qv4-models stays node1's local copy. `live` is NOT shared: its
  box-only files (watchdog state, night mark, server logs, scheduler.json)
  and its appended ledgers need per-box names and locked appends first.
- The worker's database access: ruling 144; the line is in (node2 pg_hba line 130,
  reloaded); node1 logs in as qv4_read through 10.0.0.10.
- Sharing `live`: tranche a on main (f5fd099, per-box watchdog and night-mark
  names). Tranche b (support.appendline, every shared record's writer locked) is on
  branch node1-live-tranche-b, NOT main: test_worker's takeover test failed 3 of 12
  on node2 with it and 0 of 10 without; cause not found at 00:30 on 6 November.
  The mount, by Arthur, is the whole work folder `/home/user/querynzv4-work`, not
  just live: jobs also write `inbox/cards` and `scratch/<lane>`.
- Overnight 5 to 6 November: node1 serves Flash-Next (qv4-radiance, 127.0.0.1:8060)
  with nothing calling it; no worker there; node2 runs exactly as before.
- 6 November, 08:5x: the takeover regression was not tranche b. Unchanged main failed
  the same test 4 of 16: node2's MemAvailable dips to 12 GB, under the 16 GB reserve,
  and in those seconds no job is eligible. The worker tests now pin free memory (328d8fd;
  12 of 12, suite green). Tranche b merged (1efcac9); both release copies moved to it.
  node2's worker restart is owed (it still runs the old append code) and must happen
  before qv4-worker@node1 starts. The work-folder scripts are in scratch node1/:
  work-export.sh (node2), work-mount.sh (node1; moves node1's own folder aside).
  The societies lane's tests error at setup on main too (a missing expenses sample).
- 6 November, 09:01: Arthur ran work-export.sh and work-mount.sh; the whole work folder is
  node2's over NFS on node1 (automount; node1's own 8 KB folder kept as
  querynzv4-work.node1-own-2026-11-06). Cross-box proof (scratch node1/appendline-proof.sh,
  both boxes from one agreed second, 16,000 lines of 3 KB): unlocked 43 torn lines and
  0 of 8 writers whole, or 7,199 lines lost with a held descriptor; locked 16,000 whole,
  8 of 8, three runs, 227 to 335 box switches. A first version never overlapped the boxes
  and passed unlocked too: the start had to be agreed.
- 10:06: qv4-worker@node1 started (unit linked from node1's release copy, f33722c), reads
  only: jobs.toml `[boxes.node1] only_profiles = text-reader, review`, and its night window
  never opens. Reason: node1's old folder is a 17 October copy (44 GB against node2's 80),
  so its loads would read stale input. node2's worker restarted on 34f717e at 09:58.
- Open: a row's pieces run only on its lease holder, so the courts backlog (row 1687,
  2,408 pieces) stays on node2 and node1 takes only new reading rows. Sharing one row's
  pieces across boxes is a scheduler change, not made.
- Not done (superseded above): qv4-worker@node1 (line 4: waits for node1's card reservation
  beside querynz-vision-ocr in jobs.toml, and the credential files). The
  installer's --box path is unproven and wrong for a second box: with
  --units it enables a worker named node1 on node2, and it never pulls code.
- Ruling 145 (6 November, about 10:20): continuous uptime, fungibility, pooled capability; the election hold lifted.
- 10:27 to 10:41, node1 rebuilt as a streaming standby (scratch node1/standby-node1.sh, Arthur): postgresql 18.6,
  the old data directory kept as data.before-2026-11-06, a base backup of 540 GB in 14 minutes, slot node1_standby made
  again (the first run stopped at once: the lost slot was still there; the script now drops it over the replication
  login itself), primary_conninfo pointed at 10.0.0.10. Slot active, 0 bytes behind. The address switcher stays off and
  /etc/querynz/not-primary stays: node1 is the standby.
- 10:48, helpers (fbcff15): a worker with nothing of its own joins another box's leased row and takes its pieces.
  After both workers restarted, node1 owns the courts row 1687 and node2 helps; both read with their own Flash-Next.
