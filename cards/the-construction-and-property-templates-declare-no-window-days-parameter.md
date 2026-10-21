# The construction and property templates read `window_days` but declare it in no template.toml, so a reader's window is refused
kind: finding
state: open
use-case: 7 construction and phoenix detection; 12 property developer due diligence
session: fix-report-2
opened: 2026-10-21

The shape carries template parameters (card
`the-report-carries-no-template-parameters`, closed 2026-10-21): a template
declares each in its `template.toml` under `[[params]]` with `name`, `kind`
(`integer`, `text` or `date`), an optional `default` and `means`; the
builder sets every declared parameter under its name in `report["params"]`
and on the report itself, and refuses a name the template does not declare.
`products/templates/07-construction/rules.py` and
`products/templates/12-property/rules.py` already read `report["window_days"]`
(`WINDOW_KEY`, `_window_days`), but neither template.toml declares it, so
`python -m products.report render REF --template construction --set
window_days=365` is refused today ("declares no parameter named
window_days") and the page offers no field.

The fix, in each template folder: in template.toml

    [[params]]
    name = "window_days"
    kind = "integer"
    means = "days either side of a failure's Gazette date within which a going company is set beside it; not set: every gap is shown"

(no default: ruling 65 makes the window the reader's setting, and none is
the template's), then the comment in `rules.py` and the limits line saying
the shape cannot yet carry one come out, and the template's own test renders
with `--set window_days=365` and sees the cut. A value that is not a whole
number of days reaches the rule as the text given, as the rules already
expect.
