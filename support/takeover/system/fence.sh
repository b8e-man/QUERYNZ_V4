#!/bin/bash
# qv4 fence: this box stops accepting writes NOW. The floating address off first (every writer reaches the
# primary through it), then the database stopped immediately: no shutdown checkpoint, which on a busy primary
# can take longer than the agent's 4 s fence limit; the rejoin's rewind runs the recovery. Marks the box
# not-primary for the old address unit. Exit 0 only when the database is down.
JOB=fence; . "$(dirname "$0")/lib.sh"
mkdir -p "$(dirname "$MARKER")"; touch "$MARKER"
if has_vip; then ip addr del "$VIP/24" dev "$DEV" || true; fi
if pg_up; then
  systemctl kill -s SIGQUIT --kill-whom=main postgresql || true
  systemctl stop postgresql || true
fi
if pg_up; then die "the database is still running"; fi
say "fenced: $VIP off, database stopped"
