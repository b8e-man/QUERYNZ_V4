"""The presentation rules of plan 5.1, checked on every finished report, so
a report that breaks one is refused by the surface rather than printed:

  1. every connection is dated or marked undated;
  2. every statement carries a citation;
  3. coincidence is never joined to cause: no word of cause in the report's
     own words;
  4. a nominee is never shown as an owner: no "owner" or "owns" in the
     report's own words;
  5. absence is not a finding: a section with nothing says "none found in …"
     or "not held: …", and nothing stronger;
  6. no suppressed name on any surface: a suppressed row's name columns never
     appear in its title or statement;
  7. no home address: the only address-shaped statement is a company's
     registered office;
  8. a near connection carries its reason;
  9. a flag keeps the contract: fired cites, clear names its sources, blocked says why.

Whose words a rule reads. Rules 3 and 4 read the report's own words: the
statement pattern's text, the reasons, the notes, the flags. A register's
own values (a name, a title, a role, a notice's action) are the register's
words, quoted as it states them, and are masked out before the search: a
pest-control company or a donor named Lane is not the report joining two
facts (the recruitment checkpoint's two refusals). Rule 7 reads everything,
values included: a street in a name column is exactly the fault it exists
to catch, so an address is recognised by its shape (a street number before
the street word, or a locality and postcode after it), never by a street
word and a year standing apart.

Pure: a report in, a list of problems out (empty when the rules hold)."""
from __future__ import annotations

import re

from products.report import catalogue as cat

CAUSE = re.compile(r"\b(because|therefore|hence|thus|consequently|so that|due to|as a result|owing to|linked to|connected to|"
                   r"associated with|controls?|controlled by|behind|beneficial)\b", re.I)
OWNER = re.compile(r"\b(owner|owners|owns|owned|ownership)\b", re.I)
STREET = r"(?:street|road|avenue|drive|place|lane|crescent|terrace|highway|parade|way|close|court|grove|rise|esplanade|st|rd|ave|cres|tce|hwy|pl)"
#: a street number (a number standing alone, not the tail of a money figure or a date), up to four words, a street word:
#: "12 Smith Street", "2/14 Victoria St", "148 Victoria Street"; not "$100,000.00 Gary Rodney Lane"
ADDRESS_NUMBERED = re.compile(r"(?<![\d.,$/:-])\b\d{1,5}[a-z]?(?:/\d{1,5}[a-z]?)?(?![\d.,/])[\s,]+(?:[\w'’.-]+\s+){0,4}?" + STREET + r"\b", re.I)
#: a street word, a comma, one to three locality words, a four-digit postcode: "Smith Street, Epsom, Auckland 1051"
ADDRESS_POSTCODED = re.compile(r"\b" + STREET + r"\b\s*,\s*(?:[A-Za-z'’-]+,?\s+){1,3}\d{4}\b", re.I)
BLANK_OK = re.compile(r"^(none found in .+|not held: .+|none found)(; (none found in .+|not held: .+))*$")
MASK_MIN = 3   # a register value this short or shorter is not masked (it cannot carry a word of cause)


def address_shaped(text: str) -> bool:
    """True when the text carries something shaped like a street address."""
    return bool(ADDRESS_NUMBERED.search(text or "") or ADDRESS_POSTCODED.search(text or ""))


def register_values(it: dict) -> list:
    """The register's own words that fill the item's statement: every text
    value of its row (title, names, roles, actions, headings as the lane
    published them) and the title of the row it sits on. Longest first, so a
    longer value is removed before a shorter one inside it."""
    vals = set()
    for x in (it.get("row") or {}).values():
        if isinstance(x, str):
            x = " ".join(x.split())
            if len(x) > MASK_MIN:
                vals.add(x)
    for k in ("entity_title", "title"):
        x = " ".join(str(it.get(k) or "").split())
        if len(x) > MASK_MIN:
            vals.add(x)
    return sorted(vals, key=len, reverse=True)


def own_words(it: dict, prose: bool = False) -> str:
    """The item's text with the register's values masked out: what is left is
    the report's own wording (the pattern, the joins), which is what rules 3
    and 4 judge. With `prose`, the reason and the note the report adds beside
    the line (read by rule 3 only: a note may say "never an owner")."""
    text = f"{it.get('title', '')} {it.get('statement', '')}"
    if prose:
        text = f"{it.get('reason') or ''} {it.get('note') or ''}"
    text = " ".join(text.split())
    for v in register_values(it):
        text = text.replace(v, " ")
    return text


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
        words = own_words(it)
        m = CAUSE.search(words) or CAUSE.search(own_words(it, prose=True))
        if m:
            out.append(f"{ref}: a word of cause in the report's own words: {m.group(0)!r} (rule 3)")
        m = OWNER.search(words)
        if m:
            out.append(f"{ref}: shown as an owner in the report's own words: {m.group(0)!r} (rule 4)")
        if it.get("suppressed"):
            v = cat.BY_NAME.get(it.get("view"))
            text = f"{it.get('title', '')} {it.get('statement', '')}"
            for col in (v.names if v else ()):
                val = str((it.get("row") or {}).get(col) or "").strip()
                if len(val) > 2 and val.lower() in text.lower():
                    out.append(f"{ref}: a suppressed name appears (rule 6)")
                    break
        if it.get("view") != "company_addresses" and (address_shaped(it.get("title", "")) or address_shaped(it.get("statement", ""))):
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
        for text in (s.get("text") or "", s.get("blank") or ""):
            m = CAUSE.search(text)
            if m:
                out.append(f"section {s['name']}: a word of cause in its text: {m.group(0)!r} (rule 3)")
    for h in report.get("hubs", []):
        m = CAUSE.search(h.get("text") or "")
        if m:
            out.append(f"hub {h.get('ref')}: a word of cause in its text: {m.group(0)!r} (rule 3)")
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
