"""The results site's index (profile `ec-results-elections-index`): every
general election and by-election with the polling day the Commission
states. Every window in the lane starts from one of these days.

    index(data)   ([Election], [(item, why)] set aside)
"""
import datetime as dt
import html
import re
from dataclasses import dataclass

_MONTHS = {m: i for i, m in enumerate(("January", "February", "March", "April", "May", "June", "July", "August",
                                        "September", "October", "November", "December"), 1)}
_ITEM = re.compile(r'<li>\s*<a href="([^"]*)">(.*?)</a>\s*</li>', re.S)
_LABEL = re.compile(r"^(\d{4}) (.+?) - (\d{1,2}) ([A-Z][a-z]+) (\d{4})$")


@dataclass(frozen=True)
class Election:
    key: str            # ge-2023 | be-2025-tamaki-makaurau
    kind: str           # general | by-election
    name: str           # as printed
    electorate: str     # a by-election's electorate; None for a general election
    polled_on: str      # ISO day
    href: str           # the results address, relative to the site
    place: str          # where on the index page


def slug(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def _section(t: str, head: str) -> str:
    m = re.search(rf"<h3>\s*{head}\s*</h3>\s*<ul>(.*?)</ul>", t, re.S)
    return m.group(1) if m else ""


def index(data: bytes) -> tuple:
    t = data.decode("utf-8", "replace")
    out, aside = [], []
    for kind, head in (("general", "General Elections"), ("by-election", "By-elections")):
        for n, (href, label) in enumerate(_ITEM.findall(_section(t, head)), 1):
            label = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", label))).strip()
            place = f"{head} item {n}"
            m = _LABEL.match(label)
            if not m or m.group(4) not in _MONTHS:
                aside.append((place, f"{label!r}: not 'YEAR NAME - D Month YYYY'"))
                continue
            try:
                day = dt.date(int(m.group(5)), _MONTHS[m.group(4)], int(m.group(3))).isoformat()
            except ValueError:
                aside.append((place, f"{label!r}: not a real day"))
                continue
            name = m.group(2)
            if kind == "general":
                key, electorate = f"ge-{m.group(1)}", None
            else:
                electorate = re.sub(r"\s+By-election$", "", name)
                key = f"be-{m.group(1)}-{slug(electorate)}"
            out.append(Election(key, kind, f"{m.group(1)} {name}", electorate, day, href, place))
    return out, aside
