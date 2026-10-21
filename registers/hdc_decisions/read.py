"""The lane's reading of the Health and Disability Commissioner's published
decisions and case studies (www.hdc.org.nz), from the four profiles proposed
in `profile-proposed.jsonl` (version 1; the integrator appends them at the
merge): `hdc-decisions-listing`, `hdc-decision-page`,
`hdc-case-studies-listing` and `hdc-case-study-page`. No model; nothing
fetched. A page is first recognised by its shape (the site's own blocks);
a page that is not its shape is set aside whole.

What is read, and only this (hard limits 11, 15 and 16):

  a decision    its page address (the key: `hdc_decisions/decision/<slug>`),
                the Commissioner's file number (from the address, else the
                number the page states most), the page's date, the kind (the
                gravest finding the page states), the provider kinds, the
                occupations and the Code rights the Commissioner tags the
                page with, the Code rights the page says were breached, the
                findings headed per party ("Opinion: X — breach"), the
                headings of its recommendations and whom they are addressed
                to, and the roles of individuals the Commissioner names, with
                the ground of the naming policy the page states
  a provider    one row per provider organisation the Commissioner names: as
                the page names it (the notice's exceptions, the parties block
                at the head, a finding's heading resolved through the page's
                own definition, an advice header's PROVIDER line), with its
                findings, the rights it breached, whether a recommendation is
                addressed to it, and a company, NZBN or charity number only
                where the page prints one beside the name

Never read: the heading (it describes the consumer's care), any paragraph's
words, the consumer, a family member, anyone the page anonymises (a letter
label is never kept; an individual is kept as a role), an individual
practitioner's name (a named practitioner is kept as a role and a naming
ground), the Commissioner's staff and advisers. Every kept text value passes
`consumer_detail`; a value that trips it is dropped and the catch log gets a
line naming the field, never the value.
"""
import datetime as dt
import hashlib
import html
import re
from collections import Counter

LISTING_PROFILE = "hdc-decisions-listing"
DECISION_PROFILE = "hdc-decision-page"
CASE_STUDIES_PROFILE = "hdc-case-studies-listing"
CASE_STUDY_PROFILE = "hdc-case-study-page"
PROFILE_VERSION = 1
READER = "registers.hdc_decisions.read 1"
KEY_PREFIX = "hdc_decisions"
BASE = "https://www.hdc.org.nz"
DECISIONS_PATH = "/decisions/search-decisions/"
CASE_STUDIES_PATH = "/decisions/case-studies-nga-matai-take/"
PER_PAGE = 12
SINCE = dt.date(2017, 1, 1)          # ruling 71: the window opens in 2017

#: an address segment made of the Commissioner's file numbers or the site's own id
OPAQUE = re.compile(r"(?:cas-[0-9a-z]{4,8}-[0-9a-z]{4,8}|\d{2}hdc\d{5}(?:-\d{2}hdc\d{5})*(?:-decision)?)")
_MAIN = re.compile(r"<main\b.*?</main>", re.S)
_BLOCK = re.compile(r"<title>\s*(?:Just a moment|Attention Required|Access denied)", re.I)
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")
_TILE = re.compile(r'<a class="o-tile[^"]*" href="(/decisions/(?:search-decisions/(\d{4})|case-studies-nga-matai-take)/'
                   r'([a-z0-9-]+)/)">(.*?)</a>', re.S)
_TILE_HEAD = re.compile(r'<h3 class="o-tile__heading">(.*?)</h3>', re.S)
_TILE_DATE = re.compile(r'<p class="o-tile__text">\s*(\d{1,2} [A-Z][a-z]{2,4} \d{4})\s*</p>')
_PAGES = re.compile(r'c-pagination__status">\s*Page (\d+) of (\d+)')
_PODS = re.compile(r'class="c-listing-pods"')
_DATE = re.compile(r'<span class="ss360-date">\s*([^<]*?)\s*</span>')
_BODY = re.compile(r'class="t-link-parent c-rte__body-text">(.*)', re.S)
_META = re.compile(r'<strong>([^<]*?)\s*:</strong>\s*<span class="ss360-category-[a-z-]+">(.*?)</span>', re.S)
_WEB_ID = re.compile(r'<span class="u-hidden">\s*(CAS-[0-9A-Z-]+)\s*</span>')
_CRUMB = re.compile(r'class="c-breadcrumb__link t-link">\s*<span itemprop="name">([^<]*)</span>')
_FILE_NO = re.compile(r"\bC?(\d{2}HDC\d{5})\b")
_SLUG_NO = re.compile(r"(\d{2})hdc(\d{5})")
_HEADING = re.compile(r"<h([2-5])\b[^>]*>(.*?)</h\1>", re.S)
_PARA = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S)
_NOTICE = re.compile(r"Names have been removed\s*(?:\(except ([^)]*)\))?\s*to protect", re.I)
_FINDING = re.compile(r"^(?:(?:Opinion|Decision)\s*:\s*)?(.+?)\s+[—–-]+\s+(breach|no breach|adverse comment|educational comment|"
                      r"other comment|other comments|no further action)\s*\.?$", re.I)
