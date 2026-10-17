"""The text layer, per page (plan 1.10; the reader contract's "text layer
first"). Carried from the old `ec_pageread.read`: `pdftotext -layout` one
page at a time, and a page with fewer than PAGE_TEXT_MIN characters is an
image page, because the EC's returns are MIXED (printed form pages carry
text, the schedule pages behind them are photographs) and a file-level
threshold mislabels real returns in both directions.

    text_pages(data)        1-based page → text layer, '' for a raster
    thin_pages(texts)       the pages whose text layer is unusable
    read_from(data)         'text' | 'pixels' | 'mixed' for the document
"""
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
