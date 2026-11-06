#!/bin/bash
# qv4-takeover: this box, a standby, becomes the primary. Refuses while anything on the wire answers for the
# floating address (release it on the other box, or that box is off). Promotes with no password (the job runs
# as root and calls the database as postgres: track A lesson 1), reserves the other box's slot AT promotion
# (the 24 August drill's lesson), then takes the address and announces it.
JOB=takeover; . "$(dirname "$0")/lib.sh"
if has_vip && pg_up && ! in_recovery; then say "already the primary and holding $VIP"; exit 0; fi
pg_up || die "the database is not running on this box"
in_recovery || die "the database is not a standby (two primaries would follow)"
vip_free_on_wire || die "something on the wire answers for $VIP: release it there first (qv4-release) or power that box off"
# replay what was received before promoting, up to 30 s
recv=$(sql "select coalesce((select flushed_lsn from pg_stat_wal_receiver)::text, '')")
for _ in $(seq 1 30); do
  [ -z "$recv" ] && break
  [ "$(sql "select pg_last_wal_replay_lsn() >= '$recv'::pg_lsn")" = t ] && break
  sleep 1
done
say "promoting at replay $(sql 'select pg_last_wal_replay_lsn()') (received ${recv:-nothing: no sender})"
[ "$(sql 'select pg_promote(true, 60)')" = t ] || die "pg_promote did not finish in 60 s"
if in_recovery; then die "still in recovery after the promote"; fi
sql "select pg_create_physical_replication_slot('${PEER}_standby', true) where not exists (select 1 from pg_replication_slots where slot_name = '${PEER}_standby')" > /dev/null
rm -f "$MARKER"
systemctl enable --now querynz-vip.service
has_vip || ip addr add "$VIP/24" dev "$DEV"
has_vip || die "promoted, but $VIP did not come up on $DEV"
arping -U -q -I "$DEV" -c 3 "$VIP" || true
say "primary: timeline $(sql 'select timeline_id from pg_control_checkpoint()'), $VIP on $DEV, slot ${PEER}_standby reserved"
