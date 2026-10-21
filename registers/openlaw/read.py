"""The lane's reading (plan 5.4 item 1): one page of OpenLaw NZ's `cases`
list, as the capture landed it, into one row per case, one row per party
and role, the citation graph and the statute links. No model reads anything:
the interface has parsed the judgments already, and the caption grammar is a
fallback for a record whose party table is empty.

Profiles before readers: the reading runs from the profile
`openlaw-graphql-cases-page` (`profile()`: the ledger in support.profiles,
else this lane's `profile-proposed.jsonl` until the integrator appends it),
recognises a page by its shape, and stamps every row with the profile's
slug and version.

A court's suppression order binds every surface (plan 5.4; hard limit 16).
A case is `suppressed` when its text or its title carries a suppression or
anonymisation marker (`MARKS`), or one of its parties is anonymised. Then
every party's name but the Crown's is `withheld`, and the case's title with
them; the rows, roles and the case stay. Names and titles go to the private
twin, never to a table the session reader sees. An anonymised party ("W",
"Mr X") is kept as the court wrote it and never expanded. No address is
read. Counsel are not asked for. Every function here is pure.
"""
import datetime as dt
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE, PROFILE_VERSION = "openlaw-graphql-cases-page", 1
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
READER = "registers.openlaw.read"
#: the keys every record of a page carries (the lane's query asks for them; null allowed)
ASKED = ("id", "caseName", "caseDate", "courtFilingNumber", "location", "court", "pdf", "caseCitations",
         "casesCitedsByCaseOrigin", "legislationToCases", "experimentalPartyAndRepresentatives")
MAX_RECORDS = 10

NEUTRAL = re.compile(r"^\[(\d{4})\]\s*(NZ[A-Z][A-Za-z]*)\s+(\d{1,6})$")
#: the text's own suppression markers, by name; case-insensitive, the whole text. A false hit withholds more, never less
MARKS = (
    ("order-prohibiting-publication", r"ORDER\s+PROHIBITING\s+PUBLICATION"),
    ("suppressing-the-name", r"SUPPRESS(?:ING|ION\s+OF)\s+(?:THE\s+)?(?:NAMES?|IDENTIT)"),
    ("name-suppression", r"NAME\s+SUPPRESS"),
    ("suppression-order", r"SUPPRESSION\s+ORDERS?"),
    ("publication-prohibited", r"PUBLICATION\s+OF\s+(?:THE\s+)?(?:NAMES?|IDENTIT\w*|IDENTIFYING)[^.]{0,160}?PROHIBIT"),
    ("identifying-particulars", r"IDENTIFYING\s+PARTICULARS"),
    ("family-courts-11b", r"S{1,2}\s*11B"),
    ("care-of-children-139", r"(?:S|SECTION)\s*139\s+OF\s+THE\s+CARE\s+OF\s+CHILDREN"),
    ("oranga-tamariki-438", r"(?:S|SECTION)\s*438\s+OF\s+THE\s+ORANGA\s+TAMARIKI"),
    ("criminal-procedure-200-to-211", r"(?:S|SS|SECTIONS?)\s*(?:20\d|21[01])\b[^.]{0,60}CRIMINAL\s+PROCEDURE\s+ACT"),
)
_MARKS = tuple((n, re.compile(p, re.I)) for n, p in MARKS)
#: a title's own markers
TITLE_MARKS = (("title-suppressed", re.compile(r"SUPPRESS|\[NAME|WITHHELD|ANONYMI", re.I)),)
#: a party rendered as an initial or two, "X (SC 60/2023)", or "Mr X": the court's anonymisation, never expanded
ANON = (re.compile(r"^[A-Z](?:\.?\s?[A-Z]){0,1}\.?(?:\s*\([A-Z0-9 /\-]+\))?$"),
        re.compile(r"^(?:MR|MS|MRS|MISS|DR)\.?\s+[A-Z]\.?$|SUPPRESSED|\[NAME|WITHHELD", re.I))
