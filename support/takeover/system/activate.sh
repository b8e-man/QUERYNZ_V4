#!/bin/bash
# Turn automatic takeover ON for this box (the drill, on Arthur's word). Run with sudo on the PRIMARY first, then
# on the standby (a standby's agent alone would hear no primary for 30 s and ask for the role). Safe to run twice.
#  - the old address unit off for good: the role agent and its jobs own 10.0.0.10 now
#  - the database no longer starts at boot by itself: the agent asks the voter first and starts it as the
#    primary (only if this box held the role last and nobody has since) or as the standby
#  - qv4-roled enabled and started
# Undo (back to the hand drill): systemctl disable --now qv4-roled; systemctl enable postgresql; and on the
# primary only, systemctl enable querynz-vip.
set -euo pipefail
systemctl disable querynz-vip-bridge.service querynz-vip.service 2>/dev/null || true
systemctl disable postgresql.service
systemctl enable --now qv4-roled.service
sleep 3
PYTHONPATH=/usr/local/lib/qv4-takeover python3 -m support.takeover status || true
