"""Advertisements of an application to the High Court to put a company into
liquidation (profile `gazette-winding-up-application`): every notice in the
Gazette's section `aw`, recognised by that code, then read. No model.

One template since 2000, reworded about 2011 ("This document notifies you
that:"): an application for putting <COMPANY> into liquidation was filed
in the High Court at <place> on <date>; its reference number
(CIV-2014-404-1234); it is to be heard at <place> on <date> at <time>; and
"The plaintiff is <NAME>, whose address for service is …". A few apply to
remove a liquidator, or are made by the Registrar or the Financial Markets
Authority. The plaintiff is read up to "whose" or "of" and no further: its
address for service is never read.

    recognise(code, title, text)    the reasons, empty if not this profile
    read(title, text)               Reading(companies, action, court, reference, filed_on, event_on, party, …, unread)
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette.entries import Entry, Reading

CODE = "aw"
_DAY = LQ._DAY
_CO = rf"[A-Z0-9(][^;]{{0,200}}?{LQ._SUFFIX}\b\.?(?:\s*\([^()]*\))*"
#: "putting X into liquidation" bounds the name on both sides, so a name with no legal suffix (a partnership,
#: an overseas company) is taken there; elsewhere a name must end in its suffix
_PUTTING = re.compile(rf"(?:putting|to\s+put|to\s+place)\s+(?P<co>[A-Z0-9(“\"][^;]{{1,200}}?)\s+(?:in)?to\s+liquidation"
                      rf"|(?:removal|replacement)\s+of\s+(?:a\s+|the\s+)?liquidators?\s+(?:of|for)\s+(?P<co3>{_CO})(?=\s*(?:by\b|was\b|has\b|is\b|,|\.|\(|$))"
                      rf"|(?:putting\s+into\s+liquidation|for\s+the\s+liquidation\s+of|to\s+liquidate|winding[\s-]+up\s+of|to\s+wind\s+up)\s+(?P<co2>{_CO})(?=\s*(?:by\b|was\b|has\b|is\b|,|\.|\(|$))", re.S)
#: within one sentence: a stop inside a name ("C.G.S Limited") is followed by no space
_SAME = r"(?:[^.]|\.(?=\S))"
_FILED = re.compile(rf"(?:[Oo]n|[Dd]ated)\s+(?:the\s+)?(?P<d>{_DAY}){_SAME}{{0,200}}?\bfiled\b|\bfiled\b{_SAME}{{0,120}}?\bon\s+(?:the\s+)?(?P<d2>{_DAY})")
_COURT = re.compile(r"\bfiled\s+(?:in|by|with)\s+the\s+(?P<c>High\s+Court(?:\s+at\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)?)")
_REF = re.compile(r"\b(CIV[-\s]?\d{4}[-\s]?\d{3}[-\s]?\d{1,6}(?!\d)|M\.?\s*(?:No\.?\s*)?\d{1,5}(?:-[A-Z]{1,3})?/\d{2,4}(?!\d))")
_HEARD = re.compile(rf"\bheard\b[^.]{{0,120}}?\bon\s+(?:[A-Z][a-z]+day,?\s+)?(?:the\s+)?(?P<d>{_DAY})(?:\s*,?\s*at\s*(?P<t>{LQ._TIME}))?")
_PLAINTIFF = re.compile(r"\b[Tt]he\s+(?:plaintiffs?|applicants?)(?:['’]s?\s+names?)?\s+(?:is|are)\s+(?P<p>.{2,160}?)(?=\s*(?:,?\s*whose|,\s*of\s|,?\s*and\s+(?:its|their|his|her)\s+address|address|\(|$))")


def recognise(code: str, title: str, text: str) -> list:
    return ["the Gazette's section aw (application to put a company into liquidation)"] if code == CODE else []


def _action(title: str, text: str) -> str:
    t = f"{title} {text[:400]}"
    if re.search(r"removal\s+of\s+(?:the\s+)?liquidator|remove\s+(?:the\s+)?liquidator", t, re.I):
        return "application to remove a liquidator"
    if re.search(r"into\s+liquidation|liquidat|wind(?:ing)?[\s-]+up", t, re.I):
        return "application to put into liquidation"
    return None


def read(title: str, text: str) -> Reading:
    title, text = title or "", text or ""
    r = Reading(shape="notice", corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
    r.action = _action(title, text)
    m = _PUTTING.search(text)
    names = []
    if m:
        names = [LQ._clean(LQ._PAREN.sub(" ", m.group("co") or m.group("co2") or m.group("co3")))]
    elif not re.match(r"^\s*(?:Corrigendum\s*[—–\-:]*\s*)?(?:Advertisement|Notice|Application)\b", title, re.I):
        names, left = LQ.split_names(title)
        for x in left:
            r.unread.append(("title", "a part of the title that ends in no legal suffix"))
    if not names:
        r.unread.append(("company", "the notice names no company the reader can find"))
    numbers = list(dict.fromkeys(LQ._NUMBER.findall(text)))
    r.companies = [Entry(i, n, number=numbers[0] if len(names) == 1 and len(numbers) == 1 else None)
                   for i, n in enumerate(names, 1)]
    f = _FILED.search(text)
    r.filed_on = LQ._date(f.group("d") or f.group("d2")) if f else None
    c = _COURT.search(text)
    r.court = LQ._clean(c.group("c")) if c else None
    ref = _REF.search(text)
    r.reference = re.sub(r"\s", "-", ref.group(1)) if ref else None
    h = _HEARD.search(text)
    if h:
        r.event_on, r.event_at, r.event_basis = LQ._date(h.group("d")), LQ._clean(h.group("t") or "") or None, "hearing"
    p = _PLAINTIFF.search(text)
    if p:
        party = LQ._clean(p.group("p"))
        if len(party) > 120 or re.search(r"\d{2,}|\b(?:Street|Road|Box|Level)\b", party):
            r.unread.append(("plaintiff", "the plaintiff's name runs into an address: not read"))
        else:
            r.party = party
    sec = LQ._SECTION.search(text)
    r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
    d = LQ._DATED.search(text)
    r.dated_on = LQ._date(d.group("d")) if d else None
    return r
