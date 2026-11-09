"""The news section of the one report (step 9.3 and 9.4; docs/research/step-9-news-search.md): the registers first, the
news after (Arthur, 9 November 2026). Once stage 1 has built the subject's records, they are turned into probes, the probes
are searched over the news index on the boxes (support/textindex, hard limit 10), and each article hit is judged against the
whole probe set by exact folded spans re-read in the article's own text, never by the index's word.

    news(conn, w, index, source=None, papers_past=None) -> {"news": [items], "news_results": [Papers Past results],
                                                            "news_stats": {...}}

`w` is stage1.walk1's result; `index` the news index's folder (None or missing: the section says the index is not built);
`source` reads the articles, their suppressed spans and the hop-1 companies' trading names (PubSource: the published views);
`papers_past` is a callable (query, limit=) -> registers/papers_past/search.search's result, its connection closed over by
the caller (a product may import only support/), or None.

The grades (9.4, Arthur: "4 is right"):

- **mention**: a name of the subject's and nothing else of its records. "An article that mentions this name"; never a link
  to the person.
- **connection**: a name and something from the subject's own records (a company, trading name, body, role, co-officer or
  place of record) inside its date window; or a distinctive company, trading name or body of the subject's own (hop 1),
  with or without the name: the article is connected by the register's link (the horse farm), carried as `via` and `rule`.
- **near**: a distinctive thing only stage 1's hop 2 reaches, with stage 1's reason; never confirmed.
- A co-officer, a role, a place or a thing too common to search alone never makes an item by itself.

What an item carries is what the legal position allows (docs/legal/positions/news-articles.md): the headline, publisher,
byline, date, link, at most two excerpts of at most SNIPPET characters, the grade and its evidence; never the text whole. An
excerpt over a suppressed span has the span replaced; an address-shaped excerpt is withheld and the item says so (hard
limits 15, 16). A suppressed row gives no probe; only the count of such rows is kept. Papers Past hits are search results,
never judged and never stored (hard limit 17). Nothing here writes anything: no row, no link (hard limit 14)."""
from __future__ import annotations

import re

from products.report import catalogue as cat
from products.report import rules
from support.textindex import read as tx
from support.textindex import write as txw

SNIPPET = tx.SNIPPET        # characters in one excerpt, at most (the legal position: 320)
EXCERPTS = 2                # excerpts an article, at most
CEILING = 2_000             # a thing probe with more hits than this is too common to search alone (to be measured)
PER_PROBE = 500             # the top hits read for one searched probe; the rest are counted, never silent
ROLE_NEAR = 80              # a role corroborates where it stands within this many characters of the subject's name
LISTED = {"connection": 100, "near": 20, "mention": 20}
GRADES = ("connection", "near", "mention")
FIELDS = ("headline", "text")
SUPPRESSED = "name suppressed"

#: one word that alone is not distinctive (a list to be measured on the copied corpus)
COMMON = {"new", "zealand", "nz", "national", "group", "holdings", "trust", "services", "society", "company", "the", "and",
          "of", "investments", "properties", "property", "farm", "farms", "trading", "international", "limited", "ltd", "inc",
          "incorporated", "labour", "green", "act", "first", "auckland", "wellington", "christchurch", "otago", "canterbury",
          "waikato", "northland", "southland", "board", "council", "association", "club", "foundation", "charitable", "global",
          "pacific", "south", "north", "east", "west", "central", "consulting", "management", "enterprises", "developments"}
LEGAL = re.compile(r"\s+(limited partnership|limited|ltd|incorporated|inc|tapui limited)$")
LEADING = {"hon", "honourable", "rt", "right", "dr", "mr", "mrs", "ms", "miss", "sir", "dame", "the", "rev", "prof"}
TRAILING = {"mp", "qc", "kc", "jp", "cnzm", "onzm", "mnzm", "qso", "dcnzm", "gnzm", "knzm", "dnzm", "obe", "mbe", "cbe"}
ORG_VIEWS = {"companies": "company", "limited_partnerships": "company", "societies": "body", "charities": "body",
             "parties": "body", "commerce_commission_parties": "company"}
BODY_COLS = ("party", "body")
ROLE_DEFAULT = {"directors": "director", "society_officers": "officer", "charity_officers": "officer"}
THING = ("company", "trading name", "body")

