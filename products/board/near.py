"""Near matches on the search tab (ruling 83), below the exact results and
never among them: two classes, each found by the estate's own readings and
never a looser rule.

- **names**: a person name whose given name and surname are reversed against
  the query ("MILLS PHILLIP" for Phillip Mills, or "Phillip, Mills"), read by
  keys.names.person_name (honorifics off, "Family, Given" turned round) in
  its view's order (ruling 85): only a Name whose order is stated
  (catalogue.STATED) can contradict the query; in an AMBIGUOUS one either
  order is exact and never near. A FAMILY_GIVEN name with no comma reads its
  first word as the family. A middle name may be absent on either side; an
  initial matches a given name it begins. The query is the first and last
  name fields when both are filled, else the search box when it reads as a
  person's name.
- **addresses**: the same street number and street, by keys.addresses'
  fold (address_key), with a different unit, spelling, suburb or town
  form, or the same building at a different level; only over the address
  columns of the field search (catalogue.ADDRESS_COLUMNS: registered
  addresses organisations publish, never a home address, hard limit 15).
  A postcode or a town that both name and that differ say it is not near.
  The query is the address field, else the search box when it reads as an
  address (a number and a word).

Each view is read by a SQL filter wide enough to hold every near row, with
the exact search's own clause excluded and its suppression guard kept
(hard limit 16); the reading in Python decides. At most CANDIDATES rows per
view are read; past that the count says "or more". Nothing is written."""
from __future__ import annotations

import re

from products.board import catalogue as cat
from products.board import db, fold, search

NEAR_LIMIT = 25      # rows shown per class; the whole count beside them
CANDIDATES = 2000    # rows read per view for the reading to decide on


# ── names ───────────────────────────────────────────────────────────────────

def tokens(raw: str) -> list:
    """A person name's words, given-first as keys.names reads it, folded as
    person_key folds (diacritics decomposed, apostrophes out, punctuation a space)."""
    n = fold.person_name(raw or "")
    s = fold._APOS.sub("", fold.fold_diacritics(n.full).lower())
    return re.sub(r"[^a-z0-9]+", " ", s).split()


def _toks(value: str) -> list:
    s = fold._APOS.sub("", fold.fold_diacritics(value or "").lower())
    return re.sub(r"[^a-z0-9]+", " ", s).split()


def compatible(a: str, b: str) -> bool:
    """The same given name, or an initial and a name it begins."""
    return a == b or (len(a) == 1 and b.startswith(a)) or (len(b) == 1 and a.startswith(b))


def is_organisation(raw: str) -> bool:
    """keys.names' organisation word, but a person with a weak surname ('Richard Chambers') stays a person."""
    if not fold.ORG_WORDS.search(raw or ""):
        return False
    t = _toks(raw)
    return not (2 <= len(t) <= 3 and t[-1] in fold.WEAK_SURNAMES and not fold.ORG_WORDS.search(" ".join(t[:-1])))


def name_query(q: str, asked: dict):
    """(given, [middle names], [surname words]) to reverse, or None. The name
    fields when the first and last are both filled; else the search box when
    it is two to four words, no number, no organisation word."""
    if asked.get("first") and asked.get("last"):
        g, m, s = _toks(asked["first"]), _toks(asked.get("middle", "")), _toks(asked["last"])
        if g and s:
            return g[0], g[1:] + m, s
        return None
    if not q or re.search(r"\d", q) or is_organisation(q):
        return None
    words = q.split()
    if not 2 <= len(words) <= 4:
        return None
    n = fold.person_name(q)
    g, m, s = _toks(n.given), _toks(n.middle), _toks(n.family)
    if not g or not s or len(s[0]) < 2:
        return None
    return g[0], m, s


