"""The reading of the `parliament-diaries` records (profile `mcp-diary-entry`, v1).

A document is one record of the ingest MCP's `parliament-diaries` corpus as
support/mcpsource landed it: the record's JSON, keys sorted, without its
`seq`. Each record is one meeting or event of a minister's monthly diary
release (a Beehive proactive release, a PDF), which Arthur's provider read
from the PDF on its own box, outside the estate (ruling 78). The reading
takes the provider's fields as served: no model, no inference, nothing
fetched, nothing looked up. Where the MCP has served a record more than
once with different bytes, the entry is read from the version the pull saw
last (`items` come in the order the pull landed them; never the highest
`seq`), and the others are kept in `files` as older versions.

    read(items, get_bytes)   items: [(sha256, seq or None, record id or None)] → Result

What the reading keeps, and what it holds back:

  - names as the release prints them (the minister, who attended), a public
    role at most beside a name, nothing resolved or linked (that is product
    (b), after links);
  - the release's own withholdings ("Withheld under s9(2)(f)(iv)", "Withheld
    under OIA") kept as released, and each entry's withheld fields counted;
  - the location only where the release gives it as a place of business: a
    location that names a home (a residence, "home", a private address) or a
    street address with no place of business named is held back
    (`location_held` says why; the value as released goes to the private
    table); a street address in the meeting or attendees is masked the same
    way (hard limit 15);
  - the provider's `text` (its own join of the fields) goes to the private
    table only.

The release (one per `source_url`) is the PDF: its minister, the month, the
PDF's address where the provider served one (most serve the Beehive's file
address; some serve a file name only, and then no address is made up), and
its entry count.
"""
import datetime as dt
import json
import re
import urllib.parse
from dataclasses import dataclass, field

READER = "registers.ministers_diaries.read"
PROFILE = "mcp-diary-entry"
PROFILE_VERSION = 1
SOURCE_NOTE = ("one meeting of a minister's monthly diary release (a Beehive proactive release), read from the "
               "release PDF by Arthur's provider off-estate and served by the query-nz ingest MCP (ruling 78); the "
               "estate never fetched the PDF")
PDF_HOST = "https://www.beehive.govt.nz/"
KNOWN = ("id", "rowid", "minister", "portfolio", "date", "year", "time", "meeting", "location", "attendees",
         "source_url", "_collected", "updated_at", "capture", "text")
CAPTURE = ("_collected", "source_url")
FIELDS = ("portfolio", "time", "meeting", "location", "attendees")      # where a withholding is looked for
MONTHS = ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october",
          "november", "december")

# A withholding the release prints in place of what it held back (Official Information Act 1982, ss 6, 9, 18)
WITHHELD = re.compile(r"\bwithheld\b|\bredacted\b|\b9\s*\)?\s*\(\s*2\s*\)\s*\(\s*[a-k]\s*\)|"
                      r"\b(?:s|section)\s*\.?\s*6\s*\(\s*[a-d]\s*\)", re.I)
# A location that names a home, whatever else it says
HOME = re.compile(r"\bhome\b|\bresidences?\b|\bhomestead\b|\bprivate\s+(?:address|property|dwelling)\b|"
                  r"[’']s\s+(?:house|place|property|farm)\b", re.I)
# A street address: a number, one to three capitalised words, a street word
STREET = re.compile(r"\b\d{1,5}[A-Za-z]?(?:\s*[-/]\s*\d{1,5}[A-Za-z]?)?,?\s+(?:[A-ZĀĒĪŌŪ][\w'’.-]*\s+){1,3}"
                    r"(?:Street|St|Road|Rd|Avenue|Ave|Terrace|Tce|Drive|Dr|Place|Pl|Crescent|Cres|Lane|Ln|Way|Grove|"
                    r"Quay|Highway|Hwy|Parade|Square|Sq|Esplanade|Rise|Close|Boulevard|Blvd|Mews|Court|Ct)\b\.?")
# A place of business named beside a street address (outside the address itself)
BUSINESS = re.compile(r"\b(?:Ltd|Limited|Inc|Incorporated|Council|Offices?|Buildings?|House|Centre|Center|School|"
                      r"College|Kura|Hotel|University|Hospital|Marae|Ministry|Department|Embassy|Commission|Club|Hall|"
                      r"Church|Station|Port|Airport|Library|Museum|Courts?|Tower|Plaza|Trust|Group|Parliament|Beehive|"
                      r"Wharf|Studios?|Restaurant|Cafe|Café|Bar|Theatre|Stadium|Park|Factory|Plant|Mill|Mine|Base|Camp|"
                      r"Police|Prison|Clinic|Society|Association|Institute|Foundation|Chambers|Board|Authority|Agency|"
                      r"Services?|Company|Lodge|Venue|Conference|Room|Suite|Level|Floor|Arena|Pavilion|Gallery|Hub|"
                      r"Campus|Academy|Polytechnic|Wānanga|Wananga|Terminal|Headquarters|HQ)\b")