MENTION = "an article that mentions this name"
CONNECTION = "names {name} and {thing}, which the {register} register ties to the subject"
CONNECTION_LINK = "names {thing}, which the {register} register ties to the subject: connected by the register's link{named}"
NEAR = "names {thing}, which only stage 1's second hop reaches: {reason}"
NOT_BUILT = "the news index is not built yet"


# ── the probes ──────────────────────────────────────────────────────────────

def words_of(text: str) -> list:
    return tx.fold(text or "").split()


def name_forms(texts) -> list:
    """The folded forms of a person's printed names: honorifics and post-nominals gone, and first-and-last beside a form
    with middle names (articles drop them); a form of one word is no probe."""
    out = []
    for t in texts:
        ws = [" ".join(words_of(w)) for w in (t or "").split()]      # a hyphenated surname stays one name
        ws = [w for w in ws if w]
        while ws and ws[0] in LEADING:
            ws = ws[1:]
        while ws and ws[-1] in TRAILING:
            ws = ws[:-1]
        for f in (ws, ws[:1] + ws[-1:] if len(ws) > 2 else ws):
            s = " ".join(f)
            if len(f) >= 2 and s not in out:
                out.append(s)
    return out


def stem(text: str) -> str:
    """An organisation's name folded, its legal ending made optional (taken off)."""
    s = " ".join(words_of(text))
    while True:
        t = LEGAL.sub("", s)
        if t == s:
            return s
        s = t


def distinct(text: str) -> bool:
    """Two words, or one that is not a common word."""
    ws = text.split()
    return len(ws) >= 2 and not all(w in COMMON for w in ws) or (len(ws) == 1 and ws[0] not in COMMON and len(ws[0]) > 3)


def _window(dates) -> tuple | None:
    """(first year, last year) a dated thing corroborates in: a year before it began to a year after it ended; None when
    the row carries no dates (it then corroborates at any date)."""
    d = dates or {}
    start, end = d.get("start"), d.get("end")
    if not start and not end:
        return None
    return ((start.year - 1) if start else None, (end.year + 1) if end else None)


def _probe(text, kind, origin, hop, dates=None, shown=None, **extra) -> dict:
    p = {"text": text, "kind": kind, "origin_ref": origin["ref"], "register": origin.get("register") or "",
         "hop": hop, "window": _window(dates), "distinct": False, "searched": False, "shown": shown or text}
    p.update(extra)
    return p


def _row_names(it) -> list:
    v, r = cat.BY_NAME.get(it.get("view")), it.get("row") or {}
    texts = [it.get("title") or ""]
    for c in (v.names if v else ()):
        if r.get(c):
            texts.append(str(r[c]))
    for a, b in (("given_names", "surname"), ("first_name", "last_name")):
        if r.get(a) and r.get(b):
            texts.append(f"{r[a]} {r[b]}")
    return texts


def _hubs(w) -> set:
    out = {h.get("ref") for h in w.get("hubs") or [] if isinstance(h, dict)}
    for it in w.get("stage1") or []:
        if any(f.get("kind") == "stage-hub" for f in it.get("flags") or []):
            out.add(it["ref"])
    return out


