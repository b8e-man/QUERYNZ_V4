# node2 lost its wired link, and an orphaned links load holds the links locks
kind: blocker
state: open
use-case: estate (step 0 boxes); links (4.2); every product reading pub.links
session: ownership-1
opened: 2026-10-21

At 07:50:59 on 21 October both of node2's wired ports went to no carrier
(`enp13s0: atlantic: link change old 10 new 0`; enp12s0 down too); the box
is on wifi only, so 10.0.0.2 and the database address 10.0.0.10 are gone
and `db-primary` does not answer. Postgres itself runs and answers on
127.0.0.1. Every connection made over 10.0.0.x before the drop is stuck in
a zero-window probe. The links reload started 07:49:59 (`links.build_all
--schema links`) failed on the client side at 08:24 (connection timeout),
but its server backend (a COPY by qv4_owner from 10.0.0.2:45734) still
holds AccessExclusive on `links.decisions`, `links.old_decisions` and
`links.readings`, so every read of `pub.links` waits past its time limit:
the report shape, the board and every template checkpoint. TCP keepalive
would end it near 10:00. For Arthur: the cable or switch between node2 and
node1 (the link was at 10 Mb/s before it dropped). For the integrator:
terminate that backend, re-run the reload once the link is back, and
check the VIP unit restored 10.0.0.10. Seen by ownership-1, which read
through 127.0.0.1 (PGHOSTADDR) with the session reader.
