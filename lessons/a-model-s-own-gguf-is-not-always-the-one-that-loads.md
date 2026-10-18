A model's own GGUF is not always the one that loads: read the conversion's card, because TeleOCR's says "not for llama.cpp", the loadable one sits under the model's former name, and it needs a server patched in a shared library.
area: models, the model server, the trial, the installer
paid-for-by: 2026-10-18, trial session, step 3.1

Three traps in one model. (1) `rleo/TeleOCR-GGUF` is a custom-runtime
file; `nandraj/NaviDC-OCR-GGUF` (credited by the model's authors) is the
llama.cpp one. (2) It loads only with four guarded hunks in
`src/models/qwen2vl.cpp` (head_dim 128 ≠ n_embd/n_head; optional QK
norms), which upstream had not taken on 18 October. (3) The installer's
VERSION.json hashes `llama-server`, and that binary is byte-identical
after the patch: the model code is in `libllama.so`. A build record for a
patched server must hash the library (or carry PATCH.json, as
`<live>/llama/built-teleocr/` does), or two different servers look the
same.
