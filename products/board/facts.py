"""What the rows say about the entity (ruling 117): the dossier folds the
rows that say the same thing into one entry and states it as a fact about
the person or body, never the shape of the database.

A row says a fact: what it makes the entity (a noun, or the role in the
register's words), the body a role relation names (a company, a charity),
where (an electorate, an election, a party), and an event (listed,
removed). Rows equal on those say the same thing and fold: a director of
one company across filings is one entry, a director and shareholder of it
one entry with both roles, five Gazette celebrant lists one entry. The
fold is by what the row says (`SAYS`, a line per view, data), never by
view: a view no line names says its own title, and folds with nothing.

The entry is one sentence ("Trustee of Keystone New Zealand Property
Education Trust since 11 March 2025"; "Candidate, Whangārei, 2026 General
Election"); the dates, roles and counts go in a small line under it, and
where it came from in one more (the register, each row's document). No
register name, view name or row count is in the sentence.

A suppressed row never reaches here (the dossier leaves it out before):
it is neither counted nor named (hard limit 16). Pure functions over rows
already read, but `refer`, one query per far view by key."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

from products.board import catalogue as cat
from products.board import db, panes


@dataclass(frozen=True)
class Says:
    """What one view's row says about the entity it names. A lane's line, as data."""
    noun: str = ""                  # what the row makes the entity ("director"); empty: the role column's value, else the title
    role: str = ""                  # a column holding the role in the register's words ("Trustee"), read in place of the noun
    by: tuple = ()                  # (column, pattern, noun): the noun read from a column's value, the first match wins
    of: str = "of"                  # the word before the body a role relation names
    body: bool = True               # a role relation's body names the fact and folds it
    where: tuple = ()               # columns whose values follow the noun; a column `REFER` names reads its far row's name
    to: str = ""                    # the word before `where` ("to": a donor to a party)
    same: tuple = ()                # more columns that must be equal for two rows to say the same thing
    event: tuple = ()               # (column, {value: word}, default word): what happened ("listed", "removed")
    counted: tuple = ("record", "records")   # one row, counted in the small text
    held: bool = False              # a role held from a day ("since 11 March 2025"), not a list across years
    start: str = ""                 # the column a held role starts on (else the view's first date)
    end: str = ""                   # the column it ends on
    detail: tuple = ()              # (label, column) said in the small text, each value once
    flags: tuple = ()               # (column, words): said in the small text where any folded row's column is true
    what: str = ""                  # a column saying what one row is about, for a line of its own (a speech's subject)
    card: str = ""                  # the entity card's word ("charity {role}"); empty: the noun


ROLE_HELD = dict(held=True, end="ended_on")
SAYS = {
    "directors": Says("director", start="appointed_on", counted=("filing", "filings"), flags=(("in_latest", "in the latest file"),), **ROLE_HELD),
    "shareholders": Says("shareholder", detail=(("{} shares", "shares"),), counted=("filing", "filings"), flags=(("in_latest", "in the latest file"),)),
    "company_lookup_roles": Says("", role="role_type", start="started_on", **ROLE_HELD),
    "company_lookup_holdings": Says("shareholder", detail=(("{} shares", "shares"),), start="started_on", **ROLE_HELD),
    "society_officers": Says("officer", role="role_type", start="started_on", card="society {role}", **ROLE_HELD),
    "charity_officers": Says("officer", role="role", start="started_on", detail=(("status", "status"),), card="charity {role}", **ROLE_HELD),
    "limited_partnership_partners": Says("partner", role="kind", start="started_on", **ROLE_HELD),
    "promoter_people": Says("", role="role", of="for", detail=(("year", "year"),)),
    "party_board_roles": Says("board member", role="role", card="party {role}"),
    "gazette_celebrants": Says("celebrant", by=(("statute", r"marriage", "marriage celebrant"),
                                                 ("statute", r"civil union", "civil union celebrant")),
                               event=("action", {"removal": "removed"}, "listed"), counted=("Gazette list", "Gazette lists"),
                               detail=(("under", "statute"),)),
    "gazette_liquidators": Says("", role="role", event=("role", {}, "named in the Gazette"), counted=("Gazette notice", "Gazette notices"),
                                what="companies"),
    "gazette_practitioners": Says("", role="role", event=("role", {}, "named in the Gazette"), counted=("Gazette notice", "Gazette notices"),
                                  what="companies"),
    "gazette_appointments": Says("", role="role", where=("body",), start="starts_on", end="ends_on", held=True,
                                 counted=("Gazette notice", "Gazette notices"), detail=(("by", "by_whom"),)),
    "gazette_bankruptcies": Says("named in a bankruptcy notice", where=("kind",), event=("kind", {}, "published"),
                                 counted=("Gazette notice", "Gazette notices")),
    "gazette_prohibitions": Says("named in a prohibition order", where=("action",), event=("action", {}, "published"),
                                 counted=("Gazette notice", "Gazette notices")),
    "candidates": Says("candidate", where=("electorate", "election"), body=False, counted=("candidacy", "candidacies"),
                       detail=(("{}", "party"), ("list place", "list_place"), ("{} votes", "votes"))),
    "members": Says("member of Parliament", where=("electorate",), body=False, start="from_on", end="ended_on", held=True,
                    detail=(("{}", "party"), ("by {}", "route"))),
    "hansard_speeches": Says("spoke in the House", card="speaks in the House", event=("", {}, ""), counted=("speech", "speeches"), what="subject"),
    "parliament_written_questions": Says("named on written questions to ministers", card="on written questions", body=False, event=("", {}, ""),
                                         counted=("question", "questions"), what="title"),
    "beehive_release_ministers": Says("named on Beehive releases", card="on Beehive releases", event=("", {}, ""), counted=("release", "releases"), what="title"),
    "minister_diary_releases": Says("minister's diary released", card="minister's diary released", event=("", {}, ""), counted=("month", "months"), what="month"),
    "mp_expenses": Says("expenses filed as a member", card="member's expenses filed", event=("", {}, ""), counted=("expense line", "expense lines"), what="category"),
    "minister_expenses": Says("expenses filed as a minister", card="minister's expenses filed", event=("", {}, ""), counted=("expense line", "expense lines"), what="category"),
    "mp_interest_returns": Says("return of pecuniary interests filed", card="declares interests", event=("", {}, ""), counted=("return", "returns"),
                                detail=(("{}", "party"),)),
    "mp_interests": Says("declared interest", card="declares interests", where=("heading",), body=False, event=("", {}, ""), counted=("declaration", "declarations")),
    "party_return_donors": Says("donor", where=("party",), to="to", body=False, event=("", {}, ""),
                                counted=("donation in a party return", "donations in party returns")),
    "candidate_return_donors": Says("donor to a candidate", where=("surname", "electorate"), body=False, event=("", {}, ""),
                                    counted=("donation in a candidate return", "donations in candidate returns")),
    "disclosures": Says("donor", where=("party",), to="to", body=False, event=("", {}, ""),
                        counted=("large-donation disclosure", "large-donation disclosures")),
    "disclosure_items": Says("contributor to a large donation", body=False, event=("", {}, ""), counted=("item", "items")),
    "candidate_return_totals": Says("candidate return filed", card="candidate return filed", where=("electorate",), event=("", {}, ""), counted=("return", "returns")),
    "building_practitioner_decisions": Says("subject of a Building Practitioners Board decision", where=("decision_kind",),
                                            event=("", {}, ""), counted=("decision", "decisions")),
    "court_judgment_parties": Says("", role="role", where=("court",), event=("", {}, ""), counted=("judgment", "judgments"), what="citation"),
    "local_election_returns": Says("local election candidate", where=("council", "election_year"), body=False, counted=("return", "returns")),
    "councillor_interests": Says("councillor's interests declared", where=("council",), event=("", {}, ""), counted=("register", "registers")),
}

#: a `where` column that names another view's row by key: (far view, its key column, the column read as its name)
REFER = {
    ("candidates", "electorate"): ("electorates", "key", "name"),
    ("candidates", "election"): ("elections", "key", "name"),
    ("members", "electorate"): ("electorates", "key", "name"),
}

NUMBER_WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
CITE_AT = 6                 # documents named on a fact's citation line; the rest counted


def says_of(v: cat.View) -> Says | None:
    return SAYS.get(v.name)


def count_words(n: int, one: str, many: str) -> str:
    """'five Gazette lists', '12 Gazette notices', 'one speech'."""
    return f"{NUMBER_WORDS[n] if n < len(NUMBER_WORDS) else f'{n:,}'} {one if n == 1 else many}"


def _day(x) -> dt.date | None:
    if isinstance(x, dt.datetime):
        return x.date()
    return x if isinstance(x, dt.date) else None


def day_words(x) -> str:
    return x.strftime("%-d %B %Y") if isinstance(x, dt.date) else ""


def first_day(v: cat.View, r: dict) -> dt.date | None:
    """The row's first dated column, else a year it files as 1 January."""
    for _, c in v.dates:
        d = _day(r.get(c))
        if d:
            return d
    for c in ("year", "election_year", "filed_year"):
        y = r.get(c)
        if isinstance(y, int) and 1000 < y < 3000:
            return dt.date(y, 1, 1)
    return None


