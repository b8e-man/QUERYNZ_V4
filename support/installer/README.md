# support/installer — the installer (plan step 2.11)

`python -m support.installer plan|apply|check [--units] [--box HOST] [--repo PATH] [--only UNIT ...]`.
It installs only `qv4-` units and never changes or removes any other job;
it copies the model server beside the old build, never over it; it copies
credential files box to box directly, never through the repository.
`spec.md` is the five-line spec.
