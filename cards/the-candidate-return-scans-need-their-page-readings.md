# 713 candidate returns wait on a page reading of their declaration page
kind: finding
state: open
use-case: 1
session: candidate-returns
opened: 2026-10-20

The candidate-returns lane reads a return's totals from its declaration
page (nearly always page 1). Of the 1,105 in-window returns (2020, 2022
Tauranga, 2023), 713 are set aside at stage `read`
(`candidate_returns.set_aside`): 574 are images with no stored GLM-OCR
reading, 139 carry a scanner's own OCR layer that lost the form's heading
(`ELECTTON`, or nothing legible). Step 3's trial stored readings for 24 of
them; the lane replays those (18 rows) and never calls a model.

The job, outside the lane's fence (the scheduler's catalogue,
`support/scheduler/jobs.toml`, installed by the integrator):

1. `qv4-candidate-returns-read`, one piece per return, on a worker holding
   the GLM-OCR profile (prompt "OCR", 200 or 300 dots; every page as an
   image, since a scanner's OCR layer is itself a reading). Pages 1 and 2
   first: about 1,430 pages, some two hours at the trial's 5.4 s a page.
   Store each under profile `ec-candidate-return-scan` (the lane's
   `read.stored_page` takes any GLM-OCR reading with the prompt "OCR"
   under a candidate-return profile).
2. Then the Part A pages of the returns whose declaration shows donations
   (Part A on image pages is not read from pixels yet: a second card's
   work, `the-candidate-return-part-a-sets-aside`).

The set-aside line names each return's hash and pages. Rebuild the lane
after the readings land (`python -m registers.candidate_returns.replay
run` measures it first).
