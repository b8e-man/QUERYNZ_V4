# The overclocking test gave the database bad reads; querynz_v4 reads clean since the cold boot, the old databases are unverified
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-29

Between node2's six reboots on 29 October (07:36 to 09:11, Arthur's
overclocking test) reads from the one database server came back wrong.
The kernel counted 18 BTRFS checksum failures on `nvme1n1p3`, the root
filesystem that holds the clusters, all at 07:55, and PostgreSQL raised
"invalid page in block" about five hundred times in the user journal:
in six querynz_v4 tables (`gazette.celebrants`, `grants.grants`,
`companies.entities`, `companies.directors`, `mcpsource.arrivals`,
`ministers_diaries.entries`) and in seven relations of the old estate's
three databases, two of them hit many times each. The old estate's
`pg_dump` at 07:55 failed on one. Two qv4 jobs failed on it: the board's
checks at 08:01 (25 alarms sent; six modules red only on the read error)
and the site build at 08:02 (rebuilt by hand later that morning).

After the cold boot at 14:34 the integrator re-read every one of the six
querynz_v4 tables whole (every row rendered as text) and the exact block
each error named: all clean, and `pg_stat_database` shows no checksum
failure since the restart (data checksums are on). So for querynz_v4 the
bad pages were in memory under the overclock, not on disk. The BTRFS
counter is cumulative and still says 18.

Not shown: the old estate's relations, which the integrator has no reader
for; and that no job wrote a page computed from a bad read in the window.
Writers in the window were `qv4-disclosures-load` at 07:44 (green, 14 s),
the old estate's own timers, and the three gates after 09:11 if the clock
was still raised then.

Arthur's: confirm the overclock is off; `btrfs scrub` the root filesystem
(reads every block against its checksum; root); run the old estate's own
checks, or `pg_amcheck`, over the relations named in the journal; reset the
device statistics after the scrub so a new failure shows as one.
