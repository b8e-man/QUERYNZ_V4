The old estate's requirements-factory.txt lists 18 of the 24 editable packages its live environment holds; the truth is ops/requirements-factory.lock plus the `__editable__*finder.py` files in the live venv's site-packages.
area: old estate, environment, reference copy, baseline
paid-for-by: 2026-10-18, founding session 2, step 1.2

Building the reference copy's environment from `requirements-factory.txt`
alone would have left out `registers`, `pi`, `docread`, `docreview`,
`corpus_search` and `estate-dsn`, five of which the root `conftest.py`
imports, so the old root suite would not even collect. The live venv's
`__editable__*finder.py` files name every editable package and its source
folder, and `ops/requirements-factory.lock` (a pip freeze, editables
excluded) pins the rest, model wheels included.

How to apply: when the environment of the old estate is rebuilt or measured
(step 1.3's "programs on each box"), read the lock and the finder files, not
the requirements file. The reference copy's environment was built that way
and its installed list matches the live one exactly (pip's patch version
apart).
