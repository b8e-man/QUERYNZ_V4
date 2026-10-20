# An applied old decision is never withdrawn when the old estate withdraws it
kind: finding
state: open
use-case: 1
session: founding
opened: 2026-10-21

`fix-links` (21 October) copies the old ledgers incrementally and applies
each donation's latest non-withdrawn decision whatever its weights version.
What it does not do, and says so: an old decision already applied as a link
or a hold stays applied if the old estate later withdraws it
(`withdrawn_at`) or re-judges the same donation to a different company or
person. The copy re-reads `withdrawn_at` on the rows held, so the fact is
in `links.old_decisions`; the application step only adds. Recommended: at
each build, a decision whose old row is now withdrawn, or superseded by a
later decision on the same donation, is unapplied and the link or hold it
made falls back to the rules' own reading, with the change counted in
`links.check`. The lane's fix.
