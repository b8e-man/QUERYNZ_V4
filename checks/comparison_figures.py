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
         "party_spend", "broadcast_allocation", "public_spent", "part", "sub_threshold", "anonymous", "overseas",
         "protected", "broadcast", "unreconciled_by", "referendum", "referendum_2020", "cannabis_2020", "eol_2020",
         "sighted_total", "public_expenses"}
#: keys that are prose, stamps or template plumbing, never figures
META = {"basis", "generated_at", "template", "template_version", "known_limits", "donors_basis", "note",
        "received_note", "namesake_note", "coverage_note", "donations_made_basis", "mps_basis",
        "donor_total_basis", "donors_cut_basis", "tracker_note", "mps_note", "board_note", "board_basis",
        "financials_basis", "top_donors_note", "positions_note", "window_from", "totals_from", "named_from",
        "cycles", "map_cycles", "cycle_years", "headline_parties", "subject", "kind", "key", "name", "name_key",
        "party", "electorate", "found", "variants", "search_aliases", "website", "abbreviation", "found",
        "name_forms", "name_match", "freshness", "elections", "years_covered", "window", "line", "statute",
        "stamp", "map_boundary_review", "candidate_rows_gap"}


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


def sections(old_doc: dict, new_doc: dict, mapped: set, figures: dict, added: set = frozenset()) -> None:
    """One figure per top-level key one side has and the other lacks, when
    it is not metadata and not already read as figures. `added` is the
    template's own list of keys the rebuilt page carries and the frozen page
    never did (`sections_added` in ftm.json): those are the shape's, not a
    difference."""
    for k in old_doc:
        if k in META or k in mapped:
            continue
        figures.setdefault(f"section/{k}", ("present", "present" if k in new_doc else ABSENT))
    for k in new_doc:
        if k in META or k in mapped or k in old_doc or k in added:
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


def figures_held(p: dict) -> int:
    """How many by-year figures a party entry holds (not None)."""
    return sum(1 for k in ("declared_by_year", "named_by_year", "disclosed_by_year")
               for v in (p.get(k) or {}).values() if v is not None)


def parties_by_name(entries) -> list:
    """A home page's party entries, one per name: the rebuilt home lists a
    name once per registration (New Zealand Loyal has two), and the entry
    with most to show stands for the name, as the site's own page rule has
    it (template `settled.party_page_key`)."""
    out = {}
    for p in entries or []:
        name = p.get("party")
        if name in out and figures_held(out[name]) >= figures_held(p):
            continue
        out[name] = p
    return list(out.values())


# ── home ──────────────────────────────────────────────────────────────────────

def home(side: str, d: dict) -> dict:
    f = {}
    old = side == "old"
    for p in parties_by_name(d.get("parties")):
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
    home_sections(d, f)
    el = d.get("electorates")
    if old or not not_held(el):
        # both sides: the window total and each year's figure per electorate
        # (the rebuilt side carries them since the template's second version)
        for e in el or []:
            name = e.get("electorate")
            f[f"electorates/{name}/spend"] = cents(e.get("spend"))
            f[f"electorates/{name}/declared"] = cents(e.get("declared"))
            for y, v in sorted((e.get("spend_by_year") or {}).items()):
                f[f"electorates/{name}/spend/{y}"] = cents(v)
            for y, v in sorted((e.get("declared_by_year") or {}).items()):
                f[f"electorates/{name}/declared/{y}"] = cents(v)
    mapped = {"parties", "totals", "donors", "recent_disclosures", "electorates"} | HOME_SECTIONS
    return f, mapped


HOME_SECTIONS = {"party_transfers", "race_donations", "race_spend", "race_spend_total", "party_funding", "donor_categories",
                 "party_spend", "race_public", "public_money", "promoter_spend", "donors_sighted"}


def _by_year_money(f: dict, prefix: str, d: dict | None) -> None:
    for y, v in sorted((d or {}).items()):
        f[f"{prefix}/by_year/{y}"] = cents(v)


