# support/installer — the installer (plan step 2.11)

`python -m support.installer plan|apply|check|build [--units] [--box HOST] [--repo PATH] [--only UNIT ...] [--ref REF]`.
It installs only `qv4-` units and never changes or removes any other job;
a timer whose job is timetabled in the catalogue is superseded (step 2.12);
it copies the model server beside the old build, never over it, and
`build` makes the estate's own from source beside the copy; it copies
credential files box to box directly, never through the repository.
`spec.md` is the five-line spec.