#: the Crown and public prosecutors: not a person, shown even in a suppressed case
CROWN = {"R", "REGINA", "REX", "THE QUEEN", "THE KING", "HER MAJESTY THE QUEEN", "HIS MAJESTY THE KING", "CROWN",
         "THE CROWN", "POLICE", "NEW ZEALAND POLICE", "NZ POLICE", "ATTORNEY-GENERAL", "ATTORNEY GENERAL",
         "THE ATTORNEY-GENERAL", "SOLICITOR-GENERAL", "SOLICITOR GENERAL", "THE SOLICITOR-GENERAL",
         "ACCIDENT COMPENSATION CORPORATION", "ACC"}
PARTY_TYPES = {"APPLICANT", "PLAINTIFF", "APPELLANT", "RESPONDENT", "DEFENDANT"}

# the caption grammar (ideas from the old courts_register/parse.py; not its code)
_REGISTRY = re.compile(r"^\s*([A-ZĀĒĪŌŪ'\- ]{3,40}?)\s+REGISTRY\s*$", re.M)
_ROLE = re.compile(r"^(?:(?:First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth)\s+)?(?:Intended\s+)?"
                   r"(Appellants?|Respondents?|Applicants?|Plaintiffs?|Defendants?|Interveners?|Intervenors?|"
                   r"Interested\s+Part(?:y|ies))(?:\s*\([^)]{1,40}\))?$", re.I)
_STOPS = ("Hearing:", "Court:", "Counsel:", "Judgment:", "Solicitors:", "Appearances:", "Sentence:", "Coram:")
HEAD = 20000


class Unrecognised(ValueError):
    """The document is not a page this profile describes."""


def profile(path: str = None) -> dict:
    """The profile the reading runs from, at the version stamped on its rows:
    the ledger's, else the lane's proposed line. No profile, no reading."""
    from support import profiles
    p = profiles.profile(PROFILE, path) if path else profiles.profile(PROFILE)
    if p is None or int(p.get("version") or 0) < PROFILE_VERSION:
        p = profiles.profile(PROFILE, PROPOSED)
    if p is None or int(p["version"]) != PROFILE_VERSION:
        raise LookupError(f"openlaw: no profile {PROFILE} v{PROFILE_VERSION}; a reading is made from a profile")
    return p


def recognise(body: bytes):
    """(records, '') for a page of the profile's shape, by shape alone; else
    (None, why)."""
    try:
        j = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None, "not JSON"
    if not isinstance(j, dict):
        return None, "not a JSON object"
    if j.get("errors"):
        return None, "the interface answered with errors"
    cases = (j.get("data") or {}).get("cases") if isinstance(j.get("data"), dict) else None
    if not isinstance(cases, list):
        return None, "no data.cases list"
    if len(cases) > MAX_RECORDS:
        return None, f"{len(cases)} records: more than the profile's page of {MAX_RECORDS}"
    return cases, ""


def parse_page(body: bytes) -> list:
    cases, why = recognise(body)
    if cases is None:
        raise Unrecognised(why)
    return cases


def text(v):
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip()
    return s or None


def day(v):
    """A Date as filed, `YYYY-MM-DD…` → ISO day; anything else None."""
    s = text(v)
    if not s or not re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        return None


def neutral(citations) -> tuple:
    """(the neutral citation, every citation as written). The first one of
    the shape [YYYY] NZXX N, normalised to single spaces."""
    written = [text(c.get("citation")) for c in citations or () if isinstance(c, dict) and text(c.get("citation"))]
    for c in written:
        m = NEUTRAL.match(c)
        if m:
            return f"[{m.group(1)}] {m.group(2)} {m.group(3)}", written
    return None, written


def marks(case_text, title) -> list:
    """The names of the suppression markers found; never the text around them."""
    out = [n for n, rx in _MARKS if case_text and rx.search(case_text)]
    out += [n for n, rx in TITLE_MARKS if title and rx.search(title)]
    return out


def norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[.,;:]+$", "", (s or "").strip())).upper()


def is_crown(name: str) -> bool:
    return norm_name(name) in CROWN


def is_anonymised(name: str) -> bool:
    n = text(name) or ""
    return not is_crown(n) and any(rx.search(n) for rx in ANON)


def registry_of(location, case_text):
    loc = text(location)
    if loc:
        return re.sub(r"\s+REGISTRY$", "", loc, flags=re.I).strip().upper() or None
    m = _REGISTRY.search((case_text or "")[:HEAD])
    return m.group(1).strip() if m else None


