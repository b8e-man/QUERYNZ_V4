# fix-support-offsite-1: a restored database carries its source's collation, ctype and locale provider
branch: fix/support-offsite-1 (pushed, f7a0225; one commit on 8618b41)
session: fix-support-offsite-1 (scope support/offsite/)
raised: 2026-10-23
claims: support/offsite/ (copy.py, restore.py, spec.md, tests/test_locale.py); card closed: the-restore-rehearsal-loses-the-source-collation; lessons/a-restore-must-carry-the-source-collation.md

## The finding, confirmed

- 22 October 13:00 (copy 20261021T210010): extractions 75/75, incoming_news 22/22 and nzbn_canonical 137/137 restored
  equal, then querynz_v4 failed after 6,779 s with CheckViolation `links_pair_order` on links.links.
- The leftover scratch server (port 5434) has every database at datcollate/datctype C.UTF-8. Live has en_NZ.UTF-8,
  provider libc, for every database. Live has 3 links.links rows (of 2,815,766) with `row_a collate "C" >= row_b
  collate "C"`.
- **The 19 October scheduled run (10:33 NZDT) failed in 6 s for another reason.** It got `DROP DATABASE "extractions"`:
  ObjectInUse, "1 other session using the database". A hand rehearsal's scratch server, with the same unit, port and
  folder, had been up for 13 minutes. The record file was overwritten since then; the traceback is in the user
  journal.
- **Correction to the brief: the copy has restored EQUAL once.** The hand bucket restore of 19 October 19:40 to 21:30
  was EQUAL, querynz_v4 35/35 (offsite-2b, item 1). At that time links.links held no row that "C" orders the other way;
  the one failing row with a date is from 21 October.

## The change

- **copy.py**: `database_locale(cur)` reads `LOCALE_SQL` from pg_database for the current database: the encoding, the
  provider (libc, icu or builtin), datcollate, datctype, datlocale and daticurules. Each night's manifest records them as
  `databases.<db>.locale`. The query was run on live querynz_v4 and returns UTF8 / c / en_NZ.UTF-8 / en_NZ.UTF-8.
- **restore.py**: `database_locales(man, dbs, live)` takes the manifest's settings, or, when a manifest has none, the
  live server's, read at restore time (`live_locale`, through the login pieces.py gives that database). Each one is
  marked `"from": "manifest"` or `"from": "live server"`.
  - The scratch server's initdb takes the first database's settings (`-E`, `--locale-provider`, `--locale`,
    `--lc-collate`, `--lc-ctype`, and `--icu-locale` or `--builtin-locale` where needed).
  - Each database is created with `CREATE DATABASE … TEMPLATE template0 ENCODING … LOCALE_PROVIDER … LC_COLLATE …
    LC_CTYPE …` (plus ICU_LOCALE/ICU_RULES or BUILTIN_LOCALE).
  - The record carries `server_locale` and `databases.<db>.locale`, each with its `from`.
  - The live read now happens inside the try, so if it fails, the failure is recorded.
  - `stop_server` uses the runner it was given.
- **Tests** (`tests/test_locale.py`, fakes only):
  - the copy reads the locale from pg_database;
  - a fake manifest and a fake runner: initdb and CREATE DATABASE carry en_NZ.UTF-8, and C.UTF-8 appears nowhere;
  - ICU and builtin settings each name their own locale;
  - a manifest that lacks the locale makes `rehearse` read the live server, and the record says "live server".
- **Live proof** (session scratch, a separate server on port 5439, now stopped): the three live key pairs, loaded under
  the same CHECK. In a database the new `create_database` made in en_NZ.UTF-8: 3 of 3 accepted. In one made in C.UTF-8:
  CheckViolation links_pair_order. No bucket fetch and no rehearsal.

Checked: `bin/fast support/offsite` green (24 tests, sample filled); tests/test_imports_one_way.py,
test_lessons_search.py and test_reading_limits.py green. Known to fail: nothing.

**Not fixed here (a card if you want it):** two rehearsals can still share one scratch server, which is the 19 October
failure. A lock like the copy's spool lock would refuse the second one.

## What the integrator does after the merge

1. Stop the leftover scratch server from 22 October: `systemctl --user stop qv4-restore-scratch` (node2). Then remove
   `/mnt/hdd2/qv4-restore/{pgdata,sock,work,trees}`; the new initdb only runs on an empty pgdata. That folder holds
   restored registers, home addresses included, and it is all regenerable.
2. Queue the rehearsal: `python -m support.scheduler enqueue qv4-offsite-rehearsal` (node2, in
   `/home/user/querynzv4`, after the merge so the worker runs the new code). It takes about two hours.
3. What EQUAL looks like in `/home/user/querynzv4-work/live/checks/offsite-restore-last.json`:
   - `"equal": true` and no `why`;
   - each of the four databases has `equal == tables` and empty `in_bad` and `out_bad`;
   - every tree has `bad: 0`;
   - `databases.<db>.locale` is `{"collate": "en_NZ.UTF-8", "ctype": "en_NZ.UTF-8", "provider": "libc", "encoding":
     "UTF8", …}`;
   - `server_locale` is the same.

   The `from` field is "live server" until a copy made after this merge is the newest. The first is tonight's 21:00
   nightly. Run after that, it reads "manifest". The job log ends `restore EQUAL in … s`.

## Result (integrator, 2026-10-23 13:50 NZDT)

Merged with `release-copy-1` on one integrate branch: `e433ea0 merge
integrate/release-copy-1: gate green` (fast tier green on the combined
branch; `bin/fast support/offsite` green in 44 s). Branches and the working
copy retired. Done after the merge: the leftover scratch server
`qv4-restore-scratch` stopped at 13:16 (it had run since 22 October 13:00);
its folders under `/mnt/hdd2/qv4-restore` (pgdata 114 GB, work 33 GB,
regenerable, restored registers with home addresses inside) are Arthur's
`rm -rf`, which the session's hooks refuse the integrator; the rehearsal is
queued once that folder is clear, since initdb needs an empty pgdata. The
correction to the brief is noted: the copy restored EQUAL by hand on 19
October, before the three out-of-order rows existed.