def _plain(x) -> str:
    """A register's value as words: an all-capitals role in lower case ("DIRECTOR" reads "director")."""
    s = re.sub(r"\s+", " ", str(x if x is not None else "")).strip()
    return s.lower() if s.isupper() and len(s) > 3 else s


def noun_of(v: cat.View, r: dict, s: Says) -> str:
    if s.role and r.get(s.role) not in (None, ""):
        return _plain(r[s.role])
    for column, pattern, noun in s.by:
        if re.search(pattern, str(r.get(column) or ""), re.I):
            return noun
    return s.noun


def event_of(r: dict, s: Says) -> str:
    if not s.event:
        return ""
    column, words, default = s.event
    return words.get(r.get(column), default) if column else default


def body_of(x: dict, v: cat.View, r: dict, s: Says):
    """(relation, (far view, far row)) of the row's first role relation whose body is held, else None."""
    if not s.body:
        return None
    for i, rel in enumerate(v.relations):
        if rel.kind != "role":
            continue
        hit = (x.get("bodies") or {}).get((v.name, str(r["key"]), i))
        if hit:
            return rel, hit
    return None


def where_of(x: dict, v: cat.View, r: dict, s: Says) -> tuple:
    out = []
    for c in s.where:
        val = r.get(c)
        if val in (None, ""):
            continue
        far = (x.get("referred") or {}).get((v.name, c, str(val)))
        out.append(str(far if far else _plain(val)))
    return tuple(out)