HELD_HOME = "names a home"
HELD_STREET = "a street address with no place of business named"
MASK = "[street address held back]"


@dataclass
class Result:
    entries: list = field(default_factory=list)
    releases: list = field(default_factory=list)
    private: list = field(default_factory=list)        # (key, location, meeting, attendees, text) as served: private
    files: list = field(default_factory=list)          # (sha256, record id, seq, status)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def _stamp(sha: str, place: str, loaded_at: str) -> dict:
    return {"document": sha, "page": 1, "place": place, "read_from": "text", "reader": READER, "profile": PROFILE,
            "profile_version": PROFILE_VERSION, "loaded_at": loaded_at}


def _str(v):
    return v.strip() if isinstance(v, str) and v.strip() else None


def _iso_date(v):
    if not isinstance(v, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v.strip()):
        return None
    try:
        return dt.date.fromisoformat(v.strip()).isoformat()
    except ValueError:
        return None


def recognise(rec) -> str:
    """'' when the document is this profile's shape, else why not."""
    if not isinstance(rec, dict):
        return "not a JSON object"
    if not _str(str(rec.get("id")) if rec.get("id") is not None else None):
        return "no id"
    if not _str(rec.get("source_url")):
        return "no source_url: no release to place it in"
    if not _str(rec.get("minister")):
        return "no minister"
    for f in FIELDS + ("date", "year", "text"):
        if rec.get(f) is not None and not isinstance(rec[f], str):
            return f"`{f}` is not text"
    return ""


def unread(rec: dict) -> list:
    out = set(rec) - set(KNOWN)
    if isinstance(rec.get("capture"), dict):
        out |= {f"capture.{k}" for k in rec["capture"] if k not in CAPTURE}
    return sorted(out)


def withheld(rec: dict) -> list:
    """The fields in which the release prints a withholding, in field order."""
    return [f for f in FIELDS if WITHHELD.search(rec.get(f) or "")]


def place_of_business(location):
    """(location to publish, why it is held back or None). A withholding is
    the release's own and is kept."""
    loc = _str(location)
    if loc is None:
        return None, None
    if WITHHELD.search(loc):
        return loc, None
    if HOME.search(loc):
        return None, HELD_HOME
    if STREET.search(loc) and not BUSINESS.search(STREET.sub(" ", loc)):
        return None, HELD_STREET
    return loc, None


def mask_street(v):
    """(value with every street address masked, how many)."""
    s = _str(v)
    if s is None:
        return None, 0
    return STREET.subn(MASK, s)


def release_parts(source_url: str) -> dict:
    """The PDF's address (only where the provider served one on the Beehive's
    host), its file name, the site's upload folder (`YYYY-MM`) and the month
    the file name gives (`YYYY-MM`), each None where not given."""
    s = source_url.strip()
    url = s if s.startswith(PDF_HOST) else None
    name = urllib.parse.unquote(s.rsplit("/", 1)[-1])
    folder = re.search(r"/files/(\d{4}-\d{2})/", s) if url else None
    named = {f"{y}-{MONTHS.index(mo.lower()) + 1:02d}"
             for mo, y in re.findall(r"\b(" + "|".join(MONTHS) + r")[\s_.,-]*((?:19|20)\d{2})\b", name, re.I)}
    return {"pdf_url": url, "file_name": name, "upload_folder": folder.group(1) if folder else None,
            "month_named": named.pop() if len(named) == 1 else None}     # a span of months names no one month


def _bump(n: dict, k: str, by: int = 1) -> None:
    n[k] = n.get(k, 0) + by


def read_one(sha: str, rec: dict, seq, versions: int, out: Result, loaded_at: str) -> None:
    n = out.counts
    key = str(rec["id"]).strip()
    held_loc = rec.get("location")
    location, why = place_of_business(held_loc)
    meeting, m1 = mask_street(rec.get("meeting"))
    attendees, m2 = mask_street(rec.get("attendees"))
    w = withheld(rec)
    on = _iso_date(rec.get("date"))
    if why:
        _bump(n, f"locations held back: {why}")
    if m1 or m2:
        _bump(n, "entries with a street address masked in the meeting or attendees")
    if w:
        _bump(n, "entries with a withholding")
    if rec.get("date") is not None and on is None:
        _bump(n, "dates not ISO")
    year = _str(rec.get("year"))
    if on and year and year != on[:4]:
        _bump(n, "years that are not the date's")
    cap = rec.get("capture") if isinstance(rec.get("capture"), dict) else {}
    if cap.get("source_url") is not None and cap.get("source_url") != rec["source_url"]:
        _bump(n, "capture blocks naming another source_url")
    out.entries.append({
        "key": key, "release": rec["source_url"].strip(), "rowid": rec.get("rowid") if isinstance(rec.get("rowid"), int) else None,
        "minister": _str(rec.get("minister")), "portfolio": _str(rec.get("portfolio")), "entry_on": on,
        "date_as_released": _str(rec.get("date")), "year": year, "time": _str(rec.get("time")),
        "meeting": meeting, "attendees": attendees, "location": location, "location_held": why,
        "addresses_masked": m1 + m2, "withheld": w, "collected_at": _str(rec.get("_collected")) or _str(cap.get("_collected")),
        "updated_at": _str(rec.get("updated_at")),
        "text_words": len(rec["text"].split()) if isinstance(rec.get("text"), str) else 0,
        "fields_unread": unread(rec), "versions": versions, "seq": seq, "source_note": SOURCE_NOTE,
        **_stamp(sha, "record", loaded_at)})
    out.private.append((key, held_loc if isinstance(held_loc, str) else None,
                        rec.get("meeting") if m1 else None, rec.get("attendees") if m2 else None,
                        rec.get("text") if isinstance(rec.get("text"), str) else None))