def _by_year_fields(f: dict, prefix: str, d: dict | None, money: tuple, counts: tuple) -> None:
    for y, v in sorted((d or {}).items()):
        v = v or {}
        for k in money:
            if k in v:
                f[f"{prefix}/by_year/{y}/{k}"] = cents(v.get(k))
        for k in counts:
            if k in v:
                f[f"{prefix}/by_year/{y}/{k}_n"] = _count(v.get(k))


def _rows(d: dict, key: str) -> list:
    v = d.get(key)
    return [r for r in v if isinstance(r, dict)] if isinstance(v, list) else []


def _count(v):
    """A count as published: a number, or the length of a list the page
    gives instead of the number; None for nothing."""
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, (list, dict)):
        return len(v)
    return None


def _block(d: dict, key: str) -> dict:
    v = d.get(key)
    return v if isinstance(v, dict) else {}


def home_sections(d: dict, f: dict) -> None:
    """The home page's money sections (the template's second version
    carries every one the frozen page has, under the frozen keys): per
    party, per year, and the page's own totals. A count whose key is a
    money word elsewhere (`returns`) is read as `returns_n`."""
    for t in _rows(d, "party_transfers"):
        n = t.get("party") or t.get("name")
        f[f"party_transfers/{n}/total"] = cents(t.get("total"))
        f[f"party_transfers/{n}/n"] = _count(t.get("rows"))
        _by_year_money(f, f"party_transfers/{n}", t.get("by_year"))
    for t in _rows(d, "race_donations"):
        n = t.get("party") or t.get("name")
        f[f"race_donations/{n}/total"] = cents(t.get("total"))
        f[f"race_donations/{n}/n"] = _count(t.get("rows"))
        _by_year_money(f, f"race_donations/{n}", t.get("by_year"))
    for t in _rows(d, "race_spend"):
        n = t.get("party") or t.get("name")
        f[f"race_spend/{n}/spend"] = cents(t.get("spend"))
        f[f"race_spend/{n}/candidates"] = _count(t.get("candidates"))
        f[f"race_spend/{n}/with_figure"] = _count(t.get("with_figure"))
        _by_year_money(f, f"race_spend/{n}", t.get("by_year"))
    if isinstance(d.get("race_spend_total"), (int, float)):
        f["race_spend/total"] = cents(d.get("race_spend_total"))
    for t in _rows(d, "party_funding"):
        n = t.get("party") or t.get("name")
        f[f"party_funding/{n}/total"] = cents(t.get("total"))
        _by_year_money(f, f"party_funding/{n}", t.get("by_year"))
        for k, v in sorted((t.get("parts") or {}).items()):
            f[f"party_funding/{n}/part/{k}"] = cents(v)
    dc = _block(d, "donor_categories")
    for k in ("named", "sub_threshold", "anonymous", "overseas", "protected"):
        if k in dc:
            f[f"donor_categories/{k}"] = cents(dc.get(k))
    if "party_years" in dc:
        f["donor_categories/party_years"] = _count(dc.get("party_years"))
    ps = _block(d, "party_spend")
    for k in ("total", "broadcast", "unreconciled_by"):
        if k in ps:
            f[f"party_spend/{k}"] = cents(ps.get(k))
    for k in ("returns", "parties_with_figure", "unreconciled"):
        if k in ps:
            f[f"party_spend/{k}_n"] = _count(ps.get(k))
    _by_year_fields(f, "party_spend", ps.get("by_year"), ("spend", "broadcast", "unreconciled_by"), ("returns", "with_figure", "unreconciled"))
    for t in _rows(d, "race_public"):
        n = t.get("party") or t.get("name")
        f[f"race_public/{n}/total"] = cents(t.get("total"))
        f[f"race_public/{n}/spent"] = cents(t.get("spent"))
        _by_year_money(f, f"race_public/{n}", t.get("by_year"))
    pm = _block(d, "public_money")
    for k in ("allocated", "spent"):
        if k in pm:
            f[f"public_money/{k}"] = cents(pm.get(k))
    for k in ("parties", "allocated_nothing"):
        if k in pm:
            f[f"public_money/{k}_n"] = _count(pm.get(k))
    _by_year_fields(f, "public_money", pm.get("by_year"), ("allocated", "spent"), ("parties", "allocated_nothing"))
    pr = _block(d, "promoter_spend")
    for k in ("total", "referendum_2020", "cannabis_2020", "eol_2020"):
        if k in pr:
            f[f"promoter_spend/{k}"] = cents(pr.get(k))
    for k in ("returns", "promoters", "people", "nil_returns", "agree", "read_from_the_return", "named"):
        if k in pr:
            f[f"promoter_spend/{k}_n"] = _count(pr.get(k))
    _by_year_fields(f, "promoter_spend", pr.get("by_year"), ("spend", "referendum"), ("returns",))
    ds = _block(d, "donors_sighted")
    if ds:
        f["donors_sighted/n"] = _count(ds.get("n"))
        f["donors_sighted/total"] = cents(ds.get("total"))


