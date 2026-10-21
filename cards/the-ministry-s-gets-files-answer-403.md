# The ministry's GETS open-data files answer 403 to the estate, so the award notices cannot be refreshed
kind: blocker
state: open
use-case: 10 tender and award intelligence; 9 government procurement integrity
session: tenders-1
opened: 2026-10-21

Step 6's done-line asks that the award notices be "refreshed on a
schedule". On 21 October 2026 `www.mbie.govt.nz` answered HTTP 403 to both
files asked through the fetch gate with the estate's own User-Agent
(`GETS-product-categories.csv`, and the lower-case
`gets-product-categories-historic.csv`), and `www.data.govt.nz` answered
with an Incapsula challenge page; the government data catalogue
(`catalogue.data.govt.nz`) answered and lists the same four MBIE URLs, so
there is no second copy. Each is a failed read (hard limit 6): logged in
`tenders.capture_set_aside`, not retried, not got around. The old estate got
the files by sending a browser-like User-Agent; we do not.

The lane holds and reads the old estate's raw files of 14 August 2026
(report date 15 July 2026, 29,874 notices). Its refresh job asks nothing
until 2 November (80 days after that acquisition), then tries once a night
with a week's rest after any block, so it will go red each week while the
block stands.

What closes it: the ministry lets the estate's User-Agent read the files.
That is a letter to an outside body, so Arthur's: the publisher's contact
in the catalogue is `opendata@mbie.govt.nz`. The same letter can ask for the
supplier file's business numbers as text (card
`the-gets-supplier-file-loses-its-business-numbers`). Until then the
done-line's "refreshed on a schedule" stays open; the rest of it ("read,
checked against the source's own count") is met.

22 October 2026: the letter sent by Arthur to opendata@mbie.govt.nz (`docs/letters/mbie-gets-files-request.md`); it also asks for the supplier file's business numbers as text. Waits on the ministry's answer.