def probes(w: dict, source=None) -> tuple:
    """(probes, stats) from the stage-1 walk `w`: names, companies, trading names, bodies, roles, co-officers and places of
    record, each with the row it came from. A suppressed row gives no probe."""
    out, suppressed = [], 0
    start = w.get("start") or {}
    members = [m for m in w.get("members") or [] if m.get("grade", "confirmed") == "confirmed"]
    if start and start.get("ref") not in {m.get("ref") for m in members}:
        members = [start] + members
    org_subject = start.get("kind") == "organisation"
    # names
    for m in members:
        if m.get("suppressed"):
            suppressed += 1
            continue
        if m.get("kind") not in ("person", "organisation", "figure"):
            continue
        forms = [stem(t) for t in _row_names(m)] if m.get("kind") == "organisation" else name_forms(_row_names(m))
        for f in dict.fromkeys(f for f in forms if len(f.split()) >= 2 or (org_subject and distinct(f))):
            out.append(_probe(f, "name", m, 0, shown=m.get("title")))
    names = {p["text"] for p in out}
    # organisations: the subject's own (hop 1), and stage 1's farther ones (hop 2, near)
    orgs = []
    for e in w.get("entities") or []:
        orgs.append((e, 1 if e.get("grade", "confirmed") == "confirmed" else 2))
    for it in w.get("stage1") or []:
        if it.get("kind") == "organisation":
            orgs.append((it, 1 if (it.get("stage_hop") or 1) <= 1 and it.get("grade", "confirmed") == "confirmed" else 2))
    best = {}
    for e, hop in orgs:                                 # each organisation once, at its nearest hop
        if e.get("ref") not in best or hop < best[e["ref"]][1]:
            best[e.get("ref")] = (e, hop)
    hop1_companies = []
    for e, hop in best.values():
        if e.get("suppressed"):
            suppressed += 1
            continue
        kind = ORG_VIEWS.get(e.get("view"), "body")
        extra = {"rule": e.get("rule"), "reason": e.get("reason")}
        texts = {stem(t) for t in _row_names(e)}
        for t in texts:
            out.append(_probe(t, kind, e, hop, e.get("dates"), shown=e.get("title"), **extra))
        r = e.get("row") or {}
        for t in re.split(r"[;|\n]", str(r.get("other_names") or "")) + [str(r.get("trading_as") or "")]:
            if t.strip():
                out.append(_probe(stem(t), "trading name", e, hop, e.get("dates"), shown=t.strip(), **extra))
        if hop == 1 and e.get("view") == "companies":
            hop1_companies.append(e)
    if source is not None and hop1_companies:
        by_ref = {e["ref"]: e for e in hop1_companies}
        for ref, ts in (source.trading_names([e["ref"] for e in hop1_companies]) or {}).items():
            e = by_ref.get(ref)
            for t in ts if e else ():
                out.append(_probe(stem(t), "trading name", e, 1, e.get("dates"), shown=t, rule=e.get("rule")))
    # bodies and roles on the subject's own rows
    for m in members:
        if m.get("suppressed"):
            continue
        r = m.get("row") or {}
        for c in BODY_COLS:
            if r.get(c):
                out.append(_probe(stem(str(r[c])), "body", m, 1, m.get("dates"), shown=str(r[c])))
        v = cat.BY_NAME.get(m.get("view"))
        role = (r.get(v.role) if v and v.role else None) or ROLE_DEFAULT.get(m.get("view"))
        if role and m.get("kind") == "person":
            shown = f"the role {str(role).lower()}" + (f" of {m['entity_title']}" if m.get("entity_title") else "")
            out.append(_probe(" ".join(words_of(str(role))), "role", m, 1, m.get("dates"), shown=shown,
                              body=m.get("entity_title")))
    # co-officers: the people on the subject's own organisations; a hub's people are not followed
    hubs = _hubs(w)
    for it in list(w.get("stage1") or []) + list(w.get("second") or []):
        if it.get("kind") != "person" or it.get("via") in hubs:
            continue
        if it.get("suppressed"):
            suppressed += 1
            continue
        for f in name_forms(_row_names(it)):
            if f not in names:
                out.append(_probe(f, "co-officer", it, it.get("stage_hop") or 2, it.get("dates"), shown=it.get("title")))
    # places of record: the registered office's town of a hop-1 company
    keys = {str((e.get("row") or {}).get("key")): e for e in hop1_companies}
    for b in ("roles", "office", "stage1"):
        for it in w.get(b) or []:
            r = it.get("row") or {}
            if it.get("view") != "company_addresses" or str(r.get("entity_key")) not in keys:
                continue
            if "registered" not in str(r.get("kind") or "registered").lower():
                continue
            town = town_of(r)
            if town:
                out.append(_probe(" ".join(words_of(town)), "place", it, 1, shown=town))
    # a thing whose text is one of the subject's own names is that name, not a thing; each probe once
    kept, seen = [], set()
    for p in out:
        if p["kind"] != "name" and p["text"] in names:
            continue
        k = (p["text"], p["kind"], p["origin_ref"])
        if p["text"] and k not in seen:
            seen.add(k)
            p["distinct"] = p["kind"] == "name" or (p["kind"] in THING and distinct(p["text"]))
            kept.append(p)
    stats = {"probes": {}, "suppressed_rows": suppressed}
    for p in kept:
        stats["probes"][p["kind"]] = stats["probes"].get(p["kind"], 0) + 1
    return kept, stats


