"""Notices of a receiver's appointment, or of a receiver ceasing to act
(profile `gazette-receivership`): every notice in the Gazette's section
`ar`, recognised by that code, then read. No model.

The companies are named in the title as the liquidation notices name them
("ACME LIMITED (in receivership)"), or in the body ("receivers and managers
of the property of ACME LIMITED"). The action is the notice's own heading:
"Notice of Appointment of Receiver(s) and Manager(s)" (Receiverships Act
1993 s 8), "Notice of Ceasing to Act as Receiver" (s 15), or both at once.
The date is the one printed near the operative words; who appointed is the
court where the notice says so, else the instrument ("under the powers
contained in a general security agreement"), with the secured creditor's
name where the notice prints "appointed by <NAME LIMITED>". The receivers
are read from the signature as the liquidators are (liquidations.py), else
from the operative sentence. No address, telephone or email is read.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(companies, action, by_whom, event_on, people, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette.entries import Entry, Reading

#: a body's own word: a subject with none of these and no legal suffix may be a person whose property is in
#: receivership, and is never published as a company
_BODY = re.compile(r"\b(?:PARTNERSHIP|Partnership|TRUST|Trust|TRUSTEES?|Trustees?|SOCIETY|Society|COMPANY|Company|"
                   r"INCORPORATED|Incorporated|CORPORATION|Corporation|BOARD|Board|LP)\b")

CODE = "ar"
_SIGNED = re.compile(r"(?P<names>(?<![A-Za-z])[A-Z](?:[^.:;|]|(?<=\b[A-Z])\.){1,150}?),\s*(?P<role>(?:Joint\s+(?:and\s+Several\s+)?|Former\s+|Interim\s+)?"
                     r"[Rr]eceivers?(?:\s+and\s+[Mm]anagers?)?)\b(?!\s+of\b)")
_APPOINT = re.compile(r"\bappoint(?:ed|ment)\b", re.I)
_CEASE = re.compile(r"\bceas(?:ed|ing|e)\b|\bcessation\b|\bretire(?:d|ment)?\b|\bvacat(?:ed|ion)\b|\breceivership\b[^.]{0,40}\b(?:ended|terminated|completed)\b", re.I)
_BODY_CO = re.compile(rf"(?:receivers?(?:\s+and\s+managers?)?\s+of\s+(?:all\s+)?(?:the\s+)?(?:(?:\w+\s+){{0,6}}?of\s+)?|receivership\s+of\s+)"
                      rf"(?P<co>[A-Z0-9][\w&'’.,()\-]*(?:\s+[A-Z0-9(][\w&'’.,()\-]*){{0,10}}?\s+{LQ._SUFFIX})\b")
_BY = re.compile(rf"appointed\b[^.]{{0,160}}?\bby\s+(?P<who>(?:[A-Z][\w&'’.\-]*\s+){{1,8}}?(?:{LQ._SUFFIX}|Bank|Corporation|Council))\b")


def recognise(code: str, title: str, text: str) -> list:
    return ["the Gazette's section ar (receivership)"] if code == CODE else []


def _action(head: str) -> str:
    a = bool(re.search(r"Appointment\s+of\s+(?:a\s+|the\s+)?Receivers?|appointed\s+(?:as\s+)?(?:joint\s+(?:and\s+several\s+)?)?receivers?", head, re.I))
    c = bool(_CEASE.search(head))
    return "appointment; ceased to act" if a and c else "appointment" if a else "ceased to act" if c else None


def _when(text: str, words) -> tuple:
    """(date, time) printed near the first of `words` that has one, else (None, None)."""
    for a in words.finditer(text):
        found = [(LQ._date(w.group("d")), LQ._clean(w.group("t") or "") or None)
                 for w in LQ._WHEN.finditer(text, max(0, a.start() - 200), min(len(text), a.end() + 200))
                 if not re.search(r"Dated\b[^.]{0,30}$", text[max(0, w.start() - 40):w.start()])]   # the Dated day is not the event
        found = [f for f in found if f[0]]
        if found:
            days = list(dict.fromkeys(f[0] for f in found))
            return (found[0] if len(days) == 1 else (None, None))
    return None, None


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(shape="notice", corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    r.action = _action(f"{title} {text[:500]}")
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    if r.action == "ceased to act":
        (r.event_on, r.event_at), r.event_basis = _when(text, _CEASE), "ceased to act"
    else:
        (r.event_on, r.event_at), r.event_basis = _when(text, _APPOINT), "appointment"
    if not r.event_on:
        r.event_basis = None
    by = _BY.search(text)
    r.by_whom = ("court" if re.search(r"order\s+of\s+the\s+(?:High\s+)?Court|by\s+the\s+(?:High\s+)?Court", text) else
                 LQ._clean(by.group("who")) if by else
                 "security instrument" if re.search(r"security\s+agreement|debenture|mortgage|deed\s+of\s+charge|charge\b", text, re.I)
                 else None)
    if LQ._BARE.match(title) or re.match(r"^\s*(?:Notice\s+of\s+)?(?:Appointment|Cessation|Ceasing|Retirement)\b", title, re.I):
        names = list(dict.fromkeys(LQ._clean(LQ._PAREN.sub(" ", m.group("co"))) for m in _BODY_CO.finditer(text)))
        left = []
    else:
        names, left = LQ.split_names(LQ._title_head(title, text))
    for x in left:
        r.unread.append(("title", "a part of the title that ends in no legal suffix"))
    kept = [n for n in names if (LQ._ENDS.search(n) or _BODY.search(n))
            and not any(p and not (LQ._ENDS.search(p) or _BODY.search(p)) for p in n.split(",")[:-1])]
    if len(kept) < len(names):
        r.unread.append(("subject", "a subject, or a part of one, with no legal suffix, perhaps a person's property: not read"))
    if not names:
        r.unread.append(("company", "the notice names no company the reader can find"))
    names = kept
    numbers = list(dict.fromkeys(LQ._NUMBER.findall(text)))
    r.companies = [Entry(i, n, number=numbers[0] if len(names) == 1 and len(numbers) == 1 else None)
                   for i, n in enumerate(names, 1)]
    r.people, bad = LQ._liquidators(text, _SIGNED)
    if not r.people and not bad:
        r.people = LQ._from_sentence(text)
    if bad:
        r.unread.append(bad)
    return r
