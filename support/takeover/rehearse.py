"""THE REHEARSAL (track A: "build and rehearse it beside the live database, on a scratch pair"). Two scratch
PostgreSQL instances on this box (own data folders, own ports, data checksums on), the real voter and the
real agents of `daemon.py` on the loopback, and a writer that inserts a numbered row every 0.2 s through
whichever instance holds the stand-in address (a file naming the holder). Then the failures, for real:

  1. steady running                 the primary keeps the role
  2. the primary dies               (agent stopped, database stopped immediately) the standby takes over
  3. it returns                     rewinds and follows as the standby
  4. a planned switchover back      seconds, not a lease
  5. the cable pulled for 70 s      nothing changes
  6. the voter down for 70 s        nothing changes
  7. the primary cut off from both  it fences itself, the standby takes over, it rejoins when healed

Every write the writer saw acknowledged is looked for on the final primary; the ones missing are the
asynchronous gap of an unplanned takeover and are counted. At no moment may both instances accept a write.

    python -m support.takeover.rehearse [--dir DIR]       (as the estate's user; nothing live is touched)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import threading
import time

from support.takeover import daemon, quorum as q

PG = "/usr/bin"
KEY = b"rehearsal-key-not-a-credential-0123456789"


def sh(*cmd, check=True, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run(list(cmd), capture_output=True, text=True, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)}: {r.stderr.strip()[-500:]}")
    return r


class Box:
    def __init__(self, root: str, name: str, port: int, peer: "Box | None" = None):
        self.name, self.port, self.root = name, port, root
        self.data = os.path.join(root, f"pg-{name}")
        self.peer = peer

    def sql(self, query: str, port: int | None = None) -> str | None:
        r = sh(f"{PG}/psql", "-XAtq", "-h", "127.0.0.1", "-p", str(port or self.port), "-d", "postgres",
               "-c", query, check=False, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None

    def running(self) -> bool:
        return sh(f"{PG}/pg_ctl", "status", "-D", self.data, check=False).returncode == 0


class ScratchActions:
    def __init__(self, box: Box, vip: str):
        self.box, self.vip = box, vip
        self.last_streaming = time.monotonic()

    def holder(self) -> str | None:
        try:
            return open(self.vip).read().strip() or None
        except FileNotFoundError:
            return None

    def initial_role(self) -> str:
        if not self.box.running():
            return "down"
        return {"t": "standby", "f": "primary"}.get(self.box.sql("select pg_is_in_recovery()") or "", "down")

    def caught_up(self) -> bool:
        if self.box.sql("select coalesce((select status from pg_stat_wal_receiver), '')") == "streaming":
            self.last_streaming = time.monotonic()
        return time.monotonic() - self.last_streaming < 2 * q.TTL

    def _take_vip(self) -> bool:
        # the stand-in for arping: refuse while the other instance holds the address AND answers as a primary
        h = self.holder()
        if h and h != self.box.name and self.box.peer.running() and \
                self.box.peer.sql("select pg_is_in_recovery()") == "f":
            return False
        with open(self.vip, "w") as f:
            f.write(self.box.name)
        return True

    def run(self, name: str) -> bool:
        b = self.box
        if name == "FENCE":
            if self.holder() == b.name:
                os.unlink(self.vip)
            if b.running():
                sh(f"{PG}/pg_ctl", "stop", "-D", b.data, "-m", "fast", "-w", "-t", "20", check=False)
            return not b.running()
        if name == "PROMOTE":
            if not (b.running() and b.sql("select pg_is_in_recovery()") == "t"):
                return False
            if b.sql("select pg_promote(true, 60)") != "t":
                return False
            b.sql(f"select pg_create_physical_replication_slot('{b.peer.name}_standby', true) where not exists "
                  f"(select 1 from pg_replication_slots where slot_name = '{b.peer.name}_standby')")
            return self._take_vip()
        if name == "START_PRIMARY":
            sig = os.path.join(b.data, "standby.signal")
            if os.path.exists(sig):
                return False
            sh(f"{PG}/pg_ctl", "start", "-D", b.data, "-w", "-t", "60", "-l", b.data + ".log", check=False)
            return b.running() and b.sql("select pg_is_in_recovery()") == "f" and self._take_vip()
        if name == "REJOIN":
            if b.running():
                sh(f"{PG}/pg_ctl", "stop", "-D", b.data, "-m", "fast", "-w", check=False)
            for sig in ("standby.signal", "recovery.signal"):     # a failed rejoin leaves one; recovery refuses it
                if os.path.exists(os.path.join(b.data, sig)):
                    os.unlink(os.path.join(b.data, sig))
            r = sh(f"{PG}/pg_rewind", "-D", b.data, f"--source-server=host=127.0.0.1 port={b.peer.port} dbname=postgres",
                   check=False, timeout=600)
            if r.returncode != 0:
                open(os.path.join(b.data, "standby.signal"), "w").close()
                print(f"rewind {b.name}: {r.stderr.strip()[-300:]}", flush=True)
                return False
            auto = os.path.join(b.data, "postgresql.auto.conf")
            # pg_rewind copied the source's settings file, its port included (on the live boxes both are 5432)
            lines = [l for l in open(auto) if not l.startswith(("primary_conninfo", "primary_slot_name", "port"))]
            lines += [f"port = {b.port}\n",f"primary_conninfo = 'host=127.0.0.1 port={b.peer.port} application_name={b.name}'\n",
                      f"primary_slot_name = '{b.name}_standby'\n"]
            open(auto, "w").writelines(lines)
            open(os.path.join(b.data, "standby.signal"), "w").close()
            sh(f"{PG}/pg_ctl", "start", "-D", b.data, "-w", "-t", "60", "-l", b.data + ".log", check=False)
            for _ in range(60):
                if b.sql("select coalesce((select status from pg_stat_wal_receiver), '')") == "streaming":
                    return True
                time.sleep(1)
            return False
        raise ValueError(name)


def setup(root: str) -> tuple[Box, Box]:
    if os.path.exists(root):
        for d in ("pg-node1", "pg-node2"):
            p = os.path.join(root, d)
            if os.path.exists(p):
                sh(f"{PG}/pg_ctl", "stop", "-D", p, "-m", "immediate", check=False)
        shutil.rmtree(root)
    os.makedirs(root)
    a, b = Box(root, "node1", 55432), Box(root, "node2", 55433)
    a.peer, b.peer = b, a
    sh(f"{PG}/initdb", "-D", a.data, "--data-checksums", "-A", "trust", "-U", os.environ.get("USER", "user"))
    with open(os.path.join(a.data, "postgresql.conf"), "a") as f:
        f.write(f"port = {a.port}\nlisten_addresses = '127.0.0.1'\nunix_socket_directories = '{root}'\n"
                "wal_level = replica\nmax_wal_senders = 5\nmax_replication_slots = 5\nhot_standby = on\n"
                "wal_keep_size = 256MB\nshared_buffers = 64MB\n")
    with open(os.path.join(a.data, "pg_hba.conf"), "a") as f:
        f.write("host replication all 127.0.0.1/32 trust\n")
    sh(f"{PG}/pg_ctl", "start", "-D", a.data, "-w", "-l", a.data + ".log")
    a.sql("create table w (n bigint primary key, at timestamptz default now())")
    a.sql("select pg_create_physical_replication_slot('node2_standby', true)")
    sh(f"{PG}/pg_basebackup", "-h", "127.0.0.1", "-p", str(a.port), "-D", b.data, "-X", "stream", "-R",
       "-S", "node2_standby")
    with open(os.path.join(b.data, "postgresql.auto.conf"), "a") as f:
        f.write(f"port = {b.port}\nprimary_slot_name = 'node2_standby'\n")
    sh(f"{PG}/pg_ctl", "start", "-D", b.data, "-w", "-l", b.data + ".log")
    with open(os.path.join(root, "vip"), "w") as f:
        f.write("node1")
    return a, b


class Writer(threading.Thread):
    """A row every 0.2 s through the stand-in address; records every acknowledged row and every gap."""

    def __init__(self, root: str, boxes: dict):
        super().__init__(daemon=True)
        self.vip, self.boxes = os.path.join(root, "vip"), boxes
        self.acked: list[int] = []
        self.both_writable = 0
        self.stop = threading.Event()
        self.n = 0
        self.last_ok = time.monotonic()
        self.gaps: list[float] = []

    def run(self):
        while not self.stop.is_set():
            self.n += 1
            try:
                h = open(self.vip).read().strip()
            except FileNotFoundError:
                h = None
            ok = False
            if h in self.boxes:
                ok = self.boxes[h].sql(f"insert into w (n) values ({self.n}) returning n") == str(self.n)
            # the invariant, measured from outside: both instances answering as primaries
            prim = [x for x in self.boxes.values() if x.running() and x.sql("select pg_is_in_recovery()") == "f"]
            if len(prim) > 1:
                self.both_writable += 1
            now = time.monotonic()
            if ok:
                if now - self.last_ok > 1.0:
                    self.gaps.append(round(now - self.last_ok, 1))
                self.last_ok = now
                self.acked.append(self.n)
            time.sleep(0.2)


class Rehearsal:
    def __init__(self, root: str):
        self.root = root
        self.a, self.b = setup(root)
        self.boxes = {"node1": self.a, "node2": self.b}
        self.vstop = threading.Event()
        self.vthread = None
        self.agents, self.stops = {}, {}
        self.start_voter()
        for name in self.boxes:
            self.start_agent(name)
        self.w = Writer(root, self.boxes)
        self.w.start()
        self.record = []

    def start_voter(self):
        self.vstop = threading.Event()
        state = os.path.join(self.root, "voter-state.json")
        if not os.path.exists(state):
            json.dump({"holder": "node1", "epoch": 1}, open(state, "w"))
        self.vthread = threading.Thread(target=daemon.run_voter, args=(KEY, state), daemon=True,
                                        kwargs=dict(bind=("127.0.0.1", 18741), stop=self.vstop,
                                                    log_path=os.path.join(self.root, "voter.jsonl")))
        self.vthread.start()

    def start_agent(self, name):
        port = {"node1": 18742, "node2": 18743}
        peer = "node2" if name == "node1" else "node1"
        st = os.path.join(self.root, f"agent-{name}.json")
        if not os.path.exists(st) and name == "node1":
            json.dump({"held_epoch": 1}, open(st, "w"))
        ag = daemon.Agent(name, peer, KEY, voter_addr=("127.0.0.1", 18741), peer_addrs=[("127.0.0.1", port[peer])],
                          actions=ScratchActions(self.boxes[name], os.path.join(self.root, "vip")), state_path=st,
                          bind=("127.0.0.1", port[name]), log_path=os.path.join(self.root, f"agent-{name}.jsonl"))
        stop = threading.Event()
        threading.Thread(target=ag.run, args=(stop,), daemon=True).start()
        self.agents[name], self.stops[name] = ag, stop

    def kill_box(self, name):
        self.stops[name].set()
        time.sleep(0.5)
        self.agents[name].w.sock.close()
        sh(f"{PG}/pg_ctl", "stop", "-D", self.boxes[name].data, "-m", "immediate", check=False)

    def roles(self):
        return {n: a.a.role for n, a in self.agents.items() if not self.stops[n].is_set()}

    def wait(self, cond, limit) -> float | None:
        t0 = time.monotonic()
        while time.monotonic() - t0 < limit:
            if cond():
                return round(time.monotonic() - t0, 1)
            time.sleep(0.25)
        return None

    def step(self, name, seconds, ok):
        self.record.append({"step": name, "seconds": seconds, "ok": bool(ok), "roles": self.roles(),
                            "both_writable_samples": self.w.both_writable})
        print(json.dumps(self.record[-1]), flush=True)

    def primary(self):
        r = self.roles()
        p = [n for n, x in r.items() if x == "primary"]
        return p[0] if len(p) == 1 else None

    def run(self):
        time.sleep(20)
        self.step("1 steady", 20, self.primary() == "node1" and self.roles()["node2"] == "standby")

        acked_before = len(self.w.acked)
        self.kill_box("node1")
        t = self.wait(lambda: self.primary() == "node2" and len(self.w.acked) > acked_before + 5, 120)
        self.step("2 the primary dies: node2 takes over (s)", t, t is not None)

        self.start_agent("node1")
        t = self.wait(lambda: self.roles().get("node1") == "standby", 300)
        self.step("3 node1 returns and rejoins as the standby (s)", t, t is not None and self.primary() == "node2")

        time.sleep(5)
        g0 = len(self.w.gaps)
        out, acts = self.agents["node2"].a.switchover(time.monotonic())
        self.agents["node2"]._emit(out, acts)
        t = self.wait(lambda: self.primary() == "node1", 120)
        self.step("4 planned switchover to node1 (s)", t, t is not None)
        self.wait(lambda: self.roles().get("node2") == "standby", 300)
        self.step("4b node2 back as the standby; the writer's longest gap (s)", max(self.w.gaps[g0:] or [0]),
                  self.roles().get("node2") == "standby")

        for n in self.boxes:
            self.agents[n].drop = {"node2" if n == "node1" else "node1"}
        time.sleep(70)
        for n in self.boxes:
            self.agents[n].drop = set()
        self.step("5 cable pulled 70 s: nothing changes", 70, self.primary() == "node1")

        self.vstop.set(); self.vthread.join(5)
        time.sleep(70)
        self.start_voter()
        time.sleep(5)
        self.step("6 voter down 70 s: nothing changes", 70, self.primary() == "node1")

        acked_before = len(self.w.acked)
        self.agents["node1"].drop = {"voter", "node2"}
        t1 = self.wait(lambda: self.roles().get("node1") == "down", 120)
        t2 = self.wait(lambda: self.primary() == "node2" and len(self.w.acked) > acked_before + 5, 120)
        self.step("7 node1 cut off from both: fenced after (s)", t1, t1 is not None)
        self.step("7b node2 took over after a further (s)", t2, t2 is not None)
        self.agents["node1"].drop = set()
        t = self.wait(lambda: self.roles().get("node1") == "standby", 400)
        self.step("7c healed: node1 rejoined as the standby (s)", t, t is not None)

        self.w.stop.set(); self.w.join(5)
        final = self.boxes[self.primary()] if self.primary() else None
        have = set()
        if final:
            have = {int(x) for x in (final.sql("select string_agg(n::text, ',') from w") or "").split(",") if x}
        lost = [n for n in self.w.acked if n not in have]
        self.step(f"8 acknowledged writes {len(self.w.acked)}, missing on the final primary {len(lost)} {lost[:20]}",
                  None, final is not None)
        self.step("9 moments both instances answered as primaries", self.w.both_writable, self.w.both_writable == 0)
        for n in list(self.agents):
            self.stops[n].set()
        self.vstop.set()
        time.sleep(1)
        for bx in self.boxes.values():
            sh(f"{PG}/pg_ctl", "stop", "-D", bx.data, "-m", "fast", check=False)
        with open(os.path.join(self.root, "rehearsal.json"), "w") as f:
            json.dump(self.record, f, indent=1)
        return all(r["ok"] for r in self.record)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="/var/tmp/qv4-takeover-rehearsal")
    a = ap.parse_args()
    ok = Rehearsal(a.dir).run()
    print("REHEARSAL", "PASSED" if ok else "FAILED", flush=True)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