def town_of(r: dict) -> str:
    """The town of a registered office: its last line with letters, postcode and country off; never a street line."""
    lines = [str(r.get(f"line_{i}") or "").strip() for i in range(1, 5)]
    for line in reversed([x for x in lines if x]):
        t = re.sub(r"\b\d{4}\b", "", line).strip(" ,")
        if t.lower() in ("new zealand", "nz", "") or re.search(r"\d", t) or rules.address_shaped(line):
            continue
        return t if len(t.split()) <= 3 else ""
    return ""


# ── the reading of an article ───────────────────────────────────────────────

def _pattern(text: str):
    return re.compile(r"(?<!\w)" + r"\s+".join(re.escape(w) for w in text.split()) + r"(?!\w)")


def evidence(probes_: list, art: dict) -> list:
    """Every probe found in the article's headline and text, by exact folded phrase, each at its offset in that field."""
    out = []
    folded = {f: tx.fold(art.get(f) or "") for f in FIELDS}
    for p in probes_:
        pat = p.setdefault("_re", _pattern(p["text"]))
        for f in FIELDS:
            for m in pat.finditer(folded[f]):
                out.append({"kind": p["kind"], "text": p["text"], "origin_ref": p["origin_ref"], "field": f,
                            "offset": m.start(), "end": m.end(), "_p": p})
    return out


def _year(art) -> int | None:
    d = art.get("published_on")
    return getattr(d, "year", None) or (int(str(d)[:4]) if d and str(d)[:4].isdigit() else None)


def in_window(p: dict, art: dict) -> bool:
    if p["window"] is None:
        return True
    y = _year(art)
    if y is None:
        return False
    lo, hi = p["window"]
    return (lo is None or y >= lo) and (hi is None or y <= hi)


def judge(probes_: list, art: dict) -> dict | None:
    """The grade of one article by 9.4, with its evidence; None when nothing in it makes an item."""
    ev = evidence(probes_, art)
    for e in ev:
        e["graded"] = in_window(e["_p"], art)
    named = [e for e in ev if e["kind"] == "name"]
    near_name = lambda e: any(n["field"] == e["field"] and abs(n["offset"] - e["offset"]) <= ROLE_NEAR for n in named)
    own = [e for e in ev if e["graded"] and e["_p"]["hop"] <= 1 and (
        e["kind"] in THING or e["kind"] == "place" or (e["kind"] == "role" and near_name(e)))]
    own += [e for e in ev if e["graded"] and e["kind"] == "co-officer"]
    linked = [e for e in own if e["kind"] in THING and e["_p"]["distinct"]]
    far = [e for e in ev if e["graded"] and e["kind"] in THING and e["_p"]["hop"] >= 2 and e["_p"]["distinct"]]
    grade = via = rule = None
    if linked:
        t = linked[0]
        grade, via, rule = "connection", t["origin_ref"], t["_p"].get("rule") or "the register's own row"
        reason = CONNECTION_LINK.format(thing=t["_p"]["shown"], register=t["_p"]["register"],
                                        named=f"; it also names {named[0]['_p']['shown']}" if named else
                                        "; the subject's name is not in the article")
        lead = t
    elif named and own:
        t = own[0]
        grade, via, rule = "connection", t["origin_ref"], t["_p"].get("rule") or "the register's own row"
        reason = CONNECTION.format(name=named[0]["_p"]["shown"], thing=t["_p"]["shown"], register=t["_p"]["register"])
        lead = named[0]
    elif far:
        t = far[0]
        grade, via, rule = "near", t["origin_ref"], t["_p"].get("rule") or "stage1"
        reason = NEAR.format(thing=t["_p"]["shown"], reason=t["_p"].get("reason") or "a connection through a person")
        lead = t
    elif named:
        grade, reason, lead = "mention", MENTION, named[0]
    else:
        return None
    return {"grade": grade, "reason": reason, "rule": rule, "via": via, "lead": lead, "evidence": ev}


# ── what an item may show ───────────────────────────────────────────────────

