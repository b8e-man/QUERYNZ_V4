"""Who attended, one row each: the reading of an entry's `attendees` text
into its attendees, by rules (no model, nothing looked up but the director
register's given names in keys/given_names.txt).

    split(text) -> (rows, reason)

`rows` is one dict per attendee, in the order the release prints them:
`position` (1, 2, …), `attendee` (the text as written, whole), `sep_before`
(the separator text consumed before it: '' for the first), `sep_after` (any
separator left at the end, on the last row only), `kind`, `folded` and
`organisation`. `reason` is '' or why the text was not split (the entry is
then set aside, and no row is made for it). The rows reconcile: the
separators and the attendees joined in order are the text exactly, so once
folded they are the text folded (`reconciles`); a split that did not is set
aside, never published.

The rules, each from the shapes measured on 2 November 2026 (208,464
entries, 191,643 with an attendees text):

  - The separators, outside brackets only: `;` and `,` (with an `and`, `&`
    or `+` after either), and ` and `, ` & `, ` + ` standing alone. `Q&A`,
    `Beef&Lamb` and `MDP/Whaikaha` have no spaced separator and are one
    attendee; `|` is a body's two names (`Te Arawhiti | The Office for Māori
    Crown Relations`) and never separates. A few bodies' names carry a
    separator and are never split (`KEEP`: `Ministry of Business,
    Innovation and Employment`, `Department of the Prime Minister and
    Cabinet`, …).
  - An `and`, `&` or `+` inside a body's name is kept: one word and `&` or
    `+` before a capitalised word that is no group's (`Ernst & Young`, `Beef
    + Lamb New Zealand`, never `Parker + Officials`), and a tail of two or
    more words ending in a body's or group's word after a head that is no
    person, group, role or body of its own (`Mental Health & Wellbeing
    Commission`).
  - `Name, Organisation`: a person's name followed by a comma and one or two
    pieces that are neither a person, a group, a title nor withheld is one
    attendee (`Glen Webber, Acting Chief Executive, Te Arawhiti`); the
    organisation part is the last of them that is not a bare role (a role's
    `of X`, `at X`, `for X` gives X where X is a body).
  - `Name (Organisation)`: a person's name with a bracket; the bracket's last
    comma part that is not a bare role (`Michelle Hippolite (CE, Te Puni
    Kōkiri)` → `Te Puni Kōkiri`; `(MP for Kelston)` gives none).
  - Titles (`Rt Hon`, `Hon`, `Hons`, `Ministers`, `Dr`, `Sir`, `Mayor`,
    `Minister`, …) and a trailing `MP`, `KC`, `QC` are taken off before a
    name is judged or folded; the attendee text keeps them. One capitalised
    word after a titled person (`Hons Willis, Bishop, Jones`, `Hon Salesa
    and Genter`) is a surname: a person.
  - The kinds: `withheld` (the release's withholding: the whole text, never
    split), `group` (the ministry and officials boilerplate, `Officials`,
    `MBIE Officials`, `Cabinet Ministers`, `Invited guests`, `Media`, and a
    portfolio's bare words, `Trade and Investment`; its organisation part is
    what stands before the group word where that is a body's name and the
    group is not the Crown's or a party's own, so `Fonterra staff` gives
    Fonterra and `MBIE Officials` none), `role` (a role with no name: `CEO`,
    `PM`, `Secretary of Defence`), `person` (a given name the director
    register knows, or a title, and two to four words with no body's word),
    `crown` (a ministry, department, Crown agency or Cabinet committee by its
    own name or initials: the Crown's own people, never a company met; its
    organisation part is its name) and `organisation` (the rest: the
    attendee is a body, and its organisation part is its own name, outside
    any bracket).

`folded` is the attendee with titles off, folded as the scans fold a name
(products/scan/plan.fold_sql: lower case, macrons off, a legal ending off,
letters and digits only). An organisation part that folds to nothing is
none. Names are as printed and linked to nobody.
"""
import re

from keys import names as N
from registers.ministers_diaries.read import WITHHELD

