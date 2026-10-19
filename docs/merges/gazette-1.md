# gazette-1: every Gazette notice typed; the celebrant lists read
branch: session/gazette (pushed; a112cd0)
session: gazette (session 1)
raised: 2026-10-20
claims: registers/gazette/ (new `notices.py`, `celebrants.py`, `load.py`, `profile-proposed.jsonl`, tests `test_gazette_lane.py`; capture, read, check, tables, publish, sample, pane, spec); cards `the-gazette-lane-reads-only-the-celebrant-lists-so-far`, `twelve-printed-celebrant-tables-are-unread`, `civil-union-celebrant-lists-without-stops-are-unread`, `the-old-capture-missed-a-seventh-of-2019-s-gazette-notices`; lesson `a-gazette-celebrant-list-can-print-home-addresses`; docs/status/gazette.md

Step 4.1. The old estate holds the Gazette only as article text. Every
gazette.govt.nz notice row in `incoming_news.articles`, with its row in
`nzbn_canonical.gazette.notices`, was exported once on 20 October 2026
04:49 through the old read-only login (60 s statement limit, a
server-side cursor, search path set to the old schema) to
`gazette-notices-2026-10-20.jsonl`: 208,461 lines, 207,133 notices,
sha256 47de7e09…, pinned in `capture.EXPORT_SHA`. Nothing runs it at load;
every row from it says "taken from the old estate's tables; original not
held". It fetches nothing.

Typing: by the section code inside the Gazette's own notice number, never
by title. 1,328 notices were captured twice with slightly different text
(none identical): the copy the old classifier read is kept, the other is a
catch-log line.

Reading, largest unread format first (the brief's 90.8%): the celebrant
lists. The old C226 reader is replaced, not wired: measured on this
export it missed most of the class and, on the independent celebrants'
lists, took a street address for a surname. Six shapes (stops, address,
chain, marked, table, none), each measured on every notice; the action is
the notice's own words (appointment, removal, publication, annual list).
Measured on all of it, not the sample: 2,975 notices recognised, 2,941
read (110 with a part set aside), 34 set aside whole; 123,187 rows, 55,339
from 2019; 8,943 addresses in `gazette_private` only; 320 catch-log lines;
adjacent rows in alphabetical order 98.0% (chain) to 99.4% (marked).
Items in equal items out plus items set aside, asserted in `read.py`.

Outside check (`check.py`; exits 1 on any failure, unlike the old gate):
the Gazette's own counts printed in its notices. Each celebrant series'
"Notice No." per year: every held numbered notice is read as a celebrant
list (green on the full load). The year's one numbering: numbers held
against the highest held, 95.7% to 99.3% for closed years, 2019 86.4%
(card). The full lane loads in 12.4 s.

Fast tier: the lane's 25 tests green on the sample (19 notices, the hard
cases named in `sample.list` by notice number). Whole repository: one
failure, `tests/test_generators.py`, because my cards and lesson make
`docs/board.md` and `lessons/INDEX.md` stale (generated; yours to
rebuild). The test rewrote `docs/board.md` in my working copy; the fence
will not let me restore it, so it is left uncommitted.

For the merge, please:
- Append `registers/gazette/profile-proposed.jsonl` (profiles
  `gazette-notices-export` v1 and `gazette-celebrant-list` v1) to
  `support/profiles/profiles.jsonl` and delete the proposed file;
  `read.profile_version()` takes the ledger's first.
- The export's bytes are in the store (`/mnt/hdd2/qv4-docs/47/47de7e…`),
  landed by my sample fill; the copy in
  `/home/user/querynzv4-work/scratch/gazette/` can go once you have seen
  it there.
- Two scratch schemas from my full load stay in `querynz_v4_sample`:
  `scratch_gazette_full` and `scratch_gazette_full_private` (the second
  holds the 8,943 addresses; the session reader is not granted it). The
  safety hook refused my DROP; please drop both.
- `pub.gazette_notices` publishes titles, never text: bankruptcy,
  prohibition and independent-celebrant notices print home addresses.
- The parties lane can take this lane's `au` notices instead of its own
  export when it next runs (its status file says so).

## Result (integrator, 2026-10-20 07:30)

Merged into main as 39febf3 (merged main first). Done at the merge: the
two profiles appended to the ledger, the proposed file removed, the
shipped-profiles test at 32; the lesson's rule cut from 262 to 235
characters (the index refuses over 240); board and lessons index
regenerated. Fast tier and gate green; the gate's load: 207,133
notices from 208,461 lines, 1,328 captured twice, 2,975 celebrant lists
(2,941 read, 34 set aside), 123,187 celebrant rows, 8,943 addresses in
`gazette_private` (owner only, checked), 204,158 notices typed and not
yet read; published in 12 s. The export's bytes are in the store. Not
done, both outside a session's reach: the two scratch schemas
`scratch_gazette_full` and `scratch_gazette_full_private` in
`querynz_v4_sample` (the safety hook refuses DROP from every session;
Arthur's psql) and the copy under `querynz_v4-work/scratch/gazette/`
(another session's scratch; removed with the copy's retirement if the
launcher clears it, else Arthur's). Four cards stand.
