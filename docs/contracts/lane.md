# Contract: the lane

**Fixes:** what a register lane is made of. **Test:** `support/lane/tests/`
(`check_folder` runs on every lane the merge gate sees, from step 1b).
**Taken from:** `data-layer/gazette_register` and `courts_register`, which
had nearly this shape, and the lanes that did not.

One lane, one source, one folder `registers/<lane>/`, one schema of the
same name and its `_private` twin. A lane has:

| Piece | What |
| --- | --- |
| `spec.md` | Five lines: `owns:`, `reads:`, `publishes:`, `outside check:`, `jobs:` |
| `capture.py` | How its documents arrive: one of the three cases of 1.10, through the fetch gate and the landing wrapper only |
| `read.py` | The reading, from the document profile, through the reader contract; can re-read one document or one day's file alone |
| `tables.sql` | Every table it owns, in its own schema or its private twin, defined here and nowhere else |
| `publish.sql` | Its published views in `pub`: the only thing a later module reads |
| `check.py` | Its one figure checked against the outside world (the source's own total, count or list) |
| `sample.list` | The documents and keys its tests need: sha256 hashes and `key:` lines only, never bytes or rows |
| `pane.md` | How its rows appear in a pane of the board |
| `tests/` | Its tests, run by the fast tier on the sample |

At run time a lane keeps a catch log (one line for every item it could not
process: the stage and the reason) and a run record; items in equal items
out plus items set aside. It wipes and reloads its own tables inside one
transaction, never from the shell. A reading that fails its own check
publishes nothing. A lane never imports another lane.
