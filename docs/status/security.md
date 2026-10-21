# security: where track H stands

Session security-1, 22 October 2026, node2, working copy `security`
(scope `support/security/`, `docs/security/`). H.1 to H.3 built; no
rotation, no credential file touched, no job touched.

## Done

- H.1 `docs/security/inventory.md`: every secret by name, file, variable,
  reader, reach, last rotation and wave; node2 walked by verdict-only
  presence checks. `support/security/inventory.py` and its test fail when
  the new estate's code or a `qv4-` unit reads a name the inventory
  lacks, or when a value-shaped string sits under `docs/security/`.
- H.2 `docs/security/leaks.md`: places only. `support/security/leaks.py`
  (git history, files, folders, journals; liveness by hash from one named
  variable; redacted output) with a generated-fixture test. Found: the
  deploy token in use today (6 places, old project's transcript), the
  application role's password (309 places; it is a string the old
  repository carries), the alarm address (1 place). Journals, Claude
  settings files: nothing.
- H.3 `docs/security/runbooks/`: thirteen pages, one per secret in waves
  one and two, plus node1's admin rights.
- Lesson filed; three cards; two queue items (`sync.env`/`x.env`; the
  alarm file outside the credential directory).

## Half-done

- Nothing. Node1 was not walked (card); the serving role's file lines
  could not be confirmed in this session's mode (inventory says so).

## Next

- Arthur: the wave-one runbooks, the deploy token first; the queue items.
- security-2, after wave one: H.4's proofs and dates; the wave-two
  rehearsal (scratch instances, the sitting's script); H.6 (one named
  file, one function, the no-secret-in-a-job-file test).
- Rerun the leak search after each rotation; the matching places should
  read "differs".
