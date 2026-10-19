"""The results site's pages, read from their own markup (profiles
`ec-results-electorate-page`, `ec-results-successful-candidates`,
`ec-results-electorate-status`, `ec-results-overall`,
`ec-byelection-result-page`). No model.

    electorate_page(data)    Electorate: its name, candidates with party and votes, party-only rows, the printed totals
    by_election_page(data)   the same shape from a by-election page (party printed as an abbreviation)
    successful(data)         [(party, name, seat, electorate page number or None)]: 'List Seat' or an electorate
    status(data)             [(electorate, name, abbreviation)] for the leading and second candidates
    overall(data)            {party: (electorate seats, list seats, total)}, and the Total row

Every page that prints its own totals is scored against them (`Electorate.problems`).
"""
import html
import re
from dataclasses import dataclass, field

_TAG = re.compile(r"<[^>]+>")


def text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", s)).replace("\xa0", " ")).strip()


def _int(s: str):
    s = (s or "").replace(",", "").strip()
    return int(s) if s.isdigit() else None


@dataclass
class Electorate:
    name: str
    candidates: list = field(default_factory=list)      # (place, name as printed, party as printed or None, votes, poll cancelled)
    party_only: list = field(default_factory=list)      # (party, party votes)
    party_votes: dict = field(default_factory=dict)     # party → party votes, from candidate rows and party-only rows
    candidate_informals: int = None
    party_informals: int = None
    candidate_total: int = None
    party_total: int = None
    votes_counted: int = None

    def problems(self) -> list:
        out = []
        if not self.name:
            out.append("the page names no electorate")
        if not self.candidates:
            out.append("no candidate rows")
        if self.candidate_total is None:
            out.append("no candidate TOTAL printed")
        elif sum(c[3] or 0 for c in self.candidates) + (self.candidate_informals or 0) != self.candidate_total:
            out.append(f"candidate votes {sum(c[3] or 0 for c in self.candidates)} + informals "
                       f"{self.candidate_informals} != the page's TOTAL {self.candidate_total}")
        if self.party_total is not None and self.party_votes:
            s = sum(self.party_votes.values()) + (self.party_informals or 0)
            if s != self.party_total:
                out.append(f"party votes {s} with informals != the page's party TOTAL {self.party_total}")
        return out


_H2 = re.compile(r"<h2>\s*(.*?)\s*-\s*Official Result\s*</h2>", re.S)
_ROW = re.compile(r"<tr\b[^>]*>(.*?)</tr>", re.S)
_SPANS = re.compile(r"<span[^>]*>(.*?)</span>\s*<span[^>]*>(.*?)</span>", re.S)
_CANCELLED = re.compile(r"\s*\(poll cancelled\)\s*$")


def electorate_page(data: bytes) -> Electorate:
    t = data.decode("utf-8", "replace")
    m = _H2.search(t)
    e = Electorate(text(m.group(1)) if m else "")
    m = re.search(r"VOTES COUNTED:.*?<div class=\"bold\">([\d,]+)</div>", t, re.S)
    e.votes_counted = _int(m.group(1)) if m else None
    i = t.find('id="partyCandidatesResultsTable"')
    body = t[i:t.find("</table>", i)] if i >= 0 else ""
    place = 0
    for row in _ROW.findall(body):
        cells = _SPANS.findall(row)
        if len(cells) == 2:
            (cn, cv), (pn, pv) = cells
            cn, pn = text(cn), text(pn)
            if cn:
                place += 1
                cancelled = bool(_CANCELLED.search(cn))
                e.candidates.append((place, _CANCELLED.sub("", cn), pn or None, _int(text(cv)), cancelled))
            elif pn:
                e.party_only.append((pn, _int(text(pv))))
            if pn:
                e.party_votes[pn] = e.party_votes.get(pn, 0) + (_int(text(pv)) or 0)
            continue
        labels = re.findall(r"<label[^>]*>(.*?)</label>\s*<span[^>]*>(.*?)</span>", row, re.S)
        for k, (lab, val) in enumerate(labels):
            lab = text(lab).rstrip(":").lower()
            if lab == "candidate informals":
                e.candidate_informals = _int(text(val))
            elif lab == "party informals":
                e.party_informals = _int(text(val))
            elif lab == "total":
                if k == 0:
                    e.candidate_total = _int(text(val))
                else:
                    e.party_total = _int(text(val))
    return e


def by_election_page(data: bytes) -> Electorate:
    t = data.decode("utf-8", "replace")
    m = _H2.search(t)
    e = Electorate(text(m.group(1)) if m else "")
    i = t.find('id="by_election_table"')
    body = t[i:t.find("</table>", i)] if i >= 0 else ""
    place = 0
    for row in _ROW.findall(body):
        cells = [text(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.S)]
        if not cells or cells[0] in ("Candidates", ""):
            continue
        head = cells[0].rstrip(":").strip().lower()
        if head == "candidate informals":
            e.candidate_informals = _int(cells[-1])
        elif head == "total":
            e.candidate_total = _int(cells[-1])
        elif len(cells) >= 3 and _int(cells[-1]) is not None:
            place += 1
            e.candidates.append((place, cells[0], cells[1] or None, _int(cells[-1]), False))
    return e


def successful(data: bytes) -> list:
    t = data.decode("utf-8", "replace")
    i = t.find('id="successful_candidates_table"')
    body = t[i:t.find("</table>", i)] if i >= 0 else ""
    out, party = [], None
    for row in _ROW.findall(body):
        h = re.search(r"<h3>(.*?)</h3>", row, re.S)
        if h:
            party = text(h.group(1))
            continue
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(cells) != 2:
            continue
        name, seat = text(cells[0]), text(cells[1])
        link = re.search(r'electorate-details-(\d+)\.html', cells[1])
        if name:
            out.append((party, name, re.sub(r"\s+Electorate$", "", seat), int(link.group(1)) if link else None))
    return out


def status(data: bytes) -> list:
    t = data.decode("utf-8", "replace")
    i = t.find('id="electorate-status-table"')
    body = t[i:t.find("</table>", i)] if i >= 0 else ""
    out = []
    for row in _ROW.findall(body):
        cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(cells) < 3:
            continue
        for c in cells[1:3]:
            m = re.match(r"(?:Leading|2nd) Candidate:\s*(.*?)\s*\(([^()]+)\)\s*$", c)
            if m:
                out.append((cells[0], m.group(1), m.group(2)))
    return out


def overall(data: bytes) -> dict:
    t = data.decode("utf-8", "replace")
    i = t.find('id="overall-results-table"')
    body = t[i:t.find("</table>", i)] if i >= 0 else ""
    out = {}
    for row in _ROW.findall(body):
        cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        if len(cells) < 6 or not cells[0]:
            continue
        seats = tuple(0 if c in ("-", "") else _int(c) for c in cells[-3:])
        if cells[0] in out:          # the page prints a party twice (Freedoms NZ 2023): keep the row with figures
            if seats == (0, 0, 0):
                continue
        out[cells[0]] = seats
    return out


_OPTION = re.compile(r'<option value="\./electorate-details-(\d+)\.html">(.*?)</option>', re.S)


def electorate_list(data: bytes) -> list:
    """[(page number, electorate)]: the site's own list of an election's
    electorates, printed in the selector on its result pages."""
    t = data.decode("utf-8", "replace")
    i = t.find('id="electorates_select_box"')
    if i < 0:
        return []
    return [(int(n), text(name)) for n, name in _OPTION.findall(t[i:t.find("</select>", i)])]