READER = "registers.ministers_diaries.attendees"
KINDS = ("person", "organisation", "crown", "group", "role", "withheld")

SEP = re.compile(r"\s*[;,]\s*(?:(?:and|&|\+)\s+)?|\s+(?:and|&|\+)\s+", re.I)
SOFT = re.compile(r"^\s+(?:and|&|\+)\s+$", re.I)          # a separator with no comma: may sit inside a body's name
AMP = re.compile(r"^\s+[&+]\s+$")
#: bodies' names that carry a separator: never split
KEEP = re.compile(r"ministry\s+of\s+business,?\s+innovation,?\s+(?:and|&)\s+employment|business,?\s+innovation,?\s+(?:and|&)\s+"
                  r"employment|department\s+of\s+(?:the\s+)?prime\s+minister\s+(?:and|&)\s+cabinet|ministry\s+of\s+foreign\s+"
                  r"affairs\s+(?:and|&)\s+trade|ministry\s+(?:of|for)\s+housing\s+(?:and|&)\s+urban\s+development|ministry\s+"
                  r"(?:for|of)\s+culture\s+(?:and|&)\s+heritage|arts,?\s+culture\s+(?:and|&)\s+heritage|fisher\s+(?:and|&)\s+"
                  r"paykel(?:\s+healthcare|\s+appliances)?|beef\s*(?:and|&|\+)\s*lamb(?:\s+new\s+zealand)?|"
                  r"ministry\s+of\s+(?:agriculture|primary\s+industries)\s+(?:and|&)\s+(?:forestry|fisheries)|"
                  r"(?:nz|new\s+zealand)\s+trade\s+(?:and|&)\s+enterprise|forest\s*(?:and|&|\+)\s*bird|fish\s*(?:and|&|\+)\s*game|"
                  r"fire\s+(?:and|&)\s+emergency|appointments\s+(?:and|&)\s+honours|child\s+(?:and|&)\s+youth|"
                  r"advocacy\s+(?:and|&)\s+strategy|ernst\s*&\s*young|mental\s+health\s+(?:and|&)\s+wellbeing", re.I)
TITLE = re.compile(r"^(?:(?:the\s+)?(?:rt\.?\s+hon(?:ourable)?|right\s+honourable|honourable|hons?|mins?|ministers[’']?|dr|mr|mrs|ms|miss|mx|messrs|"
                   r"sir|dame|prof|professor|assoc(?:iate)?\.?\s+prof(?:essor)?|rev|reverend|judge|his\s+excellency|"
                   r"her\s+excellency|h\.?e\.?|lady|lord|deputy\s+mayor|mayor|councillor|cr|ministers|minister|"
                   r"associate\s+minister|deputy\s+prime\s+minister|prime\s+minister|kaumātua|kaumatua)\.?\s+)+", re.I)