def is_reversed(raw: str, given: str, middles: list, surname: list) -> bool:
    """Whether a filed name, read given-first, puts the query's surname
    where a given name goes and its given name after it."""
    if not raw or is_organisation(raw):
        return False
    t = tokens(raw)
    n = len(surname)
    if len(t) < n + 1 or t[:n] != surname or not compatible(t[n], given):
        return False
    if given == surname[0] and n == 1:
        return False
    rest = t[n + 1:]
    if rest and middles:
        return len(rest) == len(middles) and all(map(compatible, rest, middles))
    return True


def as_read(g: cat.Name, raw: str) -> str:
    """A filed name as keys.names should read it in its view's order: a
    FAMILY_GIVEN name with no comma gets one after its first word."""
    if g.order != cat.FAMILY_GIVEN:
        return raw
    s = fold.strip_honorifics(raw or "")
    if "," in s or len(s.split()) < 2:
        return s
    family, rest = s.split(None, 1)
    return f"{family}, {rest}"


def _name_expr(g: cat.Name) -> str:
    if g.whole:
        return g.whole
    return "concat_ws(' ', " + ", ".join(c for c in (g.first or g.given, g.middle if g.first else "", g.last) if c) + ")"


def name_filter(g: cat.Name, given: str, surname: list) -> tuple:
    """A SQL filter holding every reversed form of the name in one Name of a
    view: 'Given…, Surname', or with no comma 'Surname Given…' (the given
    name first, where the Name is FAMILY_GIVEN: 'Given… Surname')."""
    n = search.stripped_sql(_name_expr(g))
    s = r"\s+".join(re.escape(w) for w in surname)
    gp = (re.escape(given) + r"\w*" if len(given) == 1 else "(?:" + re.escape(given) + "|" + re.escape(given[0]) + r")\M")
    plain = ("^" + gp + r"[^,]*\s" + s + r"\M" if g.order == cat.FAMILY_GIVEN else "^" + s + r"\M[^\w,]*\s+" + gp)
    strip = [search._HON_SQL, search._POST_SQL]
    return (f"({search.fold_sql(_name_expr(g))} ~ %s and ({n} ~ %s or {n} ~ %s))",      # the cheap whole-word test first
            [r"\m" + s + r"\M"] + strip + [plain] + strip + ["^" + gp + "[^,]*,\\s*" + s + r"\M"])


def name_strings(g: cat.Name, r: dict) -> str:
    if g.whole:
        return r.get(g.whole) or ""
    return " ".join(str(r.get(c) or "") for c in (g.first or g.given, g.middle if g.first else "", g.last) if c)


# ── addresses ───────────────────────────────────────────────────────────────

#: a unit or a level and its number ('Unit 3', 'Level 2', 'Suite 4B'); a word alone is a street's ('Flat Bush Road')
_UNIT = re.compile(r"\b(?:unit|flat|apartment|apt|suite|level|lvl|floor|shop)\b\.?\s*(?:\d+[a-z]?|[a-z])\b")
_SLASH = re.compile(r"\b[a-z0-9]{1,4}\s*/\s*(?=\d)")
_TYPES = (r"street|st|road|rd|avenue|ave|drive|dr|place|pl|crescent|cres|terrace|tce|lane|ln|highway|hwy|way|quay|"
          r"parade|pde|boulevard|blvd|close|grove|square|esplanade|mall|rise|row|court|ct|wynd|heights|glade|green|circle")
_STREET = re.compile(r"\b(\d+[a-z]?)\s+((?:[a-z'’.-]+\s+){1,4}?)(" + _TYPES + r")\b")
_BUILDING = re.compile(r"\b(house|centre|center|tower|towers|building|plaza|chambers|arcade|complex)\b")
_PLAIN_WORDS = {"new", "zealand", "nz", "aotearoa"}


