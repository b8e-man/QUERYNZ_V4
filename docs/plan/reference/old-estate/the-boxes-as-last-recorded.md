### The boxes, as last recorded

Measure all of this in the baseline; it is here so you know what to expect.

|  | node1 | node2 |
| --- | --- | --- |
| Processor | 16 cores, 32 threads | The same |
| Memory | 62 GB | 62 GB, with the spare 64 GB to be added |
| Graphics cards | Two Radeon R9700, 34 GB each | Two Radeon R9700, 34 GB each |
| Disks | Two hard disks of 3.6 TB (`/mnt/hdd1`, `/mnt/hdd2`), a fast disk at `/mnt/ssd`, the system disk | One 2 TB fast disk, two 4 TB hard disks (one at `/mnt/hdd`, one to be mounted), the system disk |
| Normal role | Primary database, the floating address, database-side jobs | Build sessions, capture jobs, the old apps, the standby database |

- **Network:** a 10-gigabit link joins the boxes. Each reaches the internet over Wi-Fi, behind a satellite connection that allows outbound traffic only.
- **System:** Fedora 44. Every job is a user-level scheduled job, installed by copy, with a manifest saying which box runs it. 75 jobs were on record.
- **Graphics cards are AMD, not Nvidia.** The model server that works on them is llama.cpp's. Software that assumes Nvidia cards will not run as documented.
- **The old serving app held a 27 GB index in memory on node2,** which is why node2 was recorded as tight. That app is outside the carve-out, so the memory is freed if step 1.4 stops it.

