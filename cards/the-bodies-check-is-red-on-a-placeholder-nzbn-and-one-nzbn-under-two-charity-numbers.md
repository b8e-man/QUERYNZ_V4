# The bodies check is red: a placeholder NZBN of thirteen zeros and one NZBN under two charity numbers
kind: finding
state: closed
use-case: -
session: integrator-9d788fb
opened: 2026-10-30
closed: 2026-10-30 (fix-links-6: an all-zero NZBN is none; the charities of one NZBN are one body, the earliest row; the check's count becomes 0 at the next `qv4-links-build`)

`python -m links.check` on live after the @3 build (30 October, 12:4x) has one red item: "a body on two
registers is one body: no NZBN names two bodies", `nzbns_on_two_bodies: 2`. Every other item is green.

1. The charities register publishes `0000000000000` where it holds no NZBN. 35 charities rows carry it in
   `links.bodies` (three of them under a Companies Office body, 32 as their own body). The bodies build should
   read an all-zero NZBN as none, as it reads blank; then nothing joins on it.
2. NZBN 9429049642469 sits on two charity numbers, CC58580 (registered 2020, deregistered February 2023) and
   CC61425 (registered July 2023 under a changed name). The NZBN names one entity, so the design says one body:
   the Companies Office row where there is one, else the earliest charities row. Today each charity number is its
   own body.

The red is older than today's merges: `links.bodies` is built the same by links-4 and links-5, and the check has
not been run on live since the bodies table came (1f14161). The item ran with `exit 1`; a fix session on links/
takes both lines and reruns the check.
