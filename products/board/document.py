"""The originating document (ruling 86 (4)): `/doc/<sha256>` serves a
captured document's bytes from the document store, read only, whole as
captured, with its content type, so a row's "source" link opens what it
cites (a PDF at its page, `#page=<n>`).

Ruling 88 decides which documents open: every one the store holds, whole,
whatever its source, the addresses it prints included. The board listens on
the local network only and is Arthur's own instrument (hard limits 13 and
15, the limit's own exception); it still publishes no table and no export,
and a suppressed row or withheld text offers no link (hard limit 16, in
panes.source_link). A withdrawn document answers 404 and its row says so.

The handler refuses anything but 64 hex characters, reads only
`<root>/<aa>/<sha256>` (the landing wrapper's own layout) after resolving it
inside the store root, checks the bytes hash to the name before sending
them, and never lists the store. The root is `QV4_DOCS`, else the landing
wrapper's (`/mnt/hdd2/qv4-docs`). Nothing is written."""
from __future__ import annotations

import hashlib
import os
import re

from support.docstore import landing

SHA = re.compile(r"[0-9a-f]{64}")
NOT_HELD = "document not held here"
SERVED, ABSENT = "served", "not held"

#: a document's content type, by its kind in `docs.documents` and, where the kind leaves it open, its name or first bytes
TYPES = {"pdf": "application/pdf", "web-page": "text/html; charset=utf-8", "text": "text/plain; charset=utf-8",
         "csv": "text/csv; charset=utf-8"}
BY_EXTENSION = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xls": "application/vnd.ms-excel",
                ".ods": "application/vnd.oasis.opendocument.spreadsheet", ".json": "application/json", ".jsonl": "application/x-ndjson",
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".tif": "image/tiff",
                ".tiff": "image/tiff", ".webp": "image/webp", ".gz": "application/gzip",
                ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".txt": "text/plain; charset=utf-8",
                ".csv": "text/csv; charset=utf-8", ".pdf": "application/pdf", ".html": "text/html; charset=utf-8",
                ".htm": "text/html; charset=utf-8"}
MAGIC = ((b"%PDF", "application/pdf"), (b"\x89PNG", "image/png"), (b"\xff\xd8\xff", "image/jpeg"), (b"GIF8", "image/gif"),
         (b"\x1f\x8b", "application/gzip"))
#: a captured page is someone else's markup: it runs nothing and fetches nothing on the board's address
HEADERS = (("X-Content-Type-Options", "nosniff"), ("Cache-Control", "private, max-age=3600"),
           ("Content-Security-Policy", "sandbox; default-src 'none'; img-src data:; style-src 'unsafe-inline'"),
           ("Referrer-Policy", "no-referrer"))


def root() -> str:
    return os.environ.get("QV4_DOCS") or landing.ROOT


def content_type(kind: str, names=(), head: bytes = b"") -> str:
    """As stored: the kind the landing wrapper recorded; for a spreadsheet,
    an image or 'other', the extension of a name it arrived under, else its
    first bytes (JSON, a PDF, a picture), else bytes."""
    if kind in TYPES:
        return TYPES[kind]
    for n in names or ():
        path = re.sub(r"[?#].*$", "", str(n)).lower()
        ext = os.path.splitext(path)[1]
        if ext in BY_EXTENSION:
            return BY_EXTENSION[ext]
        if "wt=json" in str(n).lower():                       # a search interface's answer, asked for as JSON
            return "application/json"
    for magic, t in MAGIC:
        if head.startswith(magic):
            return t
    if head.lstrip()[:1] in (b"{", b"["):
        return "application/json"
    if kind == "spreadsheet":
        return "application/vnd.ms-excel"
    return "application/octet-stream"


UNREADABLE = ("the store's record cannot be read here: support.docstore has no documents_of yet "
              "(the patch board-4-docstore-read.patch), so nothing is opened")


def records(conn, shas) -> dict:
    """{sha: {'kind', 'source', 'withdrawn'}} through the store's own reader
    (support.docstore.landing.documents_of; a product never queries `docs`,
    the one-way test). None when the store offers no such reader: every
    document then stays closed."""
    reader = getattr(landing, "documents_of", None)
    return reader(shas, conn) if reader else None


def statuses(conn, shas) -> dict:
    """{sha: {'state': served | not held, 'kind', 'source', 'why'}}
    for the documents rows cite, in one read of the store's records."""
    want = sorted({s for s in shas if s and SHA.fullmatch(str(s))})
    out = {s: {"state": ABSENT, "kind": "", "source": "", "why": NOT_HELD} for s in want}
    if not want:
        return out
    got = records(conn, want)
    if got is None:
        return {s: {"state": ABSENT, "kind": "", "source": "", "why": UNREADABLE} for s in want}
    for sha, r in got.items():
        if sha not in out:
            continue
        if r.get("withdrawn"):
            out[sha] = {"state": ABSENT, "kind": r["kind"], "source": r["source"], "why": "document withdrawn from the store"}
        else:
            out[sha] = {"state": SERVED, "kind": r["kind"], "source": r["source"], "why": ""}
    return out


def path_in_store(sha: str, store: str = None) -> str:
    """The file for a sha inside the store root, or '' when the name is not
    64 hex characters or resolves anywhere else (a link out of the store)."""
    if not SHA.fullmatch(sha or ""):
        return ""
    base = os.path.realpath(store or root())
    p = os.path.realpath(os.path.join(base, sha[:2], sha))
    if not p.startswith(base + os.sep) or not os.path.isfile(p):
        return ""
    return p


def fetch(conn, sha: str, store: str = None) -> tuple:
    """(status, content type, bytes or a reason). 404 for a malformed sha,
    one the store does not hold or holds withdrawn, or bytes that do not hash
    to their name. No source is refused (ruling 88)."""
    if not SHA.fullmatch(sha or ""):
        return 404, "text/plain; charset=utf-8", "not a document: a document is named by 64 hex characters"
    st = statuses(conn, [sha])[sha]
    if st["state"] != SERVED:
        return 404, "text/plain; charset=utf-8", st["why"]
    p = path_in_store(sha, store)
    if not p:
        return 404, "text/plain; charset=utf-8", NOT_HELD
    with open(p, "rb") as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != sha:
        return 404, "text/plain; charset=utf-8", "the stored bytes do not hash to their name: not served"
    return 200, content_type(st["kind"], landing.names_of(sha, conn), data[:64]), data


def href(sha: str, kind: str = "", page=None) -> str:
    """The board's address for a document, at its page when it is a PDF."""
    n = int(page) if isinstance(page, int) or (isinstance(page, str) and page.isdigit()) else 0
    return f"/doc/{sha}" + (f"#page={n}" if kind == "pdf" and n > 0 else "")
