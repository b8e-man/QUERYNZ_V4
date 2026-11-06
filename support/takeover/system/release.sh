#!/bin/bash
# qv4-release: this box gives up the primary role (a planned switchover, or a fence). Marks the box
# not-primary, takes the floating address off it and stops its database cleanly, so the other box can take
# over and this one can rejoin as the standby with no rewind needed.
JOB=release; . "$(dirname "$0")/lib.sh"
mkdir -p "$(dirname "$MARKER")"; touch "$MARKER"
for u in querynz-vip-bridge.service querynz-vip.service; do
  systemctl disable --now "$u" 2>/dev/null || true
done
if has_vip; then ip addr del "$VIP/24" dev "$DEV"; fi
if has_vip; then die "the floating address $VIP is still on $DEV"; fi
if pg_up && ! in_recovery; then
  sql 'checkpoint' > /dev/null
  say "stopping the primary database cleanly at $(sql 'select pg_current_wal_lsn()')"
  systemctl stop postgresql
fi
say "released: not-primary marked, $VIP off this box, database $(pg_up && echo 'up as standby' || echo stopped)"
