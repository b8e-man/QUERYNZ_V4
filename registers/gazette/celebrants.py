"""The Registrar-General's celebrant lists (profile `gazette-celebrant-list`):
recognised, then read. No model.

The old estate's reader (`data-layer/gazette_register/celebrants.py`, card
C226) found the class and three record shapes. Measured again over this
export it misses a fourth and mis-reads a fifth:

  stops      `Surname, Given Names, Organisation.` and `Surname, Given Names.`
             run together, the stop swallowed: `…Adventist.Erika, Etuati…`
  address    the same, the third field a street address
             (`Surname, Given, 12 Some Street, Suburb, Town.`). Independent
             celebrants (Marriage Act s 10 and 11, the Civil Union Act) are
             listed so. The old reader took the street for a surname and minted
             a person; here the whole notice is in address mode and the address
             goes to the private schema only (hard limit 15)
  chain      `Surname, Given Surname, Given …` with no stops at all (most lists
             from 2019): each comma's chunk is one record's given names and the
             next record's surname. The split is the last word (with its
             particles), or the glue where the capture lost the space
             (`DonaldLologa`); the list is alphabetical, so a split that breaks
             the order is not taken
  marked     the combined annual list (from 2016): one chain of independent
             marriage and civil-union celebrants, each name preceded by its
             letters (`M`, `CU`, or both) under the printed key "CU = Civil
             Union Celebrant M = Independent Marriage Celebrant"; the letters
             cut every chunk exactly, and are kept as the row's `marks`
  table      `Name of Celebrant Name of Organisation` printed as a table, with
             nothing between the given names and the organisation: set aside
  none       a notice that names celebrants but prints no list (a correction, a
             one-line notice): typed, read as no records

The action is the notice's own operative words, read before the records:
appointment, removal, publication (the register published "for general
information", which is not an appointment event), annual list (both: the
year's list of everyone appointed for its period), and none where it says
a removal beside anything else, or nothing; a notice with no action gives no records, only a
catch-log line.

    recognise(title, text)  the reasons, empty if not this profile
    read(text)              Reading(action, statute, period, mode, records, unread)
"""
import re
from dataclasses import dataclass, field

SUBJECT = re.compile(r"celebrant", re.I)
SUBJECT_HEAD = 3000
TABLE_HEADER = re.compile(r"Name\s+of\s+Celebrant\s*Name\s+of\s+Organisation", re.I)
_FOLLOWING = re.compile(r"the following (?:names|persons|people|celebrants|person|name|marriage|civil)", re.I)
_HEADER = re.compile(r"\s*Surname,?\s*(?:First|Given)\s+Names?\s*", re.I)
_DATED = re.compile(r"\s*(?:Dated\s+(?:at|this)\b|Dated\s+\d)", re.I)

_APPOINTS = re.compile(r"have been appointed|are hereby appointed|is hereby appointed|has been appointed|"
                       r"appointed as (?:a )?(?:marriage|civil union) celebrants?", re.I)
_REMOVES = re.compile(r"will be removed from the list|have been removed from the list|has been removed from the list|"
                      r"names? (?:will|shall) be removed|removed from the list of|"
                      r"intend to remove the following", re.I)
_PUBLISHES = re.compile(r"published for general information|is published for general|"
                        r"this list of (?:marriage|civil union|independent|organisational).{0,40}is published", re.I)
_SECTION = re.compile(r"sections?\s+(\d+[A-Z]?(?:\s*(?:,|and)\s*\d+[A-Z]?)*)\s+of\s+the\s+"
                      r"(Marriage Act 1955|Civil Union Act 2004)", re.I)
_PERIOD = re.compile(r"for the period\s+(?:from\s+)?(?P<a>\d{1,2}\s+[A-Z][a-z]+\s+\d{4})"
                     r"(?:\s+(?:to|until)\s+(?P<b>\d{1,2}\s+[A-Z][a-z]+\s+\d{4}))?")

