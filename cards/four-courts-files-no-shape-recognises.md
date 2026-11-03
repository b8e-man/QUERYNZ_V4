# Four courts files no shape recognises
kind: finding
state: open
use-case: 2
session: courts-2
opened: 2026-10-30

Of the 5,611 records, 5,597 are recognised by shape and 13 have no file
(the pull caught them). The remaining 4 landed files match no profile: an
Employment Court hearing schedule, a summary of a court's engagement, a
coroner's finding, and one more sheet with neither a court line, a
citation, numbered paragraphs nor a release header. Each is set aside at
`recognise` with its reason and its hash, and stays a `documents` row with
outcome "set aside". A fifth is a courtsofnz page without a case's
headings. None is a judgment; a profile for any of them waits until the
corpus holds more than one. Accept onto the limits page if the count stays
at four after the next pulls.

3 November 2026 (ruling 140, tranche 1): the Māori Land Court's and Māori Appellate Court's judgments are a shape no
profile has. Their court line is in title case ("In the Māori Appellate Court of New Zealand", which `read.COURT`, upper
case only, misses), they cite by minute book ("[2024] Māori Appellate Court MB 84", "2025 Māori Appellate Court MB 142")
and head the decision "Reserved Judgment of the Court" beside "Nohoanga" (the sitting). Measured on 8 files of the JDO
trial: 3 own rows (2 taken for counsel's submissions, 1 set aside) and 5 the MCP already held (4 set aside, 1 taken for
submissions). A profile `courts-maori-court-judgment` with those markers and a caption reading of the minute-book
citation is owed before JDO's walk reaches those courts (they come last: about 455 decisions) and before the decisions
finder's 2,650 (tranche 2).
