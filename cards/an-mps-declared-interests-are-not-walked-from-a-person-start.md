# An MP's declared interests are never listed on a report about the MP
kind: finding
state: closed
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20
closed: 2026-10-20

A report started on an MP's interests return
(`mp_interests:036fa950…/p10/l12`, view `mp_interest_returns`, kind person)
lists none of its declaration lines (`pub.mp_interests`): the walk expands
the register's own rows (`walk.ROLES_ON`) only for entities, and a person
start is never one. Started from the MP's seat (`house:ge-2023/…`), the
interests return is reached only by a name-only near link, so it lands with
the namesakes. A board screen of a sitting or past MP shows no declared
interest. For the report lane: expand a person start's own child rows
(`mp_interest_returns` → `mp_interests`). For links: whether a member row
and its interests return join by a supporting identifier.

Closed 2026-10-20 by the report session (report-2), the report lane's half.
A row of the subject's own group whose view has child rows (an interests
return and its declarations) is now its own entity in the walk, expanded
as the subject's own filing; a return merely reached (a donor's, a
namesake's by a name-only link) stays context, as the lesson of report-1
holds (`walk.EXPAND_ONLY_AS_START` now tests membership of the group, not
identity with the start). The card's own row `mp_interests:036fa950…/p10/l12`
lists its five declarations, confirmed, the withheld one as withheld.
Measured: `python -m products.report check` builds a report on the latest
interests return with declarations, taken from the tables at run time, and
fails unless its declarations are listed as confirmed through it. The links
half stands: from the seat (`house:…`) the return is still reached by a
name-only near link, so a board screen started from a seat shows the
declarations as a namesake's until a rule joins a member row to its return;
that is a card for links, raised by the report session beside this one
(`a-member-row-and-its-interests-return-join-only-by-name`).