def key_of(x: dict, ref: str, v: cat.View, r: dict, apart: bool = False) -> tuple:
    """What the row says, as a key: rows with one key say the same thing about
    the entity. `apart`: a row whose line says what it is about (a speech's
    subject) stands alone, as a view's page of rows lists them."""
    s = says_of(v)
    if s is None or (apart and s.what):
        return ("row", ref)
    held = body_of(x, v, r, s)
    if held:
        return ("body", held[1][0].name, str(held[1][1]["key"]))
    return ("say", noun_of(v, r, s), where_of(x, v, r, s), event_of(r, s)) + tuple(str(r.get(c)) for c in s.same)


def fold(x: dict, rows=None, apart: bool = False) -> list:
    """[fact]: the rows (default the dossier's) folded by what they say, in
    date order of each fact's first day (undated last). A fact: {'key',
    'rows' [(ref, v, r)], 'nouns' (in order, each once), 'body' (far view,
    far row) or None, 'of', 'where', 'event', 'first', 'last', 'open'}."""
    out = {}
    for ref, v, r in (x["rows"] if rows is None else rows):
        k = key_of(x, ref, v, r, apart)
        f = out.get(k)
        if f is None:
            s = says_of(v)
            held = body_of(x, v, r, s) if s else None
            f = out[k] = {"key": k, "rows": [], "nouns": [], "body": held[1] if held else None,
                          "of": (s.of if s else "of"), "where": where_of(x, v, r, s) if s else (),
                          "to": s.to if s else "", "event": event_of(r, s) if s else ""}
        f["rows"].append((ref, v, r))
    facts = list(out.values())
    for f in facts:
        f["rows"].sort(key=lambda rv: (first_day(rv[1], rv[2]) or dt.date.max, rv[1].name, str(rv[2]["key"])))
        for _, v, r in f["rows"]:
            s = says_of(v)
            n = noun_of(v, r, s) if s else ""
            if n and n not in f["nouns"]:
                f["nouns"].append(n)
        span(f)
    return sorted(facts, key=lambda f: (f["first"] is None, f["first"] or dt.date.min, sentence_text(f).lower(), str(f["key"])))


