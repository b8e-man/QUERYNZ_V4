# support.security

Track H (docs/plan/track-h.md): the credential inventory, the leak finder and the rotation runbooks. Built by security-1, 22 October 2026.

- `shapes.py`: what a secret looks like on a line; shared by the finder and the inventory test.
- `inventory.py`: `python -m support.security.inventory` prints two verdicts: every name the new estate reads is in `docs/security/inventory.md`; nothing under `docs/security/` is value-shaped.
- `leaks.py`: `python -m support.security.leaks --git REPO --path FILE_OR_DIR --journal --journal-user [--live NAME,NAME] [--show-context] [--report FILE]` prints places and kinds, never a value; liveness is a hash comparison against values handed in one variable at a time.
- `tests/`: fast tier; the finder's fixture is generated, never committed.

Never reads the credential directory. Stdlib only.
