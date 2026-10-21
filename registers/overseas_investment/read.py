"""The lane's reading of the Overseas Investment Office's decision summaries,
from the profiles `oio-decisions-listing`, `oio-decision-summary` and
`oio-standing-consent-notification` (version 1, proposed in
`profile-proposed.jsonl`; the integrator appends them at the merge). No
model; nothing fetched.

A page is first recognised by its shape. A listing page carries the view's
case-number column and a pager; a summary carries the meta block (`dl`) and
one table of headed rows whose first heading is "Decision" (a consent
decision) or "Notification" (a transaction under a standing consent). A page
that is not one of those shapes is set aside whole.

One decision row per summary page, keyed by the page's own address
(`overseas_investment/decision/<slug>`; a page can carry two case numbers,
and the listing lists it once per number):

  as stated   the case numbers, the type (Decision or Notification), the
              outcome ("Consent granted", "Consent Declined", "Notification
              of a transaction under a Standing Consent") and the section
              it cites, the decision maker, the decision date, the pathway
              (the kind of consent), the class of investment, the
              consideration (or the asset value) and whether it is
              withheld, a retrospective penalty, the notification number
              and the parent case
  the land    the investment statement with every street address and legal
              description withheld (hard limit 15: a site bought or sold by
              a person is often a home); the areas as stated, and in
              hectares. The statement as published is kept in
              `overseas_investment_private`, never on a view
  rationale   the Background's own list items and its sentences naming a
              test or criterion, as stated, addresses withheld; the rest of
              the Background is not read

One party row per applicant (or consent holder) and vendor the summary
names in bold: the name as published, a status the office prints beside it
("(in receivership)"), the trust a trustee acts for, a company number only
where printed beside the name, and the ownership lines under the names
(origin as stated, share as stated). A name the office withholds is
withheld on every surface: the row stays, the name and its ownership
origins do not (hard limit 16). "More information" (the applicant's agent,
with an office address) and attachments' addresses are never read.
"""
import datetime as dt
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
from keys.names import is_organisation  # noqa: E402

PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
LISTING_PROFILE = "oio-decisions-listing"
DECISION_PROFILE = "oio-decision-summary"
NOTIFICATION_PROFILE = "oio-standing-consent-notification"
PROFILE_VERSION = 1
READER = "registers.overseas_investment.read 1"
KEY_PREFIX = "overseas_investment/decision"
BASE = "https://www.linz.govt.nz"
PATH = "/our-work/overseas-investment-regulation/decisions"
ADDRESS_WITHHELD = "[street address withheld]"
LEGAL_WITHHELD = "[legal description withheld]"

_BLOCK = re.compile(r"<title>\s*(?:Just a moment|Attention Required|Access denied)", re.I)
_VIEW = re.compile(r'views-field-field-oi-case-number')
_ROW = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
_CELL = re.compile(r'<td[^>]*class="[^"]*views-field-field-([a-z-]+)[^"]*"[^>]*>(.*?)</td>', re.S)
_LINK = re.compile(rf'href="({re.escape(PATH)}/(\d{{4}}-\d{{2}})/([A-Za-z0-9-]+))"')
_TIME = re.compile(r'<time datetime="(\d{4}-\d{2}-\d{2})')
_PAGER_CURRENT = re.compile(r'href="\?[^"]*?page=(\d+)[^"]*"\s+title="Current page"')
_PAGER_ANY = re.compile(r'<li class="page-item[^"]*">\s*<a href="\?[^"]*?page=(\d+)|href="\?[^"]*?page=(\d+)[^"]*"\s+title="Go to last page"')
_META = re.compile(r'<dl\s+class="content__wider-col node__meta-grid[^"]*">(.*?)</dl>', re.S)
_DTDD = re.compile(r'<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>', re.S)
_TABLE = re.compile(r'<div\s+class="prose[^"]*">\s*<div class="table-responsive">\s*<table[^>]*>(.*?)</table>', re.S)
_HEADED = re.compile(r"<tr[^>]*>\s*<th[^>]*>(.*?)</th>\s*<td[^>]*>(.*?)</td>\s*</tr>", re.S)
_CLEARFIX = re.compile(r'<div class="clearfix">(.*?)</div>', re.S)
_TAG = re.compile(r"<[^>]+>")
_FOOTNOTE = re.compile(r"\s*\[\d+\]\s*$")
_SECTION_FIRST = re.compile(r"^Sections?\s+\d", re.I)
#: the row that carries the money, by its heading; a figure is read only under a consideration or a price
MONEY_HEADINGS = re.compile(r"^(?:consideration|asset value|value|lease amount|lease|rent|cost of commencing business|"
                            r"price|purchase price)\b", re.I)