def span(f: dict) -> None:
    """The fact's first and last days and whether a role is still open: a held
    role from its start column to its end; a list from its first day to its last."""
    starts, ends, days, open_ = [], [], [], False
    for _, v, r in f["rows"]:
        s = says_of(v)
        d = first_day(v, r)
        if d:
            days.append(d)
        if s and s.held:
            a = _day(r.get(s.start)) if s.start else d
            b = _day(r.get(s.end)) if s.end else None
            if a:
                starts.append(a)
                if b:
                    ends.append(b)
                else:
                    open_ = True
    f["held"] = bool(starts)
    f["first"] = min(starts) if starts else (min(days) if days else None)
    f["last"] = (None if open_ else max(ends) if ends else None) if starts else (max(days) if days else None)
    f["open"] = open_


def _and(words: list) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1] if words else ""


def when_words(f: dict) -> str:
    """'since 11 March 2025', '1 May 2010 to 2 June 2015', 'listed 2020 to 2025', '2023'."""
    a, b = f["first"], f["last"]
    if a is None:
        return ""
    if f.get("held"):
        if f["open"]:
            return f"since {day_words(a)}"
        return f"{day_words(a)} to {day_words(b)}" if b and b != a else f"from {day_words(a)}"
    lead = f"{f['event']} " if f.get("event") else ""
    if len(f["rows"]) == 1:
        return lead + (day_words(a) if a.timetuple().tm_yday != 1 or not _yearly(f) else str(a.year))
    return lead + (f"{a.year} to {b.year}" if b and b.year != a.year else str(a.year))


def _yearly(f: dict) -> bool:
    """A row filed with a year alone (1 January stands for it)."""
    _, v, r = f["rows"][0]
    return not any(_day(r.get(c)) for _, c in v.dates)


def _head(f: dict) -> str:
    """The noun part: 'director and shareholder', 'Trustee', 'marriage celebrant', or a row's title where no line names its view."""
    if f["nouns"]:
        return _and(f["nouns"])
    _, v, r = f["rows"][0]
    return panes.title_of(v, r)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def sentence(f: dict, link=None, cap: bool = True, bare: bool = False) -> str:
    """The fact as one sentence, escaped HTML; `link(view, row)` the body's
    anchor. `bare`: a lone row whose line says what it is about, under a
    heading that already says the rest, reads its day and that alone."""
    _, v, r = f["rows"][0]
    s = says_of(v)
    if bare and len(f["rows"]) == 1 and s and s.what and r.get(s.what) not in (None, ""):
        return panes.esc(_cap(when_words({**f, "event": ""})) + ": " + _what(r[s.what]))
    head = panes.esc(_cap(_head(f)) if cap else _head(f))
    out = head
    if f["body"]:
        fv, fr = f["body"]
        out += f" {panes.esc(f['of'])} " + (link(fv, fr) if link else panes.esc(panes.title_of(fv, fr)))
    if f["where"]:
        out += (f" {panes.esc(f['to'])} " if f["to"] else ", ") + panes.esc(", ".join(f["where"]))
    when = when_words(f)
    if when:
        out += (" " if f.get("held") and f["body"] else ", ") + panes.esc(when)
    if len(f["rows"]) == 1 and s and s.what and r.get(s.what) not in (None, ""):
        out += ": " + panes.esc(_what(r[s.what]))
    return out


def _what(x) -> str:
    return "; ".join(map(str, x)) if isinstance(x, (list, tuple)) else _plain(x)


def sentence_text(f: dict) -> str:
    return re.sub(r"<[^>]+>", "", sentence(f))


