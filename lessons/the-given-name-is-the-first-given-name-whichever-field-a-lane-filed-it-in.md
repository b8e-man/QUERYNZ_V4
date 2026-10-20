Read the first given name as the given name and the rest as middle names whichever field a lane filed them in: a lane that files every given name in one field ("Louise Claire", surname "UPSTON") was keyed "louise claire upston" and met no other register's "Louise UPSTON".
area: links, keys, the shared reading of names, a new lane's name columns
paid-for-by: 2026-10-20, links-2, step 4.2

The candidate-returns lane publishes `given_names` and `surname`; the links
read them as the directors' `first_name` and `last_name`, so the first-and-
last key took every given name. All 385 filing candidates and 52,939
Gazette bankrupts with more than one given name would have been keyed apart
from their own director, candidate and seat rows, and rule 1 could never
compare their middle names. The one-line reading (`keys.names.person_name`)
already splits "UPSTON, Louise Claire" into Louise and Claire; the parts
reading now does the same, so the two agree (`links.rows.read_name`). When a
lane's name columns arrive, read ten rows through both paths and compare the
keys before trusting a match count.
