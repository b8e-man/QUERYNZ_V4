"""Notices of intention to remove a company from the register (profile
`gazette-removal-notice`): every notice in the Gazette's section `ds`,
recognised by that code, then read. No model.

Two shapes:

  notice   one company or a few, named in the title as the liquidation
           notices name them ("ACME LIMITED (in liquidation)", sometimes
           with "No. 123456"), given by the liquidator once the liquidation
           is complete (Companies Act 1993 s 318(1)(e)), or by a director or
           shareholder asking the Registrar to remove a company that has
           ceased business (s 318(1)(b)); a few are restorations
  list     the Registrar's own: "Notice of Intention to Remove Companies
           From the Register", the names run together, each ending in its
           legal suffix and then a stop or the company's number

The companies are cut as the liquidation profile cuts them (liquidations.
split_names): only where each part ends in a legal suffix. The action, the
section, the ground in the notice's words, who gives notice and the date
for objections are read; no address is read, because a director's notice
can print a home one.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(shape, companies, action, statute, ground, by_whom, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette.entries import Entry, Reading

CODE = "ds"
_LIST_TITLE = re.compile(r"^\s*(?:Corrigendum\s*[—–\-:]*\s*)?Notice\s+of\s+Intention\s+to\s+Remove\b", re.I)
_TITLE_NUMBER = re.compile(r"\s*\b(?:Co(?:mpany)?\.?\s*)?(?:No\.?|Number|NZBN)\s*:?\s*(\d{4,13})\s*$", re.I)
_NAME = rf"\s*(?P<name>[A-Z0-9(][^|]*?(?:{LQ._LIST_SUFFIX}|\bLP\b))(?:\s*\([^()]*\))*\.?"
#: a row with its number after it (the Registrar's newer lists), and one without: digits after a name in a list
#: that does not print numbers begin the next name ("6306902 LIMITED" is a company's whole name)
_ROW = re.compile(rf"{_NAME}(?:\s*(?P<n>\d{{5,8}})(?!\d))?(?=\s*(?:[A-Z0-9«]|$))")
_ROW_PLAIN = re.compile(rf"{_NAME}(?P<n>)(?=\s*(?:[A-Z0-9«]|$))")
NUMBERED = 0.8                    # the share of rows followed by a number that makes a list a numbered one
#: past a row the reader cannot take: up to the next name's end, so one bad row costs only itself
_SKIP = re.compile(rf"[^|]*?{LQ._LIST_SUFFIX}(?:\s*\([^()]*\))*\.?(?:\s*\d{{5,8}}(?!\d))?")
_LIST_END = re.compile(r"\bUnless\b|\bDated\b|\bAny\s+objections?\b|\bRegistrar\s+of\s+Companies\b", re.I)
#: a sentence of the intro: prose, and never across a name in capitals ("ABLE LIMITED 1234567 Unless, …" is a list's
#: last row and its closing words, not a sentence to skip)
_CHAR = r"(?:(?!\b(?:LIMITED|LTD|PARTNERSHIP|INCORPORATED|TRUST)\b)[^.])"
_SENTENCE = re.compile(rf"\s*{_CHAR}*?\b[a-z]{{2,}}\s+[a-z]{{2,}}\b{_CHAR}*?\.(?!\d)")
_S318 = re.compile(r"section\s+318\s*\(\s*1\s*\)\s*\(\s*([a-z]{1,2})\s*\)", re.I)
_OBJECT_BY = re.compile(rf"(?:delivered|lodged|received)\s+(?:to|with|by)\s+the\s+Registrar[^.]{{0,40}}?\bby\s+(?:the\s+)?(?P<d>{LQ._DAY})", re.I)


def recognise(code: str, title: str, text: str) -> list:
    return ["the Gazette's section ds (removal from the register)"] if code == CODE else []


def _action(head: str) -> str:
    if re.search(r"restor", head, re.I):
        return "restoration"
    if re.search(r"apply\s+for|application\s+for|request(?:ed|s)?\s+(?:for\s+)?(?:the\s+)?removal|intends?\s+to\s+(?:make\s+)?(?:an\s+)?application", head, re.I):
        return "application for removal"
    if re.search(r"intention\s+to\s+remove|intend(?:s|ed)?\s+to\s+remove|propose[sd]?\s+to\s+remove|will\s+remove|may\s+remove|be\s+removed", head, re.I):
        return "intention to remove"
    if re.search(r"liquidation\s+(?:of\s+the\s+[\w-]+\s+compan(?:y|ies)\s+)?(?:has|have)\s+been\s+completed|completion\s+of\s+(?:the\s+)?liquidation", head, re.I):
        return "liquidation completed"
    if re.search(r"\b(?:has|have)\s+been\s+removed\b|\bremoval\s+of\b", head, re.I):
        return "removal"
    return None


def _ground(text: str, letter: str) -> str:
    if re.search(r"final\s+report|liquidation\s+(?:of\s+the\s+\w+\s+compan(?:y|ies)\s+)?(?:has|have)\s+been\s+completed|completed\s+(?:the|their|his|her)\s+(?:duties|liquidation)", text, re.I):
        return "liquidation completed"
    if re.search(r"ceased\s+to\s+carry\s+on\s+business", text, re.I):
        return "ceased business"
    return {"e": "liquidation completed", "b": "ceased business", "c": "ceased business", "d": "ceased business"}.get(letter)


def _by_whom(text: str, shape: str) -> str:
    tail = text[-400:]
    if shape == "list" or re.search(r"Registrar\s+of\s+Companies\s*\.?\s*$|,\s*(?:Deputy\s+|Assistant\s+)?Registrar\b", tail):
        return "Registrar"
    if re.search(r"\b[Ll]iquidators?\b", tail) or re.search(r"\bliquidators?\s+of\s+the\b|\bwe,?\s+[^.]{0,120}liquidators\b", text, re.I):
        return "liquidator"
    for who in ("director", "shareholder", "board", "solicitor"):
        if re.search(rf"\b{who}s?\b", text, re.I):
            return who
    return None


def _cut(seg: str, row) -> tuple:
    """[(name, number)] and [(place, why)] from a list's segment, one row pattern."""
    pos, held, rows, unread = 0, len(seg), [], []
    while pos < held:
        m = row.match(seg, pos)
        if not m or m.end() == pos:
            skip = _SKIP.match(seg, pos)
            if not skip or skip.end() == pos:
                break
            unread.append((f"after row {len(rows)}", "a list row that is not a company name"))
            pos = skip.end()
            continue
        pos = m.end()
        name = LQ._clean(m.group("name"))
        if len(name) > 160 or re.search(r"\b[a-z]{3,}\s+[a-z]{3,}\b", name):
            unread.append((f"after row {len(rows)}", "a list row that is not a company name"))
            continue
        rows.append((name, m.group("n") or None))
    rest = LQ._clean(seg[pos:])
    if rest and re.search(r"[A-Z]{2,}|[A-Z][a-z]+\s+[A-Z]", rest):
        unread.append(("list", "the list's end the reader cannot cut"))
    return rows, unread


