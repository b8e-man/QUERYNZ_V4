An officer check that reads only rows carrying `through` never sees a trust board's trustees (reached via the board's own charity, with no `through`): read the entity's own charity's officer rows by name, or the check clears.
area: subject reports, products/templates, healthcare, charities, officer checks, clears
paid-for-by: 2026-10-21, fix-templates-1, step 5.2

The healthcare template's `disqualified-officer` collected marks from an
organisation start as "rows with `through`": the officers reach stamps every
row it reaches from a followed director with the director's ref. A
charitable trust board lists no officer on its companies register row; its
trustees come from the Charities Register, beneath the charity the walk
joins to the board by business number (`walk.NUMBER_JOINS`). Those officer
rows are confirmed rows on an entity, via the charity, with no `through`.
So the day the template read the register, a trustee the register marks
disqualified would have been invisible to the officer branch; only the
"no officers listed" gap kept the flag from clearing. The fix reads the
entity's own charity's officer rows directly (`_own_charity_officers`) and
fires on them before the `through` branch, with a fixture and a mutant
("the entity's own charity's trustees are not read") that fail without it.

The same shape in the other templates' charity flags: a clear needs the
name looked up. The walk looks a person's name up in `pub.charity_officers`
only from the views in `walk.NAME_JOIN_FROM`; a shareholder start is not
among them, so each template's charity clear checks the start's view
(`NAME_LOOKED_UP`) as well as `walk.skipped` and the omitted count.
