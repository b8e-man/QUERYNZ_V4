"""Where the archive's text is kept (step 8.6; Arthur, 2 November 2026: "use the 4tb HDD"): compressed files on the 4 TB disk
at /mnt/hdd2, outside the database, which keeps only the catalogue (key, paper, date, title, length, sha256, and the file
and place of the text). Never on /mnt/hdd (the old estate's disk), never a PostgreSQL tablespace.

The files are build output: regenerable from the dump, which is the document and is never moved, copied or changed.

    /mnt/hdd2/qv4-papers-past/<store>/text/<PAPER>/<YYYY>.zst      (<store>: the database and schema the catalogue is in)

A file is zstd frames appended one after another and never rewritten (append-only; a crash leaves at most a tail no
catalogue row points at). A frame holds up to FRAME bytes of records, each `key \\t bytes \\t sha256 \\n` then the text's
UTF-8 bytes then `\\n`, so a file read alone still says what it holds (`zstd -dc` prints it). An item is found by
(file, frame_at, frame_bytes, at, bytes): the frame's offset and length in the file, the text's offset and length in the
decompressed frame. `text(...)` reads one item back and checks its sha256.

    w = Writer(root); w.add(key, paper, year, text) -> None; w.close() -> {key: Place}
"""
import fcntl
import hashlib
import os
import shutil
from compression import zstd
from dataclasses import dataclass

ROOT = "/mnt/hdd2/qv4-papers-past"
FRAME = 256 * 1024          # raw bytes of records per frame (measured on batch 1: ratio 2.47 at level 9, 2.17 at 128 KB)
LEVEL = 9
BUFFERED = 256 << 20        # raw bytes held across all groups before the largest groups are written out


@dataclass(frozen=True)
class Place:
    file: str               # relative to the store: text/EP/1904.zst
    frame_at: int
    frame_bytes: int
    at: int
    bytes: int
    sha256: bytes


def store_dir(database: str, schema: str, root: str = ROOT) -> str:
    return os.path.join(root, f"{database}.{schema}")


def _check_root(path: str) -> None:
    p = os.path.realpath(path)
    if p == "/mnt/hdd" or p.startswith("/mnt/hdd/"):
        raise RuntimeError(f"{path} is on the old estate's disk; the archive's text goes on /mnt/hdd2")


def wipe(path: str, root: str = ROOT) -> None:
    """The store's text removed whole (build output, rebuilt with its catalogue). Only a store directly under the root."""
    _check_root(path)
    if os.path.dirname(os.path.realpath(path)) != os.path.realpath(root):
        raise RuntimeError(f"{path} is not a store under {root}")
    shutil.rmtree(os.path.join(path, "text"), ignore_errors=True)


def group_file(paper: str, year) -> str:
    if not paper.isalnum():
        raise ValueError(f"not a paper code: {paper!r}")
    return os.path.join("text", paper, f"{int(year):04d}.zst" if year else "undated.zst")


class Writer:
    """Buffers items per paper and year and appends them to that group's file in frames of about FRAME bytes."""

    def __init__(self, path: str, frame: int = FRAME, level: int = LEVEL, buffered: int = BUFFERED):
        _check_root(path)
        os.makedirs(os.path.join(path, "text"), exist_ok=True)
        self.path, self.frame, self.level, self.buffered = path, frame, level, buffered
        self._lock = open(os.path.join(path, ".lock"), "w")
        fcntl.flock(self._lock, fcntl.LOCK_EX | fcntl.LOCK_NB)        # one writer at a time
        self._groups = {}       # file -> [bytearray, [(key, at, n, sha)]]
        self._held = 0
        self.places = {}
        self.frames = 0
        self.raw = 0

    def add(self, key: str, paper: str, year, text: str) -> None:
        b = text.encode("utf-8")
        sha = hashlib.sha256(b).digest()
        f = group_file(paper, year)
        buf, recs = self._groups.setdefault(f, [bytearray(), []])
        head = f"{key}\t{len(b)}\t{sha.hex()}\n".encode()
        at = len(buf) + len(head)
        buf += head + b + b"\n"
        recs.append((key, at, len(b), sha))
        self._held += len(head) + len(b) + 1
        if len(buf) >= self.frame:
            self._write(f)
        elif self._held > self.buffered:
            for g in sorted(self._groups, key=lambda g: -len(self._groups[g][0]))[:max(1, len(self._groups) // 4)]:
                self._write(g)

    def _write(self, f: str) -> None:
        buf, recs = self._groups.pop(f)
        if not recs:
            return
        data = zstd.compress(bytes(buf), self.level)
        full = os.path.join(self.path, f)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "ab") as fh:
            frame_at = fh.tell()
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        for key, at, n, sha in recs:
            self.places[key] = Place(f, frame_at, len(data), at, n, sha)
        self._held -= len(buf)
        self.frames += 1
        self.raw += len(buf)

    def close(self) -> dict:
        for f in list(self._groups):
            self._write(f)
        fcntl.flock(self._lock, fcntl.LOCK_UN)
        self._lock.close()
        return self.places


def frame(path: str, file: str, frame_at: int, frame_bytes: int) -> bytes:
    with open(os.path.join(path, file), "rb") as fh:
        fh.seek(frame_at)
        return zstd.decompress(fh.read(frame_bytes))


def text(path: str, file: str, frame_at: int, frame_bytes: int, at: int, n: int, sha256: bytes = None) -> str:
    """One item's text, read back from its place; raises if its sha256 is not the one catalogued."""
    b = frame(path, file, frame_at, frame_bytes)[at:at + n]
    if sha256 is not None and hashlib.sha256(b).digest() != bytes(sha256):
        raise RuntimeError(f"{file}@{frame_at}+{at}: the text's sha256 is not the catalogued one")
    return b.decode("utf-8")


def records(raw: bytes):
    """(key, at, bytes, sha256 hex) of every record in one decompressed frame: the file read without the catalogue."""
    i = 0
    while i < len(raw):
        j = raw.index(b"\n", i)
        key, n, sha = raw[i:j].decode().split("\t")
        yield key, j + 1, int(n), sha
        i = j + 1 + int(n) + 1


def disk_bytes(path: str) -> int:
    """Bytes the store's files take on disk (allocated blocks)."""
    total = 0
    for dirpath, _, files in os.walk(os.path.join(path, "text")):
        for f in files:
            total += os.stat(os.path.join(dirpath, f)).st_blocks * 512
    return total
