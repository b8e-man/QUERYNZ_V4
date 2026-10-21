# The construction template counts a lapsed intention to remove as a failure
kind: finding
state: open
use-case: 7 construction and phoenix detection
session: property-1
opened: 2026-10-21

`products/templates/07-construction/rules.py`, `_failures` (main and
session/construction-2 alike): a Gazette company notice of kind "removal"
makes its company failed, dated from the notice, whatever the company's
status. An intention to remove that lapsed (the company filed, or someone
objected) leaves the company Registered, and the notice reads as a failure
set beside the person's going companies. Seen on template 12's checkpoint
(2026-10-21): BROOKS HOMES LIMITED, intentions published 2008 and 2011,
Registered in the August 2026 file; the property template's first version
copied the idea and two of its twelve subjects' results rested on such
notices (lesson `an-intention-to-remove-is-not-a-removal`).

A fix in the construction folder: count a removal only where the
company's `_ending` is not "going", as `products/templates/12-property/
rules.py` `_failures` does, with a fixture of a Registered company carrying
an old intention and a mutant for it.
