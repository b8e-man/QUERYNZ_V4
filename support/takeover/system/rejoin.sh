#!/bin/bash
# qv4-rejoin: this box comes back as the standby of whichever box holds the floating address. Never while this
# box holds it. Rewinds onto the primary's timeline (only the changed blocks; data checksums are on), points
# the standby at the floating address and its own slot, and starts it.
JOB=rejoin; . "$(dirname "$0")/lib.sh"
if has_vip; then die "this box holds $VIP: it is the primary"; fi
if vip_free_on_wire; then die "nothing answers for $VIP: there is no primary to follow"; fi
mkdir -p "$(dirname "$MARKER")"; touch "$MARKER"
systemctl disable --now querynz-vip-bridge.service querynz-vip.service 2>/dev/null || true
if pg_up && in_recovery && [ "$(receiver)" = streaming ]; then say "already a streaming standby"; exit 0; fi
if pg_up; then systemctl stop postgresql; fi
u=$(cred REPLICATION_USER); p=$(cred REPLICATION_PASSWORD)
[ -n "$u" ] && [ -n "$p" ] || die "no replication login in $CREDS"
say "rewinding onto the primary at $VIP"
# pg_rewind runs crash recovery itself on a box that went down hard (PG 13 on), so no start-stop is needed
if ! PGPASSWORD="$p" runuser -u postgres -- pg_rewind --target-pgdata="$PGDATA" \
     --source-server="host=$VIP port=5432 user=$u dbname=postgres" --progress; then
  die "pg_rewind refused: the fallback is a full copy (the standby rebuild), not automatic"
fi
# 'no rewind required' writes no recovery settings (the 24 August drill), so they are always written here
auto="$PGDATA/postgresql.auto.conf"
sed -i -e '/^primary_conninfo *=/d' -e '/^primary_slot_name *=/d' "$auto"
printf "primary_conninfo = 'host=%s port=5432 user=%s password=%s application_name=%s'\nprimary_slot_name = '%s_standby'\n" \
  "$VIP" "$u" "$p" "$ME" "$ME" >> "$auto"
touch "$PGDATA/standby.signal"
chown postgres:postgres "$PGDATA/standby.signal" "$auto"
systemctl enable --now postgresql
for _ in $(seq 1 60); do
  [ "$(receiver 2>/dev/null)" = streaming ] && break
  sleep 2
done
in_recovery || die "the database came up as a primary"
[ "$(receiver)" = streaming ] || die "standby up but not streaming"
say "standby of $VIP, streaming on slot ${ME}_standby"
