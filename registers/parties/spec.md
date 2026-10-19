owns: schema `parties` (the Register of Political Parties and each party's lifecycle: registrations, renames, deregistrations, by document hash) and `parties_private` (nothing published lives there)
reads: the Commission's register pages and notices the old estate already holds under `var/staging/ec-party-register/`, taken by hash, read-only; fetches nothing until the public site is switched (step 4.1, copied and built)
publishes: `pub.parties` (one row per party with its registration window) and `pub.party_names` (every name a party has carried, with the window; a renamed party is the same party; four renames are known)
outside check: the Commission's own count of registered parties on a date against the rows live on that date
jobs: a `qv4-parties-load` job on the scheduler once the lane reads; no capture job before the switch
