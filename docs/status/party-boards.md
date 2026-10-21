# party-boards-1: where it stands

**Date:** 2026-10-21. **Ruling:** 72, the declared tier of party boards,
built and not deployed. **Lane:** `registers/party_boards/`. **Merge
request:** `party-boards-1` (raised).

## Done

- Profile `party-website-board-page` v1 (`profile-proposed.jsonl`): 19
  shapes over ten parties' sites and their theme eras, each by address,
  opening heading and the markup of a name and a role; a refusal marker for
  a theme's placeholder people; one known layout dropped by name (ALCP
  2020-22). The reader executes the profile; no shape lives in code.
- Capture: the old `party-boards` folder by hash, 2017 onward (ruling 71):
  870 captures, 869 documents in the window, 190 before it listed and not
  landed, the manifest landed as the index.
- Full build in the sample database (`scratch_party_boards_1_full`, read
  from the old folder's bytes): 2,876 role rows; pages read 440, a section
  with no names 1, drop-notes 429 (no shape for the address 410, the ALCP
  layout 15, placeholders 2, no board heading 2); 37 names set aside (36
  name repeats its role, 1 vacancy). Outside check (the manifest) green.
- Rows per party: National 1,504; NZ First 506; ACT 274; ALCP 210; Animal
  Justice 126; Te Pāti Māori 120; Women's Rights 49; Conservative 42; NZ
  Outdoors & Freedom 28; Opportunity 17; Labour, Greens, Vision 0.
- Fast tier green for the lane (30 tests; 67 s with the fill, target 60 s
  missed and recorded). Mutating a shape or the reader fails the pinned
  sample tests.

## Carded

- New: `labour-and-green-boards-are-not-in-the-party-boards-capture` (their
  boards, and ACT's officers' contact page, are in the whole-site capture).
- `party-boards-have-no-lane`: a progress line; stays open until Arthur
  rules boards into the template.

## Next

1. Integrator: append the profile line to `support/profiles/profiles.jsonl`;
   add `qv4-party-boards-load` to `jobs.toml`; load the lane (it lands
   ~870 pages in the store); drop `scratch_party_boards_1_full` in the
   sample database.
2. Arthur: whether boards go into the Follow the Money template, and whether
   the lane reads the whole-site capture's governance pages.
