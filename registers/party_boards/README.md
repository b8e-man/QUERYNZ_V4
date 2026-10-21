# registers/party_boards — the boards the parties declare

A lane reading the held party-website capture (the old estate's
`party-boards` capture, 1,061 files in the frozen site's listing, copied by
hash, never fetched) into one row per declared board role: party, the name
as declared, the role as declared, the page and its capture date as the
citation, source tier `declared`. Ruling 72 (21 October 2026): built, not
deployed: the tables are published under `pub`, nothing goes on the Follow
the Money site and nothing enters the links until Arthur rules.

| File | What |
| --- | --- |
| `spec.md` | the five lines |
| `profile-proposed.jsonl` | the document profile `party-website-board-page` v1: every site's shapes (address, the heading that opens the board, the markup of a name and a role, what closes it), the refusal markers; the integrator appends it to `support/profiles/profiles.jsonl` |
| `capture.py` | the manifest, the window (2017 onward, ruling 71), copying by hash |
| `page.py` | a page's bytes (gzip, zstandard; the Archive's toolbar cut) as lines with their markup |
| `read.py` | the reading, run from the profile's shapes; no site's shape lives in code |
| `load.py`, `tables.sql`, `publish.sql` | the build, the tables, `pub.party_board_roles` and `pub.party_board_pages` |
| `check.py` | the capture's own manifest against the page rows; the counts per party; unrecognised pages by reason |
| `sample.list`, `sample.py`, `tests/` | the fast tier's pages (one at least per party, every shape, the hard cases) |
| `pane.md` | how the rows appear on the board |

    python -m registers.party_boards.check --schema scratch_party_boards_1 --database querynz_v4_sample [--frozen]
