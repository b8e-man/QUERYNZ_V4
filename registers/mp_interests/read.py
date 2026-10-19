"""The reading: each edition through its document profile (profiles before
readers), page by page from its text layer (`support.docread.pages`, the
reader contract's "text layer first"), parsed by `parse.py` into register
rows under the row contract, or catch-log lines saying why not. No model is
called: every held edition has a text layer on every page that carries a
member (measured 20 October 2026).

Two checks run on every edition before anything is published:

  verbatim       every declaration's text, whitespace folded, is found in
                 the edition's own text: a parse that invents, truncates or
                 glues a line fails here, and its declaration is set aside
  the numbering  the edition's introduction lists its categories by number
                 and heading; every number a member's return files under
                 must carry, by its heading, the category the introduction
                 gives that number (`check.py`; the lane's outside check)

A declaration filed under "Real property" can place a member's home (a
suburb, a town): its text is held in the private schema, keyed by the row,
and the published row carries the category and the fact it is withheld
(hard limit 15; the decision queue asks whether the property's kind may be
shown).

    profile(slug)                           the current version, shared ledger or proposed
    edition_rows(pages, sha, year, at)      -> {edition, members, declarations, private, numbering, set_aside}
"""
import datetime as dt
import os

from keys import names, parties
from support import profiles
from registers.mp_interests import parse

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "parliament-pecuniary-interests-summary"
READER = "support.docread 1: text-layer (pdftotext -layout, per page)"


def profile(slug: str = PROFILE) -> dict:
    found = [p for p in (profiles.profile(slug), profiles.profile(slug, PROPOSED)) if p]
    if not found:
        raise LookupError(f"no document profile {slug}: profiles come before readers")
    return max(found, key=lambda p: int(p["version"]))


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _fold(s: str) -> str:
    return " ".join((s or "").split())


def edition_rows(pages: dict, sha256: str, year_label: int = None, loaded_at: str = None) -> dict:
    """pages: 1-based page → text layer. Returns the edition's rows and catch-log lines."""
    at = loaded_at or now()
    prof = profile()
    stamp = {"reader": READER, "profile": prof["slug"], "profile_version": int(prof["version"]), "read_from": "text",
             "loaded_at": at}
    out = {"edition": None, "members": [], "declarations": [], "private": [], "numbering": [], "set_aside": []}
    ed = parse.edition(pages)
    for p, i, stage, why in ed.set_aside:
        out["set_aside"].append((f"{sha256}/p{p}/l{i}" if p else sha256, stage, why))
    if not ed.members:
        return out
    whole = _fold(" ".join(pages[p] or "" for p in sorted(pages)))
    thin = [p for p in sorted(pages) if len((pages[p] or "").strip()) < 80]
    first, last = ed.members[0].page, (ed.annex_at[0] if ed.annex_at else max(pages))
    for p in thin:
        if first <= p <= last:
            out["set_aside"].append((f"{sha256}/p{p}", "page", f"page {p}, among the members, has no usable text "
                                                                f"layer; it needs the page reader and was not read"))
    out["edition"] = {
        "key": sha256, "document": sha256, "page": 1, "place": "title page", "year_label": year_label,
        "as_at": ed.as_at.isoformat() if ed.as_at else None, "as_at_printed": ed.as_at_printed,
        "categories": " | ".join(f"{n} {h} [{s}]" for n, (h, s) in sorted(ed.categories.items(), key=lambda x: int(x[0]))),
        "members": len(ed.members), "declarations": len(ed.declarations), "wrapped": ed.wrapped,
        "annex_page": ed.annex_at[0] if ed.annex_at else None, **stamp}
    mkeys = []
    for m in ed.members:
        key = f"{sha256}/p{m.page}/l{m.line}"
        mkeys.append(key)
        party, basis = parties.party_name(m.party) if m.party else (None, "not stated")
        out["members"].append({
            "key": key, "edition": sha256, "document": sha256, "page": m.page, "place": f"page {m.page}, line {m.line}",
            "as_at": out["edition"]["as_at"], "printed": m.printed, "member": m.name,
            "name": names.person_name(m.name).display, "party_label": m.party, "party": party, "party_basis": basis,
            "electorate": m.electorate, "statement": m.statement, **stamp})
    for d in ed.declarations:
        key = f"{sha256}/p{d.page}/l{d.line}"
        if _fold(d.text) not in whole:
            out["set_aside"].append((key, "verbatim", f"page {d.page}, line {d.line}: the declaration as read is not in "
                                                      f"the edition's own text ({d.text[:60]!r}); not published"))
            continue
        private = d.category in parse.PRIVATE_CATEGORIES
        out["declarations"].append({
            "key": key, "edition": sha256, "member": mkeys[d.member], "document": sha256, "page": d.page,
            "place": f"page {d.page}, line {d.line}", "as_at": out["edition"]["as_at"], "number_printed": d.number,
            "heading": d.heading, "category": d.category, "text": None if private else d.text, "withheld": private,
            **stamp})
        if private:
            out["private"].append({"key": key, "text": d.text})
    body = {}
    for d in ed.declarations:
        body.setdefault(d.number, set()).add((d.heading, d.category))
    for n in sorted(set(body) | set(ed.categories), key=int):
        intro_h, intro_c = ed.categories.get(n, (None, None))
        cats = {c for _, c in body.get(n, ())}
        out["numbering"].append({
            "edition": sha256, "number": int(n), "intro_heading": intro_h, "intro_category": intro_c,
            "body_headings": " | ".join(sorted(h for h, _ in body.get(n, ()))) or None,
            "body_category": next(iter(cats)) if len(cats) == 1 else (" | ".join(sorted(map(str, cats))) or None),
            "agrees": (not cats) or (cats == {intro_c} and intro_c is not None)})
    return out
