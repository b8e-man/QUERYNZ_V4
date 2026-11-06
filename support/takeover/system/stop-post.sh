#!/bin/bash
# qv4-roled stopped (by hand, by a crash, or by its watchdog): a box whose agent is gone must not stay a
# writable primary, because nothing renews its lease and the standby takes over when it runs out. So unless
# maintenance holds the role (`/run/qv4-takeover/hold`, written by `python -m support.takeover hold on`),
# a box that was primary, promoting or fencing is fenced; a fence that does not finish in 4 s restarts the box.
JOB=stop-post; . "$(dirname "$0")/lib.sh"
role=$(cat /run/qv4-takeover/role 2>/dev/null || echo unknown)
if [ -e /run/qv4-takeover/hold ]; then say "agent stopped as $role under maintenance hold: no fence"; exit 0; fi
case "$role" in
  primary|promoting|fencing)
    say "agent stopped as $role: fencing"
    timeout 4 "$(dirname "$0")/fence.sh" && exit 0
    say "fence did not finish in 4 s: restarting the box"
    systemctl reboot --force --force ;;
  *) say "agent stopped as $role: nothing to fence" ;;
esac