#: A surname: one to four capitalised words, the particles a New Zealand
#: surname carries, an apostrophe or a hyphen; never a digit or a lowercase word.
_PART = r"(?:van|von|de|den|der|du|le|la|ter|te|di|da|dos|del|ten|ah|bin|binti|al|el|o)"
_CAP = r"[A-Z’'À-ɏḀ-ỿ][\w’'\-À-ɏḀ-ỿ()]*"
SURNAME = re.compile(rf"^(?:{_PART}\s+){{0,3}}{_CAP}(?:[\s\-]+(?:{_PART}|{_CAP})){{0,3}}$")
GIVEN = re.compile(rf"^{_CAP}(?:\.?[\s\-]*(?:{_CAP}|{_PART}|\(\w[\w\s’'\-]*\)))*\.?$")
_GLUE = re.compile(r"(?<=[a-zà-ɏ)])(?=[’']?[A-ZÀ-ÞĀĒĪŌŪ])")
_PREFIXES = {"mc", "mac", "de", "di", "da", "du", "la", "le", "van", "von", "fitz", "te", "st", "del", "della", "des", "dos", "o"}
_STOP = re.compile(rf"\.(?=\s*(?:(?:{_PART}\s+)*[A-Z’'À-ɏ]|$))")
_INITIAL = re.compile(r"(?:^|[\s,])[A-Z]$")
_DIGIT = re.compile(r"\d")
_NOT_PLACE = re.compile(r"sections?\s+\d+[A-Z]?(?:\s*(?:,|and)\s*\d+[A-Z]?)*|\d{1,2}(?:st|nd|rd|th)?\s+(?:day\s+of\s+)?[A-Z][a-z]+,?\s+\d{4}|\b(?:19|20)\d{2}\b", re.I)
#: A list whose record ends with one of these is an address list.
_STREET = re.compile(r"\b(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Way|"
                     r"Grove|Close|Court|Ct|Parade|Highway|Rise|Heights|Square|Mews|PO Box|P\.O\. Box|RD|Private Bag)\b")

MIN_RECORDS = 3


def recognise(title: str, text: str) -> list:
    """The reasons this notice is a celebrant list; empty if it is not.
    The subject word is required in the title, the head or the printed
    column header (a bankruptcy list has a celebrant list's shape)."""
    why = []
    if SUBJECT.search(title or ""):
        why.append("title names celebrants")
    if SUBJECT.search((text or "")[:SUBJECT_HEAD]) and _SECTION.search((text or "")[:SUBJECT_HEAD]):
        why.append("head names celebrants under the Marriage or Civil Union Act")
    if TABLE_HEADER.search(text or ""):
        why.append("printed column header")
    return why


def action(text: str):
    """appointment | removal | publication | annual list | None (says none, or
    a removal beside anything else). An annual list says both that the
    persons "have been appointed" (for the year's period) and that the list
    "is published for general information": it names everyone holding the
    office at that date, and is neither a week's appointments nor silent."""
    app, rem, pub = bool(_APPOINTS.search(text)), bool(_REMOVES.search(text)), bool(_PUBLISHES.search(text))
    if app and pub and not rem:
        return "annual list"
    if rem and not app and not pub:
        return "removal"
    if app and not rem and not pub:
        return "appointment"
    if pub and not app and not rem:
        return "publication"
    return None


def statute(text: str):
    m = _SECTION.search(text or "")
    return f"{m.group(2)} s {re.sub(r'\s+', ' ', m.group(1))}" if m else None


def period(text: str) -> tuple:
    m = _PERIOD.search(text or "")
    return (m.group("a"), m.group("b")) if m else (None, None)


@dataclass
class Record:
    ordinal: int
    surname: str
    given_names: str
    organisation: str = None
    address: str = None           # private: never published
    split: str = "delimited"      # delimited | last word | glue
    marks: str = None             # a marked list's letters before the name: M (independent marriage), CU (civil union)