# ── parties ────────────────────────────────────────────────────────────────

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
    if "unaffiliated_sitting" in d:
        f["unaffiliated_sitting/n"] = d.get("unaffiliated_sitting")
    for k in ("junk_labels", "unmatched_disclosures"):
        v = d.get(k) or {}
        if v:
            f[f"{k}/n"] = v.get("rows")
            f[f"{k}/total"] = cents(v.get("total"))
    mapped = {"registered", "historic", "unfolded_returns", "unresolved_returns", "registered_n", "unaffiliated_sitting",
              "junk_labels", "unmatched_disclosures"}
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
    one_year = str(d.get("year") or "").isdigit()
    for e in d.get("electorates") or []:
        name = e.get("electorate")
        f[f"electorate/{name}/listed"] = True
        if not one_year:
            # the all-years file: the frozen entry carries the all-time total
            # (and its latest race, compared in that year's file); the
            # rebuilt entry the window's total
            f[f"electorate/{name}/declared_total"] = cents(e.get("total_all") if old else e.get("declared_total"))
        elif old:
            ye = e.get("ye") or {}
            f[f"electorate/{name}/declared_total"] = cents(ye.get("declared_total"))
            f[f"electorate/{name}/candidates"] = len(ye.get("candidates") or [])
            won = [c.get("display") or c.get("candidate") for c in ye.get("candidates") or [] if c.get("elected")]
            f[f"electorate/{name}/elected"] = person_key(won[0]) if won else None
        else:
            f[f"electorate/{name}/declared_total"] = held_or(e.get("declared_total"))
            f[f"electorate/{name}/candidates"] = e.get("candidates")
            f[f"electorate/{name}/elected"] = person_key(e.get("elected")) if e.get("elected") else None
    money = d.get("money")
    if not one_year:
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
        f["totals/declared_total"] = held_or(money, lambda m: cents(m.get("declared_total")) if isinstance(m, dict) else cents(m))
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
    if old:
        f["money/declared_total"] = cents(d.get("total_all"))
    else:
        m = d.get("money")
        f["money/declared_total"] = held_or(m, lambda v: cents((v or {}).get("declared_total")))
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

