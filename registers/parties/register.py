"""The Commission's register page → one entry per registered party, as
the page stood when it was captured.

The page is rendered HTML: each party is a `parties__party-info` block, its
name the block's `<h2>` and every field an `<h3>` label followed by its
value. The secretary's contact lines (a postal address that is sometimes a
home, a telephone, an email) are kept apart for the private schema and
never reach an entry's published fields (hard limit 15); the secretary's
name is the register's public role and is kept.

    read(data)     Page(entries, skipped)
"""
import html
import re
from dataclasses import dataclass, field

from registers.parties.notices import DATE, iso

_BLOCK = re.compile(r'<div class="parties__party-info">')
_H2 = re.compile(r"<h2>(.*?)</h2>", re.S)
_H3 = re.compile(r"<h3>(.*?)</h3>", re.S)
_LOGOS = re.compile(r'<div class="parties__party-info__logos"')
_TAIL = re.compile(r'pagecomponent-file-files|<footer')
#: some blocks print a field's label in bold inside the secretary's cell
_STRONG = re.compile(r"<strong>\s*([^<]*?:)\s*</strong>")

#: label as printed → field
LABELS = {
    "party registered": "registered",
    "component parties": "components",
    "abbreviation": "abbreviation",
    "logo registered": "logo_registered",
    "party rules": "rules",
    "party secretary name and contact details": "secretary",
    "deadline for providing financial statements": "statement_deadline",
    "audit requirement for financial statements": "audit",
    "website": "website",
    "registered logo": None,
}


@dataclass
class Entry:
    ordinal: int
    name: str
    registered_on: str = None
    abbreviation: str = None
    abbreviation_on_ballot: bool = False
    components: str = None
    logo_registered_on: str = None
    previous_logos: list = field(default_factory=list)     # ISO dates
    rules_title: str = None
    rules_href: str = None
    secretary: str = None
    contact: str = None                                    # private: the lines after the name
    statement_deadline: str = None
    audit: str = None
    website: str = None


@dataclass
class Page:
    entries: list = field(default_factory=list)
    skipped: list = field(default_factory=list)            # (place, reason)


def text(fragment: str) -> list:
    """The fragment's visible lines."""
    t = re.sub(r"(?s)<(script|style|svg).*?</\1>", "", fragment)
    t = re.sub(r"<br\s*/?>|</p>|</div>|</h\d>|</a>", "\n", t)
    t = html.unescape(re.sub(r"<[^>]+>", "", t)).replace("\xa0", " ")
    return [re.sub(r"\s+", " ", l).strip() for l in t.splitlines() if l.strip()]


def _date(s: str):
    m = DATE.search(s or "")
    return iso(m) if m else None


_SHORT = re.compile(r"(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w* ((?:19|20)\d\d)")
_SHORT_N = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}


def _short_date(s: str):
    m = _SHORT.search(s or "")
    return f"{int(m.group(3)):04d}-{_SHORT_N[m.group(2)]:02d}-{int(m.group(1)):02d}" if m else None


def _entry(block: str, n: int) -> Entry:
    name = " ".join(text(_H2.search(block).group(1)))
    e = Entry(ordinal=n, name=name)
    tail = _TAIL.search(block)
    block = _STRONG.sub(r"<h3>\1</h3>", block[:tail.start()] if tail else block)
    parts = _LOGOS.split(block, 1)
    head, logos = parts[0], (parts[1] if len(parts) > 1 else "")
    marks = list(_H3.finditer(head))
    for i, m in enumerate(marks):
        label = " ".join(text(m.group(1))).rstrip(":").strip().lower()
        raw = head[m.end():marks[i + 1].start() if i + 1 < len(marks) else len(head)]
        lines = text(raw)
        f = LABELS.get(label, "?")
        if f == "registered":
            e.registered_on = _date(" ".join(lines))
        elif f == "components":
            e.components = None if " ".join(lines).lower() in ("", "none") else "; ".join(lines)
        elif f == "abbreviation":
            a = " ".join(lines)
            e.abbreviation_on_ballot = "used on the ballot paper" in a.lower()
            a = re.sub(r"\s*\(used on the ballot paper\)", "", a, flags=re.I).strip()
            e.abbreviation = None if a.lower() in ("", "none") else a
        elif f == "logo_registered":
            e.logo_registered_on = _date(" ".join(lines))
        elif f == "rules":
            h = re.search(r'href="([^"]+)"', raw)
            e.rules_href, e.rules_title = (h.group(1) if h else None), (" ".join(lines) or None)
        elif f == "secretary":
            e.secretary = lines[0] if lines else None
            e.contact = "; ".join(lines[1:]) or None
        elif f in ("statement_deadline", "audit", "website"):
            setattr(e, f, lines[0] if lines else None)
    e.previous_logos = [d for d in (_short_date(s) for s in re.findall(r"Registered:\s*([^<]+)", logos)) if d]
    return e


def read(data: bytes) -> Page:
    page = Page()
    src = data.decode("utf-8", "replace")
    blocks = _BLOCK.split(src)[1:]
    for n, b in enumerate(blocks, 1):
        if not _H2.search(b):
            page.skipped.append((f"party {n}", "a party block with no name heading"))
            continue
        e = _entry(b, n)
        if not e.registered_on:
            page.skipped.append((f"party {n}", "no registration date read"))
            continue
        page.entries.append(e)
    return page
