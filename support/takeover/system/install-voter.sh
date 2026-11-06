#!/bin/bash
# Install or update the voter on the third machine, from node2 (or node1), as the estate's user:
#   bash support/takeover/system/install-voter.sh [arthur@192.168.68.57]
# Copies the voter's code (standard library only) to ~/qv4-takeover there, places the user unit qv4-voter,
# turns lingering on so it runs with nobody logged in, and (re)starts it. The key file ~/.querynz/voter.env
# must already be there (copied once, by hand, from a box).
set -euo pipefail
dest=${1:-arthur@192.168.68.57}
pkg=$(cd "$(dirname "$0")/.." && pwd)
ssh -o BatchMode=yes "$dest" 'mkdir -p ~/qv4-takeover/support/takeover ~/.config/systemd/user ~/.local/state/qv4-voter
  : > ~/qv4-takeover/support/__init__.py; : > ~/qv4-takeover/support/takeover/__init__.py'
scp -q -o BatchMode=yes "$pkg/quorum.py" "$pkg/wire.py" "$pkg/daemon.py" "$pkg/__main__.py" "$dest:qv4-takeover/support/takeover/"
scp -q -o BatchMode=yes "$pkg/system/qv4-voter.service" "$dest:.config/systemd/user/qv4-voter.service"
ssh -o BatchMode=yes "$dest" 'test -r ~/.querynz/voter.env || { echo "no ~/.querynz/voter.env on the voter"; exit 1; }
  loginctl enable-linger "$USER"
  systemctl --user daemon-reload
  systemctl --user enable qv4-voter.service >/dev/null 2>&1
  systemctl --user restart qv4-voter.service
  sleep 2
  systemctl --user is-active qv4-voter.service
  tail -2 ~/.local/state/qv4-voter/voter.jsonl 2>/dev/null || true'
