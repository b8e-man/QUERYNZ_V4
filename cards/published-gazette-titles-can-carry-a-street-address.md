# Published Gazette notice titles can carry a street address
kind: finding
state: closed
use-case: -
session: gazette-5
opened: 2026-10-20
closed: 2026-10-21

`pub.gazette_notices` publishes every notice's title as the Gazette prints
it. Some titles name a property by its street address: measured on the full
load of 20 October 2026, 1,642 titles under `ln` (land taken, roads,
reserves), 24 under `al`, 21 `ds`, 7 `ar`, 3 `go`, 1 `md` and 1 `ot` match
"<number> <Name> Street|Road|Avenue|…". Whether a given one is a home
cannot be told from the title, and hard limit 15 says no published table
carries a home's address. gazette-5 cut the possession notices' titles
(`gn`, where the property is usually a home) before the property they name
and holds the check to it; the other sections were left as they are,
being outside its brief. Recommended: the same cut for every section,
the full title kept in the lane's own table only, and a check that no
published title carries a number followed by a street word. Next gazette
session; the `ln` notices are use case 12's when that lane is read.

Closed by gazette-6 (2026-10-21). `cut.py` cuts every published text, not
only titles, before a street address, a land description or a number the
words before it place, at the read (`read.read`, so every reader and the
sample share it); the uncut value goes to `gazette_private.uncut` only.
Measured on every notice: 1,463 titles cut (`ln` 1,434; the card's 1,642
counted a highway's number before a road, which is not a property), 71
companies as printed and 2 plaintiffs run on into an address. A company
named for an address is the register's name and is kept whole. No title
carries a vehicle's registration or a residence. `check.py` fails on any
published text the detector finds (0 on the cut load; 1,496 notices on
gazette-5's uncut load, exit 1).