@dataclass
class Reading:
    action: str = None
    statute: str = None
    period_from: str = None
    period_to: str = None
    mode: str = "none"            # stops | address | chain | table | none
    records: list = field(default_factory=list)
    unread: list = field(default_factory=list)    # (place, why): a catch-log line each


def body(text: str):
    """The list: after the operative sentence, before the signature.
    (start, end) offsets, or None where the notice prints no list."""
    m = _FOLLOWING.search(text[:SUBJECT_HEAD])
    if not m:
        return None
    rest = text[m.end():m.end() + 500]
    col = rest.find(":")
    if col >= 0:
        start = m.end() + col + 1
    else:
        # "… removed from the list … as at 26 March 2024." and then the list
        stop = re.search(r"\d{4}\s*[.,:]|\.(?=\s|[A-Z’'])", rest)
        if not stop:
            return None
        start = m.end() + stop.end()
    h = _HEADER.match(text, start)
    start = h.end() if h else start
    d = _DATED.search(text, start)
    end = d.start() if d else len(text)
    return (start, end) if end > start else None


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip(" ,;")


def _is_address(extra: list) -> bool:
    """A record's fields after the given names are an address when one holds
    a number, or a street word with a town after it. A street word alone is
    not enough: Lane, Court, Way and Close are surnames, and The Way a church."""
    return any(_DIGIT.search(x) for x in extra) or (len(extra) >= 2 and any(_STREET.search(x) for x in extra))


def _located(seg: str) -> bool:
    """A number in the list that is not a section of the Act, a date or a year."""
    return bool(_DIGIT.search(_NOT_PLACE.sub(" ", seg)))


def _stops(seg: str) -> tuple:
    """[(surname, given, extra fields)], [why] for a stop-delimited list."""
    out, bad = [], []
    parts, buf = [], ""
    for piece in _STOP.split(seg):
        buf = f"{buf}.{piece}" if buf else piece
        # an initial ("Mary J.") or "St." ends no record
        if _INITIAL.search(buf.rstrip()) or re.search(r"\b(?:St|Mt|Ltd|Inc|Rev|Dr|P\.O|N\.Z)$", buf.rstrip()):
            continue
        parts.append(buf)
        buf = ""
    if buf.strip():
        parts.append(buf)
    for p in parts:
        p = _clean(p)
        if not p:
            continue
        f = [_clean(x) for x in p.split(",")]
        if len(f) < 2 or not SURNAME.match(f[0]) or not f[1] or not GIVEN.match(f[1]):
            bad.append(p)
            continue
        out.append((f[0], f[1], [x for x in f[2:] if x]))
    return out, bad


def glue_points(word: str) -> list:
    """Where a capture lost the space inside one word (`SusanAdamson`,
    `Sione’Akau’ola`, `(Maliu)’Uhila`), never at a name's own capital
    (`McDonald`, `DeVries`, `LeBlanc`)."""
    out, prev = [], 0
    for g in _GLUE.finditer(word):
        if word[prev:g.start()].lower().strip("’'") in _PREFIXES:
            continue
        out.append(g.start())
        prev = g.start()
    return out


def _split_chunk(chunk: str) -> list:
    """The ways one chain chunk splits into (given names, next surname).
    Where the last word holds a glue point the cut is there (the glue is
    always inside the last word: given names then the next surname); else
    the next surname is the last word, with its particles."""
    words = chunk.split()
    if not words:
        return []
    lw = words[-1]
    points = glue_points(lw)
    if points:
        cut = len(chunk) - len(lw) + points[-1]
        given, sur = chunk[:cut].strip(), chunk[cut:].strip()
        return [(given, sur, "glue")] if given and SURNAME.match(sur) and GIVEN.match(given) else []
    ways = []
    for k in range(1, min(4, len(words))):
        given, sur = " ".join(words[:-k]), " ".join(words[-k:])
        if k > 1 and not re.match(rf"^{_PART}\b", words[-k], re.I):
            continue                    # a longer surname only through a particle
        if SURNAME.match(sur) and GIVEN.match(given):
            ways.append((given, sur, "last word"))
    # a particle belongs to the surname (`Peter van Dijk`)
    longer = [w for w in ways if " " in w[1]]
    return [max(longer, key=lambda w: len(w[1]))] if longer else ways


