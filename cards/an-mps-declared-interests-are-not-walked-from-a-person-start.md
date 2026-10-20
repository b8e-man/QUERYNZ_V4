# An MP's declared interests are never listed on a report about the MP
kind: finding
state: open
use-case: subject report (5.1); 8 recruitment board screen
session: recruitment
opened: 2026-10-20

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