def small(f: dict) -> str:
    """The small line, escaped HTML: where several kinds of record fold, each
    one's words and days; how many rows say it and their days; the details
    each adds, each value once."""
    by_view = {}
    for _, v, r in f["rows"]:
        by_view.setdefault(v.name, []).append((v, r))
    several = len(by_view) > 1
    kinds = {name: _and(sorted({noun_of(v, r, says_of(v) or Says()) for v, r in items} - {""})) for name, items in by_view.items()}
    named = several and len(set(kinds.values())) > 1           # a director and a shareholder: each says its own word
    parts = []
    for items in by_view.values():
        v = items[0][0]
        s = says_of(v) or Says()
        bits = []
        if named:
            bits.append(kinds[v.name])
        if s.held and s.start:
            label = next((lab for lab, c in v.dates if c == s.start), "from")
            days = [f"{label} {day_words(_day(r.get(s.start)))}" for _, r in items if _day(r.get(s.start))]
            days += [f"ended {day_words(_day(r.get(s.end)))}" for _, r in items if s.end and _day(r.get(s.end))]
        else:
            days = [day_words(d) for d in sorted({first_day(v, r) for _, r in items if first_day(v, r)})
                    if not (d.month == 1 and d.day == 1 and _yearly(f))]
        if len(items) > 1 or (several and not named):
            bits.append(count_words(len(items), *s.counted) + (": " + ", ".join(days) if days else ""))
        elif several and days:
            bits.append(", ".join(days))
        for label, c in s.detail:
            vals = []
            for _, r in items:
                x = r.get(c)
                if x not in (None, "") and str(x) not in vals:
                    vals.append(str(x))
            if vals:
                bits.append(label.format("; ".join(vals)) if "{}" in label else f"{label} {'; '.join(vals)}")
        for c, words in s.flags:
            if any(r.get(c) is True for _, r in items):
                bits.append(words)
        if bits:
            parts.append(", ".join(b for b in bits if b))
    return panes.esc(" · ".join(parts))


def cite(f: dict, docs: dict = None) -> str:
    """One line: the register, then each row's document as a link to the captured copy (its page), the rest counted."""
    regs = []
    for _, v, _ in f["rows"]:
        plain = panes.REGISTER_NAME.get(v.register, v.register)
        if plain not in regs:
            regs.append(plain)
    links, seen = [], set()
    for _, v, r in f["rows"]:
        doc = r.get("document")
        if not doc or (doc, r.get("page")) in seen:
            continue
        seen.add((doc, r.get("page")))
        st = (docs or {}).get(doc)
        words = f"{doc[:8]}…" + (f" p. {r['page']}" if r.get("page") not in (None, "") else "")
        if st and st.get("state") != "absent" and not panes.is_suppressed(v, r) and not panes.is_withheld(v, r):
            from products.board import document
            links.append(f'<a class="source" href="{panes.esc(document.href(doc, st["kind"], r.get("page")))}" title="{panes.esc(doc)}">'
                         f"{panes.esc(words)}</a>")
        else:
            links.append(f'<code title="{panes.esc(doc)}">{panes.esc(words)}</code>')
    more = len(links) - CITE_AT
    return ('<div class="cite">source: ' + panes.esc("; ".join(regs))
            + (" · " + " · ".join(links[:CITE_AT]) if links else " · no document named")
            + (f" · and {more:,} more" if more > 0 else "") + "</div>")


def view_words(v: cat.View, n: int, first, last, nouns=()) -> tuple:
    """A view's section in the many-rows dossier as a fact: ('Spoke in the House,
    2017 to 2026', 'one thousand ... speeches'), escaped HTML; `nouns` the
    words its rows on the page say where the line reads them from a column."""
    s = says_of(v)
    if s is None:
        return panes.esc(panes.REGISTER_NAME.get(v.register, v.register)), panes.esc(count_words(n, "record", "records"))
    head = _and(list(nouns)) if s.role and nouns else (s.noun or _and(list(nouns)) or "records")
    if first and last:
        head += ", " + (f"{first.year} to {last.year}" if first.year != last.year else str(first.year))
    return panes.esc(_cap(head)), panes.esc(count_words(n, *s.counted))


