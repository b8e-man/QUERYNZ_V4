owns: schema `mp_interests` (the Register of Pecuniary and Other Specified Interests of Members of Parliament, every edition, one row per member and category, keyed on the category heading, never its number) and `mp_interests_private` (nothing published lives there)
reads: the published editions as files, by hash (step 1.10: find in the baseline whether the old estate holds them; if not, card it and read what is held); fetches nothing until Arthur says so
publishes: `pub.mp_interests` (member, edition, category, the declared item as printed, citation)
outside check: the edition's own count of members against the rows for that edition
jobs: a `qv4-mp-interests-load` job on the scheduler once the lane reads; no capture job before the switch