def _key(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower().replace("’", "").replace("'", ""))


def _chain(seg: str) -> tuple:
    """[(surname, given, [], split)], [why] for a list with no stops."""
    chunks = [_clean(c) for c in seg.split(",")]
    chunks = [c for c in chunks if c]
    if len(chunks) < 2 or not SURNAME.match(chunks[0]):
        return [], [f"the list does not open with a surname ({len(chunks)} chunks)"]
    out, bad = [], []
    sur, how = chunks[0], "delimited"
    for i, c in enumerate(chunks[1:], 1):
        if i == len(chunks) - 1:
            if GIVEN.match(c):
                out.append((sur, c, [], how))
            else:
                bad.append(f"record {len(out) + 1}: the last given names are not names")
            break
        ways = _split_chunk(c)
        if len(ways) > 1:
            # the list is alphabetical: keep the splits whose surname sorts between its neighbours
            nxt = _key(chunks[i + 1].split()[-1]) if i + 1 < len(chunks) - 1 else "~"
            ways = [w for w in ways if _key(sur) <= _key(w[1]) <= nxt] or ways
            if len({w[1] for w in ways}) > 1:
                last = [w for w in ways if w[2] == "last word"]
                ways = last[:1] if len(last) == 1 and not any(w[2] == "glue" for w in ways) else ways
        if len(ways) != 1:
            bad.append(f"record {len(out) + 1}: {len(ways)} ways to end the given names")
            # resynchronise on the most likely split so one doubt costs one record
            if ways:
                sur, how = ways[-1][1], ways[-1][2]
            else:
                sur, how = c.split()[-1], "last word"
            continue
        given, nsur, nhow = ways[0]
        out.append((sur, given, [], how))
        sur, how = nsur, nhow
    return out, bad


#: The combined annual list's key: "CU = Civil Union Celebrant M = Independent Marriage Celebrant".
_LEGEND = re.compile(r"(?:(?:\b|(?<=[a-z]))(?:CU|M|I)\s*=\s*(?:Civil Union|Independent Marriage)\s+[Cc]elebrants?\s*){2}")
_MARK = {"M", "I", "CU"}


def _marked(seg: str) -> tuple:
    """[(surname, given, marks)], [why] for the combined list: a chain in
    which every name is preceded by its letters, so the letters cut each
    chunk exactly into one record's given names and the next one's surname."""
    # a comma between two letters (`M, CU Smith`, the 2025 print) separates no records
    seg = re.sub(r"\b(M|CU|I),\s*(?=(?:M|CU|I)\b)", r"\1 ", seg)
    chunks = [_clean(c) for c in seg.split(",")]
    chunks = [c for c in chunks if c]
    out, bad = [], []

    def cut(words):
        """(given words, marks, surname words) at the last run of letters followed by a name."""
        i = len(words) - 1
        while i >= 0 and words[i] not in _MARK:
            i -= 1
        j = i
        while j - 1 >= 0 and words[j - 1] in _MARK:
            j -= 1
        return (words[:j], words[j:i + 1], words[i + 1:]) if i >= 0 and i + 1 < len(words) else None

    if len(chunks) < 2:
        return [], [f"the marked list has {len(chunks)} chunks"]
    first = cut(chunks[0].split())
    if not first or first[0] or not SURNAME.match(" ".join(first[2])):
        return [], ["the marked list does not open with its letters and a surname"]
    sur, marks = " ".join(first[2]), " ".join(first[1])
    for n, c in enumerate(chunks[1:], 1):
        if n == len(chunks) - 1:
            if GIVEN.match(c):
                out.append((sur, c, marks))
            else:
                bad.append(f"record {len(out) + 1}: the last given names are not names")
            break
        got = cut(c.split())
        if not got or not got[0] or not SURNAME.match(" ".join(got[2])) or not GIVEN.match(" ".join(got[0])):
            bad.append(f"record {len(out) + 1}: no letters cut the given names from the next surname")
            if got and got[2]:
                sur, marks = " ".join(got[2]), " ".join(got[1])
            continue
        out.append((sur, " ".join(got[0]), marks))
        sur, marks = " ".join(got[2]), " ".join(got[1])
    return out, bad