_ADVICE = re.compile(r"^(?:PROVIDER|FACILITY|PROVIDERS?)\s*:\s*(.+)$")
_RECOMMEND = re.compile(r"\brecommend(?:s|ed)? that,?\s+((?:[^.:;]{0,120}?,\s+)?)([^.:;,]{2,100}?)(?:\s*:|\s+(?:provide|apologise|"
                        r"undertake|review|conduct|use|develop|report|arrange|consider|implement|audit|complete|attend|"
                        r"update|share|ensure|reflect|give|send|make|carry|introduce|amend|establish|confirm|remind|"
                        r"present|organise|take|engage|perform|discuss|incorporate|create|prepare|design|evaluate|"
                        r"investigate|monitor|write|seek)\b)")
_BREACH = re.compile(r"(?P<pre>[^.;]{0,240}?)\b(?P<verb>breached|in breach of|breach of)\s+(?P<word>Rights?)\s+"
                     r"(?P<list>\d{1,2}(?:\(\d{1,2}\))?(?:\([a-z]\))?(?:\s*(?:,|and|&)\s*(?:Right\s+)?\d{1,2}(?:\(\d{1,2}\))?"
                     r"(?:\([a-z]\))?)*)")
_REC_HEADING = re.compile(r"^(?:Recommendations?(?:\s+and\s+follow-up(?:\s+actions?)?)?|Follow-up actions?|"
                         r"Further recommendations?|Recommendations? (?:for|to|made to) .{2,80})\s*$", re.I)
_RIGHT = re.compile(r"\d{1,2}(?:\(\d{1,2}\))?(?:\([a-z]\))?")
_NEGATED = re.compile(r"(?:\b(?:not|no|never|didn’t|didn't|would have|could have|may have|might have|to have)\s*$)", re.I)
_QUESTION = re.compile(r"\bwhether\b|\bif\b", re.I)
_DEFINE = re.compile(r"((?:[A-Z][\w’'&.\-]*(?:[|/][A-Z][\w’'&.\-]*)*|of|and|the|for|de|on|in|at|\||/|–)(?:\s+(?:[A-Z][\w’'&.\-]*"
                     r"(?:[|/][A-Z][\w’'&.\-]*)*|of|and|the|for|de|on|in|at|\||/|–|\d+))*)\s*\(\s*(?:“|\"|‘)?((?:the\s+)?[A-Z][\w’'.\-]*(?:\s+[A-Z][\w’'.\-]*){0,3})(?:”|\"|’)?"
                     r"\s*(?:;\s*(?:trading as|t/a)\s+([^)]{2,80}))?\)")
_NUMBER_BESIDE = re.compile(r"^\s*(?:\([^()]{1,30}\)\s*)?\(?\s*(?:(?:company number|company no\.?|NZBN|NZ Business Number)\s*:?\s*(\d{6,13})|"
                            r"(?:registered charity(?: number)?|charity number|charities registration number)\s*:?\s*(CC\d{5}))", re.I)

#: the words a provider kind is made of: a name of only these (and articles) is the Commissioner's anonymised
#: description of a provider ('the pharmacy', 'Disability Support Service', 'the DHB'), never a name
GENERIC = {
    "a", "an", "the", "district", "health", "board", "dhb", "pharmacy", "medical", "centre", "center", "disability",
    "support", "service", "services", "rest", "home", "hospital", "private", "care", "clinic", "dental", "practice",
    "ambulance", "mental", "addiction", "addictions", "laboratory", "radiology", "hospice", "residential", "community",
    "village", "retirement", "aged", "facility", "provider", "unit", "general", "maternity", "screening", "fertility",
    "rehabilitation", "beauty", "chiropractic", "prison", "accident", "and", "of", "for", "public", "nursing", "midwifery",
    "group", "organisation", "trust", "company", "surgical", "day", "surgery", "specialist", "physiotherapy", "imaging",
    "urgent", "after-hours", "primary", "secondary", "family", "whānau", "kaupapa", "māori", "elder", "older", "people",
    "persons", "respite", "home-based", "agency", "network", "corrections", "health-care", "healthcare", "region",
    "regional", "local", "national", "inpatient", "outpatient", "emergency", "department", "ward", "dementia",
}
STOP = {"a", "an", "the", "and", "of", "for"}
ORG_WORD = re.compile(
    r"\b(?:Limited|Ltd|Incorporated|Inc|Trust|Board|DHB|Hospital|Hospitals|Health|Hauora|Te Whatu Ora|Care|Clinic|Centre|"
    r"Center|Services?|Practice|Pharmacy|Chemist|Home|Homes|Village|Lodge|Manor|Medical|Ambulance|Dental|Hospice|Group|"
    r"Society|Council|Ministry|Corrections|Laboratories|Laboratory|Radiology|Healthcare|Surgical|Rehabilitation|"
    r"Partners|Associates|Network|Institute|Foundation|St John|Wellness|Physio\w*)\b")
