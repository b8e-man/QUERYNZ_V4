# support/installer — the installer (plan step 2.11)

`python -m support.installer plan|apply|check|build|release [--units] [--box HOST] [--repo PATH] [--only UNIT ...] [--ref REF]`.
It installs only `qv4-` units and never changes or removes any other job;
a timer whose job is timetabled in the catalogue is superseded (step 2.12);
it copies the model server beside the old build, never over it, and
`build` makes the estate's own from source beside the copy; it copies
credential files box to box directly, never through the repository.
`spec.md` is the five-line spec.
`release` (release.py) creates or moves the release copy the worker runs
from, `/home/user/querynzv4-release`: one pushed commit of origin/main,
detached, never edited, with its own `.venv`; the integrator runs it after
every push.
