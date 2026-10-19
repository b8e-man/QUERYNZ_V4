owns: schema `gazette` (New Zealand Gazette notices the old estate holds as text: party events, public appointments, insolvency, prohibitions; one row per notice, by the export's hash and the notice number) and `gazette_private` (nothing published lives there)
reads: the old news database's `gazette` schema and its article text, exported once to a dated file and landed by hash (step 1.10 case two, as `registers/parties/capture.py` did for the register's notices); fetches nothing until the public site is switched (step 4.1, built)
publishes: `pub.gazette_notices` (every notice with its type, date and address), `pub.gazette_appointments`, `pub.gazette_insolvencies`, `pub.gazette_prohibitions`, each row with its citation
outside check: the Gazette's own count of notices under one type for one month against the lane's rows
jobs: a `qv4-gazette-load` job on the scheduler once the lane reads; no capture job before the switch
