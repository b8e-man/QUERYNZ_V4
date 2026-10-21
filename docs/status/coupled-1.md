# coupled-1: where it stands

**Date:** 2026-10-21. **Weight:** build (scope `links/`, `keys/`). **Merge request:** `coupled-1` (raised).

## Done (ruling 73)

- `keys.names.joint_parts`: the people of a coupled filed name. `is_joint_name`
  takes the published forms it missed and asks the director register's given
  names ("Bread and Roses Auction" is no longer a couple).
- `links.rows`: a coupled donation row stays one row (filed name, name key,
  kind person) and is read as no one person; a part row per person, ref
  `<donor ref>#<n>`, `part_of` the donor. `links.build`: `coupled-name@1`,
  near, donor to each part. `check.py` and the old-ledger mapping skip parts.
- Scratch `scratch_coupled_1` (+ `_pub`), real published tables: 37 coupled
  rows (party returns 14, disclosures 20, candidate returns 3), 74 parts,
  74 `coupled-name@1` links. Parts reached by the other rules: `full-name@1`
  27 (14 parts), `name-only@1` 58 (54 parts), `member-and-party-donor@1` 1.
  `check.py` 29 of 29 green. Fast tier green for links and keys.

## Next

1. Integrator: reload `links` (`tables.sql` adds `rows.part_of`; `publish.sql`
   adds `pub.names.part_of`); add `joint_parts` to `docs/contracts/keys.md` item 5;
   drop `scratch_coupled_1` and `scratch_coupled_1_pub`.
2. Card `a-coupled-donor-s-part-ref-is-found-through-pub-names`: report, board
   and site resolve a part ref through `pub.names`.
3. Unjudged and left as filed: "Drury & Alo, Rod & Rebecca" (pairing not
   stated), initials ("M and J Patterson"), "Mr & Mrs" forms.
