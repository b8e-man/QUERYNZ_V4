"""The two daemons of the quorum lease: `voter` on the third machine and `agent` on each box. Both drive the
state machines in `quorum.py` with this machine's monotonic clock and the signed datagrams of `wire.py`.

The agent runs its actions (promote, start as primary, fence, rejoin) in threads through an `actions`
object: `LiveActions` calls the root jobs in /usr/local/libexec/qv4-takeover; `ScratchActions` drives two
scratch PostgreSQL instances for the rehearsal (support/takeover/rehearse.py). Standard library only."""
from __future__ import annotations

import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time

from support.takeover import quorum as q
from support.takeover import wire

VOTER_PORT, AGENT_PORT = 8741, 8742


def _log(path: str | None, **rec) -> None:
    rec = {"at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **rec}
    print(json.dumps(rec), flush=True)
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")


# ── the voter ────────────────────────────────────────────────────────────────

def run_voter(key: bytes, state_path: str, *, bind=("0.0.0.0", VOTER_PORT), boxes=("node1", "node2"),
              log_path: str | None = None, stop: threading.Event | None = None) -> None:
    w = wire.Wire("voter", key, bind)
    v = q.Voter(time.monotonic(), wire.read_state(state_path))
    addrs: dict[str, str] = {}
    _log(log_path, event="voter up", state=v.state())
    last = v.state()
    while not (stop and stop.is_set()):
        got = w.recv(1.0)
        if not got:
            continue
        sender, msg, addr = got
        if sender not in boxes and sender != "ctl":
            continue
        if sender in boxes:
            addrs[sender] = addr[0]
        reply = v.handle(msg, time.monotonic())
        st = v.state()
        if st != last:
            wire.write_state(state_path, st)          # before the answer leaves
            _log(log_path, event="voter state", op=msg.get("op"), box=msg.get("box"), state=st)
            last = st
        reply["addrs"] = addrs
        w.send(addr, reply)


# ── a box's agent ────────────────────────────────────────────────────────────

class Agent:
    def __init__(self, box: str, peer: str, key: bytes, *, voter_addr: tuple[str, int],
                 peer_addrs: list[tuple[str, int]], actions, state_path: str, role_path: str | None = None,
                 bind=("0.0.0.0", AGENT_PORT), log_path: str | None = None, notify: bool = False):
        self.box, self.peer = box, peer
        self.w = wire.Wire(box, key, bind)
        self.voter_addr, self.peer_addrs = voter_addr, list(peer_addrs)
        self.learned: tuple[str, int] | None = None     # the peer's other address, as the voter last saw it
        self.actions, self.state_path, self.role_path, self.log_path = actions, state_path, role_path, log_path
        self.notify = notify
        st = wire.read_state(state_path) or {}
        now = time.monotonic()
        self.a = q.Agent(box, peer, actions.initial_role(), now, held_epoch=st.get("held_epoch"))
        self.done_q: queue.Queue = queue.Queue()
        self.running: set[str] = set()
        self._persisted = (st.get("held_epoch"), None)
        self.drop: set[str] = set()                     # rehearsal: paths to treat as cut ("voter", the peer)
        _log(log_path, event="agent up", box=box, role=self.a.role, held_epoch=self.a.held_epoch)

    def _to(self, dest: str, msg: dict) -> None:
        if dest in self.drop:
            return
        if dest == "voter":
            self.w.send(self.voter_addr, msg)
        else:
            for addr in self.peer_addrs + ([self.learned] if self.learned else []):
                self.w.send(addr, msg)

    def _emit(self, out, acts) -> None:
        for dest, msg in out:
            self._to(dest, msg)
        for name in acts:
            if name in self.running and name != "FENCE":
                continue
            self.running.add(name)
            threading.Thread(target=self._act, args=(name,), daemon=True).start()

    def _act(self, name: str) -> None:
        t0 = time.monotonic()
        try:
            ok = bool(self.actions.run(name))
        except Exception as e:                       # an action that raises has failed
            _log(self.log_path, event="action error", action=name, error=str(e)[:300])
            ok = False
        self.done_q.put((name, ok, time.monotonic() - t0))

    def _persist(self) -> None:
        cur = (self.a.held_epoch, self.a.role)
        if cur[0] != self._persisted[0]:
            wire.write_state(self.state_path, {"held_epoch": self.a.held_epoch})
        if self.role_path and cur[1] != self._persisted[1]:
            with open(self.role_path, "w", encoding="utf-8") as f:
                f.write(self.a.role + "\n")
        if cur != self._persisted:
            _log(self.log_path, event="role", box=self.box, role=self.a.role, held_epoch=self.a.held_epoch,
                 epoch=self.a.epoch, last=self.a.log[-1] if self.a.log else None)
        self._persisted = cur

    def _prepare_switchover(self) -> None:
        t0 = time.monotonic()
        ok = bool(getattr(self.actions, "checkpoint", lambda: True)())
        self.done_q.put(("_SWITCHOVER", ok, time.monotonic() - t0))

    def _sd_notify(self, text: str) -> None:
        path = os.environ.get("NOTIFY_SOCKET")
        if not (self.notify and path):
            return
        if path.startswith("@"):
            path = "\0" + path[1:]
        s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            s.sendto(text.encode(), path)
        except OSError:
            pass
        finally:
            s.close()

    def step(self, budget: float) -> None:
        """One CHECK period: the lease check, the tick when due, finished actions, then datagrams."""
        now = time.monotonic()
        self._emit([], self.a.check(now))
        if now >= getattr(self, "_next_tick", 0.0):
            self._next_tick = now + q.RENEW
            if self.a.role == "standby":
                self.a.caught_up = bool(self.actions.caught_up())
            self._emit(*self.a.tick(now))
        while not self.done_q.empty():
            name, ok, took = self.done_q.get()
            self.running.discard(name)
            _log(self.log_path, event="action", action=name, ok=ok, seconds=round(took, 2))
            if name == "_SWITCHOVER":
                self._emit(*self.a.switchover(time.monotonic()))
            else:
                self._emit(*self.a.done(name, ok, time.monotonic()))
        self._persist()
        if self.a.watchdog_ok(time.monotonic()):
            self._sd_notify("WATCHDOG=1")
        end = time.monotonic() + budget
        while (left := end - time.monotonic()) > 0:
            got = self.w.recv(left)
            if not got:
                break
            sender, msg, addr = got
            now = time.monotonic()
            if sender == "voter":
                if "voter" in self.drop:
                    continue
                peer_ip = (msg.get("addrs") or {}).get(self.peer)
                if peer_ip:
                    self.learned = (peer_ip, self.peer_addrs[0][1] if self.peer_addrs else AGENT_PORT)
                self._emit(*self.a.reply(msg, now))
            elif sender == self.peer:
                if self.peer in self.drop:
                    continue
                if "re" in msg:
                    self._emit(*self.a.reply(msg, now))
                else:
                    self.w.send(addr, self.a.request(msg, now))
            elif sender == "ctl" and addr[0] == "127.0.0.1":
                self.w.send(addr, self._control(msg, now))

    def _control(self, msg: dict, now: float) -> dict:
        op = msg.get("op")
        if op == "switchover":
            if self.a.role != "primary":
                return {"ok": False, "role": self.a.role, "why": "only the primary switches over"}
            # a checkpoint first, while still holding the role, so the immediate stop leaves little to recover;
            # in a thread, so renewals go on meanwhile
            threading.Thread(target=self._prepare_switchover, daemon=True).start()
            return {"ok": True, "role": self.a.role, "started": "checkpoint, then the switchover"}
        if op == "drop":                              # rehearsal only: cut a path
            self.drop = set(msg.get("paths", []))
            return {"ok": True, "drop": sorted(self.drop)}
        return {"ok": True, "box": self.box, "role": self.a.role, "epoch": self.a.epoch,
                "held_epoch": self.a.held_epoch, "lease_left": round(max(self.a.voter_ok, self.a.peer_ok) - now, 1),
                "caught_up": self.a.caught_up, "log": self.a.log[-10:]}

    def run(self, stop: threading.Event | None = None) -> None:
        self._sd_notify("READY=1")
        while not (stop and stop.is_set()):
            self.step(q.CHECK)


def control(key: bytes, op: str, *, port: int = AGENT_PORT, timeout: float = 3.0, **extra) -> dict | None:
    """Ask the agent on this box (127.0.0.1) for its status, or to switch over."""
    w = wire.Wire("ctl", key, ("127.0.0.1", 0))
    w.send(("127.0.0.1", port), {"op": op, **extra})
    got = w.recv(timeout)
    return got[1] if got else None


# ── actions on the live boxes ────────────────────────────────────────────────

LIBEXEC = "/usr/local/libexec/qv4-takeover"


class LiveActions:
    SCRIPTS = {"PROMOTE": "takeover.sh", "START_PRIMARY": "start-primary.sh", "FENCE": "fence.sh",
               "REJOIN": "rejoin.sh"}

    def __init__(self):
        self.last_streaming = time.monotonic()

    def _sql(self, query: str) -> str | None:
        r = subprocess.run(["runuser", "-u", "postgres", "--", "psql", "-XAtq", "-d", "postgres", "-c", query],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    def initial_role(self) -> str:
        if subprocess.run(["systemctl", "is-active", "-q", "postgresql"]).returncode != 0:
            return "down"
        rec = self._sql("select pg_is_in_recovery()")
        return {"t": "standby", "f": "primary"}.get(rec or "", "down")

    def checkpoint(self) -> bool:
        r = subprocess.run(["runuser", "-u", "postgres", "--", "psql", "-XAtq", "-c", "checkpoint"],
                           capture_output=True, text=True, timeout=600)
        return r.returncode == 0

    def caught_up(self) -> bool:
        if self._sql("select coalesce((select status from pg_stat_wal_receiver), '')") == "streaming":
            self.last_streaming = time.monotonic()
        return time.monotonic() - self.last_streaming < 2 * q.TTL

    def run(self, name: str) -> bool:
        timeout = {"FENCE": 60, "PROMOTE": 300, "START_PRIMARY": 300, "REJOIN": 7200}[name]
        r = subprocess.run([f"{LIBEXEC}/{self.SCRIPTS[name]}"], capture_output=True, text=True, timeout=timeout)
        sys.stdout.write(r.stdout[-2000:] + r.stderr[-2000:])
        return r.returncode == 0
