`systemctl --user enable --now` leaves a running unit on its old definition after its file changes, so a swap that brings up the incoming unit uses `restart`, not `start`.
area: installer, units, standing servers, releases
paid-for-by: 26 November 2026, qv4-radiance renamed from Flash-Next to the 27B proxy while Flash-Next ran under it on node1

The installer reloads and enables; it never restarts a standing server (deliberately: a release must not cut every reader's requests). So the first scheduled swap would have stopped qv4-radiance-flash (not running), waited for :8060 to go quiet (it never does: the old Flash container still runs under qv4-radiance's old definition) and then "started" qv4-radiance, already active, reading back the wrong model for ever. The swap now restarts the incoming unit, and each box is cut over by hand once, its swaps recorded.
