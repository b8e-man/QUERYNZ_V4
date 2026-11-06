"""The quorum lease's messages on the wire: one JSON object per UDP datagram, signed.

A lost datagram is never resent as such: every holder asks again on its next tick, so loss costs one round.
Each datagram carries the sender's name, a boot nonce and a counter; a receiver drops a datagram whose
signature is wrong, and one from a (sender, boot) it has already seen a higher counter from (a replay).
The key is one per estate, in `~/.querynz/voter.env` (`QV4_VOTER_KEY=`) on each of the three machines and
nowhere else (hard limit 1). Standard library only: the voter runs none of the estate's other code."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import socket

MAX = 4096


def load_key(path: str) -> bytes:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("QV4_VOTER_KEY="):
                k = line.split("=", 1)[1].strip()
                if len(k) >= 32:
                    return k.encode()
    raise SystemExit(f"no QV4_VOTER_KEY of 32 characters or more in {path}")


class Wire:
    def __init__(self, name: str, key: bytes, bind: tuple[str, int]):
        self.name, self.key = name, key
        self.boot = secrets.token_hex(8)
        self.n = 0
        self.seen: dict[tuple[str, str], int] = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(bind)

    def _sig(self, body: bytes) -> str:
        return hmac.new(self.key, body, hashlib.sha256).hexdigest()

    def send(self, addr: tuple[str, int], msg: dict) -> None:
        self.n += 1
        env = {"m": msg, "s": self.name, "b": self.boot, "n": self.n}
        body = json.dumps(env, sort_keys=True, separators=(",", ":")).encode()
        try:
            self.sock.sendto(json.dumps({"e": env, "h": self._sig(body)}).encode(), addr)
        except OSError:
            pass                         # an unreachable path is a lost datagram

    def recv(self, timeout: float):
        """One verified message, as (sender, msg, (ip, port)), or None on a timeout or a bad datagram."""
        self.sock.settimeout(max(0.0, timeout))
        try:
            data, addr = self.sock.recvfrom(MAX)
        except (socket.timeout, BlockingIOError):
            return None
        except OSError:
            return None
        try:
            outer = json.loads(data)
            env = outer["e"]
            body = json.dumps(env, sort_keys=True, separators=(",", ":")).encode()
            if not hmac.compare_digest(self._sig(body), str(outer["h"])):
                return None
            k = (str(env["s"]), str(env["b"]))
            if self.seen.get(k, 0) >= int(env["n"]):
                return None
            self.seen[k] = int(env["n"])
            if len(self.seen) > 256:
                self.seen.pop(next(iter(self.seen)))
            return str(env["s"]), dict(env["m"]), addr
        except (ValueError, KeyError, TypeError):
            return None


def write_state(path: str, state: dict) -> None:
    """Written whole and fsynced before the caller answers anyone."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    d = os.open(os.path.dirname(path) or ".", os.O_RDONLY)
    try:
        os.fsync(d)
    finally:
        os.close(d)


def read_state(path: str) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return None
