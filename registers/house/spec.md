owns: schema `house` (candidates at each election and by-election, electorates, results, and who sits in the House and when, by document hash) and `house_private` (nothing published lives there)
reads: the Commission's files the old estate already holds under `var/staging/ec-candidate-list/`, `ec-results/` and `ec-byelections/`, taken by hash, read-only; fetches nothing until the public site is switched (step 4.1, built; boundary shapes need a key that is Arthur's to place)
publishes: `pub.candidates` (person, party, electorate or list place, election), `pub.electorates` (name, election, joined to Stats NZ's name), `pub.members` (who sat, from when to when, by what route), each with its citation
outside check: the Commission's own count of candidates at an election against the rows; electorate names join Stats NZ's 72 of 72
jobs: a `qv4-house-load` job on the scheduler once the lane reads; no capture job before the switch
