# site: where it stands

**Date:** 2026-10-20. **Step:** 4.4, the published-site shape and the Follow
the Money template, `products/published_site/` and `products/templates/ftm/`.
**Merge request:** `site-1`.

## Done

- The template `products/templates/ftm/ftm.json`: 22 pub views with
  licence and attribution, the ten kinds as sections, 13 rules, the
  known-limits page, the frozen site's settings (window 2017, races
  2020/2023/2026 under rulings 361/363/366, seven parties by registration
  key, the $15,000 line, the disclosure regimes).
- The shape: `build.py` (template → listing pin → pub views → figures →
  ten kinds → version folder → six gates → `built` row → stop); the frozen
  site's path rule; the listing pin (`pin.py`, the watcher's listings);
  the read layer (pub only, the template is the whole of what may be
  read); the figures; the kinds (home, parties, electorates ×5, pickers,
  subject party ×30 and person ×1,261, electorate ×82, donor ×623,
  size-bands ×27, cite ×1,300; board-member "not held"); suppression
  machinery; the preview on 8430 (never 8300/8301); `check.py`; the
  proposed `qv4-site-build` job and `qv4-site-preview` unit.
- Real build from listing 2026-10-20T0620: 3,332 files, 8 MB, 0.9 s, every
  gate green; 46 party-years of disclosures equal the Commission's table
  to the cent; 86 of 125 front-page party-year figures equal the frozen
  home file (the rest are the lanes' carded differences and Part A rows
  not yet read). 52 tests, each gate shown failing on a planted defect.
- Cards: the suppressed-names list has no owner; what the rebuilt site
  cannot show yet; a party-year with two returns is chosen by nobody.
  Queue: the window, 2017 or 2019 (default 2017). Lesson: "none chosen"
  is a property of the year.

## Half-done

- Nothing.

## Next

1. Integrator: merge `site-1`; add `qv4-site-build` to the catalogue from
   `jobs-proposed.toml`; the preview unit when the installer reaches
   `products/*/units/`; register `products.published_site.check.check` on
   the board; point `QV4_SITE_OUT` at `<live>/site`.
2. The comparison session (4.5) reads `<live>/site/v/<stamp>/` beside the
   frozen folder, figure by figure.
3. When candidate-returns publishes: electorate money; when links' rules
   are read: donations made on person pages; financial statements on party
   pages.
