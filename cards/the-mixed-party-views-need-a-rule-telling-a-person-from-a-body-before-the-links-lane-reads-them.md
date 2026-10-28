# The mixed party views need a rule telling a person from a body before the links lane reads them
kind: finding
state: open
use-case: 1
session: integrator
opened: 2026-10-28

Ruling 114. Five published views name a notice's or a case's parties in one
`name` column with no first and last name split and no kind: court judgment
parties (590 rows), FMA parties (611), WorkSafe parties (668), Commerce
Commission parties (1,734) and Overseas Investment parties (2,870). The
links lane reads none of them. Its people rules key a first and last name,
its organisation rules key a body's name against a register, and a row of
these views could be either, so neither rule may take it as it stands.

Wanted: a rule that says, for one of these names, person or body, from the
name alone and the view's own columns (`named_in`, a role, a statute), with
an abstain where it cannot tell; measured on a sample of each view before
the lane reads them. A company-type word (Limited, Trust, Incorporated) is
a start and not the rule: a trading name has none, a person's name may
carry one as a surname. Until the rule is written these rows stay text on
the board, which is the honest state.

Not worked by the links fix ruling 114 launched (fix-links-3), which takes
the eight split people views and the three organisation registers.
