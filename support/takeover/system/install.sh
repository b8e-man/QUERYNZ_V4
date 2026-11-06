#!/bin/bash
# Install the takeover jobs on THIS box from the release copy. Run with sudo on each box; safe to run twice.
#  1. the four scripts into /usr/local/libexec/qv4-takeover, the four units into /etc/systemd/system
#  2. the polkit rule: the estate's account may start qv4-release, qv4-takeover and qv4-rejoin, nothing else
#  3. qv4-role-guard enabled, so a box whose floating address is held elsewhere boots not-primary
#  4. the same access lines on both boxes (track A lesson 4): replication and pg_rewind from either box, and a
#     box reaching itself through the floating address; then a reload, never a restart
#  5. on the primary only, the four file functions pg_rewind reads through (they reach the standby by replay)
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
lib=/usr/local/libexec/qv4-takeover
install -d -m 755 "$lib"
install -m 755 "$src/lib.sh" "$src/release.sh" "$src/takeover.sh" "$src/rejoin.sh" "$src/role-guard.sh" "$lib/"
install -m 644 "$src/qv4-release.service" "$src/qv4-takeover.service" "$src/qv4-rejoin.service" \
  "$src/qv4-role-guard.service" /etc/systemd/system/
install -m 644 "$src/50-qv4-takeover.rules" /etc/polkit-1/rules.d/
touch /var/log/qv4-takeover.log; chmod 644 /var/log/qv4-takeover.log
restorecon -R "$lib" /etc/systemd/system/qv4-*.service /etc/polkit-1/rules.d/50-qv4-takeover.rules /var/log/qv4-takeover.log
systemctl daemon-reload
systemctl enable qv4-role-guard.service

hba=$(runuser -u postgres -- psql -XAtq -c 'show hba_file')
[ -e "$hba.before-takeover" ] || cp -a "$hba" "$hba.before-takeover"
added=0
while read -r line; do
  if ! grep -qxF "$line" "$hba"; then echo "$line" >> "$hba"; added=1; fi
done <<'EOF'
host replication replicator 10.0.0.1/32 scram-sha-256
host replication replicator 10.0.0.2/32 scram-sha-256
host postgres replicator 10.0.0.1/32 scram-sha-256
host postgres replicator 10.0.0.2/32 scram-sha-256
host all all samehost scram-sha-256
EOF
[ "$added" = 1 ] && runuser -u postgres -- psql -XAtq -c 'select pg_reload_conf()' > /dev/null
if [ "$(runuser -u postgres -- psql -XAtq -c 'select pg_is_in_recovery()')" = f ]; then
  runuser -u postgres -- psql -XAtq -d postgres -c "grant execute on function pg_ls_dir(text, boolean, boolean) to replicator;
    grant execute on function pg_stat_file(text, boolean) to replicator;
    grant execute on function pg_read_binary_file(text) to replicator;
    grant execute on function pg_read_binary_file(text, bigint, bigint, boolean) to replicator;" > /dev/null
fi
echo "access lines in force (errors would show in the last column):"
runuser -u postgres -- psql -XAtq -c "select line_number, type, database, user_name, address, error from pg_hba_file_rules
  where user_name && array['replicator'] or address = 'samehost' or error is not null"
echo "rewind grants: $(runuser -u postgres -- psql -XAtq -d postgres -c "select has_function_privilege('replicator', 'pg_read_binary_file(text, bigint, bigint, boolean)', 'execute')")"
echo "$(hostname -s): takeover jobs installed; role guard $(systemctl is-enabled qv4-role-guard.service)"
