# The name reading keeps a judge's title as a given name, drops a surname particle, and keeps a post-nominal without a comma
kind: finding
state: open
use-case: links (4.2); the board's search
session: links-2
opened: 2026-10-20

Three shapes `keys.names.person_name` reads wrongly, found reading the
Gazette appointments and the House's rows into `pub.names` (links-2):

- "The Honourable Justice Geoffrey John Venning" reads as given "The",
  middle "Honourable Justice Geoffrey John": 436 of 3,155 Gazette
  appointees start with "The", 7 with "Justice" or "Judge". The honorific
  list has "hon" and "honourable" but not "the honourable", "justice",
  "judge", "his honour", "her honour".
- "van Velden, Brooke" reads as family "Velden", middle "van": a particle
  ("van", "de", "te", "van der") is split off a family name. Every register
  reads it the same way, so the rows still meet, but the printed family
  name is wrong on the board.
- "Robert Smellie QC" keeps "qc" in the key: the post-nominal rule needs a
  comma. The old stale key for that donor is gone (party-returns-5 fixed
  the row; the links re-read it), but the new key is "qc robert smellie".

For keys/ (a fix session): add the titles to the honorific list, keep a
particle with the family name, and strip a bare post-nominal. The links
read every name through this one function and need no change.