def releases_of(entries: list, loaded_at: str) -> list:
    """One release per `source_url`: its minister (as the entries name them;
    more than one is counted, never chosen silently), portfolios in order of
    first appearance, the month, the PDF's address, and its entry count. It
    cites the document of its first entry (lowest rowid, then key)."""
    by = {}
    for e in entries:
        by.setdefault(e["release"], []).append(e)
    out = []
    for src, es in by.items():
        es = sorted(es, key=lambda e: (e["rowid"] is None, e["rowid"] or 0, e["key"]))
        ministers = list(dict.fromkeys(e["minister"] for e in es if e["minister"]))
        portfolios = list(dict.fromkeys(e["portfolio"] for e in es if e["portfolio"]))
        days = sorted(e["entry_on"] for e in es if e["entry_on"])
        months = sorted({d[:7] for d in days})
        parts = release_parts(src)
        out.append({
            "key": src, "source_url": src, **parts, "minister": ministers[0] if ministers else None,
            "ministers_named": len(ministers), "portfolios": portfolios,
            "entries_month": months[0] if len(months) == 1 else None, "months": len(months),
            "month": parts["month_named"] or (months[0] if len(months) == 1 else None),
            "first_on": days[0] if days else None, "last_on": days[-1] if days else None,
            "entries": len(es), "withheld_entries": sum(1 for e in es if e["withheld"]),
            "locations_held": sum(1 for e in es if e["location_held"]),
            "source_note": SOURCE_NOTE, **_stamp(es[0]["document"], f"release of {len(es)} entries; first entry {es[0]['key']}",
                                                 loaded_at)})
    return out


def read(items, get_bytes, loaded_at: str = None) -> Result:
    """Every document in `items` (in the order the pull saw them) read or set
    aside, then the releases built from the entries. A document's record id is
    its own `id`; where `items` names one too, the two must agree."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    newest, last, order, named = {}, {}, [], {}
    for pos, (sha, seq, rid) in enumerate(items):
        if sha not in newest:
            order.append(sha)
        newest[sha], last[sha] = seq, pos
        if rid is not None:
            named.setdefault(sha, set()).add(str(rid))
    by_record = {}
    for sha in order:
        try:
            rec = json.loads(get_bytes(sha))
        except (OSError, ValueError) as e:
            out.set_aside.append((sha, "open", f"{type(e).__name__}: {str(e)[:200]}"))
            out.files.append((sha, None, newest[sha], "set aside"))
            continue
        why = recognise(rec)
        if not why and named.get(sha) and named[sha] != {str(rec["id"]).strip()}:
            why = "the arrival names another record"
        if why:
            out.set_aside.append((sha, "recognise", why))
            out.files.append((sha, str(rec["id"]) if isinstance(rec, dict) and rec.get("id") is not None else None,
                              newest[sha], "set aside"))
            continue
        by_record.setdefault(str(rec["id"]).strip(), []).append((last[sha], sha, rec))
    for rid, versions in by_record.items():
        versions.sort(key=lambda v: v[0])           # the version the pull saw last is the record's current one
        _, sha, rec = versions[-1]
        read_one(sha, rec, newest[sha], len(versions), out, loaded_at)
        out.files.append((sha, rid, newest[sha], "read"))
        out.files += [(s, rid, newest[s], "older version") for _, s, _ in versions[:-1]]
    out.releases = releases_of(out.entries, loaded_at)
    out.counts.update({"documents": len(order), "entries": len(out.entries), "releases": len(out.releases),
                       "older versions": sum(len(v) - 1 for v in by_record.values()),
                       "ministers": len({e["minister"] for e in out.entries}),
                       "withheld fields": sum(len(e["withheld"]) for e in out.entries),
                       "set aside": len(out.set_aside)})
    return out
