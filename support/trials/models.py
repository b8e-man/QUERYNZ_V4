"""THE TRIAL'S MODEL FILES (plan step 3.1): which files each page reader is
served from, fetched once, politely, onto the second hard disk, and checked
against the hub's own hash before anything is served from them.

    python -m support.trials.models plan            what is wanted, what is held
    python -m support.trials.models fetch [NAME …]  download what is missing, one file at a time
    python -m support.trials.models check           every wanted file present and hash-equal

Each model is in the form the estate's model server loads (GGUF weights plus
the image projector) at two levels of compression where the hub offers
them, because community conversions vary (3.1: keep the smaller only if it
reads the same). The files go under `/mnt/hdd2/qv4-models/<model>/`
(`QV4_TRIAL_MODELS`), never under the frozen product's models folder, and
the scheduler's profiles name them by absolute path. A download is one
connection, resumed where it stopped, with the estate's own user agent; a
file is kept only when its sha256 equals the hub's LFS hash, and every
fetch is one line in `downloads.jsonl` beside the files.

What is NOT fetched: GLM-OCR's Q8_0 and its projector, which the box holds
already under the models folder and which are hash-equal to the hub's
(checked 18 October 2026). TeleOCR's own GGUF (rleo/TeleOCR-GGUF) is not
loadable by the model server (its card says so); the conversion served
here is the community one its authors credit, under the model's former
name NaviDC-OCR, which needs a patched server build (its PATCHES.md;
upstream has not taken the fix as of 18 October 2026).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.environ.get("QV4_TRIAL_MODELS") or "/mnt/hdd2/qv4-models"
HUB = "https://huggingface.co"
AGENT = "querynzv4-trial/1 (+arthur@betelgeuse.co.nz)"
LEDGER = "downloads.jsonl"
CHUNK = 1 << 20

# model → repo, family (for the second reader), licence, and the files wanted:
# (hub file name, role, level). The first weights/mmproj pair at each level
# is what a profile serves; the order is smallest model first so the small
# ones can be tried while the large one is still arriving.
MODELS: dict[str, dict] = {
    "ovisocr2": {
        "repo": "Abiray/OvisOCR2-GGUF", "family": "qwen (3.5 base, small)", "licence": "Apache-2.0",
        "upstream": "ATH-MaaS/OvisOCR2",
        "files": [("OvisOCR2-Q8_0.gguf", "weights", "q8_0"), ("mmproj-F16.gguf", "mmproj", "f16"),
                  ("OvisOCR2-F16.gguf", "weights", "f16"), ("mmproj-F32.gguf", "mmproj", "f32")],
    },
    "teleocr": {
        "repo": "nandraj/NaviDC-OCR-GGUF", "family": "qwen (2.5 base)", "licence": "Apache-2.0",
        "upstream": "bbsai/TeleOCR (formerly StarDoc-AI/NaviDC-OCR)",
        "files": [("NaviDC-OCR-Q8_0.gguf", "weights", "q8_0"), ("NaviDC-OCR-mmproj-q8_0.gguf", "mmproj", "q8_0"),
                  ("NaviDC-OCR-f16.gguf", "weights", "f16"), ("NaviDC-OCR-mmproj-f16.gguf", "mmproj", "f16"),
                  ("PATCHES.md", "notes", "")],
        "needs": "a patched model server (PATCHES.md in the conversion)",
    },
    "glm-ocr": {
        "repo": "ggml-org/GLM-OCR-GGUF", "family": "zhipu (GLM-V)", "licence": "MIT",
        "upstream": "zai-org/GLM-OCR",
        "files": [("GLM-OCR-f16.gguf", "weights", "f16"), ("mmproj-GLM-OCR-Q8_0.gguf", "mmproj", "q8_0")],
        "held": {"q8_0": ["/home/user/models/vision-glm-ocr/GLM-OCR-Q8_0.gguf",
                          "/home/user/models/vision-glm-ocr/mmproj-GLM-OCR-Q8_0.gguf"]},
    },
    "chandra-ocr-2": {
        "repo": "mradermacher/chandra-ocr-2-GGUF", "family": "qwen (3.5 base, mid)",
        "licence": "modified OpenRAIL-M: free under US$2M revenue or funding; no use competing with the maker's service",
        "upstream": "datalab-to/chandra-ocr-2 (the conversion names the mirror vasu-12/chandra-ocr-2 as its base)",
        "files": [("chandra-ocr-2.Q8_0.gguf", "weights", "q8_0"), ("chandra-ocr-2.mmproj-f16.gguf", "mmproj", "f16"),
                  ("chandra-ocr-2.Q4_K_M.gguf", "weights", "q4_k_m"), ("chandra-ocr-2.mmproj-Q8_0.gguf", "mmproj", "q8_0")],
    },
    "infinity-parser2-pro": {
        "repo": "glebkudr/Infinity-Parser2-Pro-Q8-GGUF", "family": "qwen (3.5 base, large, 35B mixture)",
        "licence": "Apache-2.0", "upstream": "infly/Infinity-Parser2-Pro",
        "files": [("Infinity-Parser2-Pro-Q8_0.gguf", "weights", "q8_0"),
                  ("Infinity-Parser2-Pro-mmproj-bf16.gguf", "mmproj", "bf16"),
                  ("Infinity-Parser2-Pro-mmproj-Q8_0.gguf", "mmproj", "q8_0")],
        "notes": "the only conversion on the hub is Q8_0 (36.9 GB), larger than one card; the second level is made here with the quantiser",
    },
}


def _get(url: str, timeout: float = 60, headers: dict = None) -> urllib.request.addinfourl:
    req = urllib.request.Request(url, headers={"User-Agent": AGENT, **(headers or {})})
    return urllib.request.urlopen(req, timeout=timeout)


def hub_tree(repo: str) -> dict[str, dict]:
    """hub file name → {size, sha256} from the hub's tree listing (the LFS
    object id is the file's sha256)."""
    with _get(f"{HUB}/api/models/{repo}/tree/main") as r:
        rows = json.loads(r.read())
    out = {}
    for s in rows:
        lfs = s.get("lfs") or {}
        out[s["path"]] = {"size": int(s.get("size") or 0), "sha256": lfs.get("oid")}
    return out


