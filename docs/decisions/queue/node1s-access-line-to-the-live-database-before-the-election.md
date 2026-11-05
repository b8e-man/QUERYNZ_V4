# node1's worker needs an access line on the live database server; hard limit 22 says not before the election
default: no default
blocks: qv4-worker@node1 and every two-box proof of step 2 (cards/node1-setup-as-the-second-box.md, line 4)
recommendation: Rule that one line in node2's pg_hba.conf for the new estate's own logins from 10.0.0.1 (qv4_* roles, database querynz_v4 and querynz_v4_sample, scram) may go in before 7 November. It adds a client; it changes no setting the old estate's jobs or the frozen site use, and the release reads nothing through it. Otherwise it goes in on 8 November.
raised: 2026-11-05 by integrator-9d788fb (node1's return)

node1 came back on 5 November and connects through 10.0.0.10 as it
should. The server answered `FATAL: no pg_hba.conf entry for host
"10.0.0.1", user "qv4_read", database "querynz_v4"`. The server is the
live one the frozen product stands on, and hard limit 22 puts changes to
"its database server settings" on Arthur's word and not before the
election. Only Arthur can say whether an added client line counts.
