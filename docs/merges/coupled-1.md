# coupled-1: a coupled donor name is one row joined to each person it names (ruling 73)
branch: session/coupled-1 (pushed; 923f2aa)
session: coupled-1 (build, scope links/ and keys/)
raised: 2026-10-21
claims: keys/names.py, keys/__init__.py, keys/tests/test_names.py; links/rows.py, build.py, rules.py, check.py, old.py, tables.sql, publish.sql, spec.md, README.md, tests; docs/status/coupled-1.md, docs/status/links.md; one card, one lesson

- `keys.names.joint_parts(name)`: the people a coupled filed name names
  ("Greenlees, Craig & Shayne" → Craig Greenlees, Shayne Greenlees; "Stewart
  Menzies and Megan Jean Harrison" → both whole). `is_joint_name` now also takes
  the real filed forms it missed (a middle initial, a whole name on each
  side, "Surname, A & Other, B", Sir/Lady) and asks that one given name be
  known to the director register: "Bread and Roses Auction" (a candidate
  return) goes from True to None. Organisations are never cut on "&";
  initials and "Drury & Alo, Rod & Rebecca" stay unjudged.
- `links.rows`: on the four donation views a coupled row keeps its filed
  name, name key and kind (the site's donor page is unchanged) and is read
  as no one person; one part row per person, ref `<donor ref>#<n>`, the
  donor's view, key, entity and dates, `part_of` the donor's ref.
- `links.build`: `coupled-name@1`, near, donor row to each part, evidence the
  filed string, the part and its number; `member-and-party-donor@1` reads a
  part's donor row. `check.py` counts filed rows only; the old-ledger mapping
  skips parts.
- Schema: `links.rows.part_of` (with its ALTER line), `pub.names.part_of`
  (appended to the view).

Scratch `scratch_coupled_1` on the real published tables: 37 coupled rows
(party returns 14, disclosures 20, candidate returns 3), 74 parts, 74
`coupled-name@1` links; the parts are reached by `full-name@1` 27 links, 14 parts
(e.g. the two Fisher filings join through "Stephen B Fisher"), `name-only@1` 58,
`member-and-party-donor@1` 1. 2,815,868 links in all. `check.py` 29 of 29 green
(`--pub scratch_coupled_1_pub`). Fast tier green: links, keys.

For the integrator: reload `links` (`tables.sql`, `publish.sql`); add
`joint_parts` to `docs/contracts/keys.md` item 5 (outside my fence); drop
`scratch_coupled_1` and `scratch_coupled_1_pub` in querynz_v4.
New card: `a-coupled-donor-s-part-ref-is-found-through-pub-names` (report, board
and site take a ref's key from the ref; a part's key ends `#n`).
Lesson: `a-couple-shape-is-not-a-couple-until-a-given-name-says-so`.

## Result (integrator, 2026-10-21 15:04 NZDT)

Merged into main as 1ca0ddf (`merge integrate/coupled-1: gate green`). Branch `integrate/coupled-1` from `session/coupled-1` (923f2aa), main merged. Integrator items: `joint_parts` written into `docs/contracts/keys.md` item 5 with ruling 73; `docs/status/coupled-1.md` folded into `docs/status/links.md` (2,757 bytes); the card and lesson as filed. Fast tier green in 322.3 s (target 300 missed under load, recorded). Gate green, nothing to load. The links reload from a detached copy of main (`links.build_all --schema links`, publish, `links.check`) started 15:06; its figures go in the next records commit. `scratch_coupled_1` and `scratch_coupled_1_pub` are Arthur's to drop. Branches and the working copy retired.
