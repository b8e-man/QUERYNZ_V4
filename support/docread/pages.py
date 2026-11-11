"""The text layer, per page (plan 1.10; the reader contract's "text layer
first"). Carried from the old `ec_pageread.read`: `pdftotext -layout` one
page at a time, and a page with fewer than PAGE_TEXT_MIN characters is an
image page, because the EC's returns are MIXED (printed form pages carry
text, the schedule pages behind them are photographs) and a file-level
threshold mislabels real returns in both directions.

    text_pages(data)        1-based page → text layer, '' for a raster
    text_pages_cached(data, sha256)   the same, kept by the file's hash (a nightly reader extracts once)
    thin_pages(texts)       the pages whose text layer is unusable
    read_from(data)         'text' | 'pixels' | 'mixed' for the document
"""
import gzip
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor

from support.docread.pagereader import is_pdf, page_total

PAGE_TEXT_MIN = 80       # per page: below this the page is an image
SCAN_CHARS = 200         # per document: below this there is no text layer at all
WORKERS = 4              # pages read side by side


def page_text(data: bytes, page: int) -> str:
    """One page's text layer with layout kept, or '' (a raster, or no layer)."""
    if not is_pdf(data):
        return ""
    try:
        r = subprocess.run(["pdftotext", "-q", "-layout", "-f", str(page), "-l", str(page), "-", "-"],
                           input=data, capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.decode("utf-8", "replace") if r.returncode == 0 else ""


def text_pages(data: bytes, max_pages: int = None, workers: int = WORKERS) -> dict:
    """Every page's text layer. The pages are read side by side (pdftotext
    is a separate process per page, so threads buy real time: a 22-page
    return falls from about 0.9 s to 0.25 s with four)."""
    n = page_total(data)
    if max_pages:
        n = min(n, max_pages)
    numbers = list(range(1, n + 1))
    if workers > 1 and n > 1:
        with ThreadPoolExecutor(max_workers=min(workers, n)) as pool:
            texts = list(pool.map(lambda p: page_text(data, p), numbers))
    else:
        texts = [page_text(data, p) for p in numbers]
    return dict(zip(numbers, texts))


#: the text layer of a stored file, by its sha256: a document is its bytes, so its layer never changes while the tool
#: does not. Regenerable (deleted freely); opened by key only, never scanned. Shared by both boxes over the work folder.
TEXT_CACHE = os.environ.get("QV4_TEXTLAYER") or "/home/user/querynzv4-work/live/textlayer"
_TOOL = []


def tool() -> str:
    """The extractor named with its version: a new poppler is a new text layer, so the cache misses and fills again."""
    if not _TOOL:
        try:
            r = subprocess.run(["pdftotext", "-v"], capture_output=True, timeout=30)
            v = (r.stderr or r.stdout).decode("utf-8", "replace").splitlines()[0].strip()
        except (OSError, subprocess.SubprocessError, IndexError):
            v = "pdftotext ?"
        _TOOL.append(f"{v} -q -layout, per page")
    return _TOOL[0]


def _cache_path(sha256: str, cache: str) -> str:
    return os.path.join(cache, sha256[:2], sha256 + ".json.gz")


def text_pages_cached(data: bytes, sha256: str, cache: str = None, workers: int = WORKERS) -> dict:
    """text_pages(data) for the stored file `sha256`, kept in the cache by its hash: a load that reads a corpus every
    night extracts each file once (the courts load, 11 November 2026: 70% of its time was pdftotext on files it had
    read the night before). A cache entry of another tool, another file or unreadable is ignored and written again.
    The hash is checked against the bytes when the entry is written, so an entry is never filed under the wrong
    file."""
    cache = cache or TEXT_CACHE
    if not sha256 or len(sha256) != 64:
        return text_pages(data, workers=workers)
    path = _cache_path(sha256, cache)
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            held = json.load(f)
        if held.get("sha256") == sha256 and held.get("tool") == tool():
            return {int(p): t for p, t in held["pages"].items()}
    except (OSError, ValueError, KeyError, AttributeError, EOFError):
        pass
    texts = text_pages(data, workers=workers)
    if hashlib.sha256(data).hexdigest() != sha256:
        return texts                                   # not the file it was named for: read, never filed
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = f"{path}.{os.getpid()}.tmp"
        with gzip.open(tmp, "wt", encoding="utf-8") as f:
            json.dump({"sha256": sha256, "tool": tool(), "pages": {str(p): t for p, t in texts.items()}}, f,
                      ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass                                           # a cache that cannot be written costs time, never a reading
    return texts


def is_thin(text: str) -> bool:
    return len((text or "").strip()) < PAGE_TEXT_MIN


def thin_pages(texts: dict) -> list:
    return sorted(p for p, t in texts.items() if is_thin(t))


def read_from(data: bytes, texts: dict = None) -> str:
    """How this document must be read: 'text' (every page has a layer),
    'pixels' (none has), or 'mixed' (the thin pages need the page reader)."""
    texts = texts if texts is not None else text_pages(data)
    if not texts:
        return "pixels"
    thin = thin_pages(texts)
    if not thin:
        return "text"
    if len(thin) == len(texts) or sum(len(t.strip()) for t in texts.values()) < SCAN_CHARS:
        return "pixels"
    return "mixed"