PRICE_HEADINGS = re.compile(r"^(?:consideration|price|purchase price)\b", re.I)
ROLES = (("applicant", re.compile(r"^(?:applicants?|consent holders?)\b", re.I)),
         ("vendor", re.compile(r"^vendors?\b", re.I)),
         ("issuer", re.compile(r"^issuers?\b", re.I)))
_SPACE = re.compile(r"\s+")
_STRONG = re.compile(r"<(strong|b)\b[^>]*>(.*?)</\1>", re.S)
_LINE = re.compile(r"<br\s*/?>|</p>|<p[^>]*>|</li>|<li[^>]*>|</div>|<div[^>]*>", re.I)
_LI = re.compile(r"<li[^>]*>(.*?)</li>", re.S)
_P = re.compile(r"<p[^>]*>(.*?)</p>|<br\s*/?>\s*<br\s*/?>", re.S)

WITHHELD = re.compile(r"\b(?:withheld|redacted|name suppressed|suppressed)\b", re.I)
_PCT = re.compile(r"\(?\s*(\d{1,3}(?:\.\d+)?)\s*%\s*\)?\s*$")
_STATUS = re.compile(r"^\s*\((?:in |under )[^)]*\)\s*$|^\s*\([^)]*(?:receivership|liquidation|administration|"
                     r"amalgamated|formerly|now known)[^)]*\)\s*$", re.I)
_TRUST = re.compile(r"\bas (?:the )?(?:sole |corporate )?trustees? (?:of|for) (?:the )?(.+?)\s*$", re.I)
_NUMBER_BESIDE = re.compile(r"\(\s*(?:NZBN|NZ company number|company number|company no\.?)\s*:?\s*(\d{6,13})\s*\)", re.I)
_CLASS = re.compile(r"\binvestment in (sensitive land|significant business assets|fishing quota)", re.I)
_MONEY = re.compile(r"(?:NZ)?\$\s?(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d{1,2}))?(\s*(?:million|m)\b)?", re.I)
_OTHER_CURRENCY = re.compile(r"\b(?:AUD|USD|US\$|A\$|EUR|GBP|JPY|CNY|HK\$|S\$|C\$|€|£|¥)", re.I)
_AREA = re.compile(r"((?:approximately |about |around |a total of |circa |up to |)(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*"
                   r"(hectares|hectare|ha\b|square metres|square meters|sqm|m2|m²|acres))", re.I)
_RATIONALE = re.compile(r"\b(?:test|tests|criterion|criteria|factor|factors|benefit to New Zealand|"
                        r"national interest|not satisfied|satisfied the (?:OIO|regulator|Ministers?))\b", re.I)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

# a street address: house numbers (a range, a list, a letter suffix) then one to five capitalised words, ending a
# clause; a legal description: Lot, Section, DP, a record of title, with a number or a roman numeral
_NUM = r"\d{1,5}[A-Za-z]?(?:\s*[-–/]\s*\d{1,5}[A-Za-z]?)?"
_NUMS = rf"{_NUM}(?:\s*(?:,|and|&)\s*{_NUM})*"
_WORD = r"(?:[A-Z][\w'’.-]*|Te|te|o|of|the|on|by|de|la)"
STREET = re.compile(rf"(?<![\w$.,/-])(?<!\$ )(?<!No\. )(?<!No )(?<!RD )({_NUMS})\s+([A-Z][\w'’.-]*(?:\s+{_WORD}){{0,4}})"
                    r"(?=\s*(?:[,;.:)]|\s(?:and|in|at|to|from|being|which|with|for|on)\b|$))")
_LEGAL_ONE = (r"(?:Part\s+|Pt\s+)?(?:Lots?|Sections?|Secs?|Allotments?|DPs?|SOs?|LTs?|Block|Records? of Title|"
              r"Certificates? of Title|CTs?|Computer (?:Freehold|Interest) Registers?|Deposited Plans?|"
              r"Survey Office Plans?|Maori Freehold Land|Māori Freehold Land)\s+"
              r"(?=[\w/]*\d|[IVXL]+\b)[\w/]+(?:\s*(?:,|and|&)\s*(?=[\w/]*\d|[IVXL]+\b)[\w/]+)*")
LEGAL = re.compile(rf"\b{_LEGAL_ONE}(?:,?\s+(?:and\s+|on\s+|of\s+|in\s+)?{_LEGAL_ONE})*")


def clean(s: str) -> str:
    return _SPACE.sub(" ", html.unescape(_TAG.sub(" ", s or ""))).replace(" ,", ",").replace(" .", ".").strip()


