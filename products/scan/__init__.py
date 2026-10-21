"""The register scan shape (plan step 6.1).

A scan is a saved question asked of every row of a register or a join of
registers, declared in a template file: the question in words, the
published views it reads with their licences, the join it makes as a chain
of steps, and the trust rule it applies through the links. One runner runs
every scan the same way: it compiles the steps to one query over `pub`,
streams the answers, grades each line (confirmed, near, contested) under
the two trust settings, numbers every citation once as the report does,
flags hubs, records the freshness of every view it read, times itself, and
writes the list into the product's own schema. A page on the local network
lists the answers in pages; a CSV and a JSON carry them away, each line
with its citations.

What a scan never does: join two facts with a word of cause; show a
person's home address or a suppressed name; count an absence as a finding;
read the inside of a lane (it reads `pub.*` only, on the product reader);
write into the estate (it writes its own schema only); feed the public site.

  python -m products.scan run NAME [--limit N] [--note TEXT]   run one scan
  python -m products.scan run --stale                           re-run every scan a view has loaded since
  python -m products.scan stale                                 which scans are stale, and why
  python -m products.scan export NAME [--run ID] --out DIR     answers.csv, answers.json, citations.csv
  python -m products.scan serve [--port N]                      the page, local network only
  python -m products.scan check                                 the outside check against the real tables
  python -m products.scan sql NAME                              the query a scan compiles to

Modules: views (what a scan may read), settings (the two trust settings),
template (a scan's file), plan (steps to SQL), lines (a joined row to a
graded, cited line), hubs, run (the runner and the stale rule), state (its
own schema), out (CSV, JSON, HTML), server, rules (what a list may show),
check. A scan template under products/scan/templates/<name>/ is data; the
four use-case templates of step 6.2 follow the same file."""
VERSION = "0.1"