PERSON = re.compile(r"^(?:Dr|Mr|Mrs|Ms|Miss|Mx|Master|Baby|Professor|Prof|Associate Professor|RN|EN|NP|RM|Nurse|"
                    r"Midwife|Sister|Father|Pastor)\.?\s+\S", re.I)
LETTER_LABEL = re.compile(r"^(?:Dr|Mr|Mrs|Ms|Miss|Mx|RN|EN|NP|RM|Nurse|Midwife|Master|Baby|Professor)\.?\s+[A-Z]{1,2}$")
NOT_PARTY = re.compile(r"\b(?:expert|experts|adviser|advisers|advisor|advisors|Commissioner|independent advice)\b", re.I)
STRUCTURE = re.compile(r"^(?:Contents|Table of contents|Findings|Executive summary|Introduction|Introduction and overview|"
                       r"Background|Complaint|Complaint and investigation|Information gathered|Summary|Overview|"
                       r"Recommendations?|Related Content)\b", re.I)
GRAVITY = ("breach", "adverse comment", "educational comment", "other comment", "no breach", "no further action")
NAMING_GROUNDS = (
    ("wilful disregard for consumer rights", re.compile(r"wilful(?:ly)? disregard", re.I)),
    ("public safety concerns", re.compile(r"public safety", re.I)),
    ("non-compliance with HDC recommendations", re.compile(r"(?:not|failed to|non-?)\s*compl\w* with (?:HDC'?s? |the |my |our )?"
                                                           r"recommendation", re.I)),
    ("frequent breaches", re.compile(r"(?:frequent|previous|repeated|prior|further) breach|breached the Code (?:on|in) "
                                     r"(?:a |two |three |several )?(?:previous|prior|other)", re.I)),
    ("public interest", re.compile(r"public interest", re.I)),
)

# ── the consumer-detail guard ─────────────────────────────────────────────────
#: words that describe a consumer, a family member or their condition; any kept text that carries one is refused
_LABEL = r"\b(?:Mr|Mrs|Ms|Miss|Mx|Master|Baby|Dr|RN|EN|NP|RM)\.?\s+[A-Z]{1,2}\b(?!\w)"
_AGE = (r"\b\d{1,3}[- ](?:year|yr|month|week|day)s?[- ]old\b|\baged\s+\d{1,3}\b|\b(?:in|during) (?:her|his|their) "
        r"(?:\d0s|teens|twenties|thirties|forties|fifties|sixties|seventies|eighties|nineties)\b|\b\d{1,3}\s*(?:yo|y/o|yrs?)\b|"
        r"\bage(?:d)?\s*[:=]?\s*\d{1,3}\b")
_KIN = (r"\b(?:his|her|their|the consumer’s|the consumer's|the patient’s|the patient's|the woman’s|the man’s|the woman's|"
        r"the man's)\s+(?:mother|father|son|daughter|wife|husband|partner|sister|brother|child|children|baby|whānau|family|"
        r"granddaughter|grandson|grandmother|grandfather|aunt|uncle|niece|nephew|parents?)\b|\b(?:the consumer|the "
        r"complainant|the patient|the resident|the deceased|consumer|complainant|deceased)\b")
_PERSON_WORDS = (r"\b(?:woman|man|girl|boy|infant|newborn|toddler|child|teenager|teen|elderly|pregnant|mother|father|"
                 r"wife|husband|widow|widower|daughter|son|grandmother|grandfather)\b")
_CONDITION = (r"\b(?:cancer|tumou?r|carcinoma|lymphoma|leukaemia|melanoma|dementia|alzheimer\w*|sepsis|septic|stroke|"
              r"diabet\w*|pregnan\w*|miscarriage|stillbirth|suicid\w*|self-harm|overdose|schizophren\w*|psychosis|psychotic|"
              r"bipolar|depress\w*|anxiety|autis\w*|epilep\w*|hiv|aids|hepatitis|asthma|pneumonia|fracture\w*|"
              r"amputat\w*|paralys\w*|died|death|deceased|dying|terminal|palliative|abortion|termination|"
              r"infection|covid|cardiac arrest|heart attack|appendicitis|ectopic|haemorrhage|hemorrhage|"
              r"pressure injur\w*|fall|falls|wound|ulcer|disabilit\w*|blind|deaf|addict\w*|alcohol\w*|drug use)\b")
