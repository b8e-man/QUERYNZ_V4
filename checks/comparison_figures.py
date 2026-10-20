"""The figures of the ten kinds of published file, read the same way from
both sides (plan 4.5: "every published file of the ten kinds, figure by
figure").

The frozen site and the rebuilt one share the path rule and not the field
names, so each kind has one extractor that reads a frozen file and a new
file into the same flat dictionary: figure id -> value. The comparison then
differs the two dictionaries. A figure id is a path such as
`party/ACT New Zealand/declared/2023`; its last segment names what it is.

Values are normalised before they are compared:

- money is whole cents (an int), so there is no tolerance and no float
  noise; the id's last segment, or its parent, says it is money (MONEY);
- a count is an int, a label a string, a membership `True`;
- a multiset of rows is a sorted tuple, so two lists of donations compare
  as sets of amounts, and the difference names what is missing on each side;
- a new-side field of the form `{"held": false, "not_held": …}` is the
  sentinel NOT_HELD: the rebuilt page says plainly it does not hold the
  figure, which is a difference with its own cause, never a zero.

Top-level sections one side carries and the other does not become one
figure each (`section/<key>`), so nothing is dropped silently; metadata
keys (bases, stamps) are left out by name. Pure functions, stdlib only;
tests in checks/tests/test_comparison.py."""
from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_EVEN

NOT_HELD = "NOT HELD"
ABSENT = "ABSENT"
#: last segments (or the parent segment for by-year maps) that are money
MONEY = {"declared", "named", "over_line", "total", "disclosed", "allocated", "spent", "placed", "part_a",
         "declared_total", "expenses_total", "expenses", "spend", "open_year_disclosures", "returns",
         "by_year", "by_receiver", "amount", "rows", "electorate_spend", "electorate_declared",
         "party_spend", "broadcast_allocation", "public_spent"}
#: keys that are prose, stamps or template plumbing, never figures
META = {"basis", "generated_at", "template", "template_version", "known_limits", "donors_basis", "note",
        "received_note", "namesake_note", "coverage_note", "donations_made_basis", "mps_basis",
        "donor_total_basis", "donors_cut_basis", "tracker_note", "mps_note", "board_note", "board_basis",
        "financials_basis", "top_donors_note", "positions_note", "window_from", "totals_from", "named_from",
        "cycles", "map_cycles", "cycle_years", "headline_parties", "subject", "kind", "key", "name", "name_key",
        "party", "electorate", "found", "variants", "search_aliases", "website", "abbreviation", "found",
        "name_forms", "name_match", "freshness", "elections", "years_covered", "window", "line", "statute",
        "stamp", "map_boundary_review"}


