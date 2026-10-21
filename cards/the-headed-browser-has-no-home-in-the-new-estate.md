# The headed browser has no home in the new estate
kind: finding
state: open
use-case: 15
session: diaries-1
opened: 2026-10-21

The plan (reuse.md) moves the old headed-browser code "as it is, behind a
new contract"; it has not moved. The v4 virtual environment has no
Playwright, and the safety hook rightly refuses running the live old
folder's interpreter, so diaries-1 ran its probe under the reference
copy's (/home/user/qnz3-ref/.venv), which a live job must not depend on.
Wanted: Playwright in the v4 environment and a gated headed opener in
support/fetchgate (permission from fg.check, the gate's pacing, a refusal
recognised by the wall's own page and never reloaded). The diaries lane's
browser.py is a draft of it. Also: fg.looks_challenged marks "incapsula"
in a page's first 4 KB as a challenge, and every real Beehive page
carries that script (lesson a-real-page-can-carry-the-challenge-script).
Owner: the integrator or a fix session on support/fetchgate.
