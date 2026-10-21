# In a contested group, the start row's own company can be graded near
kind: finding
state: closed
use-case: subject report (5.1); 3 banking; every template
session: banking-1
opened: 2026-10-20
closed: 2026-10-21

Started from a shareholder row in a contested group
(`companies:companies/9429052657764/shareholder/e5a9ab7635dc`, checkpoint
subject 7), the company that row sits on (SAVAGE MOTORS LIMITED, in
liquidation) and its two Gazette notices are graded near, so the banking
flags say "a namesake's companies, not the person's until confirmed" of the
subject's own company. Likely cause, unverified: `walk.walk` appends each
member row's entity in the group's ref order and keeps the first copy; a
near member on the same company comes first and the subject's own
(confirmed) copy is dropped as a duplicate. For the report lane: the start
row's own entity is confirmed whatever other member reaches it first.

Closed 2026-10-21 by the report session (report-3). The cause was as the
card guessed: the walk appended each member's entity in the group's ref
order and kept the first copy. Now the start row is walked first and,
where two members reach one entity, a confirmed copy is kept over a near
one. The card's row (`companies:companies/9429052657764/shareholder/e5a9ab7635dc`,
a contested group of 4) now lists SAVAGE MOTORS LIMITED and its two Gazette
notices confirmed. `python -m products.report check` takes the first
shareholder row in a contested group, from the tables at run time, and
fails unless the company it sits on is confirmed.
