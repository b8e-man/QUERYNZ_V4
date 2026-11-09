"""Writes the one report's template (`template.toml` beside this file): step 9, ruling 157. The diagnostic template's
reads and sections (every table the catalogue knows, one section per register), with the first stage's walk
(`stage = 1`: no near link followed, the confirmed web added, products/report/stage1.py) and the combined checks
(`rules.py`, products/report/checks_combined.py). Run it again whenever the catalogue changes;
`tests/test_stage1.py` fails while the template on disk differs from what this writes.

    PYTHONPATH=. python products/report/templates/one/make.py
"""
import os

from products.report.templates.diagnostic import make as diagnostic

HERE = os.path.dirname(os.path.abspath(__file__))
BUCKETS = diagnostic.BUCKETS + ["stage1"]
HEAD = [
    "# The one report (step 9, ruling 157), first stage: every table the catalogue knows, the confirmed links followed to the",
    "# depth the first stage measured, no near link followed (the second stage, on request, adds them), and the combined",
    "# checks of the retired templates and the diagnostic. Written by make.py from the diagnostic template: do not edit by hand.",
    'name = "one"',
    'title = "The one report, first stage"',
    'version = "0.1"',
    'owner = "products/report, the one report (step 9)"',
    "depth = 2",
    "chain_depth = 2",
    "stage = 1",
    "",
    "limits = [",
    '  "The first stage follows confirmed links only: a name match, a shared office and a holder matched by name wait for the second stage, counted, never shown.",',
    '  "A connection through more than one person is near.",',
    '  "The web stops at the depth and the hub limits printed in the memo; what it left out is counted, never silent.",',
    "]",
    "",
]


def render() -> str:
    body = diagnostic.render().split("\n")
    first = next(i for i, line in enumerate(body) if line == "[[reads]]")
    old = "sources = [" + ", ".join(diagnostic._q(b) for b in diagnostic.BUCKETS) + "]"
    new = "sources = [" + ", ".join(diagnostic._q(b) for b in BUCKETS) + "]"
    return "\n".join(HEAD + [new if line == old else line for line in body[first:]])


def main() -> int:
    with open(os.path.join(HERE, "template.toml"), "w", encoding="utf-8") as f:
        f.write(render())
    print("one: template.toml written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
