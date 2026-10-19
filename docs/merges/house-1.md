# house-1: candidates, electorates and who sat in the House
branch: session/house (pushed; ed3da96)
session: house (session 1)
raised: 2026-10-20
claims: registers/house/ (new `recognise.py`, `workbook.py`, `nominations.py`, `results.py`, `elections.py`, `electorates.py`, `load.py`, `profile-proposed.jsonl`, tests `test_house_lane.py`; capture, read, check, tables, publish, sample, pane, spec); cards `stats-nz-2025-electorates-need-arthur-s-key`, `three-by-elections-and-two-2020-electorate-pages-are-not-held`, `who-left-the-house-mid-term-is-not-in-the-results-files`, `the-2020-and-2023-party-lists-are-not-held`; lesson `a-real-page-can-carry-the-challenge-script-recognise-a-block-by-its-own-page`; docs/status/house.md

Step 4.1. The lane copies by hash, read-only, every file the old estate
holds under `var/staging/ec-candidate-list/`, `ec-results/` and
`ec-byelections/`, and Stats NZ's two 2020 electorate files under
`var/staging/boundaries/` (outside the brief's three folders: the only
held source of Stats NZ's names; only the name and code fields are read).
It fetches nothing.

Profiles before readers: eleven profiles with recognition markers
(`recognise.py`, by shape: the results site's table ids, the workbook's
header row, the PDF's pages, Stats NZ's field names), pinned both ways by
a test. Of 167 files: 156 read, 5 held and not read (advance votes,
referendums, an election's front page that repeats its index), 6 failed
reads in the catch log (2 challenge pages, 2 Not Found, 2 browser
errors). No file unrecognised.

Measured on the real files (the lane's whole input is its sample; scratch
schema only, nothing live written):
- 28 elections with the Commission's stated polling days (10 general, 17
  by-elections, and 2026, not yet polled: no held file states its day).
- 216 electorates: 2020 and 2023 72 each, joined to Stats NZ's names 72 of
  72, all exact; 2026's 71 unjoined (its boundary set is not held: card);
  Tāmaki Makaurau 2025.
- 1,611 candidacies: 2026 530 (469 electorate, 443 list, 382 both, joined
  by name, all 382 exact); 2023 495; 2020 581 (Mana and Rongotai pages
  are browser errors: card); 5 at the 2025 by-election. Every one of the
  142 read results pages meets its own printed totals; the Commission's
  286 status-page abbreviations agree with the party printed beside each
  candidate.
- 243 seats: 2020 120, 2023 122, the 2025 by-election 1. Each window runs
  from the polling day to, at the latest, the next poll that filled the
  seat (the next general election, or a by-election for it: Tauranga and
  Hamilton West 2022, Tāmaki Makaurau 2025). `ended_on` is empty on every
  row: no held file dates an ending (contract: dates, 3; card).

Outside check (`python -m registers.house.check`): the Commission's own
figures counted again from the rows. 2026 release: 42 of 42 equal (530
candidates; 61 list only, 22 electorate only, 65 independent or
unregistered, 382 both; each of 17 parties' list and electorate counts).
Overall results: seats per party 2020 18 of 18 (120), 2023 21 of 21
(122). The Commission's PDF of the 2026 lists agrees with the list page
at 443 of 443 places (one name wrapped, a catch-log line). Two tests
remove one member and one candidate and see the check fail.

Keys: the Commission's own identities (`ge-2023/seat/epsom`,
`ge-2026/<name>/<electorate>`), not the hash and place. Rendered results
pages carry per-capture script tokens, so their hash changes at every
capture while their rows do not; the hash and place are the citation on
every row. A deliberate reading of contract (register row) 1; say if you
want hash keys instead.

For the merge, please:
- Append `registers/house/profile-proposed.jsonl` (eleven profiles, v1
  each) to `support/profiles/profiles.jsonl` with `add_version` and delete
  the proposed file; `read.profile_version()` takes the ledger's first.
  The shipped-profiles test will want its count raised by eleven.
- The four `pub` views are new names: `pub.elections`, `pub.electorates`,
  `pub.candidates`, `pub.members`.
- Records: the cards and the lesson make `docs/board.md` and
  `lessons/INDEX.md` stale; `tests/test_generators.py` rewrote
  `docs/board.md` in my working copy, not committed. Please regenerate
  both at the merge.
- Note: `bin/fast` ran under `/home/user/querynzv4/.venv/bin/python` (the
  card on the system-python fallback stands). Module: 22 passed, 13 s;
  whole repository: all green but `tests/test_generators.py`, 112 s.

## Result (integrator, 2026-10-20 08:40)

Merged into main as b3ec07c (merged main first). Done at the merge: the
eleven profiles appended to the ledger with `add_version`, the proposed
file removed, the shipped-profiles test at 43; board and lessons index
regenerated. Fast tier and gate green; the gate's load: 167 files, 28
elections, 216 electorates, 1,611 candidacies, 243 seats, 82 figures
checked, 13 set aside; published. Keys: the Commission's own identities
stand (a rendered page's hash changes per capture; the hash is the
citation), no change asked. Reading Stats NZ's two 2020 files from
`var/staging/boundaries/` is accepted as the only held source of the
names. Four cards stand; two wait on Arthur (the Stats NZ key; whether
to ask the Commission about its results site). The session ran headless
from the integrator, about 55 minutes.
