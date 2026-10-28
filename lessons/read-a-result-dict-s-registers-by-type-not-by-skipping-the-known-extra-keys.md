Read the registers of `search.search`'s answer by type (`isinstance(hits, list)`), never by skipping the extra keys you know of (`not in ("held", "hidden")`): one new key, `tabs`, broke the outside check's field and mode arms at once.
area: board, search, checks
paid-for-by: board-9, 28 October 2026

Why: board-9 (ruling 108) added `tabs` to the dict `search.search` returns, beside `held` and `hidden`. Two arms of `check.py` and one test in `tests/test_real.py` read every register by excluding `held` and `hidden` by name; the third key was iterated as if it were a register's list, and the check stopped on a TypeError before any of its other items ran. The server and the panes already filtered by type and were unaffected.

How to apply: when you read a dict that mixes data entries with a few metadata keys, filter by the data's type or by the catalogue's own list of names (`cat.REGISTERS`), and when you add a metadata key to such a dict, grep for every `not in ("held"` and `!= "held"` before you run anything; add the key only when the caller asked for it, so the old callers see the old shape.
