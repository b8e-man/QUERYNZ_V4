"""A party's election expense return: its own stated total, read (contract:
the reader; profile `ec-party-expenses-return`).

The declaration states Part A (advertising promoted solely by the party),
Part B (shared with candidates), Part C (promoted by a third party with the
party's authority) and `Total (A + B + C)`; Parts D to F are the
broadcasting allocation, a different figure entirely, and are never added
in. The schedules behind it print `TOTAL FOR PART <X>` lines. The rules
below were measured on these forty returns by the old estate
(`data-layer/registers/registers/party_expenses.py`, ruling 351) and are
taken across as rules, not code:

- The form's own `Total (A + B + C)` first, the auditor's `Total Party
  Election Expenses` second: TOP's amended 2023 return carries the
  superseded figure in the audit report stapled behind it.
- A figure belongs to the label on its own line: OCR of a two-column page
  emits every label and then every figure.
- Parts are read by their name and summed only as A + B + C. A part not
  read is not a part that is zero, so two parts of three is no total.
- A total whose parts are all read and do not add to it is refused, not
  published (an OCR pass read ACT 2020 as $91,082,166.64).

Pages come through the reader contract: the text layer where a page has
one, else the page reader's stored reading (GLM-OCR at the profile's 300
dots, prompt `OCR`, the reader step 3 kept), replayed and never called.
When the first pass yields no checked total, a second takes the stored
reading for every page that has one, because a text layer can be a
scanner's own OCR (lesson: a text layer is not one thing).

    read_return(data, sha256, store) -> Result
"""
import re
from dataclasses import dataclass, field

from support import profiles
from support import reader as rd
from support.docread import pages
from support.docread.read import read_document

PROFILE = "ec-party-expenses-return"
PAGE_MODEL = "glm-ocr"
#: the page reader's stamps, the profile's own dots first (step 3's incumbent; the trial also read at 200)
PAGE_SETTINGS = tuple(
    {"dpi": dpi, "prompt": "OCR", "prompt_sha": "5e5bea5354e3f22e", "system": None, "level": "q8_0",
     "temperature": 0.0, "max_tokens": 8000, "thinking": "default", "server_build": None,
     "weights": ["GLM-OCR-Q8_0.gguf", "mmproj-GLM-OCR-Q8_0.gguf"]} for dpi in (300, 200))
EXPENSE_PARTS = ("A", "B", "C")
TOLERANCE = 0.011

#: what a recogniser puts between a label and its figure on one line: pipes, colons, `=`, dashes
GAP = r"[ \t|:;.,=\-–—_\[\]]*"
FIGURE = r"\$?\s*(?<![\d.,])([\d][\d, ]*\.\s?\d\d)\b"
TOTALS = (
    (re.compile(r"Total\s*\(\s*A\s*\+\s*B\s*\+\s*C\s*\)" + GAP + FIGURE, re.I), "form"),
    (re.compile(r"Total\s+Party\s+Election\s+Expenses:?" + GAP + FIGURE, re.I), "auditor"),
)
#: `PART\s*`: a recogniser can run the letter onto the word (`TOTAL FOR PARTE`); lazy, and not from mid-number
PART_LINE = re.compile(r"TOTAL\s+FOR\s+PART\s*([A-F])\b[^\n$]*?\$?\s*(?<![\d.,])([\d,]+\.\d\d)", re.I)
#: the declaration block's own `Part A: … $X`; the `$` is required, these lines are prose
SUMMARY_LINE = re.compile(r"^[^\n\S]*Part\s+([A-F])\s*:[^\n$]*?\$\s*(?<![\d.,])([\d,]+\.\d\d)", re.I | re.M)
LIMIT = re.compile(r"Expenditure\s+limit[^\n]*?\$\s*([\d,]+(?:\.\d\d)?)", re.I)
NIL_TOTAL = re.compile(r"Total\s*\(\s*A\s*\+\s*B\s*\+\s*C\s*\)" + GAP + r"(NIL|Nil|nil)\b")


@dataclass
class Result:
    document: str
    total: float = None                 # the return's own total (or its parts' sum where it prints none)
    total_check: str = None             # parts-sum | stated-only | summed-parts | declared-nil
    basis: str = None                   # form | auditor | parts
    page: int = None                    # the page the total (or the last part) was read on
    read_from: str = None               # text | pixels: how that page was read
    parts: dict = field(default_factory=dict)
    limit: float = None                 # the expenditure limit the form prints, when read
    profile_version: int = None
    reading_profile: str = None         # the profile and version the page reading was made under
    reading_version: int = None
    passes: str = ""                    # which pass gave the figure: first | pixels
    unread: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)


def money(s: str):
    digits = re.sub(r"[^0-9.]", "", s or "")
    if not re.fullmatch(r"\d+\.\d\d", digits):
        return None
    return round(float(digits), 2)


