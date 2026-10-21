# The report carries no template parameters, so a reader cannot set the construction template's window
kind: finding
state: closed
use-case: 7 construction and phoenix detection; every template with a reader's setting
session: construction-2
opened: 2026-10-21
closed: 2026-10-21

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

Closed (fix-report-2, 2026-10-21). The shape carries template parameters
generally: a template declares each in its `template.toml` as `[[params]]`
(`name`, `kind` of integer, text or date, an optional `default`, `means`),
the loader refuses a bad declaration (a reserved or ill-formed name, an
unknown kind, no meaning, a default that does not read). The builder takes
`params={name: value}`, reads each as its kind (a value that does not read
is passed as the text given, so the template's rule can say "no cut is
applied"), and puts every declared parameter in `report["params"]` and
under its own name on the report, so construction's `report["window_days"]`
read stays where it is. A name the template does not declare is refused
before anything is read: `python -m products.report render REF --template T
--set window_days=365` prints "refused: …" and exits 2, the page answers
400. The page's form offers each declared parameter (its meaning as the
label, its default as the placeholder) and a since field; the memo prints
what was set, what stands by default and what did not read. Fixture test
`tests/test_params.py`. The construction and property templates declare
nothing yet, so `--set window_days` is refused on them today: card
`the-construction-and-property-templates-declare-no-window-days-parameter`.
