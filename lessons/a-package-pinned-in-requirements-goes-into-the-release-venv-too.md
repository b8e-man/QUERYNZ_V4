A package added to requirements.txt is installed into the release checkout's venv as part of the release; the worker runs from there, not from the main checkout.
area: releases, scheduler, venv, papers-past

Why: tantivy was pinned and installed into /home/user/querynzv4/.venv for the Papers Past index (step 8.6). The release only checked out the commit, so qv4-papers-past-index failed at 21:25 on 2 November 2026 with "No module named 'tantivy'", four hours after the ingest it waited on had begun, and the whole index slipped by three hours.

How to apply: when a release changes requirements.txt, run `/home/user/querynzv4-release/.venv/bin/python -m pip install -q -r requirements.txt` in /home/user/querynzv4-release before restarting anything, then import the new package with that venv's python.
