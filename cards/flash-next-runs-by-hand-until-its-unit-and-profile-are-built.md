# Flash-Next runs by hand until its unit and profile are built
kind: finding
state: open
use-case: -
session: integrator-9d788fb
opened: 2026-10-29

Ruling 121 (29 October): Qwen3.8-Flash-Next, served by Radiance on both of
node2's cards, replaces Qwen3.6 as the estate's text-reader and review
model; the frozen product's chat model left the carve-out and stays
stopped (Arthur disables it).

What runs now, started by hand by the integrator at 17:17: the container
`radiance-fn` (image docker.io/stilldeadcode/radiance:latest, model
/home/user/models/radiance/qwen3.8-next-flash-fp8-iq4r-moe.rad), port 8060
on the loopback, model name `qwen4exp`, 16 slots, 16k context bound, 4096
batched tokens, adaptive draft window, tip-only checkpoints, the n-gram
table read from disk, a 10 GiB pinned pool a rank, 2.5 GiB of card left
for the frozen OCR server. Host RSS 28 GB. Swaps 514 and 515 record it.
The start script and the measurements are in the integrator's scratch,
`/home/user/querynzv4-work/scratch/integrator-9d788fb/exp/`.

What is missing, and what closes the card: a unit `qv4-radiance` installed
by `support.installer` like every qv4- unit, so a reboot brings the server
back (today a reboot loses it); a profile `flash-next` in
`support/scheduler/profiles.toml` naming Radiance as its own server, both
cards as one profile, memory and load figures measured; text-reader and
review repointed to it and the Qwen3.6 profiles retired; the model client
accepting Radiance's answers and refusing another model name. The brief
`flash-next-1` in docs/briefs/next.md says how. Ruling 79 still holds bulk
reading until node1 returns, so the build proves itself and queues no
reading. Never the frozen product's units or program (limits 19 to 23).