POST = re.compile(r"(?:[\s,]+(?:mp|kc|qc|jp|onzm|cnzm|dnzm|knzm|mnzm|qso|qsm|mbe|obe))+\.?$", re.I)
#: a group: the ministry and officials boilerplate, by its last word …
GROUP_WORDS = frozenset("""officials official staff ministers colleagues members attendees attendee attending guests guest
advisors advisers advisor adviser representatives reps team teams delegation delegates students media invitees participants
organisers organizers stakeholders others secretariat office officers councillors mps leaders executives board panel caucus
cabinet crew whanau whānau families volunteers speakers panellists panelists hosts invited public residents community
communities parents teachers workers employees management committee committees ministry trustees family graduates
""".split())
#: … the groups whose organisation part is the Crown's or a party's own, never a company's
CROWN_GROUP = frozenset("""officials official ministers colleagues members secretariat office officers councillors mps caucus
cabinet committee committees ministry""".split())
#: … or its first
GROUP_LEAD = frozenset("various multiple relevant invited other others several some all selected select key event".split())
#: words that alone name no body, before a group word (`Health Officials`, `Cabinet Committee Members`); with the
#: portfolios' own words, a piece of these alone is a group (`Trade and Investment`, `Agriculture`)
GENERIC = frozenset("""cabinet committee health justice relevant ministry ministerial ministers minister other various multiple all
event invited government select senior key local departmental agency agencies sector official officials office officers the
and of for my his her their our associate parliamentary policy private press political portfolio department staff team
treasury iwi hapu hapū industry business stakeholder stakeholders school community local regional national international
overseas foreign visiting new nz zealand aotearoa centre union respective summit conference court site meeting workshop
visit project programme tour hui forum panel launch respectively both""".split())
PORTFOLIO = frozenset("""agriculture trade investment export exports forestry fisheries oceans education transport housing finance
defence police justice environment conservation energy resources tourism immigration revenue economic development social culture
heritage arts sport recreation climate change state services workplace relations safety affairs disability issues seniors youth
women pacific peoples maori māori crown treaty waitangi negotiations biosecurity food land information statistics science
innovation technology digital economy communications broadcasting research infrastructure building construction emergency
corrections courts customs veterans children ethnic rural small commerce consumer internal hospitality manufacturing employment
skills tertiary mental wellbeing racing space cyber security intelligence covid response recovery regeneration whānau whanau ora
oranga tamariki urban trades tax welfare strategy advocacy risk sustainability""".split())
#: places alone: a delegation's or a region's, never a body's name (`Canada`, `Auckland`)
PLACES = frozenset("""auckland wellington christchurch hamilton tauranga dunedin napier hastings nelson rotorua whangarei
invercargill queenstown northland waikato canterbury otago southland taranaki manawatu whanganui wairarapa gisborne marlborough
westland tasman australia canada japan china india singapore korea france germany usa us uk eu britain ireland fiji samoa tonga
vietnam indonesia malaysia thailand philippines chile mexico brazil italy spain israel taiwan""".split())
ROLE_WORDS = frozenset("""ceo ce coo cfo cto chief executive chair chairman chairwoman chairperson chairs director directors manager
managers secretary commissioner mayor president vice deputy head principal founder co-founder cofounder partner general counsel
governor ambassador consul high editor reporter journalist producer presenter host adviser advisor officer lead leader trustee
kaiwhakahaere tumuaki spokesperson spokesman spokeswoman minister mp acting interim managing executive regional national
senior assistant associate private pm dpm gm md cio ces ceos chairs heads dce dces sps ps""".split())
#: a body's word: a name with one is no person's (with keys.names' own list)
BODY = re.compile(r"\b(?:ministry|department|commission|authority|agency|office|council|university|school|college|"
                  r"hospital|bank|board|forum|alliance|network|federation|union|institute|iwi|hapū|hapu|rūnanga|runanga|"
                  r"marae|trust|ngāti|ngati|ngāi|ngai|aotearoa|zealand|nz|radio|tv|news|media|herald|"
                  r"insurance|energy|airport|police|army|navy|defence|health|group|"
                  r"limited|ltd|inc|incorporated|association|society|foundation|federated|chamber|chambers|business|"
                  r"industry|industries|services|consulting|partners|company|co|corporation|corp|holdings|club|centre|"
                  r"center|committee|team|crown|embassy|consulate|high commission|parliament|tribunal)\b", re.I)
#: a word that ends a body's name: a head ending so is a body of its own (`Auckland Council and Ports of Auckland`)
STRONG_BODY = re.compile(r"\b(?:ministry|department|commission|authority|council|university|school|college|hospital|bank|"
                         r"board|trust|association|society|foundation|federation|union|institute|limited|ltd|inc|"
                         r"incorporated|group|company|club|centre|center|network|alliance|forum|agency|office)\b", re.I)
