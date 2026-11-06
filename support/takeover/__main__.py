"""python -m support.takeover <command>

  agent --config FILE     a box's role agent (run by qv4-roled, as root)
  voter [--state FILE]    the voter (run by qv4-voter on the third machine)
  status                  this box's agent: role, epoch, lease left, last lines
  switchover              move the primary role to the other box now (from the primary; checkpoint first)
  hold on|off             maintenance: the voter grants no new holder; this box's agent may stop without fencing
  keygen [FILE]           write a new QV4_VOTER_KEY into ~/.querynz/voter.env (never printed); copy the file
                          to the other two machines with scp
"""
from __future__ import annotations

import json
import os
import secrets
import sys

from support.takeover import daemon, wire

KEYFILE = os.path.expanduser("~/.querynz/voter.env")


def conf(path: str) -> dict:
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "keygen":
        path = rest[0] if rest else KEYFILE
        if os.path.exists(path):
            print(f"{path} exists; not replaced")
            return 1
        os.makedirs(os.path.dirname(path), mode=0o700, exist_ok=True)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(f"QV4_VOTER_KEY={secrets.token_hex(32)}\n")
        print(f"written {path} (0600)")
        return 0
    if cmd == "voter":
        state = rest[rest.index("--state") + 1] if "--state" in rest else os.path.expanduser(
            "~/.local/state/qv4-voter/state.json")
        os.makedirs(os.path.dirname(state), exist_ok=True)
        daemon.run_voter(wire.load_key(KEYFILE), state, log_path=os.path.join(os.path.dirname(state), "voter.jsonl"))
        return 0
    if cmd == "agent":
        c = conf(rest[rest.index("--config") + 1])
        key = wire.load_key(c.get("key_file", "/home/user/.querynz/voter.env"))
        voter = (c["voter"], int(c.get("voter_port", daemon.VOTER_PORT)))
        peers = [(a.strip(), daemon.AGENT_PORT) for a in c["peer_addrs"].split(",") if a.strip()]
        ag = daemon.Agent(c["box"], c["peer"], key, voter_addr=voter, peer_addrs=peers, actions=daemon.LiveActions(),
                          state_path="/var/lib/qv4-takeover/state.json", role_path="/run/qv4-takeover/role",
                          log_path="/var/log/qv4-takeover.jsonl", notify=True)
        ag.run()
        return 0
    key = wire.load_key(KEYFILE if os.path.exists(KEYFILE) else "/home/user/.querynz/voter.env")
    if cmd == "status":
        r = daemon.control(key, "status")
        print(json.dumps(r, indent=1) if r else "no answer from the agent on this box")
        return 0 if r else 1
    if cmd == "switchover":
        r = daemon.control(key, "switchover", timeout=60)
        print(json.dumps(r) if r else "no answer from the agent on this box")
        return 0 if r and r.get("ok") else 1
    if cmd == "hold":
        on = (rest[:1] or ["on"])[0] == "on"
        c = conf("/etc/qv4-takeover/agent.conf")
        w = wire.Wire("ctl", key, ("0.0.0.0", 0))
        w.send((c["voter"], daemon.VOTER_PORT), {"op": "hold", "on": on, "box": "ctl"})
        got = w.recv(3)
        if on:
            open("/run/qv4-takeover/hold", "w").close()
        elif os.path.exists("/run/qv4-takeover/hold"):
            os.unlink("/run/qv4-takeover/hold")
        print(json.dumps(got[1]) if got else "no answer from the voter")
        return 0 if got else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
