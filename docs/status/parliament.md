# parliament: where it stands

Sessions parliament-1, fix-registers-parliament-1 (Opus), 27 and 28 October
2026, node2. Rulings 96, 101, 102. On main since 27 October.

## Done

- `registers/parliament`: `written_questions`, `api_items`, `wayback_pages`,
  `files`, `set_aside`, `address_flags`, `street_scan`, read by hash from
  the version the pull landed last; three pub views carrying the text whole
  with `<column>_names_address` beside it (ruling 102); the check per corpus
  against the MCP's `corpora` and `measure`.
- Fix 1c (merged 132aa81): parliament.nz's archived refusal pages are set
  aside as `blocked` (hard limit 6).
- Fix 1d (merge request `fix-registers-parliament-1d`): the check took
  1 min 55 s on the live tables and the board gives 120 s. The second
  street pattern now runs over every row at the load, after the views
  refresh (`load.stamp_scan`, 99 s), into `street_scan`; the check holds
  that stamp to each view (same rows, same load, nothing found) and re-scans
  a fixed sample of 5,000 rows per view. Live: 36 s.

## Next

- At the merge the staging load writes the first `street_scan`; until then
  the check is red with "the load's whole scan has no line for the view".
- Check red on wayback: 10,067 documents taken, 8,836 records read (the
  pull grew; the next load reads them).
