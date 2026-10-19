An empty list or dict passed to mean "none of these" must be tested with `is None`, never with `or`: `(given or ALL)` turns "copy no databases" into "copy every database".
area: off-site copy, backups, any function with a default set to act on
paid-for-by: 2026-10-19, offsite session 2, track B

A test of the tree copy passed `databases={}` so it would touch no
database. `Run.run` read `(databases or P.DATABASES)`, so the empty dict
fell through to all four real databases: the test began reading the press
graph and the registers through the old read login and sealing them into
pytest's temporary folder under the test passphrase, five times (the fast
tier and four hand runs) before a hang showed it. The copies sat in /tmp,
outside this session's fence, so it could not remove them. A default that
means "everything" needs `X if given is None else given`, and a test that
means "nothing" should fail loudly if anything is touched.
