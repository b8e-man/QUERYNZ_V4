# Forty-one party returns have image pages with no stored page reading
kind: finding
state: open
use-case: 1
session: party-returns
opened: 2026-10-19
updated: 2026-10-19 (party-returns session 2)

The lane reads a scanned return by replaying the page reader's stored
readings (GLM-OCR Q8_0, 300 dots, `OCR`) and never calls the model. 41 of
the 152 landed returns are set aside at stage `read`: 23 for 2017 and
2018, 18 filed for 2024 and 2025 (and one in 2026's folder). The 2025
returns are why National, Labour, NZ First, Green, Opportunity,
Conservative, Te Pāti Māori and Vision NZ 2025 do not yet equal the frozen
site. Four of the held amendments are among them (NZ First 2024's two,
New Conservatives 2024, Conservative 2025).

**Rows 95 and 96 did not fill them.** Both ran `qv4-reread-pages`
(`support/scheduler/reread.py`), which reads ONE page per document (the
page a published row names, else page 1) and stores it: 41 readings of
page 1, under `ec-party-return-text@3`, 7 s each. The lane finds those,
and still needs 645 more image pages (2 to 34 per return) before it can
read a declaration's year from the loans page or any schedule.

Fix: a page-reader job that reads every image page of a document
(`pages.thin_pages`), under the `PAGE_SETTINGS` stamp the lane replays
(`registers/party_returns/read.py`), the 18 in-window returns first. That
is a change to the re-read job type or a new one: the scheduler's module,
not this lane. The lane picks the readings up on its next load with no
change. `party_returns.set_aside` lists the hashes (`stage = 'read'`).
