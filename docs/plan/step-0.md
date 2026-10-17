## Step 0: what Arthur does before building starts

None of this can be done by a session. Arthur has said the hardware items will be done before the build. Nothing in steps 1 and 2 depends on them technically; step 3 needs the disk, and track A needs the third machine.

- [x] **Create an empty private repository named QueryNZV4** on the GitHub account, clone it on node2 to `/home/user/querynzv4`, and give node2 push access. DONE 18 October: the repository is `git@github.com:b8e-man/QUERYNZ_V4.git` (that spelling), the local clone is `/home/user/querynzv4`, node2's key pushes.
- [x] **Save this plan as `/home/user/querynzv4/docs/PLAN.md`.** DONE 18 October, with DESIGN.md, DISCUSSION_RECORD.md and RISK_REGISTER.md beside it. From here the copy in the new repository is the plan; the old repository's `V4_ideation/` is the record of how it was drafted.
- [x] **Create the database logins for the new estate** — DONE 18 October: four roles with the plan's limits (owner 20 connections / 5 min; old-estate reader 5 / 5 min, read-only on the three old databases; session reader 5 / 30 s; product reader 10 / 30 s), `querynz_v4` and `querynz_v4_sample` owned by the owner role, details in the two v4 credential files on node2 (node1's copies when that box exists again). Each login tested. The remainder of the original item:  and put their connection details in `~/.querynz/v4.env` on both boxes. The first owns one database, which Arthur creates, `querynz_v4`, on the existing server, with a cap of 20 connections and a five-minute limit on any query. The second can only read the three old databases, and its address is the standby's. Two more logins and a second, small database, added by ruling 54, are in the table under this list.
- [x] **Check the alarm address exists:** the file `ops/config/alert-channel.env` in the live old folder, which sends a phone notification when a job fails. Present (checked 17 October). The watcher that guards the frozen site through the election depends on it.
- [x] **Mount node2's second 4 TB hard disk.** DONE 18 October: `/dev/sdb2` (was an empty NTFS volume) is ext4, label `hdd2`, mounted at `/mnt/hdd2` with `nofail` in fstab; 3.4 TB free. The Papers Past archive, its index files and the model files go there.
- [x] **Fit the spare 64 GB of memory in node2.** DONE 17 October: node2 reads 125 GB. (The same sitting took node1 down — see "Notes from Arthur, 17 October" item 5 — so today node2 holds the primary role as well; the plan's "primary stays on node1" is the target state, restored only by track A's fail-back on Arthur's word.)
- [ ] **Set up the third machine and put it on the network,** with its own path to each box. It only votes on which box holds the database, and holds no data. Any always-on computer will do. HELD 18 October, with track A: it waits on node1's return and the fail-back.
- [x] **Allow for model downloads over the satellite link:** roughly 80 GB for the four trial models, each fetched once and copied from box to box over the local link. The session runs the downloads off-peak; it needs to know there is no data cap in the way. CONFIRMED 18 October: no data cap.
- [ ] **Start the first session in `/home/user/querynzv4`,** on Fable, and paste the step 1 brief. Start it in that folder and not in the old repository: a session started in the old folder loads the old orientation file and the old hooks, and this plan overrides both. This first session has no fences yet, so it will ask before each command. It builds the fences and stops; every later session starts with them loaded.

* [x] **Wind up the session now working in the old repository.** Let it finish or drop what it has in flight, and tell it that the old repository takes no commits after the freeze tag. Two sessions changing the old estate at once is how the frozen site gets broken. DONE 18 October.

**The logins and databases in full.** Ruling 54 adds the last two rows and the sample database. Arthur creates both databases and every login, so that no login of the new estate can create a database or a login on the server that feeds the frozen site.

| Login | May | Limits | Its details go in |
| --- | --- | --- | --- |
| Owner | Own `querynz_v4` and `querynz_v4_sample` | 20 connections; five minutes a query | `~/.querynz/v4.env`, as `QV4_OWNER_URL` |
| Old-estate reader | Read the three old databases, at the standby's address — **until node1 is rewound there is no standby: point it at node2 (the primary) for now and move it when the standby exists** | 5 connections | `~/.querynz/v4.env`, as `QV4_OLD_READ_URL` |
| Session reader | Read, in the two new databases, what the owner grants it. Step 1.8 grants everything except the tables that hold a person's home address, and the seal | 5 connections; 30 seconds a query unless `bin/q --long` asks for ten minutes | `~/.querynz/v4-read.env`, as `QV4_READ_URL` |
| Product reader | Read the published tables only. The board and every product surface use it | 10 connections | `~/.querynz/v4-read.env`, as `QV4_PRODUCT_URL` |

Two dated jobs of Arthur's sit outside the build and do not move for it. They are listed with their dates under "Dated jobs" at the end: the privacy-advice backstop (1 November), and sealing the director addresses (before 18 November, with the old checks board going red on 4 November).

Rotating passwords and keys is now part of the build, as track H. It will ask Arthur for about five minutes at a provider for each key, starting with the deploy token for the public site, and for one planned sitting to change the database passwords.

