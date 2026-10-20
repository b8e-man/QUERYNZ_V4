# The walk does not follow a company holder up the ownership chain
kind: finding
state: open
use-case: subject report (5.1); 13 beneficial ownership and AML
session: ownership-1
opened: 2026-10-21

Use case 13 asks who stands at the top of a company's chain of holdings.
From a company the walk lists its holders of record (the `roles` bucket)
and stops: a holder that is a company is never resolved to its own row in
pub.companies, so its holders and directors, and theirs, are not reached.
Two halves. The companies lane's: `holder_nzbn` is empty on all 1.58 M
rows (`a-company-holder-carries-no-business-number`), so there is nothing
to join on; a name lookup is not enough (two FLETCHER RESIDENTIAL LIMITED
rows). The report lane's, once a key exists: a chain setting a template
can ask for (`chain_depth`, default 0; template 13 wants 4, the old chain
page's ceiling), walking holder → company → its holders, each hop an item
with its own dates, its depth and the hop it came through, a cut-off chain
marked as going on (old lesson L708), a company met twice listed once
(a cycle), and the shares filed on each hop carried as filed, never as a
computed fraction (see `the-shareholders-view-carries-no-parcel-or-issued-shares`).
The ownership template blocks `holding-chain` past the first hop and
`ultimate-holders` always; its `CHAIN_REACHED = 1` moves when this lands.
Seen at the ownership checkpoint (template 13, `checkpoint.list`).
