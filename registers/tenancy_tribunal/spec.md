owns: schema `tenancy_tribunal` (`orders`: order and application numbers, dates, source URL, document hash; `listings`: the source's count per month; `set_aside`); `tenancy_tribunal_private` holds nothing yet. No name or address in either
reads: `forms.justice.govt.nz` (the Tribunal's order search: its listing service and the order PDFs), through the fetch gate and the landing wrapper only, under `docs/legal/positions/tenancy-tribunal-decisions.md` (case 3 of 1.10: captured once, politely)
publishes: nothing yet; capture and hold (public for three years only; the reading comes in step 5)
outside check: each published month's count on the source's listing against the orders held for that month (`check.py`)
jobs: `qv4-tenancy-tribunal-capture`, nightly off-peak, five seconds between requests, a budget per night (`capture.py`)