def date_of(s: str):
    s = clean(s)
    for fmt in ("%d %B %Y", "%d %b %Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def withhold_addresses(text: str):
    """(text, n): every street address and legal description replaced by a marker. Over-withholding a
    business phrase that looks like an address is the accepted cost (hard limit 15)."""
    if not text:
        return text, 0
    n = 0

    def street(m):
        nonlocal n
        words = m.group(2).split()
        if words and words[0].lower() in ("hectares", "per", "percent", "years", "months", "days", "dwellings", "lots"):
            return m.group(0)
        n += 1
        return ADDRESS_WITHHELD

    def legal(m):
        nonlocal n
        n += 1
        return LEGAL_WITHHELD

    out = LEGAL.sub(legal, text)
    out = STREET.sub(street, out)
    return out, n


# ── the listing ───────────────────────────────────────────────────────────────

def recognise_listing(body: bytes) -> str:
    """'' when the page is a page of the office's decisions listing, else why not."""
    t = body.decode("utf-8", "replace")
    if _BLOCK.search(t[:4096]):
        return "a block page, not a listing"
    if not _VIEW.search(t) or "oi-investment-releases" not in t:
        return "no decisions view on the page (not the listing)"
    return ""


def read_listing(body: bytes) -> dict:
    """{'page': N, 'last_page': L, 'items': [{'slug', 'url', 'case_number', 'applicant', 'decided', 'card'}]}: the
    rows in page order (0-based pages, as the pager counts). A page carrying two case numbers is listed once per
    number. `card` is the row's fingerprint: case number, applicant and date as listed."""
    why = recognise_listing(body)
    if why:
        raise ValueError(why)
    t = body.decode("utf-8", "replace")
    items, seen = [], set()
    for row in _ROW.findall(t):
        cells = {k: v for k, v in _CELL.findall(row)}
        link = _LINK.search(cells.get("oi-case-number", ""))
        if not link:
            continue
        case = clean(cells["oi-case-number"])
        applicant = clean(cells.get("oi-applicant", ""))
        when = _TIME.search(cells.get("decision-date", ""))
        decided = when.group(1) if when else clean(cells.get("decision-date", ""))
        slug = link.group(3)
        if (slug, case) in seen:
            continue
        seen.add((slug, case))
        items.append({"slug": slug, "url": BASE + link.group(1), "case_number": case, "applicant": applicant,
                      "decided": decided, "card": "|".join((case, applicant, decided))})
    cur = _PAGER_CURRENT.search(t)
    page = int(cur.group(1)) if cur else 0
    pages = [int(a or b) for a, b in _PAGER_ANY.findall(t)]
    return {"page": page, "last_page": max([page] + pages), "items": items}


# ── a summary ─────────────────────────────────────────────────────────────────

def _meta(t: str) -> dict:
    m = _META.search(t)
    if not m:
        return {}
    out = {}
    for k, v in _DTDD.findall(m.group(1)):
        k = clean(k).lower()
        if k.startswith("case number"):
            out["case numbers"] = [clean(x) for x in _CLEARFIX.findall(v)] or [clean(v)]
        elif k == "decision date":
            when = _TIME.search(v)
            out[k] = when.group(1) if when else clean(v)
        else:
            out[k] = clean(v)
    return out


def _rows(t: str) -> list:
    m = _TABLE.search(t)
    if not m:
        return []
    return [(_FOOTNOTE.sub("", clean(h)).rstrip(":").strip(), v) for h, v in _HEADED.findall(m.group(1))]


def recognise_summary(body: bytes) -> str:
    """'' when the page is a decision summary or a standing-consent notification, else why not."""
    t = body.decode("utf-8", "replace")
    if _BLOCK.search(t[:4096]):
        return "a block page, not a summary"
    if "node--type-oi-info-release" not in t:
        return "not an overseas investment information release page"
    if not _META.search(t):
        return "no meta block (applicant, case numbers, decision date)"
    rows = _rows(t)
    if not rows:
        return "no headed table"
    if rows[0][0].lower() not in ("decision", "notification"):
        return f"the table's first heading is {rows[0][0]!r}, not Decision or Notification"
    return ""


def _lines(cell: str) -> list:
    """The cell's lines, with each bold run marked: [(text, bold text or None)]."""
    marked = _STRONG.sub(lambda m: "<br>\x01" + m.group(2) + "\x02", cell)       # each bold name begins a line
    out = []
    for raw in _LINE.split(marked):
        bold = re.findall(r"\x01(.*?)\x02", raw, re.S)
        text = clean(raw.replace("\x01", "").replace("\x02", ""))
        if not text:
            continue
        b = clean(" ".join(bold)) if bold else None
        out.append((text, b or None))
    return out


def ownership_line(text: str):
    """(origin as stated, share or None): 'Australia 87%', 'China, People's Republic of (97.18%)'."""
    m = _PCT.search(text)
    if not m:
        return text.strip(" ,;"), None
    return text[:m.start()].strip(" ,;"), float(m.group(1))


def read_parties(cell: str, role: str, role_stated: str) -> list:
    """One party per bold name in the cell (or the first line where nothing is bold); every other line is an
    ownership line of the cell's parties, or a status printed beside the name."""
    lines = _lines(cell)
    if not lines:
        return []
    parties = []
    if not any(bold for _, bold in lines):
        parties.append({"name": lines[0][0], "status": None, "lines": [t for t, _ in lines[1:]]})
    else:
        for text, bold in lines:
            if bold:
                after = clean(text.replace(bold, "", 1)) if text.startswith(bold) else ""
                if after.lower() in ("and", "&", ",", ";", "and,"):
                    after = ""                            # the connector to the next bold name
                parties.append({"name": bold, "status": after or None, "lines": []})
            elif not parties:
                continue                                  # a line before any name: not read
            elif parties[-1]["status"] is None and not parties[-1]["lines"] and _STATUS.match(text):
                parties[-1]["status"] = text
            else:
                parties[-1]["lines"].append(text)
    # ownership lines under each name are that party's; lines only under the last of several names are the cell's
    shared = len(parties) > 1 and parties[-1]["lines"] and not any(p["lines"] for p in parties[:-1])
    if shared:
        for p in parties[:-1]:
            p["lines"] = parties[-1]["lines"]
    out = []
    for p in parties:
        lines_ = p["lines"]
        origins, shares = [], []
        for line in lines_:
            o, s = ownership_line(line)
            origins.append(o)
            shares.append(s)
        name = p["name"].strip(" ,;")
        number = _NUMBER_BESIDE.search(name)
        if number:
            name = clean(name[:number.start()] + name[number.end():])
        withheld = bool(WITHHELD.search(name))
        trust = _TRUST.search(name)
        out.append({"role": role, "role_stated": role_stated, "name": None if withheld else name,
                    "withheld": withheld, "withheld_by": "the office withholds the name" if withheld else None,
                    "status": None if withheld else p["status"], "trust": None if withheld or not trust else trust.group(1),
                    "organisation": (not withheld) and is_organisation(name),
                    "company_number": None if withheld or not number else number.group(1),
                    "ownership_lines": len(lines_), "origins": None if withheld else origins, "shares": shares,
                    "ownership_scope": None if not lines_ else ("every party named in the cell" if shared
                                                                else "this party")})
    return out


def money(stated: str):
    """(NZ dollars or None, withheld): a figure only where the cell states one dollar amount and nothing else."""
    if not stated:
        return None, False
    withheld = bool(WITHHELD.search(stated))
    found = _MONEY.findall(stated)
    if withheld or len(found) != 1 or _OTHER_CURRENCY.search(stated):
        return None, withheld
    whole, cents, million = found[0]
    v = float(whole.replace(",", "")) + (float("0." + cents) if cents else 0.0)
    return (v * 1_000_000 if million.strip() else v), False


def areas(statement: str):
    """([as stated], [hectares]) for every area the statement gives."""
    stated, ha = [], []
    for m in _AREA.finditer(statement or ""):
        stated.append(m.group(1).strip())
        n = float(m.group(2).replace(",", ""))
        unit = m.group(3).lower()
        ha.append(round(n if unit.startswith(("hectare", "ha")) else n * 0.40468564224 if unit == "acres" else n / 10000, 6))
    return stated, ha


def statement(cell: str) -> str:
    """The cell as one line of text, list items joined by '; '."""
    items = _LI.findall(cell)
    if not items:
        return clean(cell)
    head = clean(_LI.sub(" ", re.sub(r"</?[uo]l[^>]*>", " ", cell)))
    parts = [re.sub(r"[;,]?\s*(?:\b(?:and|or))?\s*[;,]?\s*$", "", clean(i)) for i in items]
    return clean((head + " " if head else "") + "; ".join(p for p in parts if p))


def rationale(cell: str) -> list:
    """The Background's list items, and its sentences naming a test or criterion, as stated."""
    out = [clean(i).rstrip(";") for i in _LI.findall(cell)]
    body = clean(_LI.sub(" ", cell))
    for s in _SENTENCE.split(body):
        if _RATIONALE.search(s) and s not in out and len(s) <= 600:
            out.append(s.strip())
    return [x for x in out if x]


def read_summary(body: bytes, sha: str, slug: str, url: str = None) -> dict:
    """{'decision': row, 'parties': [rows], 'private': [rows], 'set_aside': [lines]} for one summary page."""
    why = recognise_summary(body)
    if why:
        return {"decision": None, "parties": [], "private": [],
                "set_aside": [{"document": sha, "place": f"summary={slug}", "stage": "recognise", "reason": why}]}
    t = body.decode("utf-8", "replace")
    meta, rows = _meta(t), _rows(t)
    first = rows[0][0].lower()
    profile = DECISION_PROFILE if first == "decision" else NOTIFICATION_PROFILE
    cite = {"document": sha, "page": 1, "read_from": "text", "reader": READER, "profile": profile,
            "profile_version": PROFILE_VERSION}
    key = f"{KEY_PREFIX}/{slug}"
    by = {}
    for h, v in rows:
        by.setdefault(h.lower(), v)
    outcome_cell = rows[0][1]
    lines = _lines(outcome_cell)
    if lines and _SECTION_FIRST.match(lines[0][0]):
        outcome, section = None, "; ".join(x for x, _ in lines) or None
    else:
        outcome = lines[0][0] if lines else None
        section = "; ".join(x for x, _ in lines[1:]) or None
    decided = (date_of(by.get("decision date", "")) or date_of(by.get("date", ""))
               or date_of(meta.get("decision date", "")))
    cons_head = next((h for h, _ in rows if MONEY_HEADINGS.match(h)), None)
    cons_stated = clean(by[cons_head.lower()]) if cons_head else None
    nzd, cons_withheld = money(cons_stated)
    if cons_head and not PRICE_HEADINGS.match(cons_head):
        nzd = None
    inv_stated = statement(next((v for h, v in rows if h.lower().startswith("investment")), "")) or None
    inv, n_addr = withhold_addresses(inv_stated)
    area_stated, area_ha = areas(inv_stated)
    why_ = []
    for item in rationale(by.get("background", "")):
        w, _ = withhold_addresses(item)
        why_.append(w)
    pathway = "; ".join(x for x, _ in _lines(next((v for h, v in rows if h.lower().startswith("pathway")), ""))) or None
    cls = _CLASS.search(inv_stated or "")
    parties = []
    for h, v in rows:
        role = next((r for r, rx in ROLES if rx.match(h)), None)
        if role:
            parties += read_parties(v, role, h)
    for i, p in enumerate(parties, 1):
        p.update(key=f"{key}/party/{i}", decision_key=key, ordinal=i, place=f"{p['role_stated']}[{i}]", **cite)
    applicants_withheld = any(p["withheld"] for p in parties if p["role"] == "applicant")
    listed_applicant = meta.get("applicant")
    if listed_applicant and (applicants_withheld or WITHHELD.search(listed_applicant)):
        listed_applicant = None
    outcome_l = (outcome or "").lower()
    decision = {
        "key": key, "slug": slug, "url": url or f"{BASE}{PATH}/{slug}",
        "case_numbers": meta.get("case numbers") or [], "case_number": (meta.get("case numbers") or [None])[0],
        "kind": meta.get("type") or rows[0][0], "outcome": outcome,
        "granted": True if "granted" in outcome_l else False if "declined" in outcome_l else None,
        "section": section, "decision_maker": clean(by.get("decision maker", "")) or None,
        "decided_on": decided, "pathway": pathway, "investment_class": cls.group(1).lower() if cls else None,
        "investment": inv, "addresses_withheld": n_addr, "areas_stated": area_stated, "area_ha": area_ha,
        "consideration_heading": cons_head, "consideration_stated": cons_stated, "consideration_nzd": nzd,
        "consideration_withheld": cons_withheld, "penalty_stated": clean(by.get("retrospective penalty", "")) or None,
        "notification_number": clean(by.get("notification number", "")) or None,
        "parent_case": meta.get("oi case number") or None, "applicant_listed": listed_applicant,
        "rationale": why_, "headings": [h for h, _ in rows],
        "attachments": len(re.findall(r"<a\s", by.get("attachments", ""))),
        "place": "table", **cite}
    private = [{"key": key, "investment_stated": inv_stated, "document": sha}] if inv_stated else []
    asides = []
    if not any(p["role"] == "applicant" for p in parties):
        asides.append({"document": sha, "place": f"summary={slug}", "stage": "parties", "reason": "no applicant read"})
    if decided is None:
        asides.append({"document": sha, "place": f"summary={slug}", "stage": "date", "reason": "no decision date read"})
    return {"decision": decision, "parties": parties, "private": private, "set_aside": asides}