def reading(text: str) -> dict:
    """An address read for the near rule: 'street' (address_key of the
    number, the street's name and its type), 'building' (address_key of a
    building's segment), 'rest' (the other words: suburb, town) and
    'postcodes'. A PO box is not a street: it has neither."""
    raw = fold.fold_diacritics(text or "").lower()
    out = {"street": "", "building": "", "rest": set(), "postcodes": set(), "number": "", "words": []}
    if fold.is_po_box(raw):
        return out
    s = _SLASH.sub("", _UNIT.sub(" ", raw))
    used = []
    m = _STREET.search(s)
    if m:
        out["street"], out["number"] = fold.address_key(m.group(0)), m.group(1)
        out["words"] = re.findall(r"[a-z]+", m.group(2))
        used.append((m.start(), m.end()))
    else:
        for seg in s.split(","):
            mm = re.match(r"\s*(\d+[a-z]?)\s+([a-z][a-z'’ .-]*)$", seg)
            if mm:
                out["street"], out["number"] = fold.address_key(seg), mm.group(1)
                out["words"] = re.findall(r"[a-z]+", mm.group(2))
                at = s.index(seg)
                used.append((at, at + len(seg)))
                break
    for seg in s.split(","):
        if _BUILDING.search(seg) and not re.search(r"\d", seg):
            out["building"] = fold.address_key(seg)
            if not out["street"]:
                out["words"] = re.findall(r"[a-z]+", seg)
            at = s.index(seg)
            used.append((at, at + len(seg)))
            break
    rest = s
    for a, b in sorted(used, reverse=True):
        rest = rest[:a] + " " + rest[b:]
    for w in re.findall(r"[a-z0-9]+", rest):
        if re.fullmatch(r"\d{4}", w):
            out["postcodes"].add(w)
        elif w.isalpha() and len(w) > 1 and w not in _PLAIN_WORDS:
            out["rest"].add(w)
    return out


def is_near_address(query: dict, row: dict) -> bool:
    """The same street (number, name and type, folded), or the same building
    with no street that differs; and no postcode or town both name that differ."""
    if query["street"] and row["street"]:
        same = query["street"] == row["street"]
    else:
        same = bool(query["building"]) and query["building"] == row["building"]
    if not same:
        return False
    if query["postcodes"] and row["postcodes"] and not query["postcodes"] & row["postcodes"]:
        return False
    if query["rest"] and row["rest"] and not query["rest"] & row["rest"]:
        return False
    return True


def address_query(q: str, asked: dict):
    """(the text read, its reading) or None: the address field, else the
    search box when it reads as a street or a building."""
    text = asked.get("address") or ""
    if not text and q and re.search(r"\d", q) and re.search(r"[A-Za-z]{2}", q):
        text = q
    if not text:
        return None
    r = reading(text)
    return (text, r) if (r["street"] or r["building"]) else None


def address_filter(v: cat.View, r: dict) -> tuple:
    """A SQL filter holding every near row: the street number as a whole
    word and the start of the street's longest name word; for a building,
    the start of its longest word."""
    hay = search.fold_sql("concat_ws(' ', " + ", ".join(cat.fields_of(v).address) + ")")
    pats = [r"\m" + re.escape(r["number"]) + r"\M"] if r["street"] and r["number"] else []
    words = [w for w in r["words"] if w not in ("st", "saint", "mt", "mount") and len(w) > 1]
    if words:
        pats.append(r"\m" + re.escape(max(words, key=len)))
    return (" and ".join(f"{hay} ~ %s" for _ in pats) or "false"), pats


def address_text(v: cat.View, r: dict) -> str:
    return ", ".join(str(r.get(c)) for c in cat.fields_of(v).address if r.get(c))


# ── the scan ────────────────────────────────────────────────────────────────

