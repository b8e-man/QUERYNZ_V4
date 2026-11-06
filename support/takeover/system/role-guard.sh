#!/bin/bash
# qv4-role-guard: at boot, before the database and the floating address. A box that thinks it is the primary
# (no not-primary marker) asks the wire whether the floating address is held elsewhere; if it is, the box
# marks itself not-primary and its database comes up in recovery, never as a second primary (track A
# lesson 3). The wire is asked only once the 10 GbE link has carrier; a box alone on a dead link keeps its
# role (the 15 September cold-start drill, with node2 off).
JOB=role-guard; . "$(dirname "$0")/lib.sh"
if [ -e "$MARKER" ]; then say "marked not-primary; nothing to guard"; exit 0; fi
carrier() { [ "$(cat "$SYSNET/$DEV/carrier" 2>/dev/null)" = 1 ]; }
for _ in $(seq 1 "${QV4_LINK_WAIT:-40}"); do carrier && break; sleep 1; done
if ! carrier; then say "no carrier on $DEV; keeping the primary role"; exit 0; fi
if vip_free_on_wire; then say "$VIP is free on the wire; keeping the primary role"; exit 0; fi
mkdir -p "$(dirname "$MARKER")"; touch "$MARKER"
if [ -e "$PGDATA/PG_VERSION" ] && [ ! -e "$PGDATA/standby.signal" ]; then
  touch "$PGDATA/standby.signal"; chown postgres:postgres "$PGDATA/standby.signal"
fi
say "GUARDED: $VIP is held by another box; marked not-primary, the database starts in recovery. Rejoin with qv4-rejoin"
