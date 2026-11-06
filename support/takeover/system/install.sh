#!/bin/bash
# Install the takeover machinery on THIS box from the release copy. Run with sudo on each box; safe to run
# twice. INSTALLS, SWITCHES NOTHING ON: the role agent is installed disabled; `activate.sh` turns automatic
# takeover on, at the drill, on Arthur's word.
#  1. the agent's code (standard library only) into /usr/local/lib/qv4-takeover; the jobs' scripts into
#     /usr/local/libexec/qv4-takeover; the units qv4-roled, qv4-takeover, qv4-release, qv4-rejoin
#  2. /etc/qv4-takeover/agent.conf: this box, the other box, the voter, the other box's cable address
#  3. the polkit rule: the estate's account may start qv4-release, qv4-takeover, qv4-rejoin, nothing else
#  4. the agents' port (8742/udp) open on the cable zone and the home network zone
#  5. the same access lines on both boxes (replication and pg_rewind from either box; a box reaching itself
#     through the floating address; every estate login from either box, so the clients on the box that is not
#     primary still reach the floating address after a switchover); a reload, never a restart. On the primary only, the four file functions
#     pg_rewind reads through (they reach the standby by replay)
#  6. the old role guard, if an earlier install placed it, removed
set -euo pipefail
src=$(cd "$(dirname "$0")" && pwd)
pkg=$(cd "$src/.." && pwd)
me=$(hostname -s)
case "$me" in node1) peer=node2; peer_ip=10.0.0.2 ;; node2) peer=node1; peer_ip=10.0.0.1 ;; *) echo "not node1 or node2: $me"; exit 1 ;; esac

lib=/usr/local/lib/qv4-takeover
install -d -m 755 "$lib/support/takeover"
: > "$lib/support/__init__.py"; : > "$lib/support/takeover/__init__.py"
install -m 644 "$pkg/quorum.py" "$pkg/wire.py" "$pkg/daemon.py" "$pkg/__main__.py" "$lib/support/takeover/"
x=/usr/local/libexec/qv4-takeover
install -d -m 755 "$x"
install -m 755 "$src/lib.sh" "$src/release.sh" "$src/takeover.sh" "$src/rejoin.sh" "$src/fence.sh" \
  "$src/start-primary.sh" "$src/stop-post.sh" "$src/activate.sh" "$x/"
install -m 644 "$src/qv4-roled.service" "$src/qv4-release.service" "$src/qv4-takeover.service" \
  "$src/qv4-rejoin.service" /etc/systemd/system/
install -m 644 "$src/50-qv4-takeover.rules" /etc/polkit-1/rules.d/
install -d -m 755 /etc/qv4-takeover
cat > /etc/qv4-takeover/agent.conf <<EOF
# written by support/takeover/system/install.sh
box = $me
peer = $peer
voter = 192.168.68.57
peer_addrs = $peer_ip
key_file = /home/user/.querynz/voter.env
EOF
touch /var/log/qv4-takeover.log /var/log/qv4-takeover.jsonl
chmod 644 /var/log/qv4-takeover.log /var/log/qv4-takeover.jsonl
if [ -e /etc/systemd/system/qv4-role-guard.service ]; then
  systemctl disable qv4-role-guard.service || true
  rm -f /etc/systemd/system/qv4-role-guard.service "$x/role-guard.sh"
fi
restorecon -R "$lib" "$x" /etc/qv4-takeover /etc/systemd/system/qv4-*.service \
  /etc/polkit-1/rules.d/50-qv4-takeover.rules /var/log/qv4-takeover.log /var/log/qv4-takeover.jsonl
systemctl daemon-reload

for z in querynz-lan FedoraWorkstation; do
  firewall-cmd -q --permanent --zone="$z" --add-port=8742/udp
done
firewall-cmd -q --reload

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
host all qv4_owner,qv4_read,qv4_product,qv4_oldread,querynz,querynz_serving 10.0.0.1/32 scram-sha-256
host all qv4_owner,qv4_read,qv4_product,qv4_oldread,querynz,querynz_serving 10.0.0.2/32 scram-sha-256
EOF
if [ "$added" = 1 ]; then runuser -u postgres -- psql -XAtq -c 'select pg_reload_conf()' > /dev/null; fi
if [ "$(runuser -u postgres -- psql -XAtq -c 'select pg_is_in_recovery()')" = f ]; then
  runuser -u postgres -- psql -XAtq -d postgres -c "grant execute on function pg_ls_dir(text, boolean, boolean) to replicator;
    grant execute on function pg_stat_file(text, boolean) to replicator;
    grant execute on function pg_read_binary_file(text) to replicator;
    grant execute on function pg_read_binary_file(text, bigint, bigint, boolean) to replicator;" > /dev/null
fi
echo "access lines in force (errors would show in the last column):"
runuser -u postgres -- psql -XAtq -c "select line_number, type, database, user_name, address, error from pg_hba_file_rules
  where user_name && array['replicator'] or address = 'samehost' or address like '10.0.0.%' or error is not null order by 1"
echo "access file sha256: $(sha256sum "$hba" | cut -c1-16)"
echo "rewind grants: $(runuser -u postgres -- psql -XAtq -d postgres -c "select has_function_privilege('replicator', 'pg_read_binary_file(text, bigint, bigint, boolean)', 'execute')")"
echo "agent port: $(firewall-cmd --zone=querynz-lan --query-port=8742/udp) on the cable, $(firewall-cmd --zone=FedoraWorkstation --query-port=8742/udp) on the home network"
[ -r /home/user/.querynz/voter.env ] && echo "voter key: present" || echo "voter key: MISSING (/home/user/.querynz/voter.env)"
echo "$me: takeover machinery installed; qv4-roled $(systemctl is-enabled qv4-roled.service 2>/dev/null || true) (activate.sh turns it on)"
