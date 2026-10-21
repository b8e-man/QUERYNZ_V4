"""The reading: one captured party page → the board roles it declares.

A reading runs FROM the document profile `party-website-board-page`
(`profile-proposed.jsonl` until the integrator appends it): the profile's
`config.shapes` say, for each party site and each era of its markup, how
the board is recognised (the page's own address, the heading that opens the
board's section, the markup of a name and of a role, what closes the
section) and how its lines pair. This module holds no site's shape; it
executes the profile's. Nothing here calls a model, so the fast tier runs
the same code.

A page is recognised by the first shape whose address rule matches and
whose opening heading is on the page (with its markup, where the shape
names one), and whose section holds the markup the shape `requires`, where
it names some (two themes of one site under one heading). Then the section is read in one of three forms:

  pair    a name line (by its markup) and the role lines after it, before the next name
          (several are kept in order, joined by '; ': 'Caucus Representative; Chief Whip');
          a name with no role line takes the shape's `role_default` (the role the heading
          declares for everyone listed under it) or is set aside
  cells   a table row: the role in one cell, the name in another
  line    one line holds both, by the shape's pattern (`Name (Role)`, `Role: Name`,
          `Role Name` with the site's role words), or a name alone under a heading that
          declares the role (`role_default`)

A shape may name a layout the profile knows and does not read (`drop`: a
board heading whose names and roles the markup does not pair): its pages
are drop-notes with that reason, not guesses.

What is not a person is set aside, never guessed into a row: a line the
profile's name rule refuses (one word, a sentence, a heading), a declared
vacancy, a name that repeats its role, two names where the shape does not
say how to split them. A page no shape recognises is a drop-note with its
reason: no shape for the site, no board heading on the page, a theme's
placeholder people, or bytes that are not a page. Contact lines (email,
telephone) are never read into a row and never logged.

    profile()                    the profile record this reading runs from
    read(data, capture, …)       Reading: rows, set_aside, status, shape
"""
import datetime as dt
import os
import re
from dataclasses import dataclass, field

from support import profiles
from registers.party_boards import page

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "party-website-board-page"
READER = "registers.party_boards.read 1"
TIER = "declared"

_HONORIFIC = re.compile(r"^(?:(?:the\s+)?(?:rt\.?\s+hon\.?|right\s+honourable|hon\.?|dr\.?|sir|dame|mr\.?|mrs\.?|ms\.?|miss|"
                        r"prof\.?|professor|rev\.?)\s+)+", re.I)
_POSTNOMINAL = re.compile(r"(?:\s*,?\s*\b(?:QSO|QSM|ONZM|CNZM|MNZM|DNZM|KNZM|GNZM|NZOM|ONZ|JP|KC|QC|MP|PhD|OBE|MBE|CBE|"
                          r"KNZ|DCNZM|LLB|BA|BCom|MBA)\b\.?)+\s*$")
_BRACKET = re.compile(r"\s*\(([^()]*)\)\s*$")
_TOKEN = re.compile(r"^(?:[A-ZĀĒĪŌŪ][A-Za-zĀĒĪŌŪāēīōū'’\-]*\.?|[A-Z]\.|(?:de|da|di|du|van|von|der|den|te|ki|la|le|al|bin|o'|mac)"
                    r"|\([A-ZĀĒĪŌŪ][A-Za-zāēīōū'’\-]*\))$")
_NOT_A_NAME = re.compile(r"\b(?:board|members?|president|secretary|treasurer|chair\w*|council|party|executive|committee|"
                         r"leader\w*|team|contact|email|read|more|region|national|candidates?|vacant|policy|join|donate|"
                         r"about|news|officers?|governance|directors?|trustees?|representatives?|whip|minister)\b", re.I)
