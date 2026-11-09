"""Step 9, tranche 1 (ruling 150): the use-case templates 02 to 13 are retired,
which means frozen, not removed. Each README says so; each still loads; the
board's report tab opens the one report (for now, the diagnostic template)
by default, checked in the code and, in the slow tier, on the live board."""
import os
import re
import urllib.request

import pytest

from products.board import subject_report
tpl = subject_report.template   # the board reaches the report only through its tab (tests/test_imports_one_way.py)

RETIRED = ("02-legal", "03-banking", "04-agriculture", "05-credit", "06-insurance",
           "07-construction", "08-recruitment", "11-healthcare", "12-property", "13-ownership")
LINE = "**Retired (ruling 150, 9 November 2026).**"


def test_every_use_case_template_is_on_the_list():
    on_disk = sorted(d for d in os.listdir(tpl.USE_CASE_TEMPLATES)
                     if re.fullmatch(r"\d\d-[a-z]+", d))
    assert on_disk == sorted(RETIRED), "a use-case template folder is not on tranche 1's retired list, or one is missing"


@pytest.mark.parametrize("folder", RETIRED)
def test_retired_line_and_still_loads(folder):
    path = os.path.join(tpl.USE_CASE_TEMPLATES, folder)
    with open(os.path.join(path, "README.md"), encoding="utf-8") as f:
        head = f.read().split("\n")[:4]
    assert head[2].startswith(LINE), f"{folder}: no retired line under the title"
    t = tpl.load(path)
    assert t.name and t.reads, f"{folder}: loaded but reads nothing"


def test_board_tab_defaults_to_the_one_report():
    assert subject_report.DEFAULT_TEMPLATE == "diagnostic"
    assert "diagnostic" in tpl.folders()
    assert subject_report.chosen("") == "diagnostic"
    assert subject_report.chosen("no-such-template") == "diagnostic"


@pytest.mark.slow
def test_live_board_opens_on_the_diagnostic_template():
    port = int(os.environ.get("QV4_BOARD_PORT") or 8420)
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/subject-report", timeout=30) as r:
        page = r.read().decode("utf-8")
    selected = re.findall(r'<option value="([a-z0-9-]+)" selected', page)
    assert selected == ["diagnostic"], f"the live tab opens on {selected}"
