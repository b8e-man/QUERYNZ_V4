# The off-site backup passphrase: the special case

**Why it is different:** every existing backup is sealed with the
passphrase in force when it was made. Changing it does not re-seal the
old copies. Losing either passphrase loses the backups made under it.

**Default: keep it, unless it has been exposed.** The leak search
(`docs/security/leaks.md`) says whether it has. If it has not, this
runbook is not run; the row in the inventory says "kept: not exposed" with
the date of the search.

**If it is changed:**

1. Choose the new passphrase in the password manager, as a new entry
   dated today. Keep the old entry, dated, beside it. Never one entry
   overwritten.
2. **File and variable, node2:** `~/.querynz/offsite.env`, the line
   `OFFSITE_PASSPHRASE=`. Replace it at the box.
3. Tell the session: "rotated".
4. **The session proves, verdicts only, on node2 in `/home/user/querynzv4`:**
   the next nightly copy seals and uploads with the new passphrase
   (checks board green), and a restore of that copy opens
   (`python -m support.offsite restore --databases querynz_v4_sample`).
5. **Before the old entry is ever forgotten:** a restore of a backup made
   under the old passphrase is rehearsed. The restore reads the passphrase
   from the file, so for the rehearsal the old value goes back into the
   file at the box for one run, then the new one. Record the rehearsal's
   date in the inventory row.

**Inventory line:** the passphrase row, "Last rotated: <date>; old entry
kept in the password manager dated <date>; old-backup restore rehearsed
<date>".
