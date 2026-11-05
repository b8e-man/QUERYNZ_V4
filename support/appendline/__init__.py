"""One way to add lines to a record file that more than one box writes.

Since 5 November 2026 node1 mounts node2's work folder (`/home/user/querynzv4-work`,
`live` included) over NFS. Opening a file with "a" is not enough there: O_APPEND is
not atomic across NFS clients, so two boxes adding a line at once can overwrite or
interleave each other's bytes. Every writer of a shared record (the job runs, the
alarms, the model calls, the fetch gate's decisions and refusals, the rereads and
the rest) goes through `append` instead:

  * an exclusive POSIX lock (fcntl.lockf) on the file itself. On NFSv4 the server
    holds it, and knfsd honours it against node2's own local writers too;
  * under the lock the client revalidates the file's size, so the write lands
    after every line the other box committed;
  * the whole text in one os.write, then the lock released. No fsync: releasing an NFS lock flushes
    the client's dirty pages to the server first, and on node2's btrfs an fsync a line slowed the worker
    enough to fail test_worker's takeover (5 November 2026).

    append(path, line)          one line (a newline is added when missing)
    append(path, [l1, l2, ...]) several lines under one lock
    append_json(path, obj, **dumps_kw)
"""
from __future__ import annotations

import fcntl
import json
import os


def _text(lines) -> bytes:
    if isinstance(lines, str):
        lines = [lines]
    out = "".join(l if l.endswith("\n") else l + "\n" for l in lines)
    return out.encode("utf-8")


def append(path: str, lines) -> int:
    """Add the lines to the end of `path` under an exclusive lock; the bytes written."""
    data = _text(lines)
    if not data:
        return 0
    parent = os.path.dirname(os.fspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX)
        try:
            os.lseek(fd, 0, os.SEEK_END)
            view, done = memoryview(data), 0
            while done < len(data):
                done += os.write(fd, view[done:])
        finally:
            fcntl.lockf(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)
    return len(data)


def append_json(path: str, obj, **dumps_kw) -> int:
    """One JSON line for `obj` (json.dumps with the caller's keywords)."""
    return append(path, json.dumps(obj, **dumps_kw))