def _upper_ratio(s: str) -> float:
    letters = [c for c in s if c.isalpha()]
    return sum(c.isupper() for c in letters) / len(letters) if letters else 0.0


def _name_line(ln: str) -> bool:
    return 1 < len(ln) <= 90 and _upper_ratio(ln) >= 0.6 and not re.search(r"\[\d{4}\]|^(?:CIV|CRI|CA|SC)[\s-]?\d", ln)


def caption_parties(case_text) -> list:
    """[(name, role)] from the caption: BETWEEN/AND blocks of capital lines
    closed by a role line; else the criminal `R v NAME` block. Only the head
    of the text, only before the first stop label after the block starts."""
    head = (case_text or "")[:HEAD]
    start = head.find("BETWEEN")
    if start == -1:
        start = head.find("IN THE MATTER OF")
    out = []
    if start != -1:
        end = min([i for i in (head.find(s, start) for s in _STOPS) if i != -1] or [len(head)])
        pending, collecting = [], False
        for raw in head[start:end].splitlines():
            ln = raw.strip()
            if not ln:
                continue
            if ln in ("BETWEEN", "AND", "IN THE MATTER OF"):
                collecting = True
                continue
            if not collecting:
                continue
            if _ROLE.match(ln):
                out += [(n, ln) for n in pending]
                pending = []
            elif _name_line(ln):
                pending.append(ln)
        if out:
            return out
    lines = [ln.strip() for ln in head.splitlines() if ln.strip()]
    for i, ln in enumerate(lines[:200]):
        if ln in ("v", "V") and 0 < i < len(lines) - 1:
            before, after = lines[i - 1], lines[i + 1]
            if is_crown(before) and _name_line(after) and not any(after.startswith(s) for s in _STOPS):
                return [(before, "Prosecutor"), (after, "Defendant")]
            break
    return []


def cite(sha: str, place: str, prof: dict) -> dict:
    return {"document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER,
            "profile": prof["slug"], "profile_version": int(prof["version"])}


