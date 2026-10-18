Temperature 0 on the card is not reproducible: the same server, weights, prompt and page image read twice gave different text on 2 of 97 pages, so a reading is compared with a tolerance class (equal, near, far), never by equality alone, and a replay is the stored reading, not a re-read.
area: page readers, scheduler, scoring, stored readings
paid-for-by: 2026-10-19, trial session, step 3.5

Pass one matched the old estate's readings on 2,013 of 2,124 pages and
differed on 111; the plan says a difference points at the harness first.
Before chasing flags, measure the floor: pages shared by two documents
were read twice inside the one pass, and 2 of 97 differed (a word, a
digit). That floor is about 2% of pages and explains a third of the 111
by itself; the rest is the one flag that differs (`--jinja`). So: a
stored reading is the record (ruling 50) and every replay is exact; a
fresh read is not, and a test that expects byte-equal text from a
second read of the same page will fail on the card by design.
