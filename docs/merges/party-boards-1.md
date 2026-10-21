# party-boards-1: the declared tier of party boards, built and not deployed (ruling 72)
branch: session/party-boards-1 (pushed; c1c4b51)
session: party-boards-1 (build, scope registers/party_boards/)
raised: 2026-10-21
claims: registers/party_boards/ (spec.md, profile-proposed.jsonl, capture.py, page.py, read.py, load.py, sample.py, check.py, tables.sql, publish.sql, sample.list, pane.md, README.md, tests/); docs/status/party-boards-1.md; one new card, a progress line on `party-boards-have-no-lane`; two lessons

- **Source:** the old `party-boards` capture (`var/staging/party-boards/`,
  the frozen listing's 1,061 files), copied by hash, read-only, case 1;
  captures from 2017 on (ruling 71): 870 captures, 869 documents; 190
  earlier ones listed in `pages` and not landed; the manifest landed as the
  index. Nothing fetched, no model.
- **Profile first:** `party-website-board-page` v1 in
  `profile-proposed.jsonl` (append it to `support/profiles/profiles.jsonl`).
  19 shapes: per site and theme era, the address, the heading that opens
  the board, the markup of a name and of a role, what closes the section.
  `read.py` runs the profile's shapes; no shape lives in code. A page no
  shape recognises is a drop-note with its reason; a name the rule refuses,
  a vacancy, a name repeating its role is a catch-log line (never the text).
- **Publishes:** `pub.party_board_roles` (party, name as declared and without
  honorific, qualifier, role as declared, stated or by the heading, section,
  document, url, first and last capture day, Archive copy, tier `declared`)
  and `pub.party_board_pages`. Not on the site; `products/published_site`,
  the template and `links/` untouched; the party page's board stays "not held".
- **Full build** (`scratch_party_boards_1_full`, sample database, bytes read
  from the old folder): 2,876 rows; National 1,504, NZ First 506, ACT 274,
  ALCP 210, Animal Justice 126, Te Pāti Māori 120, Women's Rights 49,
  Conservative 42, NZ Outdoors & Freedom 28, Opportunity 17; Labour, Greens,
  Vision 0. Pages: read 440, a section with no names 1, drop-notes 429 (no
  shape for the address 410, a layout the profile drops 15, theme
  placeholders 2, no board heading 2). Set aside 37. `check.py` (the
  manifest against the page rows) green; `--frozen` prints the frozen
  site's boards beside it: every name the frozen side has and this lane
  lacks is management, a members' council, an MP, a pre-2017 page or junk
  ("Share this").
- **Fast tier:** green for the lane (30 tests; 67-79 s with the fill, target
  60 s missed and recorded). Root tests green once the generated files are
  rebuilt: `tests/test_generators.py` sees `docs/board.md` and
  `lessons/INDEX.md` stale on this branch (new card, new lessons); they are
  yours to regenerate, not committed here.

For the integrator: append the profile line; add `qv4-party-boards-load` to
`jobs.toml` (`registers.party_boards.load`, no schedule of its own: a reload
when the lane changes); load the lane (it lands ~870 pages, 91 MB at most, in
the store); regenerate the board and the lessons index; drop
`scratch_party_boards_1_full` in querynz_v4_sample (its `party_boards_*` and
three unprefixed tables from a first try).
New card: `labour-and-green-boards-are-not-in-the-party-boards-capture`.
Lessons: `a-party-page-is-read-by-its-markup-not-by-guessing-which-line-is-a-name`,
`mask-digits-and-promoter-lines-in-any-dump-of-a-captured-page`.

## Result (integrator, 2026-10-21 16:14 NZDT)

Merged into main as a94f036 (`merge integrate/party-boards-1: gate green`). Branch `integrate/party-boards-1` from `session/party-boards-1` (c1c4b51), main merged. Integrator items: profile `party-website-board-page` version 1 appended (75 slugs); `qv4-party-boards-load` in the catalogue at priority 39 (class whenever, no clock), `support.scheduler check` green; `party_boards` in the lane list and its two schemas applied with grants on both databases; `docs/status/party-boards-1.md` renamed `party-boards.md`; board, lessons index and queue regenerated. Fast tier green in 381.4 s (target 300 missed under load, recorded). Gate green; staging loaded the lane from the held capture (1,060 captures, 869 documents, 2,876 rows, 37 set aside, 190 before the window not landed) and published `pub.party_board_roles` and `pub.party_board_pages`; the two board views go in at the next merge (gate-order lesson). `qv4-board` restarted 16:15. The drop of `scratch_party_boards_1_full` in the sample database is Arthur's. Branches and the working copy retired.
