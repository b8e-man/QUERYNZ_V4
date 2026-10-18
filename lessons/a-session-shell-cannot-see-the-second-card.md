A process started from a session's shell cannot see card 1 (the sandbox exposes one render node), so anything that uses a graphics card runs as a qv4- unit under systemd, placed by the installer, never as the session's background process.
area: scheduler, sessions, graphics cards, units

Seen 18 October 2026: the worker started with nohup loaded every profile on the processor; the same worker as `qv4-worker@node2.service` loaded them on card 1 in 2 to 4 seconds. The sandbox bypass flag is refused by the classifier, which is right: the unit is the production shape anyway. A unit placed from a working copy before the merge names that working copy and must be replaced by the merge's installer run.