def excerpt(text: str, at: int, spans=()) -> dict:
    """At most SNIPPET characters of `text` around offset `at`, a suppressed span inside replaced; withheld (None text)
    where the window is address shaped."""
    text = text or ""
    start = max(0, at - SNIPPET // 3)
    end = min(len(text), start + SNIPPET)
    piece = text[start:end]
    for s, e in sorted(spans, reverse=True):
        if e > start and s < end:
            a, b = max(s, start) - start, min(e, end) - start
            piece = piece[:a] + SUPPRESSED + piece[b:]
    piece = re.sub(r"\s+", " ", piece).strip()[:SNIPPET]
    if rules.address_shaped(piece):
        return {"text": None, "offset": start, "withheld": "address shaped"}
    return {"text": piece, "offset": start}


def item(art: dict, j: dict, spans=()) -> dict:
    """One article as the report may show it (the legal position): never the text whole."""
    ev = sorted(j["evidence"], key=lambda e: (e is not j["lead"], e["field"] != "text", e["offset"]))
    ev = [j["lead"]] + [e for e in ev if e is not j["lead"]]
    excerpts, flags, covered = [], [], []
    for e in ev:
        if len(excerpts) + sum(1 for f in flags if f["kind"] == "excerpt-withheld") >= EXCERPTS:
            break
        if e["field"] != "text" or any(a <= e["offset"] < a + SNIPPET for a in covered):
            continue
        x = excerpt(art.get("text"), e["offset"], spans)
        covered.append(x["offset"])
        if x["text"] is None:
            flags.append({"kind": "excerpt-withheld", "text": "an excerpt was withheld: its text is address shaped"})
        else:
            excerpts.append(x)
    if not covered and art.get("text"):     # every hit in the headline: one window from the text's start
        x = excerpt(art["text"], 0, spans)
        if x["text"] is None:
            flags.append({"kind": "excerpt-withheld", "text": "an excerpt was withheld: its text is address shaped"})
        else:
            excerpts.append(x)
    return {"ref": art["ref"], "view": "news_articles", "kind": "article", "title": art.get("headline"),
            "publisher": art.get("publisher"), "byline": art.get("byline"), "date": art.get("published_on"),
            "url": art.get("url"), "excerpts": excerpts, "grade": j["grade"], "reason": j["reason"], "rule": j["rule"],
            "via": j["via"], "evidence": [{k: e[k] for k in ("kind", "text", "origin_ref", "field", "offset", "end", "graded")}
                                          for e in j["evidence"]],
            "also_at": [], "flags": flags}


# ── the search ──────────────────────────────────────────────────────────────

class PubSource:
    """The published views the section reads (read only): pub.news_articles, pub.news_suppressed_spans and the hop-1
    companies' trading names in pub.company_lookups."""

    def __init__(self, conn):
        self.conn = conn

    def _rows(self, sql, params):
        from products.report import db
        return db.rows(self.conn, sql, params)

    def articles(self, refs: list) -> dict:
        return {r["ref"]: r for r in self._rows(
            "select ref, publisher, published_on, headline, byline, url, text, text_sha256 from pub.news_articles "
            "where ref = any(%s)", (list(refs),))}

    def spans(self, refs: list) -> dict:
        out = {}
        for r in self._rows("select ref, start, \"end\" from pub.news_suppressed_spans where ref = any(%s)", (list(refs),)):
            out.setdefault(r["ref"], []).append((r["start"], r["end"]))
        return out

    def trading_names(self, company_refs: list) -> dict:
        keys = {r.rsplit("/", 1)[-1]: r for r in company_refs}
        out = {}
        for r in self._rows("select entity_key, trading_names from pub.company_lookups where entity_key = any(%s)",
                            (list(keys),)):
            names = r.get("trading_names") or []
            names = [n.get("name") if isinstance(n, dict) else n for n in names] if isinstance(names, list) else []
            out.setdefault(keys.get(str(r["entity_key"])), []).extend(n for n in names if n)
        return out


def _empty(stats, why=None) -> dict:
    stats = dict(stats, unavailable=why) if why else stats
    return {"news": [], "news_results": [], "news_stats": stats}


def news(conn, w: dict, index: str | None, source=None, papers_past=None) -> dict:
    """The news section: articles judged against the subject's records, Papers Past results beside, and the counts."""
    import os
    source = source if source is not None else PubSource(conn)
    ps, stats = probes(w, source)
    stats.update({"searched": 0, "too_common": 0, "too_common_things": [], "not_read": 0, "hits": 0, "not_in_view": 0,
                  "syndicated": 0, "no_item": 0, "by_grade": {g: {"listed": 0, "counted": 0} for g in GRADES}})
    stats["papers_past"] = papers(ps, papers_past) if papers_past else None
    results = stats["papers_past"].pop("items") if stats["papers_past"] else []
    if not index or not os.path.isdir(index):
        out = _empty(stats, NOT_BUILT)
        out["news_results"] = results
        return out
    hit = {}
    for p in ps:
        if not p["distinct"] or p["kind"] not in ("name",) + THING:
            continue
        found = tx.phrase(index, p["text"].split(), list(txw.NEWS.texts), limit=PER_PROBE, key=txw.NEWS.key)
        if p["kind"] != "name" and found["count"] > CEILING:
            stats["too_common"] += 1
            stats["too_common_things"].append(p["shown"])
            continue
        p["searched"] = True
        stats["searched"] += 1
        stats["not_read"] += max(0, found["count"] - len(found["keys"]))
        for k in found["keys"]:
            hit.setdefault(k, None)
    arts = source.articles(list(hit)) if hit else {}
    stats["not_in_view"] = sum(1 for k in hit if k not in arts)
    spans = source.spans(list(arts)) if arts else {}
    judged, by_text = [], {}
    for ref in hit:
        art = arts.get(ref)
        if art is None:
            continue
        j = judge(ps, art)
        if j is None:
            stats["no_item"] += 1
            continue
        it = item(art, j, spans.get(ref, ()))
        sha = art.get("text_sha256")
        first = by_text.get(sha) if sha else None
        if first is not None:                     # one article published in several places: shown once, "also at"
            stats["syndicated"] += 1
            if GRADES.index(it["grade"]) < GRADES.index(first["grade"]):
                it["also_at"] = first["also_at"] + [{"publisher": first["publisher"], "url": first["url"], "date": first["date"]}]
                judged[next(i for i, x in enumerate(judged) if x is first)] = by_text[sha] = it
            else:
                first["also_at"].append({"publisher": it["publisher"], "url": it["url"], "date": it["date"]})
            continue
        if sha:
            by_text[sha] = it
        judged.append(it)
    stats["hits"] = len(judged) + stats["no_item"] + stats["syndicated"]
    shown = []
    for g in GRADES:
        xs = sorted((it for it in judged if it["grade"] == g), key=lambda it: str(it["date"] or ""), reverse=True)
        shown += xs[:LISTED[g]]
        stats["by_grade"][g] = {"listed": min(len(xs), LISTED[g]), "counted": max(0, len(xs) - LISTED[g])}
    return {"news": shown, "news_results": results, "news_stats": stats}


def papers(ps: list, search) -> dict:
    """Papers Past (hard limit 17): the subject's names only, searched as phrases; each hit a search result with its
    window of text, never judged, never a connection, never stored."""
    items, seen, count, queries = [], set(), 0, 0
    for p in ps:
        if p["kind"] != "name":
            continue
        queries += 1
        got = search(f'"{p["text"]}"', limit=20)
        count += got.get("count") or 0
        for h in got.get("hits") or []:
            if not h.get("key") or h["key"] in seen:
                continue
            seen.add(h["key"])
            snip = re.sub(r"\s+", " ", str(h.get("snippet") or "")).strip(" …")[:SNIPPET]
            flags = []
            if rules.address_shaped(snip):
                snip, flags = None, [{"kind": "excerpt-withheld", "text": "an excerpt was withheld: its text is address shaped"}]
            items.append({"ref": f"papers_past:{h['key']}", "view": "papers_past_items", "kind": "result",
                          "title": h.get("title"), "publisher": h.get("paper"), "date": h.get("published_on"),
                          "url": h.get("url"), "excerpts": [{"text": snip, "offset": None}] if snip else [],
                          "grade": None, "flags": flags})
    return {"queries": queries, "count": count, "listed": len(items), "items": items}
