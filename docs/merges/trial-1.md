# trial-1: step 3's page set, keys, readers, scoring and models; the catalogue patch; GLM-OCR through the scheduler
branch: session/trial (ee261d2)
session: trial (session 1)
raised: 2026-10-18
claims: support/trials (pageset, keys, readers, piece, rows, score, catalogue, models, queue, teleocr_server; tests, 25 green under the venv), support/trials/scheduler (the profile and job-type additions), docs/trials/page-readers.md, docs/status/trial.md, three cards, three queue items, three lessons

What it claims: the page set (255 distinct documents, 2,698 pages, text
or scan per page, every kind and shape, the four named cases whole) and
the keys (declaration totals, the Commission's table with its two wrong
2020 figures marked, the frozen site, the old page-read records, the
confirmed gold tier read at scoring time) keyed by hash; each reader with
its own documented prompt and settings; the scoring of 3.7 as pure
functions; the five models on /mnt/hdd2/qv4-models, hash-verified; a
patched server for TeleOCR beside the others; GLM-OCR run through the
scheduler on 115 declaration pages (queue 52: the swap, the pieces and
the peak memory in the ledgers).

## For the integrator, outside the trial's fence

1. Apply trial-1-catalogue.patch (beside this file) to
   support/scheduler/jobs.toml and profiles.toml: ten profiles and twelve
   job types, all qv4-trial-*, priorities 6 and 40 to 50; git apply
   --check is clean against main at c140f97. Then python -m
   support.scheduler check (green on the merged copy here: python -m
   support.trials.catalogue check). The worker on main then holds the
   trial's job types and the next trial session queues the passes
   (python -m support.trials.queue one).
2. Not in this request: the scheduler change that lets a profile name
   its own server binary (for TeleOCR's patched build). The card
   teleocr-needs-a-patched-server-the-scheduler-cannot-choose gives the
   shape (about twenty lines in registry, probe and cards); it is a fix
   session on support/scheduler, not the trial's to write.
3. The fast tier from a working copy has no pytest (system python); the
   trial's tests were run with the main checkout's venv on the path.
4. Nothing to install; no unit changes. The patched server is at
   <live>/llama/built-teleocr/ and no profile uses it until (2) lands.

## Result (integrator, founding session, 18 October 22:50)

Merged into main as d1add6d (integration branch integrate/trial-1 from
session/trial at ee261d2, gate green). Out of the trial's fence, done here:

- the catalogue patch applied line for line to support/scheduler/jobs.toml
  and profiles.toml (277 lines; `python -m support.scheduler check`: 30 job
  types, 13 profiles, green). The worker reloaded the catalogue on its own
  clock at 22:45 ("catalogue reloaded: 30 job types, 13 profiles"); no
  restart was needed.
- support/trials/keys.py imported registers.party_returns.declaration, which
  the one-way import rule forbids a support module (fast tier red). The
  declaration reader is pure functions on the standard library, so it now
  lives in support/docread/declaration.py; registers/party_returns/declaration.py
  re-exports it, and the lane and its tests read as before.
- support/installer/tests/test_installer.py asserted the four founding
  profiles were the only ones, and that no planned weight existed under
  /nowhere; the trial's profiles name the second disk by absolute path.
  Widened to: every catalogue profile is planned, the founding four among
  them, founding weights relative to the models folder.
- support/trials/tests/test_readers_catalogue.py asserted the patch still
  carried the additions; once applied the patch is empty. The test now reads
  the merged catalogue and allows an empty patch.
- two lesson rules were over the index's 240-character limit; shortened.
- board, lessons index and decisions queue regenerated.

Then, on the brief's word to keep things running tonight: queued pass one: qv4-trial-read-glm-ocr #54, 255 pieces at 200 dpi. Card 1,
scratch tables, the path the session proved on 115 pages. Scoring and the
challengers wait for the next trial session (`python -m support.trials.queue`
status/two/rows).

Not done: (2) the scheduler change for a per-profile server binary (card
teleocr-needs-a-patched-server-the-scheduler-cannot-choose) is a fix session
on support/scheduler; (3) and (4) noted, nothing to install.