def local_path(model: str, hub_file: str, root: str = None) -> str:
    return os.path.join(root or ROOT, model, hub_file)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def ledger_path(root: str = None) -> str:
    return os.path.join(root or ROOT, LEDGER)


def ledger(root: str = None) -> list[dict]:
    out = []
    try:
        with open(ledger_path(root), encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return out


def verified(root: str = None) -> dict[str, str]:
    """path → sha256 of every file the ledger says arrived whole."""
    return {r["path"]: r["sha256"] for r in ledger(root) if r.get("ok") and r.get("sha256")}


def plan(root: str = None, trees: dict = None) -> list[dict]:
    """Every wanted file: where it goes, how big, held or not."""
    root = root or ROOT
    out = []
    seen = verified(root)
    for model, m in MODELS.items():
        tree = (trees or {}).get(m["repo"])
        if tree is None:
            try:
                tree = hub_tree(m["repo"])
            except (urllib.error.URLError, OSError, ValueError) as e:
                tree = {}
                out.append({"model": model, "repo": m["repo"], "error": f"hub listing failed: {type(e).__name__}: {e}"})
        for hub_file, role, level in m["files"]:
            p = local_path(model, hub_file, root)
            want = tree.get(hub_file) or {}
            have = os.path.exists(p)
            out.append({"model": model, "repo": m["repo"], "file": hub_file, "role": role, "level": level, "path": p,
                        "size": want.get("size"), "sha256": want.get("sha256"), "on_hub": bool(want),
                        "held": have, "held_bytes": os.path.getsize(p) if have else 0,
                        "verified": seen.get(p) is not None and seen.get(p) == want.get("sha256")})
        for level, paths in (m.get("held") or {}).items():
            for p in paths:
                out.append({"model": model, "repo": m["repo"], "file": os.path.basename(p), "role": "held", "level": level,
                            "path": p, "size": os.path.getsize(p) if os.path.exists(p) else None, "sha256": None,
                            "on_hub": None, "held": os.path.exists(p), "held_bytes": os.path.getsize(p) if os.path.exists(p) else 0,
                            "verified": os.path.exists(p)})
    return out


def _record(root: str, line: dict) -> None:
    os.makedirs(root, exist_ok=True)
    line = {"at": dt.datetime.now().astimezone().isoformat(timespec="seconds"), **line}
    with open(ledger_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def fetch_file(repo: str, hub_file: str, dest: str, *, size: int = None, sha256: str = None, root: str = None,
               log=print, retries: int = 4) -> dict:
    """One file, one connection at a time, resumed from a partial copy,
    verified by hash before it is named. Returns the ledger line."""
    root = root or ROOT
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    url = f"{HUB}/{repo}/resolve/main/{hub_file}"
    t0 = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if size and have >= size:
            break
        headers = {"Range": f"bytes={have}-"} if have else {}
        try:
            with _get(url, timeout=120, headers=headers) as r:
                if have and r.status != 206:      # the server ignored the range: start again
                    have = 0
                mode = "ab" if have else "wb"
                with open(part, mode) as f:
                    while True:
                        chunk = r.read(CHUNK)
                        if not chunk:
                            break
                        f.write(chunk)
            break
        except (urllib.error.URLError, OSError) as e:
            if attempt >= retries:
                line = {"repo": repo, "file": hub_file, "path": dest, "ok": False, "why": f"{type(e).__name__}: {e}",
                        "seconds": round(time.monotonic() - t0, 1)}
                _record(root, line)
                log(f"models: {hub_file}: FAILED after {attempt} attempts: {e}")
                return line
            wait = 30 * attempt
            log(f"models: {hub_file}: {type(e).__name__}; retrying in {wait}s")
            time.sleep(wait)
    got = os.path.getsize(part)
    digest = sha256_file(part)
    ok = (sha256 is None or digest == sha256) and (size is None or got == size)
    if ok:
        os.replace(part, dest)
    line = {"repo": repo, "file": hub_file, "path": dest, "bytes": got, "sha256": digest, "hub_sha256": sha256,
            "ok": ok, "seconds": round(time.monotonic() - t0, 1), "attempts": attempt,
            "why": None if ok else "hash or size differs from the hub's; the partial file is kept as .part"}
    _record(root, line)
    log(f"models: {hub_file}: {got / 1e9:.2f} GB in {line['seconds']} s, {'verified' if ok else 'NOT verified'}")
    return line


def fetch(names: list[str] = None, root: str = None, log=print) -> list[dict]:
    root = root or ROOT
    rows = plan(root)
    out = []
    for r in rows:
        if r.get("error") or r.get("role") == "held":
            continue
        if names and r["model"] not in names:
            continue
        if r["verified"]:
            continue
        if not r["on_hub"]:
            log(f"models: {r['model']}: {r['file']} is not on the hub; skipped")
            out.append({**r, "ok": False, "why": "not on the hub"})
            continue
        if r["held"] and r["sha256"] and sha256_file(r["path"]) == r["sha256"]:
            _record(root, {"repo": r["repo"], "file": r["file"], "path": r["path"], "bytes": r["held_bytes"],
                           "sha256": r["sha256"], "hub_sha256": r["sha256"], "ok": True, "seconds": 0, "attempts": 0,
                           "why": "already held; verified now"})
            continue
        out.append(fetch_file(r["repo"], r["file"], r["path"], size=r["size"], sha256=r["sha256"], root=root, log=log))
    return out


QUANTISER = "/home/user/llama.cpp/build/bin/llama-quantize"      # the old build's tool, read-only: a program, not the frozen servers
INFINITY_Q8 = os.path.join(ROOT, "infinity-parser2-pro", "Infinity-Parser2-Pro-Q8_0.gguf")
INFINITY_Q4 = os.path.join(ROOT, "infinity-parser2-pro", "Infinity-Parser2-Pro-Q4_K_M.gguf")


def make_q4(src: str = INFINITY_Q8, dst: str = INFINITY_Q4, kind: str = "Q4_K_M", root: str = None, log=print,
            quantiser: str = QUANTISER) -> dict:
    """The second compression level for the 35B model, made here with the
    quantiser from the hub's Q8_0 (the only conversion on the hub, larger
    than one card). Twice-quantised: recorded as such in the ledger."""
    import subprocess
    root = root or ROOT
    if os.path.exists(dst):
        return {"path": dst, "ok": True, "why": "already made"}
    if not os.path.exists(src):
        return {"path": dst, "ok": False, "why": f"source missing: {src}"}
    t0 = time.monotonic()
    log(f"models: quantising {os.path.basename(src)} → {kind} (from Q8_0; twice-quantised)")
    r = subprocess.run([quantiser, src, dst + ".part", kind], capture_output=True, text=True, timeout=14400)
    ok = r.returncode == 0 and os.path.exists(dst + ".part")
    if ok:
        os.replace(dst + ".part", dst)
    line = {"repo": "made here", "file": os.path.basename(dst), "path": dst, "bytes": os.path.getsize(dst) if ok else 0,
            "sha256": sha256_file(dst) if ok else None, "hub_sha256": None, "ok": ok, "seconds": round(time.monotonic() - t0, 1),
            "attempts": 1, "why": f"made with {quantiser} from {os.path.basename(src)} ({kind}, twice-quantised)" if ok
            else f"quantiser failed: {(r.stderr or r.stdout)[-300:]}"}
    _record(root, line)
    log(f"models: {os.path.basename(dst)}: {'made' if ok else 'FAILED'} in {line['seconds']} s")
    return line


def check(root: str = None) -> list[str]:
    """Problems, as plain lines; empty when every wanted file is held and verified."""
    out = []
    for r in plan(root):
        if r.get("error"):
            out.append(r["error"])
        elif not r["held"]:
            out.append(f"{r['model']}: {r['file']} missing")
        elif r["role"] != "held" and not r["verified"]:
            out.append(f"{r['model']}: {r['file']} held but not verified against the hub")
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "plan"
    if cmd == "plan":
        for r in plan():
            if r.get("error"):
                print(r["error"])
                continue
            state = "verified" if r["verified"] else ("held" if r["held"] else "wanted")
            size = f"{(r['size'] or 0) / 1e9:.2f} GB" if r.get("size") else "?"
            print(f"{r['model']:22s} {r['role']:8s} {r['level']:7s} {size:>9s} {state:9s} {r['path']}")
        return 0
    if cmd == "fetch":
        bad = [r for r in fetch(argv[1:] or None) if not r.get("ok")]
        return 1 if bad else 0
    if cmd == "quantise":
        return 0 if make_q4().get("ok") else 1
    if cmd == "check":
        probs = check()
        print("\n".join(probs) if probs else "models: every wanted file is held and verified")
        return 1 if probs else 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
