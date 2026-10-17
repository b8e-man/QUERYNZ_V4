Import a piece of support, a lane or a product by its full dotted name (`import support.alarm`, `from support.alarm import send`), never `from support import alarm`: the one-way import test reads the second form as reaching into the whole root and refuses it.
area: tests, one-way import, support, lanes
paid-for-by: 2026-10-18, founding session 2, step 1.6

`tests/test_imports_one_way.py` judges a `from X import y` by the module
`X` alone, so `from support import alarm` written inside `support/alarm/`'s
own tests looks like `support.alarm` importing `support`, which is another
piece. The full name says which piece is meant and passes.

How to apply: inside any module under `support/`, `registers/` or
`products/`, and in its tests, name the piece in the import. A failure of
the one-way test that names your own piece is this, not a real crossing.
