# The gazette lane's pane spec says nothing about its company notices, practitioners, bankruptcies and appointments
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-20

Plan 4.9: each lane says in its `pane.md` how its rows appear in a pane,
so a new table reaches the board with no change to the board. Gazette-3
published four new views (`pub.gazette_company_notices`,
`gazette_practitioners`, `gazette_bankruptcies`, `gazette_appointments`)
and left `registers/gazette/pane.md` at the three paragraphs of
gazette-1 and -2. The integrator wrote the board's catalogue entries from
the views' columns and the merge request's description instead (no
address column exists in any of the four; an annulled person's names are
already null in the view). The lane's next session adds the four
paragraphs and checks the catalogue against them.
