#!/bin/bash
# qv4 start as primary: the agent's START_PRIMARY, run only on the voter's word that this box held the role
# last and nobody has held it since. Starts the database (never a standby: that is the rejoin's), then takes
# the floating address.
JOB=start-primary; . "$(dirname "$0")/lib.sh"
[ -e "$PGDATA/standby.signal" ] && die "standby.signal present: this box was a standby, it rejoins instead"
vip_free_on_wire || die "something on the wire answers for $VIP"
pg_up || systemctl start postgresql
for _ in $(seq 1 60); do pg_up && sql 'select 1' > /dev/null 2>&1 && break; sleep 1; done
pg_up || die "the database did not start"
if in_recovery; then die "the database came up in recovery"; fi
rm -f "$MARKER"
has_vip || ip addr add "$VIP/24" dev "$DEV"
has_vip || die "$VIP did not come up on $DEV"
arping -U -q -I "$DEV" -c 3 "$VIP" || true
say "primary again: $VIP on $DEV"