def _read(conn, v: cat.View, near_clause: str, near_params: list, q: str, asked: dict, drop: tuple, source_is_box: bool,
          also_exact: dict = None):
    """The rows of one view inside the near filter, outside the exact
    search, satisfying the rest of what was asked; None when it cannot hold
    it. `also_exact`: fields whose exact match also rules a row out (an
    address the box typed is exact in a column the box does not search)."""
    words = search.words_of(q)
    number = re.sub(r"\s", "", q) if search.is_number(q) else None
    exact = search.match_sql(v, words, number, False, asked)
    rest_fields = {f: x for f, x in asked.items() if f not in drop}
    rest = search.match_sql(v, [] if source_is_box else words, None if source_is_box else number, False, rest_fields)
    if rest is None:
        return None
    clause, params = near_clause + " and " + rest[0], near_params + rest[1]
    if exact is not None and (words or number or asked):
        clause += " and not coalesce((" + exact[0] + "), false)"
        params += exact[1]
    if also_exact:
        same = search.fields_sql(v, also_exact)
        if same:
            clause += " and not coalesce((" + same[0] + "), false)"
            params += same[1]
    g, gp = search.guard_sql(v)
    sql = (f"select *, {v.key_col} as key from pub.{v.name} where {clause}{g} "
           f"order by {v.default_order} nulls last, {v.key_col} limit %s")
    return db.rows(conn, sql, params + gp + [CANDIDATES])


def near(conn, q: str, asked: dict, registers=None, held=None) -> dict:
    """{'names': {...}, 'addresses': {...}}, each {'total', 'more', 'rows':
    [(view, row)] up to NEAR_LIMIT, 'refs': every 'view:key' found, 'why'
    when the class was not tried}."""
    asked = {f: x for f, x in (asked or {}).items() if (x or "").strip()}
    held = held if held is not None else db.pub_views(conn)
    views = [v for v in cat.VIEWS if v.name in held and (registers is None or v.register in registers)]
    out = {}
    nq = name_query(q, asked)
    c = {"total": 0, "more": False, "rows": [], "refs": []}
    if nq is None:
        c["why"] = "not tried: fill the first and last name fields, or type a given name and a surname in the box"
    else:
        given, middles, surname = nq
        from_box = not (asked.get("first") and asked.get("last"))
        if from_box:
            c["note"] = ("the box finds a name's words in any order, so a reversed name it holds is an exact match; "
                         "here are the reversed forms it misses (an initial). The name fields read the order.")
        for v in views:
            groups = [g for g in cat.fields_of(v).names if g.order in cat.STATED]     # ambiguous: either order is exact
            if not groups:
                continue
            alts, ps = [], []
            for g in groups:
                a, p = name_filter(g, given, surname)
                alts.append(a)
                ps += p
            rows = _read(conn, v, "(" + " or ".join(alts) + ")", ps, q, asked, ("first", "middle", "last"), from_box)
            if rows is None:
                continue
            c["more"] |= len(rows) >= CANDIDATES
            for r in rows:
                if any(is_reversed(as_read(g, name_strings(g, r)), given, middles, surname) for g in groups):
                    c["total"] += 1
                    c["refs"].append(f"{v.name}:{r['key']}")
                    if len(c["rows"]) < NEAR_LIMIT:
                        c["rows"].append((v, r))
    out["names"] = c
    aq = address_query(q, asked)
    c = {"total": 0, "more": False, "rows": [], "refs": []}
    if aq is None:
        c["why"] = "not tried: fill the address field with a street number and street, or a building"
    else:
        text, reading_q = aq
        from_box = not asked.get("address")
        for v in views:
            if not cat.fields_of(v).address:
                continue
            clause, ps = address_filter(v, reading_q)
            rows = _read(conn, v, "(" + clause + ")", ps, q, asked, ("address",), from_box, {"address": text})
            if rows is None:
                continue
            c["more"] |= len(rows) >= CANDIDATES
            for r in rows:
                if is_near_address(reading_q, reading(address_text(v, r))):
                    c["total"] += 1
                    c["refs"].append(f"{v.name}:{r['key']}")
                    if len(c["rows"]) < NEAR_LIMIT:
                        c["rows"].append((v, r))
    out["addresses"] = c
    return out
