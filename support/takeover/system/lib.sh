# THE TAKEOVER JOBS' COMMON PART (ruling 145, continuous uptime). Sourced by release.sh, takeover.sh,
# rejoin.sh and role-guard.sh. Every path and command is overridable so the tests run them with stand-ins.
set -euo pipefail
VIP=${QV4_VIP:-10.0.0.10}
DEV=${QV4_DEV:-enp13s0}
PGDATA=${QV4_PGDATA:-/var/lib/pgsql/data}
MARKER=${QV4_MARKER:-/etc/querynz/not-primary}
CREDS=${QV4_REPLICATION_ENV:-/home/user/.querynz/replication.env}
LOG=${QV4_TAKEOVER_LOG:-/var/log/qv4-takeover.log}
SYSNET=${QV4_SYSNET:-/sys/class/net}
# the box's name from the takeover's own config, never the hostname alone: a box with no static hostname takes
# one from the floating address's /etc/hosts entry when it holds it (node1 became "db-primary", 6 November 2026)
AGENT_CONF=${QV4_AGENT_CONF:-/etc/qv4-takeover/agent.conf}
ME=${QV4_BOX:-$(sed -n 's/^box *= *//p' "$AGENT_CONF" 2>/dev/null || true)}
ME=${ME:-$(hostname -s)}
# the peer is named only to name its slot; no job here reaches the peer by its address (track A lesson 5)
case "$ME" in node1) PEER=node2 ;; node2) PEER=node1 ;; *) PEER=${QV4_PEER:?unknown box $ME} ;; esac

say() { echo "$(date -Is) $ME $JOB: $*" | tee -a "$LOG"; }
die() { say "REFUSED: $*"; exit 1; }
sql() { runuser -u postgres -- psql -XAtq -d postgres -c "$1"; }
has_vip() { ip -4 -o addr show dev "$DEV" | grep -q " $VIP/"; }
# duplicate-address probe: exit 0 when NOTHING on the wire answers for the address (track A lesson 2)
vip_free_on_wire() { arping -D -q -I "$DEV" -c 3 -w 4 "$VIP"; }
pg_up() { systemctl is-active -q postgresql; }
in_recovery() { [ "$(sql 'select pg_is_in_recovery()')" = t ]; }
receiver() { sql "select coalesce((select status from pg_stat_wal_receiver), '')"; }
cred() { sed -n "s/^$1=//p" "$CREDS"; }
