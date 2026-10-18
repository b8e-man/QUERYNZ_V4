"""A MODEL SERVER BUILD THAT LOADS TeleOCR (plan step 3.1: "if a model needs
a newer build of the model server, install that build beside the old one").

TeleOCR's community conversion (NaviDC-OCR-GGUF) does not load on a stock
server: its decoder has head_dim 128 behind a Qwen2.5-VL config where the
loader hardcodes the Q and output projections to n_embd, and it carries
per-head QK norms the architecture does not declare. The conversion's
PATCHES.md gives four changes to `src/models/qwen2vl.cpp`; upstream has
not taken them (checked 18 October 2026). Each is guarded, so a stock
Qwen2.5-VL file still loads on the patched build.

    python -m support.trials.teleocr_server plan     what would be done
    python -m support.trials.teleocr_server build    clone (read-only on the source), patch, build beside the others

The clone and the build tree go under the session's scratch folder; the
built server goes to `<live>/llama/built-teleocr/` through the installer's
own build function, with its VERSION.json and a PATCH.json naming the
hunks. Nothing touches `<live>/llama/built/` (the estate's server) or the
frozen product's build. The scheduler cannot yet choose a server per
profile; the trial's job types require the program
`qv4-llama-server-teleocr`, which the probe does not know, so they are
never claimed until the scheduler learns it (carded).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys

from support import installer

SCRATCH = os.environ.get("QV4_SCRATCH") or "/home/user/querynzv4-work/scratch/trial"
SRC = os.path.join(SCRATCH, "llama-teleocr", "src")
BUILD = os.path.join(SCRATCH, "llama-teleocr", "build")
BUILT = os.path.join(installer.LIVE if hasattr(installer, "LIVE") else "/home/user/querynzv4-work/live", "llama", "built-teleocr")
SOURCE_REPO = installer.OLD_LLAMA_SRC
FILE = "src/models/qwen2vl.cpp"

# (what must be there, what it becomes): the four hunks of PATCHES.md, a to d
HUNKS = [
    ("b+d: Q and output projections scale with n_head * head_dim",
     "        create_tensor_qkv(layer, i, n_embd, n_embd, n_embd_gqa, n_embd_gqa, 0);\n"
     "        layer.wo = create_tensor(tn(LLM_TENSOR_ATTN_OUT, \"weight\", i), {n_embd, n_embd}, 0);\n",
     "        create_tensor_qkv(layer, i, n_embd, n_head * n_embd_head_k, n_embd_gqa, n_embd_gqa, 0);\n"
     "        layer.wo = create_tensor(tn(LLM_TENSOR_ATTN_OUT, \"weight\", i), {n_head * n_embd_head_k, n_embd}, 0);\n"
     "        // optional QK-norm (TeleOCR / NaviDC-OCR; absent on stock Qwen2.5-VL): PATCHES.md hunk a\n"
     "        layer.attn_q_norm = create_tensor(tn(LLM_TENSOR_ATTN_Q_NORM, \"weight\", i), {n_embd_head_k}, TENSOR_NOT_REQUIRED);\n"
     "        layer.attn_k_norm = create_tensor(tn(LLM_TENSOR_ATTN_K_NORM, \"weight\", i), {n_embd_head_k}, TENSOR_NOT_REQUIRED);\n"),
    ("c: apply the QK-norm before the rope",
     "                    n_embd_head, n_head, n_head_kv, il);\n\n            Qcur = ggml_rope_multi(\n",
     "                    n_embd_head, n_head, n_head_kv, il);\n\n"
     "            if (model.layers[il].attn_q_norm) {\n"
     "                Qcur = build_norm(Qcur, model.layers[il].attn_q_norm, NULL, LLM_NORM_RMS, il);\n"
     "                cb(Qcur, \"Qcur_normed\", il);\n"
     "            }\n"
     "            if (model.layers[il].attn_k_norm) {\n"
     "                Kcur = build_norm(Kcur, model.layers[il].attn_k_norm, NULL, LLM_NORM_RMS, il);\n"
     "                cb(Kcur, \"Kcur_normed\", il);\n"
     "            }\n\n            Qcur = ggml_rope_multi(\n"),
]


def _sh(cmd, timeout=1800):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def clone(log=print) -> str:
    if not os.path.isdir(os.path.join(SRC, ".git")):
        os.makedirs(os.path.dirname(SRC), exist_ok=True)
        log(f"teleocr-server: cloning {SOURCE_REPO} (read-only) into {SRC}")
        rc, out = _sh(["git", "clone", "--quiet", SOURCE_REPO, SRC])
        if rc:
            raise RuntimeError(out[-400:])
    return SRC


def patched(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        return "Qcur_normed" in f.read()


def apply_patch(src: str = None, log=print) -> list[str]:
    src = src or SRC
    path = os.path.join(src, FILE)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if "Qcur_normed" in text:
        log("teleocr-server: already patched")
        return [h[0] for h in HUNKS]
    done = []
    for name, before, after in HUNKS:
        if text.count(before) != 1:
            raise RuntimeError(f"hunk {name!r}: the source does not carry the expected lines exactly once")
        text = text.replace(before, after)
        done.append(name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    log(f"teleocr-server: patched {FILE}: {len(done)} hunks")
    return done


def build(log=print) -> dict:
    clone(log)
    hunks = apply_patch(SRC, log)
    rec = installer.build_model_server(SOURCE_REPO, None, src_dir=SRC, build_dir=BUILD, built_dir=BUILT, log=log)
    if rec.get("action") == "build":
        with open(os.path.join(BUILT, "PATCH.json"), "w", encoding="utf-8") as f:
            json.dump({"for": "TeleOCR (nandraj/NaviDC-OCR-GGUF)", "patches": "PATCHES.md hunks a-d", "file": FILE, "hunks": hunks,
                       "beside": "the estate's own build (<live>/llama/built) and its copy; never over either",
                       "at": dt.datetime.now().astimezone().isoformat(timespec="seconds")}, f, indent=1)
    return rec


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "plan"
    if cmd == "plan":
        print(json.dumps({"source": SOURCE_REPO, "clone": SRC, "build": BUILD, "built": BUILT,
                          "cloned": os.path.isdir(os.path.join(SRC, ".git")),
                          "patched": os.path.exists(os.path.join(SRC, FILE)) and patched(os.path.join(SRC, FILE)),
                          "built_present": os.path.exists(os.path.join(BUILT, "llama-server"))}, indent=1))
        return 0
    if cmd == "build":
        rec = build()
        print(json.dumps(rec, indent=1, default=str))
        return 0 if rec.get("action") == "build" else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
