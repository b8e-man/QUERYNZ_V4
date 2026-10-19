"""A general election's nominations, from the Commission's three files and
its release (profiles `ec-electorate-candidates-workbook`,
`votenz-party-lists-page`, `ec-party-lists-pdf`, `ec-candidate-lists-release`).

    workbook(data)        [(sheet row, name, electorate, party)] and [(row, why)] set aside
    party_lists(data)     [(party, place, name)] in the page's order
    pdf_pairs(data)       [(place, name)]: every 'N SURNAME, Given' on the PDF's text layer
    release(data)         the Commission's stated figures
    join(electorate, lists)   one candidacy per person: who is on both, and how they were joined

A person on the party list and standing in an electorate for that party is
one candidacy. The two files print a name the same way nearly always; where
they do not, the join takes the same surname and the same first given name,
only when that is unique in the party on both sides, and says so. Nothing
fuzzier: an unjoined pair stays two rows, never a guess.
"""
import html
import re

from keys import names
from registers.house import workbook as wb

_LI = re.compile(r"<li>(.*?)</li>", re.S)
_ACC = re.compile(r'<button class="accordion__title"[^>]*>\s*(.*?)\s*</button>\s*<div class="accordion__content"[^>]*>(.*?)</div>', re.S)
_TAG = re.compile(r"<[^>]+>")
_PAIR = re.compile(r"(?<!\S)(\d{1,2}) +((?:\S+ )*?\S+),[ ]+(\S.*?)(?= {2,}|$)", re.M)
_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
          "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
          "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20}


def text(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub(" ", s)).replace("\xa0", " ")).strip()


def workbook(data: bytes) -> tuple:
    rows, aside = [], []
    got = wb.rows(data)
    for n, cells in got[1:]:
        cells = [c.strip() for c in cells] + ["", "", ""]
        name, electorate, party = cells[:3]
        if not name and not electorate and not party:
            continue
        if not name or not electorate:
            aside.append((n, "a row without a name or an electorate"))
            continue
        rows.append((n, name, electorate, party or None))
    return rows, aside


def party_lists(data: bytes) -> list:
    t = data.decode("utf-8", "replace")
    out = []
    for head, body in _ACC.findall(t):
        party = text(head)
        for i, item in enumerate(_LI.findall(body), 1):
            out.append((party, i, text(item)))
    return out


def pdf_pairs(page_texts: list) -> list:
    out = []
    for t in page_texts:
        for line in t.splitlines():
            for m in _PAIR.finditer(line):
                last = m.group(2).split()[-1]
                if sum(c.isupper() for c in last) < 2 or any(c.isdigit() for c in m.group(2)):
                    continue                    # a surname is printed in capitals
                out.append((int(m.group(1)), f"{m.group(2)}, {m.group(3).strip()}"))
    return out


def release(data: bytes) -> dict:
    t = text(data.decode("utf-8", "replace"))
    out = {"parties": {}}

    def num(rx, key):
        m = re.search(rx, t)
        if m:
            v = m.group(1).lower()
            out[key] = int(v) if v.isdigit() else _WORDS.get(v)

    num(r"(\w+) registered political parties and a total of \d+ candidates", "registered_parties")
    num(r"A total of (\d+) candidates \(electorate and list\)", "candidates")
    num(r"(\d+) candidates are on the party lists only", "list_only")
    num(r"(\d+) candidates for registered parties are standing as electorate candidates only", "electorate_only")
    num(r"(\d+) electorate candidates are standing as independents or representing unregistered parties", "independent_or_unregistered")
    num(r"standing both as an electorate candidate and on a party list is (\d+)", "both")
    raw = data.decode("utf-8", "replace")
    i = raw.find("Registered party")
    if i >= 0:
        table = raw[i:raw.find("</table>", i)]
        for tr in re.findall(r"<tr>(.*?)</tr>", table, re.S):
            cells = [text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) != 3 or cells[0].startswith("Registered party"):
                continue
            lst, ele = (None if c in ("-", "") else int(c.replace(",", "")) for c in cells[1:])
            if cells[0].upper() == "TOTAL":
                out["list_total"], out["electorate_total"] = lst, ele
            else:
                out["parties"][cells[0]] = (lst or 0, ele or 0)
    return out


def _given_first(raw: str):
    """(surname key, first given name key) of a 'SURNAME, Given' name, as the Commission files it."""
    if "," not in raw:
        return names.person_key(raw), ""
    fam, given = raw.split(",", 1)
    first = given.split()[0] if given.split() else ""
    return names.fold_diacritics(fam).lower().strip(), names.fold_diacritics(first).lower()


def join(electorate: list, lists: list) -> tuple:
    """electorate: [(row, name, electorate, party)]; lists: [(party, place,
    name)]. Returns {row: (list index, basis)} and the list indexes joined."""
    joined, used = {}, set()
    by_party = {}
    for j, (party, place, nm) in enumerate(lists):
        by_party.setdefault(_pkey(party), []).append(j)
    for row, nm, _, party in electorate:
        cands = [j for j in by_party.get(_pkey(party), []) if j not in used
                 and names.person_key(lists[j][2]) == names.person_key(nm)]
        if len(cands) == 1:
            joined[row] = (cands[0], "name")
            used.add(cands[0])
    for row, nm, _, party in electorate:
        if row in joined:
            continue
        fk = _given_first(nm)
        if not fk[1]:
            continue
        cands = [j for j in by_party.get(_pkey(party), []) if j not in used and _given_first(lists[j][2]) == fk]
        rivals = [r for r, n2, _, p2 in electorate if r != row and r not in joined
                  and _pkey(p2) == _pkey(party) and _given_first(n2) == fk]
        if len(cands) == 1 and not rivals:
            joined[row] = (cands[0], "surname and first given name, unique in the party")
            used.add(cands[0])
    return joined, used


def _pkey(party) -> str:
    return re.sub(r"[^a-z0-9]", "", html.unescape(party or "").lower().replace("’", "'"))