#: places a consumer may be described by; a provider's own name may carry a place (it is the provider), any other
#: kept text may not
_PLACES = ("Auckland", "Wellington", "Christchurch", "Hamilton", "Tauranga", "Dunedin", "Palmerston North", "Napier",
           "Hastings", "Nelson", "Rotorua", "New Plymouth", "Whangārei", "Whangarei", "Invercargill", "Whanganui",
           "Wanganui", "Gisborne", "Timaru", "Blenheim", "Taupō", "Taupo", "Masterton", "Levin", "Ashburton", "Oamaru",
           "Queenstown", "Greymouth", "Westport", "Kaitāia", "Kaitaia", "Thames", "Whakatāne", "Whakatane", "Tokoroa",
           "Hāwera", "Hawera", "Cambridge", "Te Awamutu", "Pukekohe", "Porirua", "Lower Hutt", "Upper Hutt",
           "Kapiti", "Kāpiti", "Northland", "Waikato", "Bay of Plenty", "Hawke’s Bay", "Hawke's Bay", "Taranaki",
           "Manawatū", "Manawatu", "Canterbury", "Otago", "Southland", "West Coast", "Marlborough", "Tasman",
           "Wairarapa", "Coromandel", "Chatham Islands", "Lakes", "Tairāwhiti", "Tairawhiti", "Counties Manukau",
           "Waitematā", "Waitemata", "Capital and Coast", "Hutt Valley", "MidCentral", "Whanganui", "South Canterbury",
           "Nelson Marlborough", "Southern", "Te Tai Tokerau", "Waitaha", "Te Waipounamu", "Te Manawa Taki",
           "Te Ikaroa", "Te Toka Tumai")
_PLACE = r"\b(?:" + "|".join(re.escape(p) for p in sorted(set(_PLACES), key=len, reverse=True)) + r")\b"
GUARD_STRICT = re.compile("|".join((_LABEL, _AGE, _KIN, _PERSON_WORDS, _CONDITION, _PLACE)), re.I)
#: a provider's name may carry a place and a kind word ('Dementia Care NZ'); never a label, an age or kin
GUARD_NAME = re.compile("|".join((_LABEL, _AGE, _KIN)), re.I)


def consumer_detail(value: str, field: str = "") -> str:
    """'' when the value may be kept; else which kind of consumer detail it carries (never the value)."""
    if not value:
        return ""
    guard = GUARD_NAME if field in ("name", "abbreviation", "also_called", "recommended_to", "finding_party") else GUARD_STRICT
    m = guard.search(value)
    if not m:
        return ""
    s = m.group(0)
    for kind, pat in (("a letter label", _LABEL), ("an age", _AGE), ("a relation or the consumer", _KIN),
                      ("a description of a person", _PERSON_WORDS), ("a condition or an event of care", _CONDITION),
                      ("a place", _PLACE)):
        if re.fullmatch(pat, s, re.I):
            return kind
    return "a consumer detail"


# ── small pieces ──────────────────────────────────────────────────────────────

def clean(s: str) -> str:
    return _SPACE.sub(" ", html.unescape(_TAG.sub(" ", s or ""))).strip()


