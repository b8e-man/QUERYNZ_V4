# The LINZ Data Service key

**Why:** it is on both boxes and reaches an outside service. Data pulled
with it is under the LINZ Licence for Personal Data (ruling 271).

**Where:** data.linz.govt.nz → your account → API keys. Create a new key;
delete the old one after the proof.

**Permissions:** the key's scopes as now: "Query layer data" and
"Download / export" (the weekly pull reads the title-owners table 51564
through the data service). Nothing else.

**File and variable, both boxes:** `~/.querynz/linz.env`, the line
`LINZ_API_KEY=`. Node2 first; node1 at its own keyboard when it is back.

**Timing:** clear of the weekly `linz-titles-pull.timer` on node2 (check
its next firing with `systemctl --user list-timers linz-titles-pull.timer`).

**Tell the session:** "rotated".

**The session then proves, verdicts only, on node2 from the reference
copy `/home/user/qnz3-ref`:**

1. A dry run of the weekly pull with the key read one variable at a time:
   `ops/linz_titles_pull.py --layer 51564 --dry --max-rows 10`. "works" or
   the refusal.
2. The old key is refused: the LINZ page shows it deleted. The session
   never held it.
3. The next scheduled pull lands a manifest row.

**Inventory line:** the LINZ row, "Last rotated: <date>".
