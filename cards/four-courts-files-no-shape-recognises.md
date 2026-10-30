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
