# The walk does not follow a company holder up the ownership chain
kind: finding
state: closed
use-case: subject report (5.1); 13 beneficial ownership and AML
session: ownership-1
opened: 2026-10-21
closed: 2026-10-21

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

Closed 2026-10-21 by the report session (report-3). The walk follows a
company holder of record up the chain from a company start (`walk.chain`),
to the template's `chain_depth` (0 by default; at most `LIMITS["chain"]`,
4, the old chain page's ceiling; the shape's own template asks for 2).
Each hop resolves the holder to its own register row by `holder_nzbn`
where the file carries one (confirmed), else by the exact name when one
company in the register carries it (near, "matched by name only"; the file
carries no business number for a holder, which stays the companies lane's
card). A name none or several companies carry is not followed, and the
memo says so with the count; a company met twice is listed once (a cycle,
or two paths); at the depth limit a company holder says the chain goes on;
25 holders per company and 40 companies in all are followed, the rest
counted. Every company item carries its depth, the holder row it came
through, that row's dates as the hop and the shares as filed ("holds 200
shares of record in …, as filed"); no fraction is ever computed
(`the-shareholders-view-carries-no-parcel-or-issued-shares`). Measured on
SAILPLANE SERVICES 2005 LIMITED (`companies:companies/9429034838242`):
GILCHRIST BURNS TRUSTEES LIMITED 1 up (near by name, a nominee hub), BR
LEGAL TRUSTEE COMPANY LIMITED 2 up (holder of record in 23 companies; the
chain goes on). `python -m products.report check` builds a report on a
company whose company holder's name one company carries, taken from the
tables at run time, and fails unless the holder's company is listed up the
chain, near with its reason, the shares carried and the depth stated. The
ownership template sets `chain_depth = 4`, names `chain` in its sections'
sources and moves `CHAIN_REACHED` (a fix in its folder).
