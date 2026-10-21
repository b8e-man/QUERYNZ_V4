A page address can carry a person's name, so sample.list keys such pages by hash and the filler reads the address from the document store.
area: sample, sample.list, personal data in git, regulator actions, keys
paid-for-by: 2026-10-21, regulators-1, step 5.3

The first sample lists of the three regulator lanes carried `key: item <list> <slug> <sha>` lines, and four of the
slugs spelled a person's name (an FMA case, two Commission entries, an FMA warning). The contract keeps personal data
out of git; the landing wrapper already records each page's address as a name of its bytes. The filler looks it up
(`registers/fma/sample.py`), and the tests address their hard cases by document hash.
