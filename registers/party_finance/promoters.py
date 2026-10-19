"""The register of promoters, read (contract: the reader; profile
`ec-promoter-register-page`, proposed in `profile-proposed.jsonl`).

A promoter is anyone other than a party or a candidate who pays for
election advertising over the threshold and registers with the Commission
(Electoral Act 1993, Part 6AA). The register is a page, not a file: one
accordion block per promoter, its name on the block's button.

  2020   each field a `promoter__field__label` / `promoter__field__value` pair:
         Email, Address, Authorised representative, People in a position
         comparable with director, Trustees, Registered as a promoter for,
         Registered on
  2023   each field a paragraph led by its bold label; a paragraph with no
         label continues the field before it (one union prints three
         branches' addresses that way)

Published: the promoter's name, its authorised representative, the people
in a position comparable with a director and its trustees (the register's
own public roles), what it registered for, and the day it registered.
Never published: the email and the address. A promoter can be one person,
and the address the register prints for a person can be a home, so every
contact line goes to the lane's private schema, and so does any field with
a label this reader has not met (hard limit 15). Deterministic: a regex
over captured HTML, no model.

    read(html_bytes) -> Reading(promoters, skipped)
"""
import html as _html
import re
from dataclasses import dataclass, field

from keys.dates import filed_date

READER = "registers.party_finance.promoters 1"
MODEL = "html"
PROFILE = "ec-promoter-register-page"

_BUTTON = re.compile(r'<button class="accordion__title"[^>]*>(.*?)</button>', re.S)
_FIELD_2020 = re.compile(r'<div class="promoter__field__label">(.*?)</div>\s*'
                         r'<div class="promoter__field__value">(.*?)</div>\s*</div>', re.S)
_PARA = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)
_LEAD = re.compile(r"^\s*<strong>(.*?)</strong>", re.S | re.I)

#: label → field. The public fields; everything else is private.
PUBLIC = {
    "authorised representative": "authorised_representative",
    "people in a position comparable with director": "comparable_with_director",
    "trustees": "trustees",
    "registered as a promoter for": "registered_for",
    "registered on": "registered_on",
}
PRIVATE = {"email": "email", "address": "address"}
PEOPLE = ("authorised_representative", "comparable_with_director", "trustees")
NONE_WORDS = {"", "n/a", "na", "nil", "none", "-", "not applicable"}


@dataclass
class Promoter:
    ordinal: int
    name: str
    public: dict = field(default_factory=dict)       # field → [lines]
    private: dict = field(default_factory=dict)      # label → [lines]; never published
    registered_on: str = None                        # ISO, as filed
    unknown: list = field(default_factory=list)      # labels not met before (their values are private)


@dataclass
class Reading:
    promoters: list = field(default_factory=list)
    skipped: list = field(default_factory=list)


def lines(fragment: str) -> list:
    t = re.sub(r"<br\s*/?>", "\n", fragment or "", flags=re.I)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t)).replace("\xa0", " ")
    return [" ".join(x.split()) for x in t.split("\n") if x.strip()]


def label_key(raw: str) -> str:
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", raw or "")).replace("\xa0", " ").replace(":", " ").split()).lower()


def _fields_2020(body: str) -> list:
    return [(label_key(lab), lines(val)) for lab, val in _FIELD_2020.findall(body)]


def _fields_2023(body: str) -> list:
    out = []
    for p in _PARA.findall(body):
        m = _LEAD.match(p)
        lab = label_key(m.group(1)) if m else ""
        rest = p[m.end():] if m else p
        if lab:
            out.append((lab, lines(rest)))
        elif out:
            out[-1][1].extend(lines(p))                       # a paragraph with no label continues the field before
        else:
            out.append(("", lines(p)))
    return out


def people(values: list) -> tuple:
    """(names, statements). The 2023 page prints one person a line, the 2020
    page a comma list. A line of only 'N/A' or the like is no one; a line
    carrying a figure ('37 religious leaders (please contact the
    Commission…)') is the register's statement, kept as printed, never a
    name."""
    out, said = [], []
    for v in values:
        if re.search(r"\d", v):
            said.append(v)
            continue
        for part in re.split(r"\s*[;,]\s*", v):
            if part.strip().lower() not in NONE_WORDS:
                out.append(part.strip())
    return out, said


def blocks(page: str) -> list:
    """[(button html, body html)]: a block's body runs from its button to the next."""
    found = list(_BUTTON.finditer(page))
    return [(m.group(1), page[m.end():(found[i + 1].start() if i + 1 < len(found) else len(page))])
            for i, m in enumerate(found)]


def read(data: bytes) -> Reading:
    page = data.decode("utf-8", errors="replace")
    out = Reading()
    shape = _fields_2020 if "promoter__field__label" in page else _fields_2023
    for n, (button, body) in enumerate(blocks(page), 1):
        name = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", button)).split())
        if not name:
            out.skipped.append((n, f"block {n}: no promoter named"))
            continue
        p = Promoter(n, name)
        for lab, vals in shape(body):
            if lab in PUBLIC:
                p.public.setdefault(PUBLIC[lab], []).extend(vals)
            elif lab in PRIVATE:
                p.private.setdefault(PRIVATE[lab], []).extend(vals)
            else:
                p.unknown.append(lab or "(no label)")
                p.private.setdefault(lab or "(no label)", []).extend(vals)
        on = " ".join(p.public.get("registered_on") or [])
        when = filed_date(on) if on else None
        p.registered_on = when.isoformat() if when else None
        if p.registered_on is None:
            out.skipped.append((n, f"block {n} ({name!r}): no readable 'Registered on' date"))
            continue
        out.promoters.append(p)
    return out


def blocks_seen(data: bytes) -> int:
    return len(_BUTTON.findall(data.decode("utf-8", errors="replace")))
