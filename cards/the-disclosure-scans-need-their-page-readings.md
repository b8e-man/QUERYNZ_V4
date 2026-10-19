# 251 scanned large-donation declarations have no page reading yet
kind: finding
state: open
use-case: 1
session: disclosures
opened: 2026-10-19

The disclosures lane checks each declaration's amount in the Commission's
table against the total printed on the scanned form (`form_check`). Of the
276 scans the table links (2023 on), 29 have a stored GLM-OCR reading (step
3's trial): 25 equal the table, none differ, 4 have no legible total. 247
rows show `no reading held`.

Two pieces, neither inside the lane's fence:

1. **The job.** `qv4-disclosures-read`, one piece per scan,
   `python -m registers.disclosures.read --scan <sha256>`, on a worker
   holding the GLM-OCR profile (prompt "OCR", 200 dpi, profile
   `ec-donation-disclosure-20k`, every page as an image: the form's text
   layer carries labels, never the typed values). About 250 scans, one to
   three pages each. Catalogue entry in `support/scheduler/jobs.toml`,
   installed by the integrator after the merge; queued once, then on the
   lane's rebuild for a scan with no reading.
2. **Two stamps for one reader.** The trial stored its readings under
   `support.trials`' settings (dpi, prompt, weights, level, temperature …);
   `support.docread.read_document` keys a page reading on `{dpi, prompt}`
   alone. So `read_document` cannot replay the trial's 46 pages, and the job
   above would read those 29 scans a second time under another key. The
   lane replays by globbing the store (`form.stored`), so nothing breaks;
   the fix belongs in `support/docread` (one settings shape for the page
   reader, or a lookup that accepts a reading made under a superset).
