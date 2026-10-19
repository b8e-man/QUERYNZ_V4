"""Which return an amendment replaces, as the Commission states it (plan
4.1, tranche 2). Never inferred: not from a file name, not from a later
date, not from a total that differs.

The Commission's statement is its listing, "Party donations and loans by
year" (`elections.nz/…/party-donations-and-loans-by-year/`), held as a
captured page in the old folder's `var/staging/ec-donations/index/` and
landed by hash like the returns. From the 2022 returns on it is a table
with one row per party and year, the row's links being that party-year's
files; before that it is a list, one link per file, its text naming the
party and the year. Either way the Commission marks an amended return in
the link's own text: `NZ First (amended 5/6/2024)`, `(PDF, 2.6MB amended
2026)`, `Download the HeartlandNZ annual return 2021 (amended)`.

So within one party-year as the listing groups it, every file the
Commission marks amended replaces every file it does not; between two
amended files, the one whose stated date is later replaces the other, and
two amended files with no dates to order them replace neither each other
(said, not guessed). A file whose link does not say amended is never
replaced and never replaces, whatever its name says (`NZNP-Amended-…` is
linked as plain `National Party`). A listed file the lane does not hold is
a line in the catch log, so a capture can be asked for.

    listing_file()                  the held page's old path
    statements(html)                [Group(year, party, links=[Link(href, text, amended, when)])]
    held_by_name(index)             basename → sha256, from capture.old_index()
    replacements(groups, by_name)   [(replaced sha256, replaced_by sha256, group, stated)], [unheld lines], from 2017
"""
import html as H
import os
import re
from dataclasses import dataclass, field

from registers.party_returns import capture

LISTING = "live-mocracy-in-nz-political-parties-in-new-zealand-party-donations-and-loans-by-year.html"
ROW = re.compile(r"<tr\b.*?</tr>", re.S | re.I)
LINK = re.compile(r"<a\b[^>]*href=\"([^\"]+\.pdf)\"[^>]*>(.*?)</a>(?:\s*(?:<br\s*/?>)?\s*(\[[^\]<]*\]))?", re.S | re.I)
AMENDED = re.compile(r"\bamended\b", re.I)
WHEN = re.compile(r"amended\s+(\d{1,2})/(\d{1,2})/(\d{2,4})|amended\s+(?:\w+\s+)?(\d{4})", re.I)
LIST_ITEM = re.compile(r"Download\s+the\s+(?:amended\s+)?(.+?)\s+annual\s+return\s+(\d{4})", re.I)
FOLDER_YEAR = re.compile(r"/Annual-Returns/(\d{4})/", re.I)


@dataclass
class Link:
    href: str
    text: str
    amended: bool
    when: tuple = None             # (year, month, day) as stated, or None


@dataclass
class Group:
    year: int
    party: str
    links: list = field(default_factory=list)


def listing_file(folder: str = None) -> str:
    return os.path.join(folder or capture.FOLDER, "index", LISTING)


def _text(s: str) -> str:
    return " ".join(H.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def _when(text: str):
    m = WHEN.search(text)
    if not m:
        return None
    if m.group(4):
        return (int(m.group(4)), 0, 0)
    y = int(m.group(3))
    return (y + 2000 if y < 100 else y, int(m.group(2)), int(m.group(1)))


def _link(href, inner, after) -> Link:
    text = _text(inner) + (" " + _text(after) if after else "")
    return Link(href, text, bool(AMENDED.search(text)), _when(text))


def statements(page: str) -> list:
    out, in_rows = [], set()
    for row in ROW.finditer(page):
        links = [_link(*m.groups()) for m in LINK.finditer(row.group(0))]
        years = {int(y) for l in links for y in FOLDER_YEAR.findall(l.href)}
        for m in LINK.finditer(row.group(0)):
            in_rows.add(m.start() + row.start())
        if links and len(years) == 1:
            party = re.sub(r"\s*\(.*$", "", links[0].text).strip()
            out.append(Group(years.pop(), party, links))
    listed = {}
    for m in LINK.finditer(page):
        if m.start() in in_rows:
            continue
        link = _link(*m.groups())
        it = LIST_ITEM.search(link.text)
        if it:
            listed.setdefault((int(it.group(2)), it.group(1).strip()), []).append(link)
    out += [Group(y, party, links) for (y, party), links in listed.items()]
    return out


def held_by_name(index: dict) -> dict:
    """basename → sha256 for every return the old folder holds
    (`capture.old_index()`, sha256 → path), under the name the Commission
    gave the file (the archive replay prefixes its folder:
    `Party-donations-and-loans__2021-returns__<name>`). A name held twice
    with different bytes maps to None: it cannot say which."""
    out = {}
    for sha, path in index.items():
        name = os.path.basename(path).split("__")[-1].lower()
        out[name] = sha if out.get(name, sha) == sha else None
    return out


def replacements(groups: list, by_name: dict, first_year: int = capture.FIRST_YEAR):
    pairs, unheld = [], []
    for g in groups:
        if g.year < first_year:
            continue
        held = []
        for l in g.links:
            sha = by_name.get(l.href.rsplit("/", 1)[-1].lower())
            if sha is None:
                if l.amended:
                    unheld.append(f"{g.party} {g.year}: the Commission lists an amended return the lane does not hold ({l.href})")
                continue
            held.append((l, sha))
        amended = [(l, s) for l, s in held if l.amended]
        if not amended:
            continue
        dated = all(l.when for l, _ in amended)
        current = max(amended, key=lambda ls: ls[0].when) if dated else None
        for l, sha in held:
            if not l.amended:
                for al, asha in ([current] if current else amended):
                    pairs.append((sha, asha, g, al.text))
            elif current and sha != current[1] and l.when < current[0].when:
                pairs.append((sha, current[1], g, current[0].text))
    return pairs, unheld


