# site: where it stands

**Date:** 2026-10-20. **Step:** 4.4, the published-site shape and the Follow
the Money template, `products/published_site/` and `products/templates/ftm/`.
**Merge request:** `site-1` (not yet raised).

## Done

- Tranche 1 (d1f6fea): the template `products/templates/ftm/ftm.json`
  (22 pub views, ten sections, the frozen site's settings: window 2017,
  races 2020/2023/2026, seven parties, the $15,000 line); the path rule
  (the frozen site's slug+FNV, pinned to its file names); the listing pin;
  the read layer (pub only, the template is the whole of what may be
  read); the shared figures; home, parties, party subject pages, donor
  pages, search index; the version folder and manifest; the preview on
  8430.
- Tranche 2: pickers, size bands, cites (1,300); suppression machinery
  (`redact.py`, list from `pub.suppressed_names` when it exists); six
  gates (snapshot, addresses, suppressed, donor fold, the Commission's
  table re-summed by SQL, the before-and-after compare with
  `--allow-drop`); each shown failing on a planted defect. Real build:
  1,984 files, 0.7 s, all gates green; 46 party-years of disclosures equal
  the Commission's table to the cent.

## Half-done

- Nothing.

## Next

1. Tranche 3: electorates, electorate pages, person pages, board-member
   kind (not held), the outside check (`check.py`), the proposed job,
   spec, cards, lesson, merge request `site-1`.
