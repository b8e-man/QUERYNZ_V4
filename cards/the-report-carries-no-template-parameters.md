# The report carries no template parameters, so a reader cannot set the construction template's window
kind: finding
state: open
use-case: 7 construction and phoenix detection; every template with a reader's setting
session: construction-2
opened: 2026-10-21

Arthur's ruling 65 (21 October 2026): the phoenix window is the reader's
setting, not the template's. The construction template now sets every
dated failure beside every going company whatever the gap, nearest first,
and cuts only when the report carries `report["window_days"]` (a whole
number of days either side of the failure's Gazette date); it reads that
key the way a rule reads `report["since"]`. The shape passes no such key:
`since` is its one reader's value, threaded by name through `build.build`,
`server.build_report`, the page's `?since=` and the command line's
`--since`. So today no reader can narrow the list, and every gap is shown.

For the report lane: carry template parameters generally rather than one
named argument per setting. A query parameter on the page and `--param
KEY=VALUE` on the command line, passed to `build` and placed on the
report under its key (or under `report["parameters"]`, with the contract
saying which), each template declaring the keys it reads in its
`template.toml` so the page can offer them and refuse an unknown one. The
first key is `window_days` (template `construction`, read in
`products/templates/07-construction/rules.py`, `_window_days`); a value
that is not a whole number of days is shown as "no cut is applied" by the
template. If the lane chooses `report["parameters"]`, the template's
`WINDOW_KEY` read moves with it (a fix there).
