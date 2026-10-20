# A Crown entity holding shares is not flagged as the Crown
kind: finding
state: open
use-case: subject report (5.1); 3 banking; 13
session: banking-1
opened: 2026-10-20

HEALTH NEW ZEALAND holds 90 shares in ENABLE NEW ZEALAND LIMITED
(checkpoint subject 11, `societies:societies/9429000000000/officer/d323a6097c2c`);
the walk's `CROWN` pattern reads words such as "the Crown" or "Minister
of", so a Crown entity named by its own name is a company holder, not a
hub, and a board shared through it reads as more than it is. For the report
lane: a list of Crown entities (the Public Service Commission publishes
one), or a column the companies lane derives, read instead of a name
pattern.
