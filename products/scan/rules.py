"""What a scan's list may show, checked on every run before the surface
prints it (design: "Rules for everything a product shows"; the brief):

  1. every line is cited: each step carries a citation number;
  2. every step's row is dated or marked undated;
  3. no word of cause in the scan's own words: the question, the join text,
     the labels, the limits, the reasons and the hub texts (a register's
     own values, a company named "Because Ltd", are the register's words
     and are not read);
  4. a nominee is never shown as an owner: no "owner" or "owns" in the
     scan's own words;
  5. absence is never a finding: an empty run says "none found in …" and
     nothing stronger, and no scan's own words claim a "none" or "no …";
  6. no suppressed name on any surface: a suppressed step shows "name
     suppressed" and none of its name columns' values;
  7. no home address: no address-shaped text in a title or a carried value,
     a company's own registered name aside;
  8. a near or contested line carries its reasons;
  9. the grade is one of the three.

Pure: a template, a run's lines and the shape's own words in, problems out."""
from __future__ import annotations

import re

from products.scan import views as cat

CAUSE = re.compile(r"\b(because|therefore|hence|thus|consequently|so that|due to|as a result|owing to|linked to|connected to|"
                   r"associated with|controls?|controlled by|behind|beneficial|caused|causes|cause)\b", re.I)
OWNER = re.compile(r"\b(owner|owners|owns|owned|ownership)\b", re.I)
ABSENCE = re.compile(r"\b(no|none|never|nobody|nothing)\b\s+(?!found in)\b(\w+)\s+(is|are|has|have|holds?|was|were)\b", re.I)
STREET = r"(?:street|road|avenue|drive|place|lane|crescent|terrace|highway|parade|way|close|court|grove|rise|esplanade|st|rd|ave|cres|tce|hwy|pl)"
ADDRESS_NUMBERED = re.compile(r"(?<![\d.,$/:-])\b\d{1,5}[a-z]?(?:/\d{1,5}[a-z]?)?(?![\d.,/])[\s,]+(?:[\w'’.-]+\s+){0,4}?" + STREET + r"\b", re.I)
ADDRESS_POSTCODED = re.compile(r"\b" + STREET + r"\b\s*,\s*(?:[A-Za-z'’-]+,?\s+){1,3}\d{4}\b", re.I)
BLANK_OK = re.compile(r"^none found in .+$")
GRADES = ("confirmed", "near", "contested")


def address_shaped(text: str) -> bool:
    return bool(ADDRESS_NUMBERED.search(text or "") or ADDRESS_POSTCODED.search(text or ""))


def own_words(t) -> list:
    """The scan's own words: (where, text)."""
    out = [("question", t.question), ("join", t.join), ("title", t.title)]
    out += [(f"limit {i + 1}", x) for i, x in enumerate(t.limits)]
    out += [(f"label {s.label}", s.label) for s in t.steps]
    return out


def template_problems(t) -> list:
    out = []
    for where, text in own_words(t):
        m = CAUSE.search(text)
        if m:
            out.append(f"{where}: a word of cause in the scan's own words: {m.group(0)!r} (rule 3)")
        m = OWNER.search(text)
        if m:
            out.append(f"{where}: shown as an owner in the scan's own words: {m.group(0)!r} (rule 4)")
        m = ABSENCE.search(text)
        if m and where != "question":
            out.append(f"{where}: an absence stated as a finding: {m.group(0)!r} (rule 5)")
    return out


def line_problems(ln: dict) -> list:
    out = []
    n = ln.get("n", "?")
    if ln.get("grade") not in GRADES:
        out.append(f"line {n}: grade {ln.get('grade')!r} (rule 9)")
    if ln.get("grade") in ("near", "contested") and not ln.get("reasons"):
        out.append(f"line {n}: {ln.get('grade')} with no reason (rule 8)")
    for text in list(ln.get("reasons") or []) + [h.get("text", "") for h in ln.get("hubs") or []]:
        m = CAUSE.search(text)
        if m:
            out.append(f"line {n}: a word of cause in the scan's own words: {m.group(0)!r} (rule 3)")
        m = OWNER.search(text)
        if m and "never" not in text:
            out.append(f"line {n}: shown as an owner in the scan's own words: {m.group(0)!r} (rule 4)")
    for s in ln.get("steps") or []:
        if not s.get("cite"):
            out.append(f"line {n}, {s.get('label')}: no citation (rule 1)")
        if not s.get("dates"):
            out.append(f"line {n}, {s.get('label')}: no dating text (rule 2)")
        v = cat.BY_NAME.get(s.get("view"))
        texts = [s.get("title") or ""] + [str(x) for x in (s.get("values") or {}).values()]
        if s.get("suppressed"):
            if s.get("title") != "name suppressed":
                out.append(f"line {n}, {s.get('label')}: a suppressed row's title is not 'name suppressed' (rule 6)")
            for c in (v.names if v else ()):
                val = str((s.get("values") or {}).get(c) or "")
                if val and val != "name suppressed":
                    out.append(f"line {n}, {s.get('label')}: a suppressed name column is carried (rule 6)")
        if v and v.kind != "organisation":
            for text in texts:
                if address_shaped(text):
                    out.append(f"line {n}, {s.get('label')}: an address-shaped value (rule 7)")
                    break
    return out


def run_problems(t, lines: list, blank: str = None) -> list:
    """Every problem of a run: the template's own words, each line, and the
    blank an empty run shows."""
    out = template_problems(t)
    for ln in lines:
        out += line_problems(ln)
    if not lines and not (blank and BLANK_OK.match(blank)):
        out.append("an empty run says 'none found in …' and nothing else (rule 5)")
    return out