_VACANT = re.compile(r"^(?:vacant|vacancy|tbc|tba|to be (?:confirmed|appointed|announced|elected))\.?$", re.I)
_CONTACT = re.compile(r"@|\[email|email protected|\d{3}[\s-]?\d{3,}|^(?:https?:|www\.)|^(?:mobile|phone|tel|email)\s*:", re.I)
_SENTENCE = re.compile(r"[.!?]\s*$|\b(?:is|was|has|have|the|and his|and her|with|for|who|of the)\b")


@dataclass
class Reading:
    status: str                          # read | board section, no names | drop-note
    shape: str = None
    reason: str = None                   # for a drop-note, why
    rows: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)       # (place, reason)


def profile() -> dict:
    """The ledger's newest version; until the integrator appends it, the
    lane's proposed line (merge request party-boards-1)."""
    got = [p for p in (profiles.profile(PROFILE), profiles.profile(PROFILE, path=PROPOSED)) if p]
    if not got:
        raise LookupError(f"no document profile {PROFILE}")
    return max(got, key=lambda p: int(p["version"]))


def _rx(s: str):
    return re.compile(s, re.I)


def _has(line, marks) -> bool:
    return all(line.has(m) for m in (marks or []))


def split_name(text: str) -> tuple:
    """(name, qualifier): the name as a person is called, without an
    honorific, post-nominals or a trailing bracket ('(Acting)', '(Auckland)');
    the bracket is kept as the qualifier. The declared text is kept whole
    beside it in every row."""
    s = re.sub(r"\s+", " ", text).strip().rstrip(",;:").strip()
    qualifier = None
    m = _BRACKET.search(s)
    if m and s[:m.start()].strip():
        qualifier, s = m.group(1).strip(), s[:m.start()].strip()
    s = _HONORIFIC.sub("", s)
    s = _POSTNOMINAL.sub("", s).strip().rstrip(",").strip()
    return s, qualifier


def why_not_a_name(text: str):
    """None for a person's name as the profile defines one (two to six
    words, each capitalised or a name particle, no digits, no contact, no
    role or heading word); else why not."""
    name, _ = split_name(text)
    if _VACANT.match(text.strip()):
        return "declared vacant"
    if _CONTACT.search(text):
        return "a contact line, not a name"
    if any(ch.isdigit() for ch in name):
        return "not a name: it has digits"
    toks = name.split()
    if not 2 <= len(toks) <= 6 or len(name) > 60:
        return f"not a name: {len(toks)} word(s)"
    if _NOT_A_NAME.search(name):
        return "not a name: a role or heading word"
    if _SENTENCE.search(name) or not all(_TOKEN.match(t) for t in toks):
        return "not a name: not every word is a capitalised name word"
    return None


def _section(lines: list, shape: dict):
    """(opener line, [lines of the section]) or None: from the first line the
    opener matches (with its markup) to the line before the first that
    closes it."""
    opens = _rx(shape["opens"])
    start = next((ln for ln in lines if opens.match(ln.text) and _has(ln, shape.get("opens_mark"))), None)
    if start is None:
        return None
    closes = [_rx(c) for c in shape.get("closes", [])]
    out = []
    for ln in lines[start.n + 1:]:
        if opens.match(ln.text):
            continue                    # the heading printed again (a breadcrumb, a banner, the section's own h2)
        if any(c.match(ln.text) for c in closes) or (shape.get("closes_mark") and _has(ln, shape["closes_mark"])):
            break
        out.append(ln)
    return start, out[:shape.get("max_lines", 400)]


def _pairs(sec: list, shape: dict) -> list:
    """[(line n, name text, role text or None, role basis)]."""
    out = []
    names = [ln for ln in sec if _has(ln, shape["name"])]
    for i, ln in enumerate(names):
        nxt = names[i + 1].n if i + 1 < len(names) else 10 ** 9
        roles = [r.text for r in sec if ln.n < r.n < nxt and _has(r, shape["role"]) and not _CONTACT.search(r.text)]
        role = "; ".join(roles) if roles else None
        out.append((ln.n, ln.text, role, "stated" if role else None))
    return out


