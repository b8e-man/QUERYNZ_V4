owns: schema `disclosures` (large-donation disclosures over $20,000, by document hash) and `disclosures_private` (nothing published lives there)
reads: the Commission's disclosure files the old estate already holds under `var/staging/ec-donations/` (the `archive/` and `residue/donations_20k/` trees, taken by hash, read-only); fetches nothing until the public site is switched (step 4.1; ruling 241: no Wayback for this page)
publishes: `pub.disclosures` rows, one per declared donation, each citing its document; an amendment replaces only the declaration the Commission says it replaces
outside check: the Commission's own listing count of disclosures per year against the rows held
jobs: a `qv4-disclosures-read` job on the scheduler once the reading exists; no capture job before the switch
