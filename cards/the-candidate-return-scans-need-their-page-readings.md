# 668 candidate returns wait on a page reading
kind: finding
state: open
use-case: 1
session: candidate-returns
opened: 2026-10-20

The candidate-returns lane reads a return's totals from its declaration
page (nearly always page 1) and its donors from Part A (page 2 on). Ruling
62 (20 October): the page reader is not queued in bulk until the build is
done; the 60 scans read that day are the sample. Measured 21 October
(candidate-returns-2) on all 1,105 in-window returns, the queue is one
command:

    python -m registers.candidate_returns.replay run RUN.json
    python -m registers.candidate_returns.replay rereads RUN.json

which prints one line per return (hash, election, stage, pages): 668
returns, 6,287 pages. 658 at stage `read` (no stored reading of the
declaration page; every page listed), 7 at `declaration` (a scanner's own
text layer the lane will not stand on without its printed total; page 1),
3 at `part-a` (Part A on image pages with no stored reading; pages 2 to 4).

The job, outside the lane's fence (the scheduler's catalogue, installed by
the integrator when the build is done): GLM-OCR, prompt "OCR", every page
as an image (a scanner's layer is itself a reading), stored under profile
`ec-candidate-return-scan` (`read.stored_page` takes any GLM-OCR reading
with the prompt "OCR" under a candidate-return profile). Pages 1 and 2
first if the time is short. Then rebuild, measuring with `replay run` and
`compare` first.
