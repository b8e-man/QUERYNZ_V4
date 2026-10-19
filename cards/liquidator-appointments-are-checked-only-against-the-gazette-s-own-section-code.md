# Liquidator appointments are checked only against the Gazette's own section code
kind: finding
state: open
use-case: 1
session: gazette
opened: 2026-10-20

`check.py` holds the liquidator profile to the Gazette's classification:
every notice it files under `al` (43,587) is taken by the profile, read or
set aside with a reason. That proves coverage, not correctness. The figure
from outside is the Companies Office register: 4,403 company rows carry the
number the notice prints, and every company row has a name and an
appointment date that the register's liquidation records should agree
with. The companies lane is not merged yet. When it is: join number →
name (and name → number, alive on the appointment date) and report the
share that agree; fail on a printed number whose register name differs.

What the reading leaves, measured on all of it (no sample): 109 notices
with no company the reader can find (set aside); 594 signatures that are
not a list of names (catch-log lines; those notices name no liquidator);
71 title parts with no legal suffix; 90 list rows or lists not cut;
10,199 company rows with no appointer the notice states; 3,536 with no
date, mostly notices printing several dates the reader cannot place.
