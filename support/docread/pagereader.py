"""The page reader client: a page image to text through the local page
reader (GLM-OCR), via the model client (plan 1.10; carried from the old
`ingestion/ec_pageread/vision_ocr.py`, now behind the model client so the
call names its model and refuses a wrong one).

    page_total(data)              how many pages: a raster is one
    render(data, page, tmpdir)    one page as a PNG (pdftoppm), or the raster itself
    read_page(png)                the page's text from the model
    ocr_pages(data, pages)        1-based pages → text; a failed page is omitted

Every call is stamped by the model client; the reader contract's store
(`support.reader`) keys the result by the document's hash and the model.
"""
import base64
import glob
import os
import re
import subprocess
import tempfile

from support import modelclient

DPI = int(os.environ.get("PAGE_IMAGE_DPI", "200"))
TIMEOUT = float(os.environ.get("PAGE_IMAGE_TIMEOUT", "300"))
URL = os.environ.get("PAGE_IMAGE_URL") or "http://127.0.0.1:8032/v1/chat/completions"
MODEL = os.environ.get("PAGE_IMAGE_MODEL") or "glm-ocr"
LANE = "page-reader"
PROMPT = "OCR"
PDF_MAGIC = b"%PDF"
_MAGIC = ((b"\xff\xd8", ".jpg", "image/jpeg"), (b"\x89PNG", ".png", "image/png"),
          (b"II*\x00", ".tif", "image/tiff"), (b"MM\x00*", ".tif", "image/tiff"),
          (b"RIFF", ".webp", "image/webp"), (b"GIF8", ".gif", "image/gif"))


def _ext(data: bytes) -> str:
    for magic, ext, _ in _MAGIC:
        if data.startswith(magic):
            return ext
    return ".bin"


def media_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    for _, e, mt in _MAGIC:
        if e == ext:
            return mt
    return "image/png"


def is_pdf(data: bytes) -> bool:
    return data.startswith(PDF_MAGIC)


def page_total(data: bytes) -> int:
    """A raster has exactly one page; a PDF asks pdfinfo."""
    if not is_pdf(data):
        return 1
    try:
        info = subprocess.run(["pdfinfo", "-"], input=data, capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.SubprocessError):
        return 0
    m = re.search(r"Pages:\s+(\d+)", info)
    return int(m.group(1)) if m else 0


def render(data: bytes, page: int, tmpdir: str, dpi: int = None):
    """One page as an image file, or None."""
    if not is_pdf(data):
        if page != 1:
            return None
        out = os.path.join(tmpdir, f"pg1{_ext(data)}")
        with open(out, "wb") as f:
            f.write(data)
        return out
    prefix = os.path.join(tmpdir, f"pg{page}")
    try:
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi or DPI), "-f", str(page), "-l", str(page), "-", prefix],
                       input=data, capture_output=True, timeout=600)
    except (OSError, subprocess.SubprocessError):
        return None
    imgs = sorted(glob.glob(prefix + "*.png"))
    return imgs[0] if imgs else None


def read_page(png: str, *, url: str = None, model: str = None, post=None) -> str:
    """One page image through the page reader. Raises; the caller decides."""
    with open(png, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    out = modelclient.chat(url or URL, lane=LANE, model=model or MODEL,
                           messages=[{"role": "user", "content": [
                               {"type": "text", "text": PROMPT},
                               {"type": "image_url", "image_url": {"url": f"data:{media_type(png)};base64,{b64}"}}]}],
                           extra={"max_tokens": 8000, "temperature": 0.0}, timeout=TIMEOUT, post=post)
    return (out["choices"][0]["message"]["content"] or "").strip()


def ocr_pages(data: bytes, pages: list, dpi: int = None, lang: str = "eng", *, post=None, report: dict = None,
              url: str = None, model: str = None) -> dict:
    """1-based pages → text. A page the reader fails on is omitted, never
    returned empty, so the caller still sees it as unread."""
    out, failed = {}, []
    with tempfile.TemporaryDirectory() as td:
        for p in pages:
            png = render(data, p, td, dpi)
            if not png:
                failed.append(p)
                continue
            try:
                txt = read_page(png, url=url, model=model, post=post)
            except Exception:  # noqa: BLE001 — recorded by the client; the page is unread
                failed.append(p)
                continue
            if txt.strip():
                out[p] = txt
            else:
                failed.append(p)
    if report is not None:
        report.update(reader=model or MODEL, read=sorted(out), failed=failed)
    return out
