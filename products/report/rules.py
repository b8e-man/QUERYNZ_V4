"""The presentation rules of plan 5.1, checked on every finished report, so
a report that breaks one is refused by the surface rather than printed:

  1. every connection is dated or marked undated;
  2. every statement carries a citation;
  3. coincidence is never joined to cause: no word of cause in a statement;
  4. a nominee is never shown as an owner: no "owner" or "owns" in a statement;
  5. absence is not a finding: a section with nothing says "none found in …"
     or "not held: …", and nothing stronger;
  6. no suppressed name on any surface: a suppressed row's name columns never
     appear in its title or statement;
  7. no home address: the only address-shaped statement is a company's
     registered office;
  8. a near connection carries its reason;
  9. a flag keeps the contract: fired cites, clear names its sources, blocked says why.

Pure: a report in, a list of problems out (empty when the rules hold)."""
from __future__ import annotations

import re

from products.report import catalogue as cat

CAUSE = re.compile(r"\b(because|therefore|hence|thus|consequently|so that|due to|as a result|owing to|linked to|connected to|"
                   r"associated with|controls?|controlled by|behind|beneficial)\b", re.I)
OWNER = re.compile(r"\b(owner|owners|owns|owned|ownership)\b", re.I)
ADDRESS_SHAPE = re.compile(r"\b(street|road|avenue|drive|place|lane|crescent|terrace|highway|st|rd|ave)\b.*\b\d{4}\b", re.I)
BLANK_OK = re.compile(r"^(none found in .+|not held: .+|none found)(; (none found in .+|not held: .+))*$")


def _items(report: dict):
    if report.get("subject"):
        yield report["subject"]
    for m in report.get("members", []):
        yield m
    for s in report.get("sections", []):
        for it in s["items"]:
            yield it


def problems(report: dict) -> list:
    out = []
    if not report.get("found"):
        return out
    for it in _items(report):
        ref = it.get("ref", "?")
        d = it.get("dates") or {}
        if not d.get("text"):
            out.append(f"{ref}: no dating text (rule 1)")
        elif d.get("undated") != ("undated" in d["text"]):
            out.append(f"{ref}: dated and marked undated disagree (rule 1)")
        c = it.get("citation") or {}
        if not (c.get("view") and c.get("key")) or not it.get("cite"):
            out.append(f"{ref}: no citation (rule 2)")
        text = f"{it.get('title', '')} {it.get('statement', '')}"
        m = CAUSE.search(text)
        if m and not (it.get("view") == "gazette_appointments" and m.group(0).lower() == "behind"):
            out.append(f"{ref}: a word of cause in a statement: {m.group(0)!r} (rule 3)")
        if OWNER.search(text):
            out.append(f"{ref}: shown as an owner (rule 4)")
        if it.get("suppressed"):
            v = cat.BY_NAME.get(it.get("view"))
            for col in (v.names if v else ()):
                val = str((it.get("row") or {}).get(col) or "").strip()
                if len(val) > 2 and val.lower() in text.lower():
                    out.append(f"{ref}: a suppressed name appears (rule 6)")
                    break
        if it.get("view") != "company_addresses" and ADDRESS_SHAPE.search(it.get("statement", "")):
            out.append(f"{ref}: an address-shaped statement outside the registered-office view (rule 7)")
        if it.get("grade") == "near" and not it.get("reason"):
            out.append(f"{ref}: near with no reason (rule 8)")
        if it.get("grade") not in ("confirmed", "near"):
            out.append(f"{ref}: grade {it.get('grade')!r}")
    for s in report.get("sections", []):
        if not s["items"]:
            if not s.get("blank") or not BLANK_OK.match(s["blank"]):
                out.append(f"section {s['name']}: empty without 'none found in …' or 'not held: …' (rule 5)")
        elif s.get("blank"):
            out.append(f"section {s['name']}: has items and a blank")
    for f in report.get("flags", []):
        if f["status"] == "fired" and not f["citations"]:
            out.append(f"flag {f['rule']}: fired without citations (rule 9)")
        if f["status"] == "clear" and not f["sources_held"]:
            out.append(f"flag {f['rule']}: clear without the sources held (rule 9)")
        if f["status"] == "blocked" and not f["text"]:
            out.append(f"flag {f['rule']}: blocked without a reason (rule 9)")
        if CAUSE.search(f["text"]) and f["status"] == "fired":
            out.append(f"flag {f['rule']}: a word of cause in a fired flag (rule 3)")
    return out
