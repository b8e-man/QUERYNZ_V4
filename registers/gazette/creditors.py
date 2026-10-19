"""Notices to creditors (profile `gazette-creditors-notice`, every notice in
the Gazette's section `md`) and administrations (profile
`gazette-administration`, section `aa`), each recognised by its code, then
read. No model.

  md   a liquidator's or administrator's notice to a company's creditors:
       to prove their debts or claims by a day, of a meeting (and its day
       and time), of a watershed meeting in an administration, of a
       dividend; mostly "ACME LIMITED (in liquidation)" in the title
  aa   a voluntary administration: the administrators' appointment (Companies
       Act 1993 s 239I) with the first meeting, a watershed meeting, a deed of
       company arrangement, its end; "ACME LIMITED (administrators
       appointed)" in the title; the administrators signed as the
       liquidators are (liquidations.py)

The companies come from the title as the liquidation profile cuts them,
else from the body ("in the matter of ACME LIMITED"). The action is the
first of the profile's own phrases the heading or the opening holds; the
date is the one printed near it (not the Dated day). No address, telephone
or email is read.

    CreditorsNotice.recognise / .read      section md
    Administration.recognise / .read       section aa
"""
import re

from registers.gazette import liquidations as LQ
from registers.gazette import receiverships as RC
from registers.gazette.entries import Entry, Reading

_MATTER = re.compile(rf"(?:in\s+the\s+matter\s+of|liquidation\s+of|administration\s+of|administrators?\s+of|creditors\s+of)\s+(?:the\s+)?"
                     rf"(?P<co>[A-Z0-9][\w&'’.,()\-]*(?:\s+[A-Z0-9(][\w&'’.,()\-]*){{0,10}}?\s+{LQ._SUFFIX})\b")
_SIGNED = re.compile(r"(?P<names>(?<![A-Za-z])[A-Z](?:[^.:;|]|(?<=\b[A-Z])\.){1,150}?),\s*(?P<role>(?:Joint\s+(?:and\s+Several\s+)?)?"
                     r"[Aa]dministrators?)\b(?!\s+of\b)")


class _Reader:
    code, profile, why, actions, signed = None, None, None, (), None

    @classmethod
    def recognise(cls, code: str, title: str, text: str) -> list:
        return [cls.why] if code == cls.code else []

    @classmethod
    def read(cls, title: str, text: str) -> Reading:
        title, text = title or "", text or ""
        r = Reading(shape="notice", corrigendum=bool(LQ._CORRIGENDUM.match(title) or LQ._CORRIGENDUM.match(text[:40])))
        head = f"{title} {text[:600]}"
        hit = next(((a, p, basis) for a, p, basis in cls.actions if re.search(p, head, re.I)), None)
        if hit:
            r.action, pattern, basis = hit
            (r.event_on, r.event_at) = RC._when(text, re.compile(pattern, re.I))
            r.event_basis = basis if r.event_on else None
        sec = LQ._SECTION.search(text)
        r.statute = f"{sec.group('act')} s {re.sub(r'\s+', '', sec.group('s'))}" if sec else None
        d = LQ._DATED.search(text)
        r.dated_on = LQ._date(d.group("d")) if d else None
        if re.match(r"^\s*(?:Corrigendum\s*[—–\-:]*\s*)?(?:Notice|Appointment|Watershed|Meeting|Final)\b", title, re.I):
            names = list(dict.fromkeys(LQ._clean(LQ._PAREN.sub(" ", m.group("co"))) for m in _MATTER.finditer(text[:1500])))[:1]
            left = []
        else:
            names, left = LQ.split_names(LQ._title_head(title, text))
        for x in left:
            r.unread.append(("title", "a part of the title that ends in no legal suffix"))
        if not names:
            r.unread.append(("company", "the notice names no company the reader can find"))
        numbers = list(dict.fromkeys(LQ._NUMBER.findall(text)))
        r.companies = [Entry(i, n, number=numbers[0] if len(names) == 1 and len(numbers) == 1 else None)
                       for i, n in enumerate(names, 1)]
        if cls.signed is not None:
            r.people, bad = LQ._liquidators(text, cls.signed)
            if not r.people and not bad:
                r.people = LQ._from_sentence(text)
            if bad:
                r.unread.append(bad)
        return r


class CreditorsNotice(_Reader):
    code, profile = "md", "gazette-creditors-notice"
    why = "the Gazette's section md (notices to creditors)"
    #: (action, the phrase that names it and near which its date is printed, what that date is)
    actions = (("watershed meeting", r"watershed\s+meeting", "meeting"),
               ("meeting of creditors", r"meeting\s+of\s+(?:the\s+)?creditors|creditors['’]?\s+meeting", "meeting"),
               ("dividend", r"\bdividend", "dividend"),
               ("creditors to prove", r"prove\s+(?:their\s+)?(?:debts?|claims?)|claims?\s+(?:must|are\s+to)\s+be\s+(?:made|lodged|received)|"
                                      r"fix(?:es|ed)?\s+the\s+\d|as\s+the\s+day\s+on\s+or\s+before", "claims by"),
               ("notice to creditors", r"notice\s+to\s+creditors", None))


class Administration(_Reader):
    code, profile = "aa", "gazette-administration"
    why = "the Gazette's section aa (voluntary administration)"
    signed = _SIGNED
    actions = (("appointment of administrators", r"appointment\s+of\s+(?:an?\s+)?administrators?|appointed\s+(?:as\s+)?(?:joint\s+(?:and\s+several\s+)?)?administrators?", "appointment"),
               ("watershed meeting", r"watershed\s+meeting", "meeting"),
               ("deed of company arrangement", r"deed\s+of\s+company\s+arrangement", None),
               ("administration ended", r"administration\s+(?:has\s+)?(?:ended|terminated)|ceased\s+to\s+(?:be\s+)?(?:under\s+)?administration", "ended"),
               ("meeting of creditors", r"meeting\s+of\s+(?:the\s+)?creditors", "meeting"))