def stored_page(store: rd.Store, sha256: str, page: int):
    """The page reader's stored reading of one page, or None: the newest
    profile version first, the profile's own dots first."""
    for version in sorted((int(h["version"]) for h in profiles.history(PROFILE)), reverse=True):
        for settings in PAGE_SETTINGS:
            key = rd.reading_key(sha256, page, PAGE_MODEL, settings, PROFILE, version)
            if store.has(key):
                return store.get(key)
    return None


def figures(page_texts: dict) -> dict:
    """{total, basis, page, parts, part_pages, limit} over pages in order;
    the first hit for each wins."""
    out = {"total": None, "basis": None, "page": None, "parts": {}, "part_pages": {}, "limit": None, "nil": None}
    for p in sorted(page_texts):
        t = page_texts[p] or ""
        for m in LIMIT.finditer(t):
            v = money(m.group(1) + ("" if "." in m.group(1) else ".00"))
            if v and (out["limit"] is None or v > out["limit"]):
                out["limit"] = v
        for rx in (PART_LINE, SUMMARY_LINE):
            for m in rx.finditer(t):
                k = m.group(1).upper()
                if k not in out["parts"] and money(m.group(2)) is not None:
                    out["parts"][k] = money(m.group(2))
                    out["part_pages"][k] = p
        if out["nil"] is None and NIL_TOTAL.search(t):
            out["nil"] = p
    for rx, basis in TOTALS:
        for p in sorted(page_texts):
            m = rx.search(page_texts[p] or "")
            if m and money(m.group(1)) is not None:
                out.update(total=money(m.group(1)), basis=basis, page=p)
                return out
    return out


def judge(f: dict) -> tuple:
    """(total, check, why-not). The return's own arithmetic is the gate."""
    parts = f["parts"]
    have = [k for k in EXPENSE_PARTS if parts.get(k) is not None]
    if f["total"] is not None:
        if len(have) == len(EXPENSE_PARTS):
            s = round(sum(parts[k] for k in EXPENSE_PARTS), 2)
            if abs(s - f["total"]) <= TOLERANCE:
                return f["total"], "parts-sum", ""
            return None, None, f"the total read ({f['total']:.2f}, {f['basis']}) is not A + B + C as read ({s:.2f})"
        return f["total"], "stated-only", ""
    if len(have) == len(EXPENSE_PARTS):
        return round(sum(parts[k] for k in EXPENSE_PARTS), 2), "summed-parts", ""
    if f["nil"] is not None:
        return 0.0, "declared-nil", ""
    if have:
        return None, None, f"parts {', '.join(have)} read and no total: a part not read is not zero"
    return None, None, "no total and no parts read"


def _texts(data, sha256, store, prof_version, all_pixels: bool):
    """page → (text, read_from, profile, version); and the pages with neither."""
    layer = pages.text_pages(data)
    reading = read_document(data, sha256, profile=PROFILE, profile_version=prof_version, store=store, texts=layer)
    out = {}
    for r in reading.readings:
        if r.read_from == "text":
            out[r.page] = (r.text, "text", r.profile, r.profile_version)
    unread = []
    for p in sorted(layer):
        if p in out and not all_pixels:
            continue
        s = stored_page(store, sha256, p)
        if s is not None:
            out[p] = (s.text, "pixels", s.profile, s.profile_version)
        elif p not in out:
            unread.append(p)
    return out, unread


def read_return(data: bytes, sha256: str, store: rd.Store) -> Result:
    prof = profiles.profile(PROFILE)
    if prof is None:
        raise LookupError(f"no document profile {PROFILE}")
    res = Result(sha256, profile_version=int(prof["version"]))
    if not data.startswith(b"%PDF"):
        res.set_aside.append(("recognise", "not a PDF"))
        return res
    why = ""
    for pass_name, all_pixels in (("first", False), ("pixels", True)):
        texts, unread = _texts(data, sha256, store, res.profile_version, all_pixels)
        f = figures({p: t for p, (t, *_) in texts.items()})
        total, check, why = judge(f)
        if total is not None:
            page = f["page"] or max((f["part_pages"].get(k) or 0) for k in EXPENSE_PARTS) or f["nil"]
            _, how, rprof, rver = texts[page]
            res.total, res.total_check, res.basis = total, check, f["basis"] or ("nil" if check == "declared-nil" else "parts")
            res.page, res.read_from, res.parts, res.limit = page, how, f["parts"], f["limit"]
            res.reading_profile, res.reading_version, res.passes, res.unread = rprof, rver, pass_name, unread
            return res
        res.unread = unread
    tail = f"; pages with no text layer and no stored reading: {res.unread}" if res.unread else ""
    res.set_aside.append(("declaration", why + tail))
    return res