#: a place a body's name ends in, after an `and` (`… Australia and New Zealand`)
GEO = frozenset({"nz", "new zealand", "aotearoa", "australia", "the pacific", "pacific", "oceania", "australasia"})
#: a Māori body's name that begins as a person's might (`Te Puni Kōkiri`, `Te Ao Māori News`): the second word says so
TE_BODY = frozenset("""ao puni arawhiti papa whatu mana ara tari whare kura wānanga wananga rūnanga runanga hiringa pūkenga pukenga
aka matatini matawai kāhui kahui waka reo taura rau rōpū ropu kaunihera manatū manatu tāhuhu tahuhu pou hau tūāpapa tuapapa
mātāwaka matawaka waihanga""".split())
#: the Crown's own bodies: a name that begins so, or initials of these
CROWN_LEAD = re.compile(r"^(?:the\s+)?(?:ministry|department|office\s+(?:of|for)|te\s+puni\s+kōkiri|te\s+puni\s+kokiri|te\s+arawhiti|"
                        r"te\s+whatu\s+ora|te\s+tāhuhu|te\s+tahuhu|manatū|manatu|inland\s+revenue|treasury|the\s+treasury|"
                        r"crown\s+law|parliamentary\s+counsel|public\s+service\s+commission|state\s+services\s+commission|"
                        r"cabinet\b|new\s+zealand\s+defence\s+force|nz\s+defence\s+force|nz\s+police|new\s+zealand\s+police|(?:nz|new\s+zealand)\s+trade\s+(?:and|&)\s+"
                        r"enterprise)", re.I)
CROWN_INITIALS = frozenset("""mbie mpi msd mod mfat dpmc dia doc linz nzte tpk moh moe mfe mot moj ird pmo nzdf mch ero ot oag
psc ssc va aog nzta waka gcsb nzsis nzcs acc mhud hud kāinga kainga ola pco cpo cabinet cbc dev swc aph eci erd gov env pol fpd sou
leg crc nsc ehc tra cgc trc mpp mfat mbie""".split())