def read_case(rec, sha: str, i: int, prof: dict):
    """(rows, '') for one record: {'case', 'title', 'parties', 'names',
    'citations', 'statutes', 'asides'}; or (None, why) for a record this
    reading cannot take."""
    if not isinstance(rec, dict):
        return None, "not an object"
    missing = [k for k in ASKED if k not in rec]
    if missing:
        return None, f"the record lacks {', '.join(missing[:4])}: not the profile's query"
    cid = rec.get("id")
    if not isinstance(cid, str) or not cid.strip():
        return None, "no id"
    cid = cid.strip()
    place = f"data.cases[{i}]"
    c = cite(sha, place, prof)
    title = text(rec.get("caseName"))
    body = rec.get("caseText") if isinstance(rec.get("caseText"), str) else ""
    citation, written = neutral(rec.get("caseCitations"))
    court = rec.get("court") if isinstance(rec.get("court"), dict) else {}
    acr = court.get("acronyms") if isinstance(court.get("acronyms"), list) else []
    pdf = rec.get("pdf") if isinstance(rec.get("pdf"), dict) else {}

    named, src = [], "none"
    for blk in rec.get("experimentalPartyAndRepresentatives") or ():
        if not isinstance(blk, dict):
            continue
        role = text(blk.get("partyType")) or "UNSTATED"
        for n in blk.get("names") or ():
            if text(n):
                named.append((text(n), role))
    if named:
        src = "interface"
    else:
        named = caption_parties(body)
        src = "caption" if named else "none"
    found = marks(body, title)
    if any(is_anonymised(n) for n, _ in named):
        found.append("anonymised-party")
    suppressed = bool(found)

    parties, names = [], []
    for pos, (n, role) in enumerate(named, 1):
        key = f"{cid}|{role}|{pos}"
        crown = is_crown(n)
        parties.append({"key": key, "case_key": cid, "role": role, "position": pos, "anonymised": is_anonymised(n),
                        "crown": crown, "withheld": suppressed and not crown, "from_source": src, **c})
        names.append({"key": key, "name": n})

    citations, statutes, asides, seen = [], [], [], set()
    for j, e in enumerate(rec.get("casesCitedsByCaseOrigin") or ()):
        cited = text(e.get("caseCited")) if isinstance(e, dict) else None
        if not cited:
            asides.append({"document": sha, "place": f"{place}.casesCitedsByCaseOrigin[{j}]", "stage": "read",
                           "reason": "a citation with no cited case"})
            continue
        key = f"{cid}|{cited}"
        if key in seen:
            asides.append({"document": sha, "place": f"{place}.casesCitedsByCaseOrigin[{j}]", "stage": "read",
                           "reason": "the same cited case twice in one record"})
            continue
        seen.add(key)
        citations.append({"key": key, "citing_key": cid, "cited_key": cited, "citation_count": e.get("citationCount"),
                          **cite(sha, f"{place}.casesCitedsByCaseOrigin[{j}]", prof)})
    seen = set()
    for j, e in enumerate(rec.get("legislationToCases") or ()):
        lid = text(e.get("legislationId")) if isinstance(e, dict) else None
        sec = text(e.get("section")) if isinstance(e, dict) else None
        if not lid or sec is None:
            asides.append({"document": sha, "place": f"{place}.legislationToCases[{j}]", "stage": "read",
                           "reason": "a statute link with no legislation or no section"})
            continue
        key = f"{cid}|{lid}|{sec}"
        if key in seen:
            asides.append({"document": sha, "place": f"{place}.legislationToCases[{j}]", "stage": "read",
                           "reason": "the same statute and section twice in one record"})
            continue
        seen.add(key)
        leg = e.get("legislation") if isinstance(e.get("legislation"), dict) else {}
        statutes.append({"key": key, "case_key": cid, "legislation_id": lid, "legislation_title": text(leg.get("title")),
                         "legislation_year": text(leg.get("year")), "section": sec, "mentions": e.get("count"),
                         "extraction_confidence": e.get("extractionConfidence"),
                         **cite(sha, f"{place}.legislationToCases[{j}]", prof)})

    case = {"key": cid, "openlaw_id": cid, "citation": citation, "citations": written,
            "court": text(acr[0]) if acr else text(court.get("id")) or text(rec.get("courtId")),
            "court_name": text(court.get("name")), "registry": registry_of(rec.get("location"), body),
            "filing_number": text(rec.get("courtFilingNumber")), "decided_on": day(rec.get("caseDate")),
            "pdf_url": text(pdf.get("pdfUrl")), "suppressed": suppressed, "suppression_marks": found,
            "parties_from": src, "is_valid": rec.get("isValid"), "source_modified_at": day(rec.get("lastModified")),
            "parsers_version": text(rec.get("parsersVersion")), **c}
    return {"case": case, "title": {"key": cid, "title": title} if title else None, "parties": parties,
            "names": names, "citations": citations, "statutes": statutes, "asides": asides}, ""


def read_pages(docs, read_bytes, prof: dict, only: set = None):
    """Every record of the listed pages, NEWEST LANDED FIRST: `docs` is
    oldest first; a case read again from an older page is superseded.
    Yields ('page', sha, n) once per page, then ('case', sha, rows),
    ('aside', sha, line) or ('superseded', sha, id) per record. `only`: the
    case ids to read (the sample's); None for all."""
    seen = set()
    for sha in reversed(list(docs)):
        try:
            recs = parse_page(read_bytes(sha))
        except Unrecognised as exc:
            yield "page", sha, 0
            yield "aside", sha, {"document": sha, "place": "", "stage": "recognise", "reason": str(exc)}
            continue
        yield "page", sha, len(recs)
        for i, rec in enumerate(recs):
            cid = rec.get("id").strip() if isinstance(rec, dict) and isinstance(rec.get("id"), str) else None
            if only is not None and cid not in only:
                yield "skip", sha, cid
                continue
            if cid and cid in seen:
                yield "superseded", sha, cid
                continue
            rows, why = read_case(rec, sha, i, prof)
            if rows is None:
                yield "aside", sha, {"document": sha, "place": f"data.cases[{i}]", "stage": "read", "reason": why}
                continue
            seen.add(cid)
            yield "case", sha, rows