# ── what the entity is, in a few words (the results card) ─────────────────────

def card_word(v: cat.View, r: dict | None) -> str:
    """One row's word for the entity card: 'charity trustee', 'director',
    'marriage celebrant'; '' where no line names its view. Without the row,
    the line's noun alone."""
    s = says_of(v)
    if s is None:
        return ""
    role = _lower(_plain(r[s.role])) if r is not None and s.role and r.get(s.role) not in (None, "") else ""
    if s.card:
        return s.card.format(role=role) if "{role}" not in s.card or role else (s.noun if not s.role else "")
    return role or (noun_of(v, r, s) if r is not None else s.noun)


def _lower(s: str) -> str:
    """'Board Member' reads 'board member'; an acronym ('MP') and a proper name in a fixed noun stay as written."""
    return " ".join(w.lower() if w[:1].isupper() and w[1:].islower() else w for w in s.split(" "))


def what_it_is(pairs) -> str:
    """'director and shareholder, charity trustee': the words of `pairs`
    [(view, row or None)] grouped by register in its order, each register's
    words joined by 'and', at most four registers, then 'and more'."""
    order = {r: i for i, (r, _) in enumerate(cat.REGISTERS)}
    by = {}
    for v, r in pairs:
        w = card_word(v, r)
        if w:
            words = by.setdefault(v.register, [])
            if w not in words:
                words.append(w)
    regs = sorted(by, key=lambda x: (order.get(x, len(order)), x))
    out = ", ".join(_and(by[x]) for x in regs[:4])
    return out + (", and more" if len(regs) > 4 else "")


def card_columns(v: cat.View) -> tuple:
    """The columns a card needs read from a row of this view, () where the line's noun alone serves."""
    s = says_of(v)
    if s is None:
        return ()
    return tuple(c for c in (s.role,) + tuple(c for c, _, _ in s.by) if c)


# ── names of rows a `where` column points at ──────────────────────────────────

def refer(conn, rows) -> dict:
    """{(view, column, value): the far row's name} for the `where` columns REFER
    names, one query per far view by key."""
    want = {}
    for _, v, r in rows:
        for (view, column), (far, key, _) in REFER.items():
            if view == v.name and r.get(column) not in (None, ""):
                want.setdefault((far, key), set()).add(str(r[column]))
    names = {}
    for (far, key), values in want.items():
        name = next(n for (_, _), (f, k, n) in REFER.items() if f == far and k == key)
        for row in db.rows(conn, f"select {key}::text as k, {name} as n from pub.{far} where {key}::text = any(%s)", (sorted(values),)):
            names[(far, row["k"])] = row["n"]
    out = {}
    for _, v, r in rows:
        for (view, column), (far, _, _) in REFER.items():
            if view == v.name and (far, str(r.get(column))) in names:
                out[(v.name, column, str(r[column]))] = names[(far, str(r[column]))]
    return out


def name_of(v: cat.View, r: dict) -> str:
    """The person or body a row names, as filed, in reading order ('Lloyd Budd'
    from a celebrant list's surname and given names), else the row's title."""
    if panes.is_suppressed(v, r):
        return panes.SUPPRESSED
    names = cat.fields_of(v).names
    if names and not names[0].whole:
        g = names[0]
        parts = [r.get(g.first or g.given), r.get(g.middle) if g.first else None, r.get(g.last)]
        s = " ".join(str(p).strip() for p in parts if p not in (None, "") and str(p).strip())
        if s:
            return s
    if v.title and v.title[0] in v.names and r.get(v.title[0]) not in (None, ""):
        return str(r[v.title[0]])
    return panes.title_of(v, r)


def lone_words(v: cat.View, r: dict) -> str:
    """A single-row entity's card (ruling 117 (2)): what its one row says, as a
    sentence without its body (the card reads no far row), escaped HTML;
    '' where no line names its view, the row's title being its name."""
    if says_of(v) is None:
        return ""
    return sentence(fold({"rows": [(f"{v.register}:{r['key']}", v, r)]})[0], cap=False)