def read(text: str) -> Reading:
    text = text or ""
    r = Reading(action=action(text), statute=statute(text))
    r.period_from, r.period_to = period(text)
    if TABLE_HEADER.search(text):
        r.mode = "table"
        r.unread.append(("list", "a printed table: nothing delimits the given names from the organisation"))
        return r
    legend = _LEGEND.search(text[:SUBJECT_HEAD])
    if legend:
        d = _DATED.search(text, legend.end())
        seg = text[legend.end():d.start() if d else len(text)]
        r.mode = "marked"
        if _located(seg):
            # the 2015 list prints each address after the name: a town would be read as the next given names
            r.unread.append(("list", "a marked list that prints addresses: the records cannot be told apart"))
            return r
        recs, bad = _marked(seg)
        r.records = [Record(i, s, g, marks=m) for i, (s, g, m) in enumerate(recs, 1)]
        r.unread += [tuple(b.split(": ", 1)) if b.startswith("record ") else ("list", b) for b in bad]
        return _no_action(r, text)
    span = body(text)
    if span is None:
        r.unread.append(("list", "names celebrants but prints no list the reader can find"))
        return r
    seg = text[span[0]:span[1]]
    stops, commas, located = len(_STOP.findall(seg)), seg.count(","), _located(seg)
    # a stopped list has one or two commas a record (up to eight with an address); a chain has one a record
    # and almost no stops, so a few stray stops in a chain of thousands do not make it a stopped list
    if stops and commas <= (8 if located else 2.5) * stops:
        recs, bad = _stops(seg)
        located = sum(1 for _, _, x in recs if _is_address(x))
        third = sum(1 for _, _, x in recs if x)
        # an address list prints addresses for most records, some without a number or a street word (a town);
        # a list of organisations with a stray located record keeps its organisations. Either way a located
        # field is an address and is private.
        r.mode = "address" if located and 2 * located >= third else "stops"
        for i, (s, g, x) in enumerate(recs, 1):
            if x and (r.mode == "address" or _is_address(x)):
                r.records.append(Record(i, s, g, address=", ".join(x)))
            else:
                r.records.append(Record(i, s, g, organisation=", ".join(x) or None))
        r.unread += [("record", "not a record: the text between two stops has no `Surname, Given` shape") for b in bad]
    elif located:
        r.mode = "address"
        r.unread.append(("list", "an address list with no stops: the records cannot be told apart"))
    else:
        recs, bad = _chain(seg)
        r.mode = "chain"
        for i, (s, g, x, how) in enumerate(recs, 1):
            r.records.append(Record(i, s, g, split=how))
        r.unread += [tuple(b.split(": ", 1)) if b.startswith("record ") else ("list", b) for b in bad]
    return _no_action(r, text)


def _no_action(r: Reading, text: str) -> Reading:
    if r.action is None and r.records:
        r.unread.append(("action", f"says {'more than one thing' if _APPOINTS.search(text) or _REMOVES.search(text) or _PUBLISHES.search(text) else 'no action'}: "
                                   f"{len(r.records)} records not taken"))
    return r
