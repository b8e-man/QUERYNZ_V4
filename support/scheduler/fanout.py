"""One address for a box's per-card model servers (Arthur, 26 November 2026: "let's switch everything to 3.8 27b",
one instance of the dense model on each card, not one across both).

Qwen 3.8 27B runs as one Radiance server a card (`qv4-radiance-card@<card>`, :8070 and :8071, tensor parallel 1);
Radiance has no data-parallel mode. This proxy listens where the standing server always has (127.0.0.1:8060), so
the card manager, the night window, the watchdog and every job's QV4_MODEL_URL stay as they were, and spreads the
requests over the cards:

- a POST goes to the server with the fewest requests in flight through this proxy (ties in turn); one that refuses
  the connection is passed over for DOWN_S and the request tries the next, so a card's server restarting is never a
  failed request while the other answers;
- GET /v1/models answers with the first server that answers (the card manager reads the model back from it);
  503 when none does;
- GET /metrics is every server's text one after the other: the watchdog sums each counter over engines already;
- GET /health is 200 when any server answers.

The body is passed through as it comes, streamed or whole. No text is logged; the log line is method, path,
server, status and seconds. Unit: support/scheduler/units/qv4-radiance.service.

    python -m support.scheduler.fanout [--port 8060] [--backends http://127.0.0.1:8070,http://127.0.0.1:8071]
"""
from __future__ import annotations

import argparse
import http.client
import http.server
import itertools
import os
import sys
import threading
import time
import urllib.parse

BACKENDS = os.environ.get("QV4_FANOUT_BACKENDS") or "http://127.0.0.1:8070,http://127.0.0.1:8071"
PORT = int(os.environ.get("QV4_FANOUT_PORT") or 8060)
DOWN_S = 20.0            # a server that refused a connection is passed over this long
TIMEOUT_S = 1800.0       # a reader's call may run 900 s; never the proxy's to cut short
PROBE_TIMEOUT_S = 5.0
HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers",
       "transfer-encoding", "upgrade", "host", "content-length"}


class Pool:
    """The servers, the requests in flight on each, and which refused lately."""

    def __init__(self, backends: list[str], clock=time.monotonic):
        self.backends = [b.rstrip("/") for b in backends]
        self.inflight = {b: 0 for b in self.backends}
        self.down_until = {b: 0.0 for b in self.backends}
        self.clock = clock
        self.turn = itertools.count()
        self.lock = threading.Lock()

    def order(self) -> list[str]:
        """Every server, fewest in flight first, those that refused lately last; ties in turn."""
        with self.lock:
            now, t = self.clock(), next(self.turn)
            n = len(self.backends)
            return sorted(self.backends, key=lambda b: (self.down_until[b] > now, self.inflight[b],
                                                       (self.backends.index(b) - t) % n))

    def take(self, b: str) -> None:
        with self.lock:
            self.inflight[b] += 1

    def give(self, b: str) -> None:
        with self.lock:
            self.inflight[b] -= 1

    def refused(self, b: str) -> None:
        with self.lock:
            self.down_until[b] = self.clock() + DOWN_S


def _conn(base: str, timeout: float) -> http.client.HTTPConnection:
    u = urllib.parse.urlsplit(base)
    return http.client.HTTPConnection(u.hostname, u.port or 80, timeout=timeout)


def _get(base: str, path: str) -> tuple[int, dict, bytes] | None:
    try:
        c = _conn(base, PROBE_TIMEOUT_S)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read()
        c.close()
        return r.status, dict(r.getheaders()), body
    except (OSError, http.client.HTTPException):
        return None


def make_handler(pool: Pool, log=print):
    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.0"      # one request a connection: the body ends when the connection does

        def log_message(self, *a):        # the stdlib's line carries the client address; ours is below
            pass

        def _send(self, status: int, body: bytes, ctype: str = "application/json") -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path
            if path.startswith("/metrics"):
                parts = [g[2] for g in (_get(b, path) for b in pool.backends) if g and g[0] == 200]
                if not parts:
                    return self._send(503, b"no server answers\n", "text/plain")
                return self._send(200, b"\n".join(p.rstrip(b"\n") for p in parts) + b"\n", "text/plain; version=0.0.4")
            for b in pool.order():
                g = _get(b, path)
                if g is None:
                    pool.refused(b)
                    continue
                if path.startswith("/health") and g[0] != 200:
                    continue
                return self._send(g[0], g[2], g[1].get("Content-Type") or "application/json")
            self._send(503, b'{"error":"no model server answers"}')

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
            headers = {k: v for k, v in self.headers.items() if k.lower() not in HOP}
            headers["Content-Length"] = str(len(body))
            t0 = time.monotonic()
            for b in pool.order():
                c = _conn(b, TIMEOUT_S)
                try:
                    c.request("POST", self.path, body=body, headers=headers)
                except OSError:                # refused before a byte was taken: the next server
                    c.close()
                    pool.refused(b)
                    continue
                pool.take(b)
                try:
                    r = c.getresponse()
                    self.send_response(r.status)
                    for k, v in r.getheaders():
                        if k.lower() not in HOP:
                            self.send_header(k, v)
                    self.end_headers()
                    while True:
                        chunk = r.read1(65536) if hasattr(r, "read1") else r.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    log(f"POST {self.path} -> {b} {r.status} {time.monotonic() - t0:.1f}s")
                except (OSError, http.client.HTTPException) as e:
                    log(f"POST {self.path} -> {b} failed after {time.monotonic() - t0:.1f}s: {type(e).__name__}")
                    try:
                        self._send(502, b'{"error":"the model server dropped the request"}')
                    except OSError:
                        pass
                finally:
                    pool.give(b)
                    c.close()
                return
            self._send(503, b'{"error":"no model server answers"}')

    return Handler


def serve(port: int, backends: list[str], host: str = "127.0.0.1", log=print) -> http.server.ThreadingHTTPServer:
    srv = http.server.ThreadingHTTPServer((host, port), make_handler(Pool(backends), log))
    srv.daemon_threads = True
    return srv


def _notify_ready() -> None:
    """Tell systemd the proxy is listening (Type=notify), without a dependency."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    import socket
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
        s.connect(addr)
        s.sendall(b"READY=1")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--backends", default=BACKENDS)
    a = ap.parse_args(argv)
    srv = serve(a.port, [b for b in a.backends.split(",") if b], log=lambda m: print(m, flush=True))
    print(f"fanout on 127.0.0.1:{a.port} over {a.backends}", flush=True)
    _notify_ready()
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