#: how many of a party page's top donors are compared by name (the frozen list runs to every donor)
TOP_DONORS = 10


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
        f["financials/n"] = len(fin or [])
        bd = (d.get("board") or {}).get("party_asserted") or {}
        f["board/current"] = bd.get("current")
        f["mps/n"] = len(pw.get("mps") or [])
        f["leaders/held"] = bool(pw.get("leaders")) if pw.get("leaders") is not None else None
        f["rules/held"] = bool(pw.get("rules")) if pw.get("rules") is not None else None
        for t in (pw.get("top_donors") or [])[:TOP_DONORS]:
            f[f"top_donors/{t.get('name')}/total"] = cents(t.get("total"))
    else:
        card = d.get("card") or {}
        for k, v in party_card_new(card).items():
            if k.startswith("disclosed/"):
                continue
            f[f"card/{k}"] = v
        rows = d.get("donations_received") or []
        f["financials/held"] = held_or(d.get("financials"), lambda v: bool(v))
        f["financials/n"] = held_or(d.get("financials"), lambda v: len(v or []))
        f["board/current"] = held_or(d.get("board"), lambda v: v.get("current") if isinstance(v, dict) else v)
        f["mps/n"] = held_or(d.get("mps"), lambda v: len((v or {}).get("members") or []) if isinstance(v, dict) else len(v or []))
        pw = d.get("party_window") or {}
        f["leaders/held"] = held_or(pw.get("leaders"), lambda v: bool(v))
        f["rules/held"] = held_or(pw.get("rules"), lambda v: bool(v))
        for t in (pw.get("top_donors") or [])[:TOP_DONORS]:
            f[f"top_donors/{t.get('name')}/total"] = cents(t.get("total"))
    years = sorted({str(r.get("year")) for r in rows})
    for y in years:
        f[f"rows/{y}"] = rows_figure([r for r in rows if str(r.get("year")) == y], lambda r: cents(r.get("amount")))
    f["rows/total"] = cents(sum((r.get("amount") or 0) for r in rows))
    f["donations_made/total"] = cents(d.get("donations_made_total"))
    f["disclosures/sighted_total"] = cents(d.get("disclosures_sighted_total"))
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
        f["positions/n"] = len(d.get("positions") or [])
        f["properties/n"] = len(d.get("properties") or [])
        f["party_boards/n"] = len(d.get("party_boards") or []) if isinstance(d.get("party_boards"), list) else None
        f["public_expenses/total"] = cents((d.get("public_expenses") or {}).get("total")) if isinstance(d.get("public_expenses"), dict) else None
        f["interests_tree/held"] = bool((d.get("interests_tree") or {}).get("tree")) if d.get("interests_tree") is not None else None
    else:
        for r in d.get("candidacies") or []:
            el = str(r.get("election") or "")
            m = re.search(r"(20\d\d|19\d\d)", el)
            year = m.group(1) if m else el
            k = f"candidacy/{year}/{fold(str(r.get('electorate') or '').split('/')[-1]) or 'list'}"
            f[f"{k}/party"] = r.get("party") or r.get("party_filed")
            f[f"{k}/votes"] = r.get("votes")
            f[f"{k}/declared"] = held_or(r.get("declared"))
            f[f"{k}/expenses"] = held_or(r.get("expenses"))
        f["donations_made/total"] = held_or(d.get("donations_made_total"), lambda v: cents(v) if v is not None else held_or(d.get("donations_made")))
        f["positions/n"] = held_or(d.get("positions"), lambda v: len(v or []))
        f["properties/n"] = held_or(d.get("properties"), lambda v: len(v or []))
        f["party_boards/n"] = held_or(d.get("party_boards"), lambda v: len(v or []))
        f["public_expenses/total"] = held_or(d.get("public_expenses"), lambda v: cents((v or {}).get("total")))
        f["interests_tree/held"] = held_or(d.get("interests_tree"), lambda v: bool((v or {}).get("tree")))
    received = d.get("donations_received") or []
    f["donations_received/total"] = cents(d.get("donations_received_total"))
    f["donations_received/rows"] = rows_figure(received, lambda r: cents(r.get("amount")))
    mapped = {"candidacies", "donations_made", "donations_made_total", "positions", "sitting_mp", "seats",
              "namesakes_note", "candidates_available", "candidates_context_linked", "candidates_namesake_only",
              "include_candidates", "positions_not_drawn", "positions_aliases", "donations_made_not_shown",
              "matched_names", "candidate_rows", "anchored", "name_matched_count", "disclosed_count",
              "corroborated_count", "discrepancy_count", "coverage", "exposure_rollup", "donations_received",
              "donations_received_total", "properties", "party_boards", "public_expenses", "interests_tree",
              "donations_received_by_year"}
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
    for a few by-year figures a zero is too. A rebuilt page that says it
    does not hold a figure, against a frozen page that shows nothing there
    (no entry, None, an empty list, False), shows the same: nothing."""
    if o == n:
        return True
    if NOT_HELD in (o, n):
        other = n if o == NOT_HELD else o
        return other in (None, ABSENT) or other == 0 or other is False
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
