A register published as a snapshot of current roles cannot clear a history: measure how many ended rows it keeps before a rule says "none", and block every clear that needs the past.
area: subject reports, products/templates, step 5.2 templates, flags, companies
paid-for-by: 2026-10-20, banking-1 session, step 5.2 (template 03)

The banking template asks "every company this person has touched, and how
each ended". Its first draft cleared a director of failed companies on
the companies the file listed. A count showed the file can never see the
rest: none of 1,185,805 director rows has an end date, and the 1,066,680
removed companies keep 4,888 directors between them. A company the person
left, or that was struck off with them on it, is not there, nor are its
liquidations. The fix in the template: one setting (`HISTORY = False`) that
turns every clear over the person's companies into "blocked", saying what
was seen and why the rest cannot be; a `past-roles` flag that says it on
every report; a test and a mutant that hold it. Before writing a "none
found" over a register, count its ended rows (`ended_on`, `removed_on`, the
files a row was seen in): an empty column is the register's shape, not a
clean record.