def cents(v) -> int | None:
    """Money as whole cents, or None for nothing."""
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    try:
        return int((Decimal(str(v)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))
    except (ArithmeticError, ValueError):
        return None


def not_held(v) -> bool:
    return isinstance(v, dict) and v.get("held") is False


def held_or(v, f=cents):
    """A new-side field: NOT_HELD when the page says so, else f(value)."""
    if not_held(v):
        return NOT_HELD
    return f(v)


def by_year(d: dict | None, f=cents) -> dict:
    """{'2023': x} -> {'2023': f(x)}; None -> {}."""
    out = {}
    for y, v in (d or {}).items():
        out[str(y)] = f(v)
    return out


def slug_of_path(rel: str) -> str:
    """`data/subject/person/aaron-stallard-8936a9e5.json` -> `aaron-stallard`: the
    readable part of a file name, without the hash of the exact key."""
    name = rel.rsplit("/", 1)[-1]
    name = name[:-5] if name.endswith(".json") else name
    return re.sub(r"-[0-9a-f]{8}$", "", name)


def fold(s) -> str:
    """A label folded for comparing: case, spaces and macrons aside."""
    import unicodedata
    if s is None:
        return ""
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
    return t.replace(" poll cancelled", "").strip()


HONORIFICS = {"hon", "dr", "rt", "sir", "dame", "mr", "mrs", "ms", "kc", "qc", "mp", "jp", "mnzm", "onzm", "cnzm",
              "dnzm", "cbe", "obe", "mbe", "qso", "qsm"}


def person_key(name) -> str:
    """A person's name as `surname first-given`, folded: the frozen site
    writes 'Barbara Edmonds', the results 'Barbara Faith EDMONDS' or
    'EDMONDS, Barbara', and all three are one key."""
    if not name:
        return ""
    raw = str(name)
    if "," in raw:
        sur, _, given = raw.partition(",")
        toks = fold(given).split()
        sur_toks = fold(sur).split()
        sur = sur_toks[-1] if sur_toks else ""
        return f"{sur} {toks[0]}" if toks else sur
    words = [w for w in raw.split() if fold(w) not in HONORIFICS]
    caps = [w for w in words if len(w) > 2 and w.isupper()]
    if caps:
        sur = fold(caps[-1]).split()
        given = [w for w in words if w not in caps]
    else:
        sur = fold(words[-1]).split() if words else []
        given = words[:-1]
    sur = sur[-1] if sur else ""
    toks = fold(" ".join(given)).split()
    return f"{sur} {toks[0]}" if toks else sur


def spelling_key(s) -> str:
    """A donor spelling folded for matching pages across the two sides."""
    t = fold(s)
    t = re.sub(r"\blimited\b", "ltd", t)
    t = re.sub(r"\bincorporated\b", "inc", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def sections(old_doc: dict, new_doc: dict, mapped: set, figures: dict) -> None:
    """One figure per top-level key one side has and the other lacks, when
    it is not metadata and not already read as figures."""
    for k in old_doc:
        if k in META or k in mapped:
            continue
        figures.setdefault(f"section/{k}", ("present", "present" if k in new_doc else ABSENT))
    for k in new_doc:
        if k in META or k in mapped or k in old_doc:
            continue
        figures.setdefault(f"section/{k}", (ABSENT, "present"))


# ── the party card: the same figures appear on home, parties and the party page ──

def party_card_old(p: dict) -> dict:
    """The frozen site's party entry (home.json `parties[]`, or the party
    page's `party_window.headline` + `window`) as figures."""
    f = {}
    w = p.get("window") or {}
    series = {str(s["year"]): s for s in (w.get("series") or [])}
    declared = p.get("declared_by_year")
    if not isinstance(declared, dict) or not declared:
        declared = {y: s.get("total") for y, s in series.items() if s.get("basis") == "declared"}
    for y, v in sorted(declared.items()):
        f[f"declared/{y}"] = cents(v)
    for y, s in sorted(series.items()):
        if s.get("basis") == "declared":
            f[f"named/{y}"] = cents(s.get("named"))
    for y, v in sorted((p.get("disclosed_by_year") or {}).items()):
        f[f"disclosed/{y}"] = cents(v)
    for k in ("total", "named", "over_line"):
        if k in w:
            f[f"window/{k}"] = cents(w.get(k))
    for y, c in sorted((w.get("by_cycle") or {}).items()):
        for k in ("total", "named", "over_line"):
            f[f"races/{y}/{k}"] = cents(c.get(k))
    pm = p.get("public_money") or {}
    if pm:
        f["public_money/allocated"] = cents(pm.get("allocated"))
        f["public_money/spent"] = cents(pm.get("spent"))
        for y, v in sorted((pm.get("by_year") or {}).items()):
            f[f"public_money/allocated/{y}"] = cents(v)
        for y, v in sorted((pm.get("spent_by_year") or {}).items()):
            f[f"public_money/spent/{y}"] = cents(v)
    if "seats" in p:
        f["seats"] = p.get("seats")
    return f


def party_card_new(p: dict) -> dict:
    f = {}
    for y, v in sorted((p.get("declared_by_year") or {}).items()):
        f[f"declared/{y}"] = cents(v)
    for y, v in sorted((p.get("named_by_year") or {}).items()):
        if p.get("declared_by_year", {}).get(y) is not None:
            f[f"named/{y}"] = cents(v)
    for y, v in sorted((p.get("disclosed_by_year") or {}).items()):
        f[f"disclosed/{y}"] = cents(v)
    for k, src in (("total", "total_window"), ("named", "named_window"), ("over_line", "over_line_window")):
        if src in p:
            f[f"window/{k}"] = cents(p.get(src))
    for y, c in sorted((p.get("races") or {}).items()):
        for k in ("total", "named", "over_line"):
            f[f"races/{y}/{k}"] = cents(c.get(k))
    pm = p.get("public_money") or {}
    if pm:
        f["public_money/allocated"] = cents(pm.get("allocated"))
        f["public_money/spent"] = cents(pm.get("spent"))
        for y, v in sorted((pm.get("by_year") or {}).items()):
            f[f"public_money/allocated/{y}"] = cents(v)
        for y, v in sorted((pm.get("spent_by_year") or {}).items()):
            f[f"public_money/spent/{y}"] = cents(v)
    if "seats" in p:
        f["seats"] = held_or(p.get("seats"), lambda v: v.get("total") if isinstance(v, dict) else v)
    return f


def rows_figure(rows, key=lambda r: r) -> tuple:
    return tuple(sorted(key(r) for r in rows))


# ── home ──────────────────────────────────────────────────────────────────────

def home(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    for p in d.get("parties") or []:
        name = p.get("party")
        f[f"party/{name}/listed"] = True
        for k, v in (party_card_old(p) if old else party_card_new(p)).items():
            f[f"party/{name}/{k}"] = v
    totals = d.get("totals") or {}
    for k in ("broadcast_allocation", "public_spent", "party_spend", "electorate_spend", "electorate_declared"):
        if k in totals:
            f[f"totals/{k}"] = held_or(totals.get(k))
    for dn in d.get("donors") or []:
        f[f"donors/{dn.get('name')}/listed"] = True
        f[f"donors/{dn.get('name')}/total"] = cents(dn.get("total"))
    rd = d.get("recent_disclosures") or {}
    if rd:
        f["recent_disclosures/n"] = rd.get("n")
        f["recent_disclosures/total"] = cents(rd.get("total"))
        f["recent_disclosures/rows"] = rows_figure(rd.get("rows") or [],
                                                   lambda r: (fold(r.get("party")), fold(r.get("donor")), cents(r.get("amount"))))
    el = d.get("electorates")
    if old:
        for e in el or []:
            f[f"electorates/{e.get('electorate')}/spend"] = cents(e.get("spend"))
            f[f"electorates/{e.get('electorate')}/declared"] = cents(e.get("declared"))
    mapped = {"parties", "totals", "donors", "recent_disclosures", "electorates"}
    return f, mapped


# ── parties ───────────────────────────────────────────────────────────────────

def parties(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    for p in d.get("registered") or []:
        name = p.get("party")
        f[f"registered/{name}/listed"] = True
        for y, v in sorted((p.get("disclosed_by_year") or {}).items()):
            f[f"registered/{name}/disclosed/{y}"] = cents(v)
    h = d.get("historic") or {}
    f["historic/count"] = h.get("count")
    f["historic/total"] = cents(h.get("total"))
    u = d.get("unfolded_returns") if old else d.get("unresolved_returns")
    if u:
        f["unresolved_returns/count"] = u.get("returns")
        f["unresolved_returns/declared"] = cents(u.get("declared"))
    mapped = {"registered", "historic", "unfolded_returns", "unresolved_returns", "registered_n"}
    return f, mapped


# ── pickers ───────────────────────────────────────────────────────────────────

def pickers(side: str, d: dict) -> dict:
    f = {}
    for dn in d.get("donors") or []:
        f[f"donors/{dn.get('name')}/listed"] = True
        f[f"donors/{dn.get('name')}/total"] = cents(dn.get("total"))
    for m in d.get("mps") or []:
        k = person_key(m.get("name"))
        f[f"mps/{k}/listed"] = True
        f[f"mps/{k}/party"] = m.get("party")
    for k in ("donors_listed", "donor_population", "donors_not_shown", "donors_cut_at"):
        if k in d:
            f[f"counts/{k}"] = d.get(k)
    f["counts/mps"] = len(d.get("mps") or [])
    mapped = {"donors", "mps", "donors_listed", "donor_population", "donors_not_shown", "donors_cut_at"}
    return f, mapped


# ── electorates (one file per election year) ─────────────────────────────────

def electorates(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    for e in d.get("electorates") or []:
        name = e.get("electorate")
        f[f"electorate/{name}/listed"] = True
        if old:
            ye = e.get("ye") or {}
            f[f"electorate/{name}/declared_total"] = cents(ye.get("declared_total"))
            f[f"electorate/{name}/candidates"] = len(ye.get("candidates") or [])
            won = [c.get("display") or c.get("candidate") for c in ye.get("candidates") or [] if c.get("elected")]
            f[f"electorate/{name}/elected"] = person_key(won[0]) if won else None
        else:
            f[f"electorate/{name}/declared_total"] = held_or(d.get("money"))
            f[f"electorate/{name}/candidates"] = e.get("candidates")
            f[f"electorate/{name}/elected"] = person_key(e.get("elected")) if e.get("elected") else None
    if not str(d.get("year") or "").isdigit():
        pass                                   # the all-years file: its counts are sections
    elif old:
        f["counts/electorates"] = len(d.get("electorates") or [])
        this = [x for x in d.get("elections") or [] if x.get("year") == d.get("year")]
        if this:
            f["counts/candidates"] = this[0].get("candidates")
            f["totals/declared_total"] = cents(this[0].get("declared_total"))
    else:
        f["counts/electorates"] = d.get("contests")
        f["counts/candidates"] = d.get("candidates")
        f["totals/declared_total"] = held_or(d.get("money"))
    mapped = {"electorates", "elections", "contests", "candidates", "money", "with_result", "year", "tracker",
              "announced"}
    return f, mapped


# ── electorate (one file per electorate) ─────────────────────────────────────

def electorate(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    for r in d.get("races") or []:
        y = str(r.get("year") or str(r.get("election", ""))[-4:])
        if old:
            f[f"race/{y}/declared_total"] = cents(r.get("declared_total"))
            f[f"race/{y}/expenses_total"] = cents(r.get("expenses_total"))
            cands = r.get("candidates") or []
            won = [c.get("display") or c.get("candidate") for c in cands if c.get("elected")]
            f[f"race/{y}/elected"] = person_key(won[0]) if won else None
            for c in cands:
                n = person_key(c.get("display") or c.get("candidate"))
                f[f"race/{y}/candidate/{n}/declared"] = cents(c.get("declared"))
                f[f"race/{y}/candidate/{n}/expenses"] = cents(c.get("expenses"))
        else:
            f[f"race/{y}/declared_total"] = held_or(r.get("declared_total"))
            f[f"race/{y}/expenses_total"] = held_or(r.get("expenses_total"))
            f[f"race/{y}/elected"] = person_key(r.get("elected")) if r.get("elected") else None
            for c in r.get("candidates") or []:
                n = person_key(c.get("display") or c.get("candidate"))
                f[f"race/{y}/candidate/{n}/declared"] = held_or(c.get("declared"))
                f[f"race/{y}/candidate/{n}/expenses"] = held_or(c.get("expenses"))
        f[f"race/{y}/held"] = True
    mapped = {"races", "elections", "total_all", "donor_rows", "announced", "money"}
    return f, mapped


# ── donor ─────────────────────────────────────────────────────────────────────

def donor(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    t = d.get("totals") or {}
    for y, v in sorted((t.get("by_year") or {}).items()):
        f[f"by_year/{y}"] = cents(v)
    for p, v in sorted((t.get("by_receiver") or {}).items()):
        f[f"by_receiver/{p}"] = cents(v)
    f["open_year_disclosures"] = cents(t.get("open_year_disclosures"))
    f["total"] = cents(t.get("returns") if old else t.get("total"))
    mapped = {"totals", "history", "history_total_rows", "history_direct_rows", "history_via_owned_rows",
              "identity", "ownership", "exposure", "industries", "industries_untagged_companies"}
    return f, mapped


def donor_rows(side: str, d: dict) -> dict:
    """{year: {source: [cents…]}} of a donor page's history, for attributing a
    by-year difference to its cause; `source` is party|candidate|disclosure
    on the old side and return|disclosure on the new."""
    out = {}
    for h in d.get("history") or []:
        src = h.get("source")
        src = {"return": "party"}.get(src, src)
        if side == "new" and h.get("counts") is False and src == "party":
            src = "party-not-counted"
        out.setdefault(str(h.get("year")), {}).setdefault(src, []).append(
            (cents(h.get("amount")), h.get("receiver") or h.get("party_name")))
    return out


# ── size-bands ────────────────────────────────────────────────────────────────

def size_bands(side: str, d: dict) -> dict:
    f = {}
    for b in d.get("bands") or []:
        f[f"band/{b.get('key')}/total"] = cents(b.get("total"))
        f[f"band/{b.get('key')}/n"] = b.get("n")
    for y in d.get("years") or []:
        yy = str(y.get("year"))
        if y.get("declared_total") is None:
            continue
        f[f"year/{yy}/declared_total"] = cents(y.get("declared_total"))
        f[f"year/{yy}/placed"] = cents(y.get("placed"))
        f[f"year/{yy}/part_a"] = cents(y.get("part_a"))
    f["declared_total"] = cents(d.get("declared_total"))
    mapped = {"bands", "years", "declared_total", "total", "tail_year", "unaccounted", "by_race", "aside"}
    for a in d.get("aside") or []:
        f[f"aside/{a.get('key')}/total"] = cents(a.get("total"))
    return f, mapped


# ── subject: party ────────────────────────────────────────────────────────────

def subject_party(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    if old:
        pw = d.get("party_window") or {}
        card = dict(pw.get("headline") or {})
        card.setdefault("window", (pw.get("headline") or {}).get("window"))
        dc = (pw.get("headline") or {}).get("declared_cycles") or {}
        card["declared_by_year"] = {y: (v.get("total") if isinstance(v, dict) else v) for y, v in (dc.get("by_year") or {}).items()}
        card["disclosed_by_year"] = None
        card["public_money"] = (pw.get("headline") or {}).get("public_money")
        card["seats"] = card.get("mps")
        for k, v in party_card_old(card).items():
            if k.startswith("disclosed/"):
                continue
            f[f"card/{k}"] = v
        rows = [r for r in d.get("donations_received") or [] if r.get("line_kind")]
        fin = pw.get("financials")
        f["financials/held"] = bool(fin) if fin is not None else None
        bd = (d.get("board") or {}).get("party_asserted") or {}
        f["board/current"] = bd.get("current")
    else:
        card = d.get("card") or {}
        for k, v in party_card_new(card).items():
            if k.startswith("disclosed/"):
                continue
            f[f"card/{k}"] = v
        rows = d.get("donations_received") or []
        f["financials/held"] = held_or(d.get("financials"), lambda v: bool(v))
        f["board/current"] = held_or(d.get("board"), lambda v: v.get("current") if isinstance(v, dict) else v)
    years = sorted({str(r.get("year")) for r in rows})
    for y in years:
        f[f"rows/{y}"] = rows_figure([r for r in rows if str(r.get("year")) == y], lambda r: cents(r.get("amount")))
    f["rows/total"] = cents(sum((r.get("amount") or 0) for r in rows))
    mapped = {"party_window", "card", "donations_received", "donations_received_total", "mps", "financials",
              "board", "donations_received_not_shown", "name_matched_count", "disclosed_count", "corroborated_count",
              "discrepancy_count", "disclosures_sighted_total", "disclosures_open_total", "anchored",
              "party_filed_labels", "matched_names", "loans", "loans_total", "disclosures",
              "donations_received_by_race"}
    return f, mapped


# ── subject: person ───────────────────────────────────────────────────────────

def subject_person(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    if old:
        rows = (d.get("candidacies") or {}).get("rows") or []
        for r in rows:
            k = f"candidacy/{r.get('year')}/{fold(r.get('electorate')) or 'list'}"
            f[f"{k}/party"] = r.get("party") or r.get("party_filed")
            f[f"{k}/votes"] = r.get("votes")
            f[f"{k}/declared"] = cents(r.get("declared"))
            f[f"{k}/expenses"] = cents(r.get("expenses"))
        f["donations_made/total"] = cents(d.get("donations_made_total"))
    else:
        for r in d.get("candidacies") or []:
            el = str(r.get("election") or "")
            m = re.search(r"(20\d\d|19\d\d)", el)
            year = m.group(1) if m else el
            k = f"candidacy/{year}/{fold(str(r.get('electorate') or '').split('/')[-1]) or 'list'}"
            f[f"{k}/party"] = r.get("party") or r.get("party_filed")
            f[f"{k}/votes"] = r.get("votes")
            f[f"{k}/declared"] = NOT_HELD
            f[f"{k}/expenses"] = NOT_HELD
        f["donations_made/total"] = held_or(d.get("donations_made"))
    mapped = {"candidacies", "donations_made", "donations_made_total", "positions", "sitting_mp", "seats",
              "namesakes_note", "candidates_available", "candidates_context_linked", "candidates_namesake_only",
              "include_candidates", "positions_not_drawn", "positions_aliases", "donations_made_not_shown",
              "matched_names", "candidate_rows", "anchored", "name_matched_count", "disclosed_count",
              "corroborated_count", "discrepancy_count", "coverage", "exposure_rollup"}
    return f, mapped


# ── cite and board-member: compared by presence only ─────────────────────────

def cite(side: str, d: dict) -> dict:
    return {"evidence": bool(d.get("evidence_text"))}, set(d.keys())


def board_member(side: str, d: dict) -> dict:
    return {"present": True}, set(d.keys())


EXTRACTORS = {"home": home, "parties": parties, "pickers": pickers, "electorates": electorates,
              "electorate": electorate, "donor": donor, "size-bands": size_bands, "cite": cite,
              "board-member": board_member}


def figures(kind: str, rel: str, side: str, doc: dict) -> tuple:
    """(figures, mapped top-level keys) of one file of one kind on one side."""
    if kind == "subject":
        fn = subject_party if rel.split("/")[2] == "party" else subject_person
    else:
        fn = EXTRACTORS[kind]
    out = fn(side, doc)
    return out if isinstance(out, tuple) else (out, set())


#: figures where a zero is a fact of its own (a nil return is not no return);
#: for every other number a zero and no entry say the same thing: nothing
STRICT_ZERO = ("declared", "declared_total", "disclosed", "votes", "n", "count", "rows", "listed")


def same(figure_id: str, o, n) -> bool:
    """Equal as published facts: None and no entry are both 'no figure';
    for a few by-year figures a zero is too."""
    if o == n:
        return True
    nothing = {None, ABSENT}
    parts = figure_id.split("/")
    last = parts[-2] if (len(parts) > 1 and parts[-1].isdigit()) else parts[-1]
    def number_or_nothing(v):
        return v in (None, ABSENT) or (isinstance(v, int) and not isinstance(v, bool))
    if last not in STRICT_ZERO and number_or_nothing(o) and number_or_nothing(n):
        nothing = {None, ABSENT, 0}
    return o in nothing and n in nothing


def is_money(figure_id: str) -> bool:
    parts = figure_id.split("/")
    return parts[-1] in MONEY or (len(parts) > 1 and parts[-2] in MONEY and parts[-1].isdigit()) \
        or (len(parts) > 1 and parts[-2] == "by_receiver")


def show(figure_id: str, v):
    """A value for a card or a log: cents back to dollars, rows to a count."""
    if v in (NOT_HELD, ABSENT, None) or isinstance(v, (bool, str)):
        return v
    if isinstance(v, tuple):
        return f"{len(v)} row(s)"
    if isinstance(v, int) and is_money(figure_id):
        return f"${v / 100:,.2f}"
    return v
