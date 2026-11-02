"""Step 8.1 (2 November 2026): every template that reads a company's failure reads the companies file's insolvency appointments
(pub.company_insolvencies) beside the Gazette's liquidations, and none counts an appointment that follows a resolution of solvency."""
import importlib.util
import os
import tomllib

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FOLDERS = [os.path.join(HERE, t) for t in ("02-legal", "03-banking", "04-agriculture", "05-credit", "06-insurance", "07-construction",
                                           "08-recruitment", "11-healthcare", "12-property", "13-ownership")]
FOLDERS.append(os.path.join(REPO, "products", "report", "templates", "subject"))


def by_path(name, path, **bound):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    mod.__dict__.update(bound)
    spec.loader.exec_module(mod)
    return mod


CONTRACT = by_path("qv4_test_contract_insolvencies", os.path.join(REPO, "products", "report", "contract.py"))
FILE_LIQ = {"view": "company_insolvencies", "row": {"insolvency_type": "Receivership", "resolution_of_solvency": False}}
SOLVENT = {"view": "company_insolvencies", "row": {"insolvency_type": "Liquidation", "resolution_of_solvency": True}}


@pytest.mark.parametrize("folder", FOLDERS, ids=os.path.basename)
def test_the_template_reads_the_companies_files_appointments_and_never_a_solvent_winding_up(folder):
    mod = by_path(f"qv4_test_rules_{os.path.basename(folder).replace('-', '_')}", os.path.join(folder, "rules.py"), contract=CONTRACT)
    assert mod._liq_view(FILE_LIQ) and not mod._liq_view(SOLVENT) and mod._liq_view({"view": "gazette_liquidations", "row": {}})
    assert not mod._liq_view({"view": "gazette_company_notices", "row": {}})
    assert mod._liq_kind(FILE_LIQ) == "receivership (the companies file)"
    with open(os.path.join(folder, "template.toml"), "rb") as f:
        t = tomllib.load(f)
    reads = {r["view"]: r for r in t["reads"]}
    assert reads["company_insolvencies"]["attribution"] == "Companies Office" and "gazette_liquidations" in reads
    for s in t["sections"]:
        if "gazette_liquidations" in s["views"]:
            assert "company_insolvencies" in s["views"], s["name"]
