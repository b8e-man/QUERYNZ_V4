owns: schema `real_estate_authority` (`cases`: case number, year, decision date, deciding body, abstract hash; `documents`: each decision PDF's hash and complaint number; `listings`: the source's count per year; `set_aside`); `real_estate_authority_private` holds nothing yet. No name or address in either
reads: `decisions.dotnous.com/reaa/` (the Authority's decisions database: listings, abstracts, PDFs), through the fetch gate and the landing wrapper only, under `docs/legal/positions/real-estate-authority-decisions.md` (case 3 of 1.10: captured once, politely)
publishes: nothing yet; capture and hold (on the public register for three years; the reading comes in step 5)
outside check: each year's "Search Results (N)" on the database against the cases held for that year (`check.py`)
jobs: `qv4-real-estate-authority-capture`, nightly off-peak, five seconds between requests, a budget per night (`capture.py`)