def fold(s: str) -> str:
    """The scans' name fold (products/scan/plan.fold_sql), here in Python."""
    s = (s or "").lower().translate(str.maketrans("āēīōū", "aeiou"))
    s = re.sub(r"\b(?:limited|ltd|incorporated|inc|tapui)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def core(s: str) -> str:
    """The name with titles and post-nominals off."""
    s = " ".join(s.split())
    t = TITLE.sub("", s)
    t = POST.sub("", t).strip(" ,")
    return t or s


def _titled(s: str) -> bool:
    return bool(TITLE.match(" ".join(s.split())))


def _words(s: str) -> list:
    return [w for w in re.split(r"[\s/]+", s.strip()) if w]


def _bare(w: str) -> str:
    return N.fold_diacritics(w).strip(".,;:'\"’()[]").lower()


def _low(s: str) -> list:
    return [x for x in (_bare(w) for w in _words(s)) if x]


def outside_brackets(s: str) -> str:
    return " ".join(re.sub(r"\([^()]*\)|\[[^\[\]]*\]", " ", s).split())


def bracket(s: str):
    m = re.search(r"\(([^()]*)\)\s*$", s)
    return m.group(1).strip() if m else None


def _of_tail(w: list) -> int:
    """Where a body's name starts after leading group words and `of`/`from` (`Representatives of Fonterra`): its index,
    or 0."""
    i = 0
    while i < len(w) and w[i] in GROUP_WORDS | GROUP_LEAD:
        i += 1
    return i + 1 if 0 < i < len(w) - 1 and w[i] in ("of", "from") else 0


def is_group(s: str) -> bool:
    w = _low(core(outside_brackets(s)))
    if not w:
        return False
    return (w[-1] in GROUP_WORDS or w[0] in GROUP_LEAD or all(x in GENERIC or x in GROUP_WORDS for x in w)
            or all(x in PORTFOLIO or x in GENERIC for x in w) or all(x in PLACES for x in w) or bool(_of_tail(w)))


def is_role(s: str) -> bool:
    """A role with no name: every word before any `of`/`at`/`for` a role's word (`CEO`, `Chief Executive`,
    `Secretary of Defence`, `Acting Chair`)."""
    head = re.split(r"\s+(?:of|at|for|to)\s+|\s*,\s*", outside_brackets(s), maxsplit=1)[0]
    w = _low(head)
    return bool(w) and all(x in ROLE_WORDS for x in w)


def is_crown(s: str) -> bool:
    c = outside_brackets(s).strip()
    w = _low(c)
    return bool(CROWN_LEAD.match(c)) or (bool(w) and all(x in CROWN_INITIALS for x in w))


def is_person(s: str) -> bool:
    """A person's name, as printed: two to four words, none a body's, group's or role's word, the first a given
    name the director register knows; or a title and one to three such words."""
    raw = outside_brackets(s)
    c = core(raw)
    w = _words(c)
    if not w or BODY.search(c) or N.ORG_WORDS.search(c) or any(ch.isdigit() for ch in c):
        return False
    low = [_bare(x) for x in w]
    if any(x in GROUP_WORDS or x in ROLE_WORDS or x in GROUP_LEAD for x in low):
        return False
    if len(low) > 1 and low[0] == "te" and low[1] in TE_BODY:
        return False
    if not all(x[:1].isupper() or _bare(x) in ("de", "van", "von", "der", "le", "la", "du", "o", "ter", "den") for x in w):
        return False
    if _titled(raw) and c != raw.strip() and 1 <= len(w) <= 3:
        return True
    return 2 <= len(w) <= 4 and low[0] in N.given_names()


def is_surname(s: str) -> bool:
    """One capitalised word that is no body's, group's, role's or portfolio's, and no initials."""
    w = _words(s.strip())
    if len(w) != 1 or not w[0][:1].isupper() or w[0].isupper() or any(ch.isdigit() for ch in w[0]):
        return False
    x = _bare(w[0])
    return bool(x) and not (BODY.search(w[0]) or N.ORG_WORDS.search(w[0]) or x in GROUP_WORDS or x in ROLE_WORDS
                            or x in GENERIC or x in PORTFOLIO or x in GROUP_LEAD)


def _body_name(s: str) -> bool:
    s = s.strip()
    return bool(s) and (bool(BODY.search(s)) or N.is_organisation(s)) and not is_group(s) and not is_role(s)


def _named_body(s: str) -> bool:
    """A body's name, or initials (`NZCA`), and no group's, role's, portfolio's or place's words alone."""
    s = s.strip()
    w = _words(s)
    if not w or is_group(s) or is_role(s) or is_person(s):
        return False
    return _body_name(s) or (len(w) == 1 and w[0].isupper() and len(w[0]) >= 2)


def role_organisation(s: str):
    """A role's body: `CEO of Kaikoura District Council` → the council, where what follows `of`, `at` or `for` is a
    body's name; `Ministry of Transport CEO` → the ministry; `Chair NZCA` → NZCA; `Corporate Affairs General
    Manager` → none."""
    c = outside_brackets(s)
    m = re.search(r"\s(?:of|at|for)\s+(.+)$", c)
    if m and _named_body(m.group(1)):
        return m.group(1).strip()
    w = _words(c)
    i = len(w)
    while i and _bare(w[i - 1]) in ROLE_WORDS:
        i -= 1
    if 0 < i < len(w) and _named_body(" ".join(w[:i])):
        return " ".join(w[:i])
    j = 0
    while j < len(w) and _bare(w[j]) in ROLE_WORDS:
        j += 1
    if 0 < j < len(w) and _named_body(" ".join(w[j:])):
        return " ".join(w[j:])
    return None


def _ends_in_role(part: str) -> bool:
    w = _low(outside_brackets(part))
    return bool(w) and (w[-1] in ROLE_WORDS or w[0] in ROLE_WORDS)


def organisation_of_part(part: str):
    """The organisation one piece names: a role's body, a bare role none, a group's body, else the piece itself."""
    part = part.strip()
    if not part or WITHHELD.search(part) or is_person(part):
        return None
    if is_group(part):
        return group_organisation(part)
    if is_role(part) or _ends_in_role(part):
        return role_organisation(part)
    return outside_brackets(part) or None


def group_organisation(s: str):
    """`Fonterra staff`, `Representatives of Fonterra` → Fonterra; `MBIE Officials`, `Health Officials`, `Cabinet
    Committee Members`, `Hon Stanford staff` → none (the Crown's own group, a person's, or no body's name)."""
    if _titled(s):
        return None
    w = _words(core(outside_brackets(s)))
    k = _of_tail([_bare(x) for x in w])
    if k:
        w = w[k:]
    while w and _bare(w[0]) in GROUP_LEAD:
        w = w[1:]
    if any(_bare(x) in CROWN_GROUP for x in w):
        return None
    while w and (_bare(w[-1]) in GROUP_WORDS or _bare(w[-1]) in ROLE_WORDS):
        w = w[:-1]
    while w and _bare(w[-1]) in ("and", "&", "of", "for", "the", "from"):
        w = w[:-1]
    if not w or all(_bare(x) in GENERIC | GROUP_WORDS | ROLE_WORDS | PORTFOLIO | PLACES for x in w):
        return None
    head = " ".join(w)
    if is_crown(head) or is_person(head) or is_given(head):
        return None
    return head


def kind_of(s: str) -> str:
    if WITHHELD.search(s):
        return "withheld"
    if is_person(s.split(",")[0]):
        return "person"
    if is_crown(s):
        return "crown"
    if is_group(s):
        return "group"
    if is_role(s):
        return "role"
    return "organisation"


def _pieces(text: str):
    """[[sep_before, piece]] and the trailing separator, splitting at separators outside brackets and outside the
    names in KEEP; or a reason."""
    depth, spans = 0, []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
            if depth < 0:
                return None, "", "a closing bracket with none open"
        spans.append(depth)
    if depth:
        return None, "", "a bracket left open"
    for m in KEEP.finditer(text):
        for i in range(m.start(), m.end()):
            spans[i] += 1
    out, last, sep = [], 0, ""
    for m in SEP.finditer(text):
        if m.start() == m.end() or spans[m.start()]:
            continue
        out.append([sep, text[last:m.start()]])
        sep, last = m.group(0), m.end()
    out.append([sep, text[last:]])
    trailing = ""
    while out and not out[-1][1].strip():          # a separator left at the end
        trailing = out[-1][0] + out[-1][1] + trailing
        out.pop()
    while len(out) > 1 and not out[0][1].strip():  # one at the start
        lead = out[0][0] + out[0][1]
        out.pop(0)
        out[0][0] = lead + out[0][0]
    merged = []
    for sep_b, p in out:                           # an empty piece between two separators joins the separators
        if merged and not p.strip():
            merged[-1][2] += sep_b + p
            continue
        if merged and merged[-1][2]:
            sep_b = merged[-1][2] + sep_b
            merged[-1][2] = ""
        merged.append([sep_b, p, ""])
    return [[a, b] for a, b, _ in merged], trailing, ""


def _keep_soft(head: str, sep: str, tail: str, after_titled: bool = False) -> bool:
    """Whether a separator with no comma sits inside one body's name. After a titled name in the same text (`Hons
    Willis, Stanford & Upston`) it never does: the list is of people."""
    hw, tw = _words(head), _words(tail)
    if not hw or not tw or after_titled or _titled(head) or _titled(tail):
        return False
    tl = [_bare(x) for x in tw]
    if " ".join(tl) in GEO:                         # `Chartered Accountants Australia and NZ`
        return True
    if AMP.match(sep) and len(hw) == 1 and tw[0][:1].isupper() \
            and _bare(hw[0]) not in GROUP_WORDS | ROLE_WORDS | GENERIC | PORTFOLIO \
            and not (tl[0] in GROUP_WORDS | ROLE_WORDS | GENERIC | GROUP_LEAD) and not is_person(tail) \
            and not is_given(head) and not is_given(tail):
        return True
    if len(tw) >= 2 and (BODY.search(tw[-1]) or tl[-1] in GROUP_WORDS) and tl[0] not in GROUP_LEAD | ROLE_WORDS \
            and len(hw) >= 2 and not is_person(head) and not is_group(head) and not is_role(head) \
            and not is_crown(head) and not STRONG_BODY.search(hw[-1]) \
            and not re.match(r"(?i)(?:the|ministry|department|office|minister|hon|dr)\b", tw[0]):
        return True
    return False


def is_given(s: str) -> bool:
    """One capitalised word that is a given name the director register knows (`Polly and Grant, More FM`)."""
    w = _words(s.strip())
    return len(w) == 1 and w[0][:1].isupper() and not w[0].isupper() and _bare(w[0]) in N.given_names() \
        and not BODY.search(w[0]) and not N.ORG_WORDS.search(w[0])


def split(text):
    """The attendees of one entry, as rows; or ([], why not)."""
    if text is None or not text.strip():
        return [], ""
    if WITHHELD.search(text):
        lead = text[:len(text) - len(text.lstrip())]
        r = _row(1, lead, text.strip(), text[len(text.rstrip()):])
        del r["titled"]
        return [r], ""
    pieces, trailing, why = _pieces(text)
    if why:
        return [], why
    i = 1                                           # an `and`/`&`/`+` inside a body's name
    while i < len(pieces):
        sep, p = pieces[i]
        after_titled = any(_titled(q) for _, q in pieces[:i - 1])
        if SOFT.match(sep) and _keep_soft(pieces[i - 1][1], sep, p, after_titled):
            pieces[i - 1][1] += sep + p
            pieces.pop(i)
            continue
        i += 1
    rows, i = [], 0
    while i < len(pieces):
        sep, p = pieces[i]
        attendee, org, kind = p, None, None
        if rows and (rows[-1]["kind"] == "person" and rows[-1]["titled"] or _bare(rows[-1]["attendee"]) in ("pm", "dpm")) \
                and is_surname(p):
            kind = "person"                         # `Hons Willis, Bishop`: a surname after a titled person
        elif is_given(p):
            kind = "person"                         # a given name alone
        elif is_person(p) and not WITHHELD.search(p):
            b = bracket(p)
            if b is not None:
                parts = [x for x in (y.strip() for y in b.split(",")) if x]
                orgs = [o for o in (organisation_of_part(x) for x in parts) if o]
                org = orgs[-1] if orgs else None
            j, taken = i + 1, []
            while j < len(pieces) and len(taken) < 2 and pieces[j][0].strip() == ",":
                nxt = pieces[j][1]
                if is_person(nxt) or is_group(nxt) or WITHHELD.search(nxt) or _titled(nxt) or is_surname(nxt):
                    break
                taken.append(pieces[j])
                j += 1
            if taken:
                attendee = p + "".join(s + q for s, q in taken)
                orgs = [o for o in (organisation_of_part(q) for _, q in taken) if o]
                org = orgs[-1] if orgs else org
                i = j - 1
            kind = "person"
        rows.append(_row(len(rows) + 1, sep, attendee, "", org, kind,
                         titled=_titled(p) or bool(kind == "person" and rows and is_surname(p)
                                                   and (rows[-1]["titled"] or _bare(rows[-1]["attendee"]) in ("pm", "dpm")))))
        i += 1
    if rows:
        rows[-1]["sep_after"] = trailing
    if not reconciles(text, rows):
        return [], "the attendees joined again are not the text"
    for r in rows:
        del r["titled"]
    return rows, ""


def _row(pos: int, sep_before: str, attendee: str, sep_after: str = "", org=None, kind=None, titled=False) -> dict:
    k = kind or kind_of(attendee)
    if k == "group":
        org = group_organisation(attendee)
    elif k == "role":
        org = role_organisation(attendee)
    elif k in ("organisation", "crown"):
        org = outside_brackets(attendee) or attendee
    elif k == "withheld":
        org = None
    org = org.strip(" ,;") if org else None
    org = org if org and len(fold(org)) >= 2 else None
    return {"position": pos, "attendee": attendee, "sep_before": sep_before, "sep_after": sep_after, "kind": k,
            "folded": fold(core(attendee)), "organisation": org, "crown": k == "crown" or bool(org and is_crown(org)),
            "titled": titled}


def joined(rows: list) -> str:
    return "".join(r["sep_before"] + r["attendee"] + r["sep_after"] for r in rows)


def reconciles(text: str, rows: list) -> bool:
    """The parts joined in order are the text once folded (they are the text exactly, by construction)."""
    return fold(joined(rows)) == fold(text)