def _list(title: str, text: str, r: Reading) -> None:
    r.shape = "list"
    pos = 0                       # the intro is prose; the list starts at the first sentence that is not
    while (m := _SENTENCE.match(text, pos)) and m.end() > pos:
        pos = m.end()
    seg = text[pos:]
    end = _LIST_END.search(seg)
    seg = seg[:end.start()] if end else seg
    if not re.search(LQ._SUFFIX, seg):
        r.unread.append(("list", "the capture holds the notice's words and not its list"))
        return
    rows, unread = _cut(seg, _ROW)
    if rows and sum(1 for n, x in rows if x) < NUMBERED * len(rows):
        rows, unread = _cut(seg, _ROW_PLAIN)
    r.companies = [Entry(i, name, number=n) for i, (name, n) in enumerate(rows, 1)]
    r.unread += unread
    if not r.companies:
        r.unread.append(("list", "a Registrar's list with no rows the reader can cut"))


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    s318 = _S318.search(text)
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    o = _OBJECT_BY.search(text)
    if o:
        r.event_on, r.event_basis = LQ._date(o.group("d")), "objections by"
    r.action = _action(f"{title} {text[:700]}")
    r.ground = _ground(text, s318.group(1).lower() if s318 else None)
    if _LIST_TITLE.match(title):
        _list(title, text, r)
    else:
        r.shape = "notice"
        t = _TITLE_NUMBER.search(title)
        number = t.group(1) if t else None
        head = title[:t.start()] if t else title
        names, left = LQ.split_names(LQ._title_head(head, text))
        for x in left:
            r.unread.append(("title", "a part of the title that ends in no legal suffix"))
        if not names:
            r.unread.append(("title", "the title names no company"))
        numbers = list(dict.fromkeys(LQ._NUMBER.findall(text)))
        number = number or (numbers[0] if len(names) == 1 and len(numbers) == 1 else None)
        r.companies = [Entry(i, n, number=number if len(names) == 1 else None) for i, n in enumerate(names, 1)]
    r.by_whom = _by_whom(text, r.shape)
    return r
