# templates-fix (session fix-templates-1, 2026-10-21)

Where it stands: done; branch `session/fix-templates-1` pushed, merge request
`fix-templates-1` raised. Nothing half-done.

- **window_days.** Construction and property declare it in `[[params]]`
  (integer, no default, ruling 65); `--set window_days=365` is accepted and
  cuts. Card closed.
- **The Charities Register.** All ten templates read `charities`,
  `charity_officers`, `charity_returns` with licence, attribution and
  refresh; `charities` is out of every `not_held` line and
  `CHARITIES_NOT_HELD` out of every rules file. Charity flags run: officer
  rows by a person's name are near (a mark amber at most); a company's
  charity by business number is confirmed. A clear needs the name looked up.
  Insurance and ownership gained a charities section. Cards closed: banking,
  legal, agriculture, credit, insurance, construction, recruitment.
- **Still open on three cards (outside this brief):** healthcare (health
  register keys, an officer's near links, `chain` in the Gazette section),
  property (oio, building_consents, rea keys; near links; companies above),
  ownership (the chain). Each card says so.
- **Agriculture** gained a `checkpoint.list` (six keys); its 2026-10-20
  checkpoint kept none.
- `charity-officers-are-in-no-link-and-no-name-row`: read, unchanged (the
  links lane's).

Checks: fast tier `products/templates` green (35.7 s); every template's slow
tests green; `python -m products.report check` green; one-way and
reading-limit tests green. Every checkpoint re-rendered before and after
(scratch), recorded in each `limits.md`.

Next: the integrator merges. A session for the three open cards' reaches
halves would be `bin/fix products/templates/`.
