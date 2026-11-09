"""Writes the diagnostic template (`template.toml` beside this file) from the catalogue (Arthur, 9 November 2026: a
subject report that touches everything, for internal diagnostic use, to find the problems before the use-case
reports are built).

It reads every table the catalogue knows, one section per register in the catalogue's order, every reach of the walk
drawn on. A table's licence, attribution and refresh are the subject template's where it names the table, else its
register's line below. Run it again whenever the catalogue changes; `tests/test_diagnostic.py` fails while the
template on disk differs from what this writes.

    PYTHONPATH=. python products/report/templates/diagnostic/make.py
"""
import os
import tomllib

from products.report import catalogue as cat

HERE = os.path.dirname(os.path.abspath(__file__))
SUBJECT = os.path.join(os.path.dirname(HERE), "subject", "template.toml")
BUCKETS = ["members", "confirmed", "near", "roles", "pointing", "second", "named", "officers", "office", "chain", "beside"]

#: a register's licence, attribution and refresh, for a table the subject template does not name
REGISTER_TERMS = {
    "insolvency": ("the Insolvency Register, published by the Ministry of Business, Innovation and Employment for search",
                   "Insolvency and Trustee Service", "as the lane's walk reads it"),
    "linz": ("LINZ data, Creative Commons Attribution 4.0", "Toitū Te Whenua Land Information New Zealand", "as LINZ publishes changes"),
    "sanctions": ("each list as its publisher releases it for use", "the lists' publishers", "as each list changes"),
    "building_practitioners": ("the Licensed Building Practitioners register, published for search", "Ministry of Business, Innovation and Employment",
                               "as the register changes"),
    "companies": ("Companies Office bulk data and the business-number register, Creative Commons Attribution 4.0", "Companies Office",
                  "monthly file, and company by company"),
    "grants": ("as each funder publishes its grants", "the funders", "as each funder publishes"),
    "council_minutes": ("council minutes, published under the Local Government Official Information and Meetings Act 1987", "each council",
                        "as each council publishes its minutes"),
    "courts": ("New Zealand court judgments are published for reuse; a name under a suppression order or withheld is never shown",
               "the courts of New Zealand", "as the courts corpus lands"),
    "gazette": ("New Zealand Gazette, Crown copyright, Creative Commons Attribution 4.0", "New Zealand Gazette", "daily"),
    "hansard": ("Hansard, Parliamentary copyright, published for reuse", "New Zealand Parliament", "as the House sits"),
    "beehive": ("Beehive releases, Crown copyright, Creative Commons Attribution 4.0", "the New Zealand Government", "as releases are made"),
    "parliament": ("Parliament's pages, Parliamentary copyright, published for reuse", "New Zealand Parliament", "as Parliament publishes"),
    "ministers_diaries": ("proactively released ministerial diaries, Crown copyright, Creative Commons Attribution 4.0",
                          "the ministers' offices", "monthly, as released"),
    "iwi_directory": ("Te Kāhui Māngai, published for public reference", "Te Puni Kōkiri", "weekly"),
    "local_elections": ("candidate returns each council publishes under the Local Electoral Act 2001", "each council", "after each election"),
    "party_boards": ("each party's own site, read whole from its homepage", "each registered party", "as each site changes"),
    "parties": ("the Electoral Commission's register of parties", "Electoral Commission", "as the Gazette notices changes"),
    "party_finance": ("the Electoral Commission's published returns and statements", "Electoral Commission", "as the Commission publishes"),
}


def _q(text: str) -> str:
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def render() -> str:
    with open(SUBJECT, "rb") as f:
        subject = tomllib.load(f)
    terms = {r["view"]: (r["licence"], r["attribution"], r.get("refresh", "on the lane's clock")) for r in subject.get("reads", [])}
    out = [
        "# The diagnostic subject report (Arthur, 9 November 2026): every table the catalogue knows, every reach the walk",
        "# has, namesakes and near links listed with their rules. Internal, for finding problems; never a product's report.",
        "# Written by make.py from the catalogue: do not edit by hand.",
        'name = "diagnostic"',
        'title = "Diagnostic subject report"',
        'version = "0.1"',
        'owner = "products/report, the diagnostic report (9 November 2026)"',
        "depth = 2",
        "chain_depth = 2",
        "",
        "limits = [",
        '  "Internal, for finding problems: it reads every published table that names a person or a body, so it carries what no use-case report would.",',
        '  "A name match is near, never confirmed. A connection through more than one person is near.",',
        '  "The walk stops at the limits printed in the memo; what it left out is counted, never silent.",',
        "]",
        "",
    ]
    for v in cat.VIEWS:
        lic, att, ref = terms.get(v.name) or REGISTER_TERMS[v.register]
        out += ["[[reads]]", f"view = {_q(v.name)}", f"licence = {_q(lic)}", f"attribution = {_q(att)}", f"refresh = {_q(ref)}"]
    out.append("")
    for reg, plain in cat.REGISTERS:
        views = [v.name for v in cat.VIEWS if v.register == reg]
        if not views:
            continue
        out += ["[[sections]]", f"name = {_q(reg)}", f"heading = {_q(plain)}", "views = [" + ", ".join(_q(v) for v in views) + "]",
                "sources = [" + ", ".join(_q(b) for b in BUCKETS) + "]", ""]
    return "\n".join(out)


def main() -> int:
    with open(os.path.join(HERE, "template.toml"), "w", encoding="utf-8") as f:
        f.write(render())
    print("diagnostic: template.toml written,", len(cat.VIEWS), "tables")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
