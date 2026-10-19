# societies: where it stands

**Date:** 2026-10-20. **Step:** 4.1, societies, `registers/societies/`.
**Merge request:** `societies-1`.

## Done

- Export, once (20 October, 07:23 NZDT, 2 s; old read-only login,
  read-only transactions, 300 s limit, server-side cursors; the old primary,
  as node1's standby is down since 17 October): 53,597 society rows (the
  August file, with 326 vanished), 133,080 officers, 22,787 asks, pinned in
  `capture.EXPORTS`. The old officer table holds no address.
- Reading, every real row: 53,271 societies, 326 earlier states, 133,080
  officer roles (32,835 with the register's end date), 22,787 asks. Each
  part equals the old table's count; each society's officers equal its last
  ask's count (22,783), none given (3), or kept from an earlier ask (1,
  logged). Catch log: one line.
- Per-entity path proved on five pages (the party societies), through the
  gate: 51 of 51 roles keyed the same in the answer as in the export.
- Outside check green: party 18/18, hockey 189/189, tennis 430/431.
- Nightly job designed and tested (`capture.py --night`); proposed, not queued.
- Fast tier: the lane's 21 tests green.

## The four questions (NZBN API entity detail; ruling 61)

1. Open: yes, with our own free key; no lock, login or challenge.
2. Lawful copying: public registers; the register's contents are outside the
   Companies Office's CC BY 4.0 grant; the lawyer's question (card).
3. Terms: the portal's, at registration; no stated rate limit; avoid
   Wednesday 21:00 to 23:00; ETag asked for (gate card). Text not held (card).
4. Privacy and statute: names, roles, dates public; any address to
   `societies_private` only; suppressed names blanked.

## Carded

- `the-societies-capture-job-into-the-catalogue` (blocker, for the integrator).
- `the-fetch-gate-returns-no-response-headers`.
- `the-nzbn-api-terms-and-the-copying-of-register-contents`.
- `stray-societies-tables-in-the-sample-scratch-schema`.

## Next

1. The merge: position moved, floor set, job in the catalogue, real load.
2. Officers that are bodies (`roleEntity`): none met yet; read when one is.
