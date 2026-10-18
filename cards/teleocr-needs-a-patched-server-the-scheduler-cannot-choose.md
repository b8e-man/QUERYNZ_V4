# TeleOCR needs a patched model server, and the scheduler cannot choose a server per profile
kind: blocker
state: open
use-case: Follow the Money (step 3, the page-reader trial: the TeleOCR arm)
session: trial
opened: 2026-10-18

TeleOCR's own GGUF (rleo/TeleOCR-GGUF) says on its card it is not for
llama.cpp (a Qwen3-style decoder with head_dim 128 behind a Qwen2.5-VL
config). The conversion the model's authors credit, under its former name
(nandraj/NaviDC-OCR-GGUF), loads only on a server patched in
`src/models/qwen2vl.cpp` (its PATCHES.md, four guarded hunks); upstream has
not taken the fix (checked 18 October). The trial built that server beside
the others with the installer's own build function:
`<live>/llama/built-teleocr/` (VERSION.json and PATCH.json), from a clone
under the session's scratch folder; the estate's `built` and `copy` servers
and the frozen product's build are untouched (hard limit 23).

The scheduler picks one server for every profile (`profiles.toml [server]
binary`, "copy" or "built"); a profile cannot name its own. So the two
TeleOCR job types require the program `qv4-llama-server-teleocr`, which the
probe does not list, and are never claimed: honest, and stuck.

Blocks: the TeleOCR arm of 3.6 (the top-scoring published challenger).
Nothing else.

Fix (a fix session on `support/scheduler`, about twenty lines): a profile
may carry `binary = "<name>"`; `probe.PROGRAMS` learns
`qv4-llama-server-teleocr` at `<live>/llama/built-teleocr/llama-server`;
`cards.server_binary` prefers the profile's own name when it has one. Then
the two TeleOCR profiles say `binary = "qv4-llama-server-teleocr"` and the
`requires` line is dropped. The patch is guarded, so the alternative,
making the patched build the estate's `built` server, is possible but
changes what every profile loads; the decision queue carries it with the
default "beside, never over".