def date_of(s: str):
    s = clean(s).replace("Sept ", "Sep ").replace("June ", "Jun ").replace("July ", "Jul ")
    for fmt in ("%d %b %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def _text(body: bytes) -> str:
    return body.decode("utf-8", "replace")


def generic(name: str) -> bool:
    """A name made only of provider-kind words is the Commissioner's anonymised description, not a name."""
    words = [w.strip(".()") for w in re.split(r"[\s|/,–-]+", (name or "").lower().replace("’s", "")) if w]
    return any(w not in STOP for w in words) and all(w in GENERIC for w in words)


def norm(name: str) -> str:
    """For matching a provider's forms of name to one another: case, the DHB's two spellings, the macron-less forms."""
    s = (name or "").lower().replace("district health board", "dhb").replace("’", "'")
    s = s.translate(str.maketrans("āēīōū", "aeiou"))
    s = re.sub(r"^(?:the|by|at|from|to)\s+", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# ── the listings ──────────────────────────────────────────────────────────────

def recognise_listing(body: bytes) -> str:
    """'' when the page is a decisions or case-studies listing page, else why not."""
    t = _text(body)
    if _BLOCK.search(t[:4096]):
        return "a block page, not a listing"
    if not _PODS.search(t):
        return "no listing pods on the page (not a listing)"
    return ""


def read_listing(body: bytes) -> dict:
    """{'stated': pages stated (the listing's own count of its pages), 'page': this page's number, 'items': [{'slug',
    'url', 'card', 'listed_on', 'year'}]}. `card` is the fingerprint: the tile's date and a hash of its heading (the
    heading describes the consumer's care, so it is never kept, only hashed)."""
    why = recognise_listing(body)
    if why:
        raise ValueError(why)
    t = _text(body)
    pods = t[_PODS.search(t).start():]
    pods = pods[:pods.find('class="c-pagination"')] if 'class="c-pagination"' in pods else pods
    items, seen = [], set()
    for path, year, slug, inner in _TILE.findall(pods):
        if slug in seen:
            continue
        seen.add(slug)
        d = _TILE_DATE.search(inner)
        h = _TILE_HEAD.search(inner)
        listed_on = date_of(d.group(1)) if d else None
        card = f"{listed_on or ''}|{hashlib.sha256(clean(h.group(1) if h else '').encode()).hexdigest()[:12]}"
        items.append({"slug": slug, "url": BASE + path, "card": card, "listed_on": listed_on,
                      "year": int(year) if year else (listed_on.year if listed_on else None)})
    pages = _PAGES.search(t)
    return {"stated": int(pages.group(2)) if pages else 1, "page": int(pages.group(1)) if pages else 1, "items": items}


# ── a decision or a case study ────────────────────────────────────────────────

def recognise_page(body: bytes) -> str:
    t = _text(body)
    if _BLOCK.search(t[:4096]):
        return "a block page, not a decision"
    if not _DATE.search(t):
        return "no dated header (not a decision or a case study)"
    if not _BODY.search(t):
        return "no body text block (not a decision or a case study)"
    return ""


def _blocks(body_html: str):
    """The body in order: ('h', level, text, lines) and ('p', 0, text, []) blocks; a heading's lines are split at its
    line breaks (the parties block at the head of a decision puts one party on each)."""
    out = []
    for m in re.finditer(r"<h([2-5])\b[^>]*>(.*?)</h\1>|<p\b[^>]*>(.*?)</p>", body_html, re.S):
        if m.group(1):
            lines = [clean(x) for x in re.split(r"<br\s*/?>", m.group(2))]
            out.append(("h", int(m.group(1)), " ".join(x for x in lines if x), [x for x in lines if x]))
        else:
            out.append(("p", 0, clean(m.group(3)), []))
    return out


def _notice(blocks):
    """(the notice's exceptions as stated, split; whether a notice is on the page)."""
    for kind, _, text, _lines in blocks[:6]:
        m = _NOTICE.search(text)
        if kind == "p" and m:
            if not m.group(1):
                return [], True
            parts = re.split(r",\s*(?:and\s+)?|\s+and\s+(?=(?:the\s+)?[A-Z]|the\b)", m.group(1))
            return [p.strip() for p in parts if p.strip()], True
    return [], False


def _parties_block(blocks):
    """The headings the page opens with, before its first paragraph or structural heading: who the decision is about,
    as [('individual', role, label) | ('organisation', name)]."""
    out = []
    for kind, level, text, lines in blocks:
        if kind == "p":
            if not text or _NOTICE.search(text):
                continue
            break
        if STRUCTURE.match(text) or level > 2:
            break
        for line in lines:
            if "," in line:
                role, label = (x.strip() for x in line.rsplit(",", 1))
                if role and label:
                    out.append(("individual", role, label))
                    continue
            out.append(("organisation", line))
    return out


#: bodies a decision names that are never the provider complained about
NOT_PROVIDER = re.compile(r"\b(?:Health Quality (?:&|and) Safety Commission|Te Tāhū Hauora|HQSC|Accident Compensation|ACC|"
                          r"Ministry of Health|Manatū Hauora|Medical Council|Nursing Council|Pharmacy Council|Midwifery Council|"
                          r"Dental Council|Health Practitioners Disciplinary Tribunal|Human Rights Review Tribunal|"
                          r"Director of Proceedings|Coroner|Police|Health and Disability Commissioner|Commissioner|"
                          r"Royal (?:Australasian|New Zealand) College|College of|Council of|Pharmaceutical Society|"
                          r"PHARMAC|Te Pātaka|Standards New Zealand|Code)\b")


def _definitions(text: str) -> dict:
    """{norm(abbreviation): (full name as stated, abbreviation, trading as)} for definitions shaped like an
    organisation's: 'Ultimate Care Oakland (UCO; trading as …)'. `def_for` finds one by either form."""
    out = {}
    for m in _DEFINE.finditer(text):
        name, abbr, trading = m.group(1).strip(), m.group(2).strip(), (m.group(3) or "").strip(" .;") or None
        name = re.sub(r"^(?:(?:the|by|at|from|to|and|of|for|in|on)\s+)+", "", name, flags=re.I).strip(" |/–")
        if not name or not ORG_WORD.search(name) or PERSON.match(name) or len(name) > 120:
            continue
        if re.fullmatch(r"(?:the\s+)?(?:Code|HDC|Commissioner|Act)", abbr, re.I):
            continue
        out.setdefault(norm(abbr), (name, abbr, trading))
    return out


def def_for(form: str, defs: dict):
    """The definition whose abbreviation or name is `form` (or one of its '/' and '|' forms), else None."""
    wants = {norm(f) for f in [form] + re.split(r"[|/]", form or "") if f and norm(f)}
    return next((d for k, d in defs.items() if k in wants or norm(d[0]) in wants), None)


class Providers:
    """The provider organisations a page names, merged across the forms the page names them by."""

    def __init__(self):
        self.rows = []

    def find(self, form: str):
        n = norm(form)
        if not n:
            return None
        for r in self.rows:
            if n in r["forms"]:
                return r
        return None

    def add(self, name: str, how: str, forms=(), abbreviation=None, also=None):
        name = name.strip(" .,;:")
        r = self.find(name) or next((self.find(f) for f in forms if self.find(f)), None)
        if r is None:
            r = {"name": name, "abbreviation": None, "also_called": [], "found_by": [], "forms": set(),
                 "named": not generic(name)}
            self.rows.append(r)
        elif len(name) > len(r["name"]) and not generic(name):
            if r["name"] not in r["also_called"]:
                r["also_called"].append(r["name"])
            r["name"] = name
        r["named"] = r["named"] or not generic(name)
        if abbreviation and not r["abbreviation"]:
            r["abbreviation"] = abbreviation
        for a in [also] if also else []:
            if a not in r["also_called"] and a != r["name"]:
                r["also_called"].append(a)
        if how not in r["found_by"]:
            r["found_by"].append(how)
        for f in (name, abbreviation, also, *forms):
            if f:
                r["forms"].update(norm(x) for x in [f] + re.split(r"[|/]", f) if norm(x))
        return r

    def find_loose(self, form: str):
        """A form of two words or more that holds, or is held by, a provider's form of two words or more."""
        n = norm(form)
        if len(n.split()) < 2:
            return None
        for r in self.rows:
            for f in r["forms"]:
                if len(f.split()) >= 2 and (re.search(rf"\b{re.escape(f)}\b", n) or re.search(rf"\b{re.escape(n)}\b", f)):
                    return r
        return None


def _resolve(form: str, providers: Providers, defs: dict, how: str = "a finding's heading, through the page's definition"):
    """A finding's or a recommendation's party: the provider row, or None."""
    form = re.sub(r"^(?:the|by|at)\s+", "", form.strip(), flags=re.I)
    if not form or PERSON.match(form) or LETTER_LABEL.match(form):
        return None
    r = providers.find(form)
    if r is not None:
        return r
    d = def_for(form, defs)
    if d is not None and not NOT_PROVIDER.search(d[0]):
        return providers.find(d[0]) or providers.find(d[1]) or providers.add(
            d[0], how, forms=(d[1],), abbreviation=d[1], also=d[2])
    if generic(form):
        return providers.add(form, how)
    return providers.find_loose(form)


def is_person(form: str) -> bool:
    """A named individual, as a notice of names writes one: a title and a name, or a bare personal name with no
    organisation word. An abbreviation ('ACC', 'SDHB') and anything with an organisation word is not."""
    form = (form or "").strip()
    if PERSON.match(form):
        return True
    return bool(re.fullmatch(r"[A-Z][a-zà-ž’'-]+(?:\s+(?:[A-Z][a-zà-ž’'-]+|de|van|von|le|la)){1,3}", form)) \
        and not ORG_WORD.search(form)


def _individual(form: str, parties):
    """('individual', role) for a person the page names or labels; None otherwise."""
    form = form.strip()
    for p in parties:
        if p[0] == "individual" and (norm(p[2]) == norm(form) or (
                not LETTER_LABEL.match(p[2]) and PERSON.match(form) and norm(form).split()[-1] == norm(p[2]).split()[-1])):
            return p[1]
    if LETTER_LABEL.match(form) or PERSON.match(form):
        return "an individual provider"
    return None


def _subject(clause: str, providers: Providers, defs: dict):
    """The provider a breach statement is about: the last provider form in its clause; where the page names no
    provider any other way (a case study), the last organisation the page defines."""
    n = " " + norm(clause) + " "
    best, at = None, -1
    for r in providers.rows:
        for f in r["forms"]:
            for m in re.finditer(rf"\b{re.escape(f)}\b", n):
                if m.end() > at:
                    best, at = r, m.end()
    for k, d in defs.items() if not any(r["named"] for r in providers.rows) else ():
        if NOT_PROVIDER.search(d[0]) or generic(d[0]):
            continue
        for f in (k, norm(d[0])):
            for m in re.finditer(rf"\b{re.escape(f)}\b", n):
                if m.end() > at:
                    best, at = d, m.end()
    if isinstance(best, tuple):
        best = providers.find(best[0]) or providers.add(best[0], "a breach statement, through the page's definition",
                                                        forms=(best[1],), abbreviation=best[1], also=best[2])
    return best


def _naming_ground(sentence: str) -> str:
    for ground, pat in NAMING_GROUNDS:
        if pat.search(sentence):
            return ground
    return "stated, not one of the policy's grounds"


def _place(slug: str) -> str:
    """A catch-log place that never spells an address describing the case."""
    return slug if OPAQUE.fullmatch(slug or "") else "#" + hashlib.sha256((slug or "").encode()).hexdigest()[:16]


def read_page(body: bytes, sha: str, slug: str, url: str = None, kind: str = "decision") -> dict:
    """{'decision': row, 'providers': [rows], 'set_aside': [lines]} for one decision or case study page."""
    why = recognise_page(body)
    profile = DECISION_PROFILE if kind == "decision" else CASE_STUDY_PROFILE
    aside = lambda place, stage, reason: {"document": sha, "place": place, "stage": stage, "reason": reason}
    if why:
        return {"decision": None, "providers": [], "set_aside": [aside(f"page={_place(slug)}", "recognise", why)],
                "private": []}
    t = _text(body)
    main = (_MAIN.search(t) or re.search(r".*", t, re.S)).group(0)
    decided_on = date_of(_DATE.search(main).group(1))
    if decided_on is None:
        return {"decision": None, "providers": [], "set_aside": [aside(f"page={_place(slug)}", "recognise",
                                                                        "the page's date is not a date")], "private": []}
    body_html = _BODY.search(main).group(1)
    blocks = _blocks(body_html)
    # a block's end is a boundary no name runs across ('… Dr Jane Inventa' + 'Findings' + 'Invented Care Homes Limited')
    text = clean(re.sub(r"</(?:h[1-6]|p|li|td|th|div|tr|ol|ul)>|<br\s*/?>", " ¶ ", body_html))
    asides = []
    meta = {}
    for k, v in _META.findall(main):
        meta.setdefault(clean(k).lower(), []).append(clean(v))

    # the Commissioner's file number
    from_slug = ["{}HDC{}".format(*m) for m in _SLUG_NO.findall(slug)]
    stated = Counter(_FILE_NO.findall(text))
    case_number = from_slug[0] if from_slug else (stated.most_common(1)[0][0] if stated else None)
    numbers = from_slug or ([case_number] if case_number else [])

    # who the page names
    exceptions, has_notice = _notice(blocks)
    parties = _parties_block(blocks) if kind == "decision" else []
    defs = _definitions(text)
    providers = Providers()
    named_people = []
    for e in exceptions:
        if NOT_PARTY.search(e):
            continue
        if not is_person(e):
            alias = re.split(r"[/]", e)
            d = def_for(e, defs)
            if d:
                providers.add(d[0], "the notice of names", forms=alias, abbreviation=d[1], also=e if e != d[0] else d[2])
            else:
                providers.add(e, "the notice of names", forms=alias)
        else:
            named_people.append(e)
    for p in parties:
        if p[0] == "organisation":
            d = def_for(p[1], defs)
            providers.add(p[1], "the parties at the head", abbreviation=d[1] if d else None, forms=(d[1],) if d else (),
                          also=d[2] if d else None)
        elif not LETTER_LABEL.match(p[2]) and p[2] not in named_people:
            named_people.append(p[2])
    for kind_h, _, h, _lines in blocks:
        m = _ADVICE.match(h) if kind_h == "h" else None
        if m and ORG_WORD.search(m.group(1)) and not PERSON.match(m.group(1)) and not GUARD_NAME.search(m.group(1)):
            d = def_for(m.group(1), defs)
            providers.add(m.group(1), "an advice header's PROVIDER line", forms=(d[1],) if d else (),
                          abbreviation=d[1] if d else None, also=d[2] if d else None)

    # findings headed per party
    findings = []
    for kind_h, _, h, _lines in blocks:
        if kind_h != "h":
            continue
        m = _FINDING.match(h)
        if not m:
            continue
        who, outcome = m.group(1).strip(), m.group(2).lower().replace("other comments", "other comment")
        # a finding about two parties at once ('Waikato DHB and Auckland DHB — adverse comment') is one per party,
        # where each side is a party; otherwise the heading is one party, or an issue
        sides = [x.strip() for x in re.split(r"\s+and\s+|,\s*", who)]
        each = [(_resolve(x, providers, defs) or _individual(x, parties)) for x in sides] if len(sides) > 1 else []
        if each and all(each):
            findings += [(x, outcome) for x in each]
            continue
        r = _resolve(who, providers, defs)
        if r is not None:
            findings.append((r, outcome))
            continue
        role = _individual(who, parties)
        findings.append((role, outcome))             # an issue heading's text is never kept: only its outcome

    # rights stated as breached, and by whom
    breaches = []
    for m in _BREACH.finditer(text):
        pre = m.group("pre")
        clause = re.split(r"\b(?:but|however|although|whereas)\b", pre)[-1]
        if _NEGATED.search(clause) or _QUESTION.search(clause):
            continue
        rights = _RIGHT.findall(m.group("list"))
        breaches.append((_subject(clause, providers, defs), rights))
    rights_breached = list(dict.fromkeys(x for _, rs in breaches for x in rs))

    # recommendations: their headings as stated, and whom they are addressed to
    headings = list(dict.fromkeys(h for k, _, h, _l in blocks if k == "h" and _REC_HEADING.match(h)))
    to = []
    for m in _RECOMMEND.finditer(text):
        who = m.group(2).strip()
        r = _resolve(who, providers, defs, "a recommendation's addressee, through the page's definition")
        if r is not None:
            r["recommended"] = True
            to.append(r["name"] if r["named"] else f"an unnamed {r['name'].lower().removeprefix('the ')}")
        elif (role := _individual(who, parties)) is not None:
            to.append(role)

    # individuals the Commissioner names: a role and the stated ground, never the name
    named_roles, grounds = [], []
    for person in named_people:
        role = next((p[1] for p in parties if p[0] == "individual" and norm(p[2]) == norm(person)), None)
        if role is None and len(meta.get("occupations", [])) == 1:
            role = meta["occupations"][0]
        surname = person.split()[-1]
        reason = next((s for s in re.split(r"(?<=[.])\s+", text) if re.search(rf"\b{re.escape(surname)}\b", s)
                       and re.search(r"\bnam(?:e|ed|ing)\b", s, re.I) and "Names have been removed" not in s), "")
        named_roles.append(role or "a practitioner")
        grounds.append(_naming_ground(reason) if reason else "not stated on the page")

    # what is kept, through the guard
    names = sorted({x for r in providers.rows if r["named"] for x in [r["name"], r["abbreviation"], *r["also_called"]] if x},
                   key=len, reverse=True)

    def keep(field, value):
        """The value, or None and a catch-log line. A provider's own name in a heading is the provider, not a place."""
        bare = value
        for n in names if field == "recommendation_heading" else ():
            bare = (bare or "").replace(n, "")
        why = consumer_detail(bare, field)
        if why:
            asides.append(aside(f"page={_place(slug)}", "guard", f"{field}: {why}; the value is not kept"))
            return None
        return value

    def party_word(x):
        if isinstance(x, dict):
            return x["name"] if x["named"] else f"an unnamed {x['name'].lower().removeprefix('the ')}"
        return x or "an issue heading"

    finding_rows = [f"{party_word(p)} — {o}" for p, o in findings]
    finding_rows = [v for v in (keep("finding_party", f) for f in dict.fromkeys(finding_rows)) if v]
    outcomes = [o for _, o in findings] + (["breach"] if rights_breached else [])
    decision_kind = ("case study" if kind == "case study" else
                     next((g for g in GRAVITY if g in outcomes), "not stated"))
    headings = [v for v in (keep("recommendation_heading", h) for h in headings) if v]
    to = [v for v in (keep("recommended_to", x) for x in dict.fromkeys(to)) if v]
    named_roles = [keep("named_role", r) or "a practitioner" for r in named_roles]

    # an address made of file numbers or the site's own id names nobody and describes nothing; any other (a case
    # study's is its summary) is kept in the private twin, and the key is made from its hash, stable across re-reads
    opaque = bool(OPAQUE.fullmatch(slug))
    address = url or f"{BASE}{DECISIONS_PATH if kind == 'decision' else CASE_STUDIES_PATH}{slug}/"
    key = (f"{KEY_PREFIX}/{'decision' if kind == 'decision' else 'case-study'}/"
           + (slug if opaque else hashlib.sha256(slug.encode()).hexdigest()[:16]))
    cite = {"document": sha, "page": 1, "read_from": "text", "reader": READER, "profile": profile,
            "profile_version": PROFILE_VERSION}
    decision = {
        "key": key, "slug": slug if opaque else None, "kind_of_page": kind, "case_number": case_number, "case_numbers": numbers,
        "web_id": (_WEB_ID.search(main).group(1) if _WEB_ID.search(main) else None), "decided_on": decided_on,
        "kind": decision_kind, "findings": finding_rows,
        "provider_kinds": meta.get("group providers", []), "occupations": meta.get("occupations", []),
        "rights_tagged": meta.get("rights", []), "rights_breached": rights_breached,
        "recommendation_headings": headings, "recommended_to": to,
        "named_roles": named_roles, "naming_grounds": grounds, "names_removed": has_notice,
        "providers_named": 0, "url": address if opaque else None,
        "place": "header and body", **cite}

    rows = []
    for r in providers.rows:
        if not r["named"]:
            continue
        name = keep("name", r["name"])
        if name is None:
            continue
        number = None
        for form in [r["name"]] + r["also_called"]:
            for at in re.finditer(re.escape(form), text):
                m = _NUMBER_BESIDE.match(text[at.end(): at.end() + 80])
                if m:
                    number = m.group(1) or m.group(2)
                    break
            if number:
                break
        mine = [o for p, o in findings if p is r]
        rights = list(dict.fromkeys(x for who, rs in breaches if who is r for x in rs))
        rows.append({"key": f"{key}/provider/{len(rows) + 1}", "decision_key": key, "ordinal": len(rows) + 1,
                     "name": name, "abbreviation": keep("abbreviation", r["abbreviation"]),
                     "also_called": [v for v in (keep("also_called", a) for a in r["also_called"]) if v],
                     "found_by": r["found_by"], "findings": list(dict.fromkeys(mine)), "rights_breached": rights,
                     "recommended": bool(r.get("recommended")),
                     "company_number": number if number and not number.startswith("CC") else None,
                     "charity_number": number if number and number.startswith("CC") else None,
                     "decided_on": decided_on, "place": f"providers[{len(rows) + 1}]", **cite})
    decision["providers_named"] = len(rows)
    private = [] if opaque else [{"key": key, "slug": slug, "url": address, "document": sha}]
    return {"decision": decision, "providers": rows, "set_aside": asides, "private": private}
