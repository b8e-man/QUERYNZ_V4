# The primary loses its own database address when the twin cable is out
kind: finding
state: open
use-case: -
session: founding
opened: 2026-10-21

The twin LAN is a direct 10 GbE cable between node1 and node2, so each
box's `enp13s0` has carrier only while the other box is up. On 21 October
07:51 Arthur unplugged node2's cable to work on node1; NetworkManager
withdrew 10.0.0.2 and the floating address 10.0.0.10 from the port, and
every process on node2 lost the database it talks to through `db-primary`,
though Postgres kept running: the links reload failed mid-copy, the
legal-1 gate hung on its sample fill, the timers' runs failed, and the
box's hostname fell back to "fedora". The old estate fixed this for node1
on 14 September (`ops/production/system/NetworkManager-querynz-10g.conf`,
`ignore-carrier=yes` for enp13s0, installed by the C380 boot-order script)
but node2 never got it, and the 17 October failover made node2 the
primary without it.

What it needs: the same drop-in on node2 (Arthur's root lines, given 21
October 08:45) and a static hostname; in the new estate, node1's setup
card and the installer put the drop-in and the static hostname on both
boxes, and a checks-board item fails when the box holding the primary
role lacks its own address on the port. The fence (`/etc/querynz/
not-primary`) stays the guard against a re-plugged demoted box claiming
the address.

Done on node2, 21 October 08:57 (Arthur's hands): the drop-in installed,
NetworkManager reloaded, the profile and the floating address back with
the cable still out, the static hostname set to node2. What remains is the
new estate's half: both boxes by the installer and node1's setup card, and
the checks-board item.
