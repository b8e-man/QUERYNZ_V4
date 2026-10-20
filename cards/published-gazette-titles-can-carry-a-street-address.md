# Published Gazette notice titles can carry a street address
kind: finding
state: open
use-case: -
session: gazette-5
opened: 2026-10-20

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
