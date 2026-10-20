"""Overseas companies leaving New Zealand (profile
`gazette-overseas-company-ceasing`): every notice in the Gazette's section
`cb`, recognised by that code, then read. No model.

Two shapes:

  notice   one overseas company, its name the title ("ACME PTY LTD (New
           Zealand branch)"): it intends to cease to carry on business in
           New Zealand and will ask the Registrar to remove it from the
           overseas register three months on (Companies Act 1993 s 343), or
           it applies for that removal; a "Company No." in the text, and
           sometimes the day it ceases
  list     the Registrar's own "Notice of Intention to Remove Overseas
           Companies From the Register", cut as the removal profile cuts its
           lists (removals.py)

The name is the title less its brackets that are not the name's own ("(New
Zealand branch)", "(the overseas company)", "(formerly …)"). No address is
read: the notice's address for service is a firm's, but nothing needs it.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(shape, companies, action, statute, event_on, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette import removals
from registers.gazette.entries import Entry, Reading

CODE = "cb"
#: a bracket that is not part of the name: the branch, a defined term, a former name, a status
_NOT_NAME = re.compile(r"\s*\((?:[^()]*\bbranch\b[^()]*|[^()]*overseas\s+company[^()]*|\s*[\"“'‘]?the\b[^()]*|\s*(?i:formerly|previously|"
                       r"in|now|also|trading|ACN|ARBN|ABN|company\s+n(?:o|umber))\b[^()]*)\)", re.I)
_GENERIC = re.compile(r"^\s*(?:Corrigendum\s*[—–\-:]*\s*)?(?:(?:Public\s+)?(?:Notice|Advertisement)|(?:The\s+)?Companies\s+Act)\b", re.I)
_CEASE = re.compile(r"\bceas(?:e|es|ed|ing|ation)\b[^.]{0,60}?\b(?:business|trading|operations)", re.I)
_REMOVE = re.compile(r"\bremov\w*\b[^.]{0,80}?\bregister|\bderegist", re.I)
_CEASES_ON = re.compile(rf"\b(?:on|from|with\s+effect\s+from|as\s+(?:at|of))\s+(?:the\s+)?(?P<d>{LQ._DAY})[^.]{{0,120}}?\bceas"
                        rf"|\bceas\w*\b[^.]{{0,80}}?\b(?:on|from|with\s+effect\s+from|as\s+(?:at|of))\s+(?:the\s+)?(?P<d2>{LQ._DAY})")
_LIST = re.compile(r"^\s*(?:Corrigendum\s*[—–\-:]*\s*)?Notice\s+of\s+Intention\s+to\s+Remove\s+Overseas\s+Companies\b", re.I)


def recognise(code: str, title: str, text: str) -> list:
    return ["the Gazette's section cb (overseas companies)"] if code == CODE else []


def name_of(title: str) -> str:
    """The company in a title: the brackets that are not the name's own dropped."""
    t = LQ._CORRIGENDUM.sub("", title or "")
    prev = None
    while prev != t:
        prev, t = t, _NOT_NAME.sub(" ", t)
    return LQ._clean(re.sub(r"\s*\([^)]*$", "", t))


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    r.by_whom = "Registrar" if _LIST.match(title) else "the company"
    if _LIST.match(title):
        removals._list(title, text, r)
        r.action = "intention to remove"
        return r
    r.shape = "notice"
    head = text[:600]
    r.action = ("ceasing to carry on business" if _CEASE.search(head)
                else "application for removal" if _REMOVE.search(head) else None)
    if r.action is None:
        r.unread.append(("action", "the notice says neither that the company ceases business nor that it applies for removal"))
    c = _CEASES_ON.search(text)
    if c:
        r.event_on, r.event_basis = LQ._date(c.group("d") or c.group("d2")), "ceases"
    name = None if _GENERIC.match(title) else name_of(title)
    if not name or len(name) > 160 or re.search(r"\b[a-z]{3,}\s+[a-z]{3,}\s+[a-z]{3,}\b", name):
        r.unread.append(("title", "the title is not the company's name"))
        return r
    numbers = list(dict.fromkeys(LQ._NUMBER.findall(text)))
    r.companies = [Entry(1, name, number=numbers[0] if len(numbers) == 1 else None)]
    return r
