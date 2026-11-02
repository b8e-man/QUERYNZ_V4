A test that reads a file by path proves nothing once the file has moved: assert the path exists before asserting what it says.
area: tests, legal-positions, registers, sanctions

Why: `registers/sanctions` tested "the real position authorises nothing" against `registers/sanctions/position/`, the draft folder. The integrator moved the position to `docs/legal/positions/`, so the test read a folder that no longer existed, found no `authorised:` line, and stayed green whatever the real position said; its two live tests pointed the gate at the same empty folder and would have been refused. Found on 2 November 2026 when ruling 132 added the `authorised:` lines and the old test still passed.

How to apply: read the folder the code itself reads (here `support.fetchgate.POSITIONS_DIR`), assert the file exists first, and add one negative case against a folder that is truly empty, so "absent" and "says no" are told apart.
