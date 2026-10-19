# What the rebuilt site cannot show yet
kind: finding
state: open
use-case: 1
session: site
opened: 2026-10-20

The version folder carries nine of the ten kinds with figures and the
tenth as "not held"; inside the nine, these are blanks that say "not held",
each with its reason in the file, and each is a cause of difference the
comparison (4.5) will meet:

- **Board members (the tenth kind):** the frozen site read 106 party board
  members from party websites (`party-boards`, 1,061 captured files in the
  listing). No lane publishes them; no `board-member` file is written and
  the manifest's `kinds_not_held` says why.
- **Electorate money:** candidate donations, expenses and per-donor lines
  on the 82 electorate pages, the five electorates files and the home
  totals. The candidate-returns lane is building (step 4.1); when it
  publishes, `render.electorates_and_pages` takes its views and the
  template adds them to `reads`.
- **People:** donations made, interests, expenses, party boards and
  industry exposure on the 1,261 person pages. The views exist for
  interests and expenses (`pub.mp_interests`, `pub.mp_expenses`); joining a
  person to a donor row is the links' confirmed rules and is not read by
  the template yet (design: a politician joins a company role only with a
  supporting link).
- **Financial statements** on party pages: `pub.party_statement_figures`
  is read and not yet rendered.
- **Named rows on 114 of 152 returns:** the party-returns lane has Part A
  on 38; the rest show the declared total and "named rows not read".

None is a silent gap: every blank names what is not held. Fixed by the
lanes publishing and the template growing, one tranche each.
