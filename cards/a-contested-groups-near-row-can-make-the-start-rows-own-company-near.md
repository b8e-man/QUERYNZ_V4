# In a contested group, the start row's own company can be graded near
kind: finding
state: open
use-case: subject report (5.1); 3 banking; every template
session: banking-1
opened: 2026-10-20

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