def _cells(sec: list, shape: dict) -> list:
    rows = {}
    for ln in sec:
        if ln.row >= 0:
            rows.setdefault(ln.row, []).append(ln)
    out = []
    ri, ni = shape["cells"]
    for _, cells in sorted(rows.items()):
        if len(cells) <= max(ri, ni):
            continue
        out.append((cells[ni].n, cells[ni].text, cells[ri].text, "stated"))
    return out


def _lines(sec: list, shape: dict) -> list:
    pat = _rx(shape["pattern"])
    out = []
    for ln in sec:
        if not _has(ln, shape.get("line_mark")):
            continue
        m = pat.match(ln.text)
        if not m:
            continue
        g = m.groupdict()
        out.append((ln.n, g["name"].strip(), (g.get("role") or "").strip() or None, "stated" if g.get("role") else None))
    return out


FORMS = {"pair": _pairs, "cells": _cells, "line": _lines}


def shapes(prof: dict = None) -> list:
    return (prof or profile())["config"]["shapes"]


def recognise(lines: list, url: str, prof: dict = None):
    """(shape, (opener, section)) or (None, why)."""
    mine = [s for s in shapes(prof) if _rx(s["url"]).search(url)]
    if not mine:
        return None, "no shape for this page's address"
    for s in mine:
        sec = _section(lines, s)
        if sec is not None and (not s.get("requires") or any(_has(ln, s["requires"]) for ln in sec[1])):
            return s, sec
    return None, "no board heading the profile knows on the page"


def read(data: bytes, document: str, capture, loaded_at: str = None, prof: dict = None) -> Reading:
    """capture: the first capture of these bytes (capture.Capture)."""
    prof = prof or profile()
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        lines = page.lines(data)
    except page.Undecodable as e:
        return Reading("drop-note", reason=str(e))
    for refuse in prof["config"].get("refuse", []):
        if any(_rx(refuse["pattern"]).search(ln.text) for ln in lines):
            return Reading("drop-note", reason=refuse["reason"])
    shape, got = recognise(lines, capture.url, prof)
    if shape is None:
        return Reading("drop-note", reason=got)
    opener, sec = got
    if shape.get("drop"):
        return Reading("drop-note", shape=shape["id"], reason=shape["drop"])
    out = Reading("read", shape=shape["id"])
    seen = set()
    for n, name_text, role, basis in FORMS[shape["form"]](sec, shape):
        place = f"line {n}"
        if role is None and shape.get("role_default"):
            role, basis = shape["role_default"], "heading"
        if role is None:
            out.set_aside.append((place, "a name with no role beside it, and no role the heading declares"))
            continue
        people = [name_text]
        if shape.get("split") and re.search(shape["split"], name_text):
            people = [p for p in re.split(shape["split"], name_text) if p.strip()]
        for k, person in enumerate(people):
            pl = place if len(people) == 1 else f"{place} name {k + 1}"
            why = why_not_a_name(person)
            if why is None and split_name(person)[0].lower() == split_name(role)[0].lower():
                why = "the name repeats the role line"
            if why is None and len(role) > 80:
                why = "the role is longer than a role"
            if why:
                out.set_aside.append((pl, why))
                continue
            name, qualifier = split_name(person)
            if (name.lower(), role.lower()) in seen:
                out.set_aside.append((pl, "the same name and role again on the page"))
                continue
            seen.add((name.lower(), role.lower()))
            out.rows.append({
                "key": f"{document}/{shape['id']}/{pl.replace(' ', '-')}", "document": document, "page": 1,
                "place": pl, "shape": shape["id"], "section": opener.text,
                "name_as_declared": re.sub(r"\s+", " ", person).strip(), "name": name, "qualifier": qualifier,
                "role": re.sub(r"\s+", " ", role).strip().rstrip(":").strip(), "role_basis": basis,
                "tier": TIER, "read_from": "text", "reader": READER, "profile": PROFILE,
                "profile_version": int(prof["version"]), "loaded_at": loaded_at})
    if not out.rows:
        out.status = "board section, no names"
    return out
