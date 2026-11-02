"""How this lane's document arrives (plan 1.10, case one: the original is held, here, as one file).

The Papers Past archive is the old news-scraping database's dump, recovered from the Hetzner box and verified on 29 August
2026 (`verified.OK`; the whole offload against its source on 6 September). It sits on node2's system disk and is never
moved, copied or landed whole: at 124 GiB it is the document, cited by the sha256 its own `dump.sha256` carries, and each
item by its line in the dump's `public.scraper_results` section.

A batch is read by streaming the dump once from the top (`zcat`, low priority) and taking the rows of the host
paperspast.natlib.govt.nz in the order the dump holds them, `after` the line the previous batch stopped at. A row of any
other host is counted by its URL's host and never decoded (hard limit 8: no NZME masthead is read).

    source()                  the dump: (path, sha256, bytes, verified)
    rows(n, after=0, every=1) up to n Papers Past rows after dump line `after`, every `every`-th: dicts of the
                              section's columns plus `_line` (its line in the dump) and `_bytes` (the line's bytes)
"""
import os
import re
import subprocess
from urllib.parse import urlsplit

FOLDER = "/home/user/offload-2026-09-02/hetzner-recovery"
DUMP = "local-docker_news-scraping-db_newsscraping_20260825_005138.sql.gz"
SECTION = "public.scraper_results"
HOST = "paperspast.natlib.govt.nz"
#: the dump's size as read on 2 November 2026; its sha256 is read from its own dump.sha256 at run time, never copied here
BYTES = 132_692_104_796

_ESC_RE = re.compile(rb"\\(.)", re.S)
_ESC = {0x74: b"\t", 0x6E: b"\n", 0x72: b"\r", 0x5C: b"\\", 0x62: b"\b", 0x66: b"\f", 0x76: b"\v"}


def source(folder: str = FOLDER) -> tuple:
    """(path, sha256, bytes, verified): the dump as its own pins describe it; raises if the file is not the one pinned."""
    path = os.path.join(folder, DUMP)
    with open(os.path.join(folder, "dump.sha256"), encoding="utf-8") as f:
        pins = [l.split() for l in f if l.strip()]
    sha = next(p[0] for p in pins if p[-1].lstrip("*").endswith(DUMP))
    size = os.path.getsize(path)
    if size != BYTES:
        raise RuntimeError(f"the dump is {size} bytes, not the {BYTES} pinned: not the document this lane reads")
    verified = open(os.path.join(folder, "verified.OK"), encoding="utf-8").read().strip() \
        if os.path.exists(os.path.join(folder, "verified.OK")) else ""
    return path, sha, size, verified


def unescape(f: bytes):
    """One field of a COPY text row, as PostgreSQL wrote it."""
    if f == b"\\N":
        return None
    if 0x5C not in f:                               # most fields: nothing escaped
        return f.decode("utf-8", "replace")
    return _ESC_RE.sub(lambda m: _ESC.get(m.group(1)[0], m.group(1)), f).decode("utf-8", "replace")


def unescape_slow(f: bytes):
    """The same, a byte at a time (kept as the test's reference for the fast one)."""
    if f == b"\\N":
        return None
    out, i, n = bytearray(), 0, len(f)
    while i < n:
        c = f[i]
        if c == 0x5C and i + 1 < n:
            out += _ESC.get(f[i + 1], bytes([f[i + 1]]))
            i += 2
        else:
            out.append(c)
            i += 1
    return out.decode("utf-8", "replace")


def host_of(url: str) -> str:
    return (urlsplit(url or "").hostname or "").lower()


def _field(line: bytes, i: int) -> bytes:
    """The i-th tab-separated field of a COPY row, found without splitting the whole line."""
    a = 0
    for _ in range(i):
        a = line.find(b"\t", a) + 1
        if a == 0:
            return b""
    b = line.find(b"\t", a)
    return line[a:b if b >= 0 else len(line)].rstrip(b"\n")


PREFIX = b"https://" + HOST.encode() + b"/"


def take(lines, n: int, after: int = 0, every: int = 1, counts: dict = None, seen: int = 0):
    """The Papers Past rows of the section from an iterator of the dump's raw lines (bytes): up to n, after line `after`,
    every `every`-th Papers Past row from the first (a sample spread over the dump). `counts`, if given, gets the Papers
    Past rows passed over (`seen`) and the last line read (`line`). A resumed take passes `seen`, the Papers Past rows
    counted up to `after`, so the stride keeps its phase; each row carries `_seen`, the count at it."""
    section, cols, url_i, got = False, None, None, 0
    counts = counts if counts is not None else {}
    for line_no, line in enumerate(lines, start=1):
        if not section:
            if line.startswith(b"COPY " + SECTION.encode() + b" "):
                head = line.decode("utf-8", "replace")
                cols = [c.strip().strip('"') for c in head[head.index("(") + 1:head.rindex(")")].split(",")]
                url_i = cols.index("news_url")
                section = True
            continue
        if line == b"\\.\n":
            break
        if line_no <= after:
            continue
        url = _field(line, url_i)
        if not url.startswith(PREFIX) and host_of(url.decode("utf-8", "replace")) != HOST:
            continue
        seen += 1
        if (seen - 1) % every:
            continue
        parts = line.rstrip(b"\n").split(b"\t")
        row = {c: unescape(v) for c, v in zip(cols, parts)}
        row["_line"], row["_bytes"], row["_seen"] = line_no, len(line), seen
        yield row
        got += 1
        if got >= n:
            counts.update(seen=seen, line=line_no)
            return
    counts.update(seen=seen, line=line_no if section else 0)


def rows(n: int, after: int = 0, folder: str = FOLDER, every: int = 1, counts: dict = None, seen: int = 0):
    """Stream the dump, read-only and at low priority, and yield its first n Papers Past rows after line `after`
    (every `every`-th of them)."""
    path = source(folder)[0]
    p = subprocess.Popen(["ionice", "-c3", "nice", "-n", "15", "zcat", path], stdout=subprocess.PIPE, bufsize=1 << 20)
    try:
        yield from take(p.stdout, n, after, every, counts, seen)
    finally:
        p.kill()
        p.wait()
