"""The provider's gap list (ruling 160, 10 November 2026): what the old estate held that the ingest MCP lacks.

The new estate takes in the old estate's corpora, and tells the MCP what is missing so its provider can gather
it. This module measures, source by source, what the old estate holds against what the MCP holds, and writes

    <work>/handover/mcp-gaps.md     one page for the provider, the biggest gaps first
    <work>/handover/mcp-gaps.json   the same as data (schema 1, in mcp-stale.json's style)

How a source is measured, by its `match`:

  url / sha / url+sha   every old item's address (normalised: scheme, `www.`, `:80`, a trailing slash and a
                        fragment dropped) or its content sha256 is looked for among everything the MCP holds:
                        our copy of it (mcpsource.arrivals and mcpsource.files) and, past our pull's cursor,
                        the MCP's own `records` (metadata only). Missing = old items with no match, by the
                        old item's own period (its year) and kind.
  date                  the old item's key is a date (a Hansard sitting); the MCP's dates are read from the
                        addresses of the source's corpus by a pattern.
  count                 the old estate's count by period and kind beside the MCP corpus's record count. The
                        estate-* corpora's `date` is the capture day, so no period comparison is possible;
                        what is missing is the difference, said as that.

A source with no corpus is a gap in itself. A source is listed with `status`:
  gap       asked of the provider: "gather it, or say it cannot be gathered and why"
  boxes     a keyed API the boxes keep (the 5 November split); shown, not asked
  searched  Papers Past: searched, never mined (hard limit 17); shown, never asked
  held      the NZME mastheads (the NZ Herald, BusinessDesk): already in the new estate's copy of the old news
            (ruling 161); their new articles are asked in asks/news.json (ruling 169), not here; shown, not asked
  derived   built by the old estate from other sources (claims, links, derived registers); not a source
  out       left out entirely: the recovered news dump held on node1 (rulings 154, 161), fyi.org.nz (removed from
            the estate, ruling 168)

A gap is closed only when records land: a gap in the last feed whose missing count is now 0 is moved to
`closed`, dated by this run, never by the provider's answer. The rows carry source names, counts and periods;
no record's content and no personal information (hard limit 11). Stream I's inventory
(docs/research/old-estate-inventory.json), when there, adds any source it names that this module does not
measure, as `unmeasured`, so nothing is silently dropped; a source it marks OUT is left out.

    python -m support.mcpsource.gaps            measure and write both files
    python -m support.mcpsource.gaps --print    measure and print the page, writing nothing
    python -m support.mcpsource.gaps --no-mcp   our copy of the MCP only (no `records` calls for the tail)

Read-only everywhere: the old databases through the old-estate reader, querynz_v4 through the read login, the
MCP through `corpora` and `records`. Tests: support/mcpsource/tests/test_gaps.py."""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import sys
import urllib.parse

WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
GAPS_MD = os.path.join(WORK, "handover", "mcp-gaps.md")
GAPS_JSON = os.path.join(WORK, "handover", "mcp-gaps.json")
_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INVENTORY = os.path.join(_REPO, "docs", "research", "old-estate-inventory.json")
ASKED = "gather it, or say it cannot be gathered and why"
PAGE_ROWS = 25
UNDATED = "undated"
SCHEMA_VERSION = 1


# ── the old estate's sources ─────────────────────────────────────────────────

@dataclasses.dataclass(frozen=True)
class Source:
    id: str                      # stable: the gap_id's root
    label: str
    db: str                      # the old database
    sql: str                     # match url/sha/date: rows (url, sha, period, kind); count: rows (period, kind, n)
    corpus: str | None           # the MCP corpus that does or should hold it; None: no corpus
    match: str = "url+sha"       # url | sha | url+sha | date | count
    status: str = "gap"          # gap | boxes | searched | held | derived | out
    how: str = ""                # what the old rows are, in a few words
    caveat: str = ""
    date_pattern: str = ""       # match "date": the pattern that reads a date from the corpus's addresses
    category: str = "public record"   # public record | party site | news and other sites | reference dataset


def _year(col: str) -> str:
    return f"coalesce(extract(year from {col})::int::text, '{UNDATED}')"


SOURCES = (
    Source("gets-awards", "GETS award notices (MBIE open data)", "nzbn_canonical",
           "select 'https://www.gets.govt.nz/ExternalTenderDetails.htm?id='||rfx_id, null, "
           f"coalesce(substring(awarded_date from '(\\d{{4}})'), '{UNDATED}'), coalesce(award_type, 'award') from bulk.gets_award_notices",
           "gets", match="url", how="award notices from MBIE's open-data files, matched by GETS tender id",
           caveat="the MCP's gets holds tender pages; an award is matched when its tender's page is held, which "
                  "says nothing about the award fields (supplier, amount) being in the record"),
    Source("charities-register", "Charities Register: entities", "nzbn_canonical",
           f"select {_year('date_registered')}, coalesce(registration_status,'?'), count(*) from charities.charity_entities group by 1,2",
           "estate-charities", match="count", how="registered charities by year registered and status",
           caveat="the corpus's records are captured pages (1,756 of 1,767 of kind `other` on 10 November, API pages by their look), and one page may hold many rows, so the difference is not a row count"),
    Source("charities-officers", "Charities Register: officers", "nzbn_canonical",
           f"select '{UNDATED}', 'officer role', count(*) from charities.charity_officer_roles group by 1,2",
           "estate-charities", match="count", how="officer roles",
           caveat="the corpus's records are captured pages (1,756 of 1,767 of kind `other` on 10 November, API pages by their look), and one page may hold many rows, so the difference is not a row count"),
    Source("charities-returns", "Charities Register: annual returns (financials)", "nzbn_canonical",
           f"select {_year('year_ended')}, 'annual return', count(*) from public.charity_annual_financials group by 1,2",
           "estate-charities", match="count", how="annual returns by year ended",
           caveat="the corpus's records are captured pages (1,756 of 1,767 of kind `other` on 10 November, API pages by their look), and one page may hold many rows, so the difference is not a row count"),
    Source("legislation", "Legislation (legislation.govt.nz instruments)", "nzbn_canonical",
           f"select coalesce(year::text, '{UNDATED}'), coalesce(kind,'?'), count(*) from legislation.instruments group by 1,2",
           None, match="count", how="Acts, bills and secondary legislation by year and kind (titles held, not texts)"),
    Source("mp-interests", "Register of Pecuniary Interests of MPs", "nzbn_canonical",
           f"select source_url, null, {_year('as_at')}, 'register' from mp_interests.registers", None, match="url",
           how="the published registers (one document a year)"),
    Source("election-candidates", "Electoral Commission candidate lists and results", "nzbn_canonical",
           f"select coalesce(year::text, '{UNDATED}'), coalesce(type,'?'), count(*) from elections.candidates group by 1,2",
           None, match="count", how="candidates by election year and type"),
    Source("party-register", "Register of political parties", "nzbn_canonical",
           f"select '{UNDATED}', 'party', count(*) from parties.register group by 1,2", None, match="count",
           how="registered parties (a snapshot)"),
    Source("promoters", "Register of promoters (Electoral Commission)", "nzbn_canonical",
           "select source_page, source_sha, coalesce(election_year::text, 'undated'), 'promoter page' from registers.promoters",
           None, how="the register's pages"),
    Source("candidate-returns", "Candidate returns (general elections)", "nzbn_canonical",
           "select distinct null::text, source_sha, coalesce(election_year::text,'undated'), 'return' from registers.candidate_donations "
           "where source_sha is not null", "estate-candidate_returns", match="sha",
           how="the return files the old donation rows were read from, by content sha256"),
    Source("party-returns", "Party donation returns (annual)", "nzbn_canonical",
           "select distinct null::text, source_sha, coalesce(year::text,'undated'), 'return' from registers.party_donations "
           "where source_sha is not null", None, match="sha",
           how="the party return files the old donation rows were read from, by content sha256"),
    Source("disclosures", "Donation disclosures over $20,000 (Electoral Commission)", "nzbn_canonical",
           "select distinct source_url, source_sha, coalesce(year_received::text,'undated'), 'disclosure' "
           "from registers.donation_disclosures where source_url is not null or source_sha is not null",
           "estate-disclosures", how="the disclosure documents the old donation rows were read from"),
    Source("party-return-totals", "Party annual returns (totals)", "nzbn_canonical",
           "select distinct null::text, source_sha, coalesce(year::text,'undated'), 'return' from registers.party_return_totals "
           "where source_sha is not null", None, match="sha", how="the party returns the old totals were read from"),
    Source("party-election-expenses", "Party election expense returns", "nzbn_canonical",
           "select distinct source_page, document_sha, coalesce(election_year::text,'undated'), 'return' "
           "from registers.party_election_expenses", None, how="the expense returns"),
    Source("promoter-expenses", "Promoter expense returns", "nzbn_canonical",
           "select distinct source_page, document_sha, coalesce(election_year::text,'undated'), 'return' "
           "from registers.promoter_expenses", None, how="the expense returns"),
    Source("candidates-announced", "Candidates announced (party pages)", "nzbn_canonical",
           "select distinct source_url, null, coalesce(election_year::text,'undated'), 'candidate page' "
           "from registers.candidates_announced where source_url is not null", None, match="url",
           category="party site", how="the pages that announced each candidate"),
    Source("party-financials", "Party financial statements", "nzbn_canonical",
           "select source_url, sha256, coalesce(batch_year::text,'undated'), 'financial statement' "
           "from registers.party_financial_documents", None, how="the statements filed with the Electoral Commission"),
    Source("minister-expenses", "Ministers' expenses (quarterly)", "nzbn_canonical",
           f"select url, sha256, {_year('quarter_start')}, 'quarterly release' from registers.minister_expense_documents",
           None, how="the quarterly releases"),
    Source("mp-expenses", "MPs' expenses (quarterly, Parliamentary Service)", "nzbn_canonical",
           f"select url, sha256, {_year('quarter_start')}, 'quarterly release' from registers.mp_expense_documents",
           None, how="the quarterly releases"),
    Source("party-sites", "Political parties' websites (whole-site captures)", "nzbn_canonical",
           f"select url, sha256, {_year('published_at')}, coalesce(kind,'?') from registers.party_site_documents",
           None, how="pages and files captured from each party's own site", category="party site"),
    Source("worksafe-docs", "WorkSafe prosecutions and undertakings", "nzbn_canonical",
           "select url, sha256, 'undated', 'document' from registers.worksafe_documents", "estate-worksafe",
           how="the court summaries and undertakings"),
    Source("courts-cases", "Courts: judgments read by the old estate", "nzbn_canonical",
           f"select source_url, sha256, {_year('judgment_date')}, coalesce(court,'?') from courts.cases", "courts",
           how="the judgments the old courts register was read from"),
    Source("hansard-sittings", "Hansard: sitting days (per-speech transcripts)", "nzbn_canonical",
           "select sitting_date::text, null, extract(year from sitting_date)::int::text, 'sitting day' from registers.hansard_sittings",
           "parliament-hansard-debates", match="date", date_pattern=r"/(\d{4}-\d{2}-\d{2})[/-]",
           how="sitting days the old estate read speech by speech; a day is held when the MCP holds its daily PDF"),
    Source("hansard-sections", "Hansard: debate sections", "incoming_news",
           f"select '{UNDATED}', 'section', count(*) from hansard_sections group by 1,2",
           "parliament-hansard-debates", match="count", how="sections of debates read from the HTML transcript"),
    # keyed APIs the boxes keep (the 5 November split): shown with their size, not asked
    Source("companies", "Companies Register and NZBN (entities)", "nzbn_canonical",
           f"select {_year('registered_at')}, coalesce(entity_type,'?'), count(*) from public.entities group by 1,2",
           None, match="count", status="boxes", how="entities by year registered and type",
           caveat="the boxes read it through the NZBN API (the companies lane)"),
    Source("companies-roles", "Companies Register: directors and shareholders", "nzbn_canonical",
           f"select '{UNDATED}', 'director role', count(*) from public.director_roles group by 1,2 union all "
           f"select '{UNDATED}', 'shareholder role', count(*) from public.shareholder_roles group by 1,2",
           None, match="count", status="boxes", how="roles", caveat="the boxes read it through the NZBN API"),
    Source("linz-titles", "LINZ record of title owners", "nzbn_canonical",
           f"select '{UNDATED}', coalesce(owner_type,'?'), count(*) from registers.linz_title_owners group by 1,2",
           None, match="count", status="boxes", how="title owners", caveat="the boxes read it through LINZ's keyed data service"),
    # reference datasets the old estate downloaded whole
    Source("nzbn-bulk", "NZBN bulk registers (trust boards, societies, unincorporated, public sector, villages)",
           "nzbn_canonical",
           f"select '{UNDATED}', 'charitable trust board', count(*) from bulk.charitable_trust_boards_core_data group by 1,2 union all "
           f"select '{UNDATED}', 'other incorporated entity', count(*) from bulk.other_incorporated_entities_core_data group by 1,2 union all "
           f"select '{UNDATED}', 'unincorporated entity', count(*) from bulk.unincorporated_entities_core_data group by 1,2 union all "
           f"select '{UNDATED}', 'public sector entity', count(*) from bulk.public_sector_entities_core_data group by 1,2 union all "
           f"select '{UNDATED}', 'retirement village', count(*) from bulk.retirement_villages_core_data group by 1,2 union all "
           f"select '{UNDATED}', 'Maori business identifier', count(*) from bulk.maori_business_identifier group by 1,2",
           None, match="count", how="the NZBN bulk data files, one table per register"),
    Source("linz-place-names", "LINZ Gazetteer place names", "nzbn_canonical",
           f"select '{UNDATED}', 'place name', count(*) from bulk.linz_place_names group by 1,2", None, match="count",
           how="a bulk download", category="reference dataset"),
    Source("gleif", "GLEIF legal entity identifiers", "nzbn_canonical",
           f"select '{UNDATED}', 'LEI record', count(*) from bulk.gleif group by 1,2", None, match="count",
           how="a bulk download (worldwide; not a New Zealand publication)", category="reference dataset"),
    Source("ror", "Research Organization Registry", "nzbn_canonical",
           f"select '{UNDATED}', 'organisation name', count(*) from bulk.ror_names group by 1,2", None, match="count",
           how="a bulk download (worldwide; not a New Zealand publication)", category="reference dataset"),
    Source("wikidata", "Wikidata (labels, names, attributes)", "nzbn_canonical",
           f"select '{UNDATED}', 'name', count(*) from bulk.wikidata_names group by 1,2", None, match="count",
           how="a bulk download (worldwide; not a New Zealand publication)", category="reference dataset"),
    # built by the old estate, not a source
    Source("gazette-derived", "Gazette notices and the registers read from them", "nzbn_canonical",
           f"select '{UNDATED}', 'notice', count(*) from gazette.notices group by 1,2", None, match="count",
           status="derived", how="read from the Gazette pages counted under gazette.govt.nz"),
    Source("extractions", "The old estate's claims, entities and links", "extractions",
           f"select '{UNDATED}', 'claim', count(*) from v3.claims group by 1,2", None, match="count",
           status="derived", how="model readings of the documents; the documents are the sources"),
)

# The articles table: one source per host tag, measured by address. Its corpus where one should hold it.
ARTICLE_CORPUS = {
    "beehive.govt.nz": "beehive", "www.beehive.govt.nz": "beehive",
    "parliament.nz": "parliament-hansard-debates", "courtsofnz.govt.nz": "courts", "era.govt.nz": "estate-courts-era",
    "justice.govt.nz/lcdt": "courts", "justice.govt.nz/readt": "courts", "worksafe.govt.nz": "estate-worksafe",
    "comcom.govt.nz": "estate-commerce_commission", "elections.nz": "estate-disclosures",
    "elections.nz/expenses": "estate-candidate_returns",
}
COUNCIL_TAG = re.compile(r"infocouncil")
#: the NZME mastheads: in the copy already (ruling 161), new articles asked in asks/news.json (ruling 169)
NZME_TAGS = frozenset({"nzherald.co.nz", "businessdesk.co.nz"})
ARTICLE_STATUS = {"paperspast.natlib.govt.nz": "searched", **{t: "held" for t in NZME_TAGS}}
HELD_CAVEAT = ("an NZME masthead: its archive is in the new estate's copy (ruling 161); its new articles are asked "
               "in asks/news.json (ruling 169): the archive is not asked")
# Left out entirely. Ruling 154 (161 keeps it): the recovered news dump held on node1, which has no host tag in the
# catalogue; stream I's inventory marks it OUT, and any tag or source id it names OUT is left out here. Ruling 168:
# fyi.org.nz is removed from the estate.
OUT_TAGS: frozenset = frozenset({"fyi.org.nz"})


def article_corpus(tag: str) -> str | None:
    if tag in ARTICLE_CORPUS:
        return ARTICLE_CORPUS[tag]
    return "estate-council_minutes" if COUNCIL_TAG.search(tag) else None


ARTICLE_COUNTS = (f"select s, {_year('post_date')}, count(*) from (select unnest(sources) s, post_date from articles) x "
                  "group by 1,2")
ARTICLE_URLS = (f"select s, news_url, {_year('post_date')} from (select unnest(sources) s, news_url, post_date "
                "from articles where sources && %s) x where s = any(%s)")


# ── matching ─────────────────────────────────────────────────────────────────

def norm_url(u) -> str | None:
    """An address in one spelling: scheme, `www.`, a default port, a trailing slash and a fragment dropped, the
    host lower-cased, the path percent-decoded. A relative address (`/en/pb/...`, as some parliament corpora
    give) keeps its path. None for nothing."""
    if not u or not isinstance(u, str):
        return None
    u = u.strip()
    if not u:
        return None
    p = urllib.parse.urlsplit(u if "://" in u or u.startswith("/") else "http://" + u)
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = urllib.parse.unquote(p.path).rstrip("/")
    q = ("?" + p.query) if p.query else ""
    return f"{host}{path}{q}"


def host_of(u: str) -> str:
    n = norm_url(u) or ""
    return n.split("/", 1)[0].split("?", 1)[0]


PARLIAMENT = "https://www.parliament.nz"


@dataclasses.dataclass
class Held:
    """What the MCP holds, as keys: normalised addresses, content hashes, and per corpus its addresses."""
    urls: set = dataclasses.field(default_factory=set)
    shas: set = dataclasses.field(default_factory=set)
    corpus_urls: dict = dataclasses.field(default_factory=dict)

    def add(self, corpus: str, url=None, sha=None) -> None:
        if isinstance(url, str) and url.startswith("/") and corpus.startswith("parliament-"):
            url = PARLIAMENT + url                 # the parliament corpora give some addresses as a path only
        n = norm_url(url)
        if n:
            self.urls.add(n)
            self.corpus_urls.setdefault(corpus, set()).add(n)
        if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha):
            self.shas.add(sha)

    def hosts(self) -> set:
        return {u.split("/", 1)[0].split("?", 1)[0] for u in self.urls}


def record_keys(rec: dict) -> tuple:
    """(addresses, hashes) a `records` row names: its url, its urls list and its capture's url; its sha256,
    content_sha256, original_sha256 and capture's sha256."""
    urls = [rec.get("url")] + list(rec.get("urls") or []) + [(rec.get("capture") or {}).get("url")]
    shas = [rec.get("sha256"), rec.get("content_sha256"), rec.get("original_sha256"),
            (rec.get("capture") or {}).get("sha256")]
    return [u for u in urls if isinstance(u, str)], [s for s in shas if isinstance(s, str)]


def is_held(url, sha, held: Held, match: str) -> bool:
    if "url" in match and norm_url(url) in held.urls:
        return True
    if "sha" in match and sha and sha in held.shas:
        return True
    return False


def dates_held(held: Held, corpus: str, pattern: str) -> set:
    rx = re.compile(pattern)
    out = set()
    for u in held.corpus_urls.get(corpus, ()):
        m = rx.search(u)
        if m:
            out.add(m.group(1))
    return out


def tally(items, held: Held, match: str, dates: set = None) -> dict:
    """kind -> period -> [old, missing] for items (key_url, sha, period, kind). A `date` match takes the url
    column as the date itself."""
    out: dict = {}
    for url, sha, period, kind in items:
        if match == "date":
            ok = url in (dates or set())
        else:
            ok = is_held(url, sha, held, match)
        cell = out.setdefault(kind or "?", {}).setdefault(period or UNDATED, [0, 0])
        cell[0] += 1
        if not ok:
            cell[1] += 1
    return out


def tally_counts(rows) -> dict:
    """kind -> period -> [old, None] for count rows (period, kind, n)."""
    out: dict = {}
    for period, kind, n in rows:
        cell = out.setdefault(kind or "?", {}).setdefault(period or UNDATED, [0, None])
        cell[0] += int(n)
    return out


# ── the gaps ─────────────────────────────────────────────────────────────────

def gap_id(source_id: str, corpus, kind: str = None) -> str:
    """Stable: the source, its corpus (or `none`) and the kind; never a count or a date."""
    k = re.sub(r"[^a-z0-9]+", "-", (kind or "all").lower()).strip("-") or "all"
    return f"{source_id}@{corpus or 'none'}#{k}"


def _span(periods: list) -> str:
    years = sorted(p for p in periods if p != UNDATED)
    s = f"{years[0]}–{years[-1]}" if len(years) > 1 else (years[0] if years else "")
    if UNDATED in periods:
        s = (s + " and undated") if s else "undated"
    return s


def gaps_of(src: Source, tallied: dict, corpus_records=None, how_mcp: str = "") -> list:
    """One gap object per kind of a source: what is missing, by period."""
    out = []
    kinds = sorted(tallied) if src.match != "count" else [None]
    for kind in kinds:
        cells = _merge_periods(tallied) if kind is None else tallied[kind]
        old = sum(c[0] for c in cells.values())
        if src.match == "count":
            if src.corpus is None:
                missing, by = old, {p: c[0] for p, c in cells.items() if c[0]}
            else:
                missing, by = None, {}      # a record is a captured page, not a row: no difference is honest
        else:
            missing = sum(c[1] for c in cells.values())
            by = {p: c[1] for p, c in cells.items() if c[1]}
        kinds_words = ({k: sum(c[0] for c in tallied[k].values()) for k in tallied} if src.match == "count" else None)
        out.append({
            "gap_id": gap_id(src.id, src.corpus, kind),
            "source": src.label, "source_id": src.id, "old_database": src.db, "corpus": src.corpus,
            "status": src.status, "category": src.category, "kind": kind or "all",
            "old_count": old, "mcp_count": corpus_records if src.match == "count" else old - missing,
            "missing": missing, "missing_by_period": dict(sorted(by.items())),
            "period": _span(list(by)) if by else "",
            "kinds": kinds_words,
            "how_measured": _how(src, how_mcp),
            "caveats": src.caveat or None,
            "asked": ASKED if asking(src.status, missing) else None,
        })
    return out


def asking(status: str, missing) -> bool:
    """Asked of the provider: a gap still missing something, or one a count cannot settle (missing None)."""
    return status == "gap" and (missing is None or missing > 0)


PARTY_HOSTS = re.compile(r"(^|\.)(greens|act|national|labour|nzfirst|maoriparty|opportunity|conservatives|alcp|vision|"
                         r"allianceparty|womensrightsparty|nationbuilder|nzofp)\.")
PUBLIC_HOSTS = re.compile(r"(govt\.nz|parliament\.nz|elections\.nz|infocouncil|natlib|tribunal|court|privacy\.org\.nz)")


def category_of(tag: str) -> str:
    h = host_of(tag) or tag
    if PARTY_HOSTS.search(h) or h.startswith("cdn.opportunity"):
        return "party site"
    if PUBLIC_HOSTS.search(h):
        return "public record"
    return "news and other sites"


def _merge_periods(tallied: dict) -> dict:
    out: dict = {}
    for cells in tallied.values():
        for p, c in cells.items():
            m = out.setdefault(p, [0, 0])
            m[0] += c[0]
            m[1] = (m[1] or 0) + (c[1] or 0) if c[1] is not None else None
    return out


def _how(src: Source, how_mcp: str) -> str:
    base = {"url": "each old item's address looked for among every address the MCP holds",
            "sha": "each old file's content sha256 looked for among every file hash the MCP's records promise",
            "url+sha": "each old item matched by address, or by content sha256, against everything the MCP holds",
            "date": "each old sitting day looked for among the days of the corpus's daily files",
            "count": ("the old count beside the corpus's record count (the corpus's dates are capture days, so "
                      "no period is compared; missing = the difference)" if src.corpus else
                      "the old count; the MCP has no corpus for it")}[src.match]
    return f"{src.how}: {base}" + (f"; {how_mcp}" if how_mcp and src.match != "count" else "")


def article_gaps(counts, urls_by_tag: dict, held: Held, how_mcp: str) -> list:
    """The articles table, a gap per host tag. counts: (tag, period, n). urls_by_tag: tag -> [(url, period)] for
    the tags whose host the MCP holds anything under; every other tag's articles are all missing."""
    by_tag: dict = {}
    for tag, period, n in counts:
        by_tag.setdefault(tag, {})[period or UNDATED] = [int(n), int(n)]
    for tag, rows in urls_by_tag.items():
        cells: dict = {}
        for url, period in rows:
            c = cells.setdefault(period or UNDATED, [0, 0])
            c[0] += 1
            if norm_url(url) not in held.urls:
                c[1] += 1
        by_tag[tag] = cells
    out = []
    for tag, cells in by_tag.items():
        if tag in OUT_TAGS:
            continue
        corpus = article_corpus(tag)
        status = ARTICLE_STATUS.get(tag, "gap")
        src = Source(f"articles:{tag}", f"{tag} (pages held as articles)", "incoming_news", "", corpus, match="url",
                     status=status, category=category_of(tag), how=f"articles tagged {tag}, by publication year",
                     caveat=("Papers Past is searched, never mined (hard limit 17): not asked" if status == "searched" else
                             HELD_CAVEAT if status == "held" else
                             "" if tag in urls_by_tag else
                             "the MCP holds nothing under this host, so every article is counted missing without a match"))
        out += gaps_of(src, {"article": cells}, how_mcp=how_mcp)
    return out


def document_gaps(rows, held: Held, how_mcp: str) -> list:
    """incoming_news.documents, a gap per source host: rows (url, sha, period, source)."""
    per: dict = {}
    for url, sha, period, source in rows:
        per.setdefault(source or "?", []).append((url, sha, period, "document"))
    out = []
    for source, items in per.items():
        if source in OUT_TAGS:
            continue
        status = ARTICLE_STATUS.get(source, "gap")
        src = Source(f"documents:{source}", f"{source} (fetched documents)", "incoming_news", "",
                     article_corpus(source), status=status, category=category_of(source),
                     how=f"documents fetched from {source}, by capture year (no document date is kept)",
                     caveat=HELD_CAVEAT if status == "held" else "")
        out += gaps_of(src, tally(items, held, "url+sha"), how_mcp=how_mcp)
    return out


def unmeasured(inventory, measured_ids: set) -> tuple:
    """(gaps, out_ids) from stream I's inventory: any source it names that is not measured here, as `unmeasured`;
    the ids it marks OUT. Tolerant of shape: a list of sources, or {"sources": [...]}, each with `id` or `source`
    and an optional `status`/`mark`."""
    if not inventory:
        return [], set()
    rows = inventory.get("sources") if isinstance(inventory, dict) else inventory
    gaps, out = [], set()
    for r in rows or []:
        if not isinstance(r, dict):
            continue
        sid = str(r.get("id") or r.get("source") or r.get("name") or "").strip()
        if not sid:
            continue
        mark = str(r.get("status") or r.get("mark") or "").lower()
        if mark == "out":
            out.add(sid)
            continue
        if sid in measured_ids or mark in ("derived", "regenerable"):
            continue
        gaps.append({"gap_id": gap_id(f"inventory:{sid}", None), "source": r.get("label") or sid,
                     "source_id": f"inventory:{sid}", "old_database": r.get("database") or r.get("db"),
                     "corpus": None, "status": "unmeasured", "kind": "all", "old_count": r.get("count") or r.get("rows"),
                     "mcp_count": None, "missing": None, "missing_by_period": {}, "period": "", "kinds": None,
                     "how_measured": "named in stream I's inventory; not yet measured against the MCP",
                     "caveats": None, "asked": None})
    return gaps, out


ORDER = {"gap": 0, "unmeasured": 1, "boxes": 2, "held": 3, "searched": 4, "derived": 5}


def ordered(gaps: list) -> list:
    """The biggest asked gaps first; then the rest by status, each by size."""
    return sorted(gaps, key=lambda g: (ORDER.get(g["status"], 9),
                                       -(g["missing"] if g["missing"] is not None else g["old_count"] or 0), g["gap_id"]))


def feed(gaps: list, now: dt.datetime, measured_at=None, previous: dict = None, mcp: dict = None) -> dict:
    """schema 1. `gaps`: every asked gap still missing something; `noted`: the rest (not asked); `closed`: gaps in
    the last feed whose missing count is now 0, dated by this run (records landed, never the provider's word)."""
    gaps = ordered(gaps)
    asked = [g for g in gaps if asking(g["status"], g["missing"])]
    noted = [g for g in gaps if g not in asked]
    now_ids = {g["gap_id"]: g for g in gaps}
    prev = previous if isinstance(previous, dict) else {}
    closed = {}
    for c in prev.get("closed") or []:
        if c.get("gap_id") and c["gap_id"] not in {g["gap_id"] for g in asked}:
            closed[c["gap_id"]] = c
    for g in prev.get("gaps") or []:
        gid = g.get("gap_id")
        cur = now_ids.get(gid)
        if gid and cur is not None and cur["missing"] == 0:
            closed[gid] = {"gap_id": gid, "source": g.get("source"), "was_missing": g.get("missing"),
                           "closed_at": _iso(now), "by": "records landed: missing measured 0"}
    # an ask dropped by us (a source ruled out, or now shown and not asked) is withdrawn, never closed: the provider
    # stops working it, and nothing is said to have landed (rulings 168, 169: fyi.org.nz, GeoNames, the NZME archive)
    asked_ids = {g["gap_id"] for g in asked}
    withdrawn = {w["gap_id"]: w for w in prev.get("withdrawn") or [] if w.get("gap_id") and w["gap_id"] not in asked_ids}
    for gid, w in withdrawn.items():
        # a withdrawal still shown takes today's reason: a later ruling (169: NZME's new articles asked) must not
        # leave the provider reading an older one (168: not to be collected)
        cur = now_ids.get(gid)
        if cur is not None:
            w["why"] = cur.get("caveats") or NOT_ASKED.get(cur["status"], "") or w.get("why")
    for g in prev.get("gaps") or []:
        gid = g.get("gap_id")
        if gid and gid not in asked_ids and gid not in closed:
            cur = now_ids.get(gid)
            withdrawn[gid] = {"gap_id": gid, "source": g.get("source"), "was_missing": g.get("missing"),
                              "withdrawn_at": _iso(now),
                              "why": (cur.get("caveats") or NOT_ASKED.get(cur["status"], "")) if cur else
                              "no longer asked: the source is out of scope"}
    return {"schema_version": SCHEMA_VERSION, "written_at": _iso(now), "measured_at": _iso(measured_at or now),
            "asked": ASKED, "rule": "a gap is closed only when records land, never on the provider's word",
            "mcp": mcp or {}, "gaps": asked, "noted": noted,
            "closed": sorted(closed.values(), key=lambda c: c["gap_id"]),
            "withdrawn": sorted(withdrawn.values(), key=lambda c: c["gap_id"])}


def _iso(t) -> str | None:
    return t.astimezone(dt.timezone.utc).isoformat(timespec="seconds") if t else None


def _n(x) -> str:
    return "?" if x is None else f"{x:,}"


def _top_periods(g: dict, k: int = 3) -> str:
    by = g["missing_by_period"]
    top = sorted(((n, p) for p, n in by.items()), reverse=True)[:k]
    return ", ".join(f"{p}: {n:,}" for n, p in top)


NOT_ASKED = {"boxes": "a keyed API the boxes keep", "held": "in the new estate's copy; new articles asked in asks/news.json (rulings 161, 169)",
             "searched": "searched, never mined (hard limit 17)", "derived": "built by the old estate; not a source",
             "unmeasured": "in stream I's inventory; not yet measured", "gap": "nothing missing"}


CATEGORIES = (("public record", "Public records", 15), ("party site", "Party sites", 5),
              ("news and other sites", "News and other sites", 10), ("reference dataset", "Reference datasets", 5))


def _row(g: dict) -> str:
    miss = _n(g["missing"]) if g["missing"] is not None else f"? (corpus has {_n(g['mcp_count'])} records)"
    years = g["period"] + (f" ({_top_periods(g)})" if g["missing_by_period"] and g["period"] != "undated" else "")
    return f"| {g['source']} | {g['corpus'] or '**none**'} | {g['kind']} | {miss} | {_n(g['old_count'])} | {years} |"


def page(fd: dict, now: dt.datetime) -> str:
    """The provider's page: plain, one page if it can be, the biggest gaps first within each class of source."""
    t = now.astimezone(dt.timezone(dt.timedelta(hours=13)))
    asked = fd["gaps"]
    out = [f"# What the ingest MCP lacks that the old estate held, {t.day} {t:%B %Y} {t:%H:%M} NZ time", "",
           "The new estate is taking in the old estate's records (ruling 160). Each row is something the old "
           "estate held that the MCP does not: a source with no corpus (**none**), or the documents and years a "
           "corpus is missing. Missing is counted by the old item's own year. Every row, with its method and "
           "caveats, is in mcp-gaps.json; this page shows the biggest of each class.", "",
           f"Asked for each: {ASKED}. A gap is closed only when the records land in the MCP, never on an answer "
           "alone.", ""]
    for cat, title, k in CATEGORIES:
        gs = [g for g in asked if g.get("category") == cat]
        if not gs:
            continue
        nc = sum(1 for g in gs if g["corpus"] is None)
        out += [f"## {title}: {len(gs)} gaps, {nc} with no corpus", "",
                "| Source | MCP corpus | Kind | Missing | Old estate held | Years missing (most) |",
                "| --- | --- | --- | ---: | ---: | --- |"]
        out += [_row(g) for g in gs[:k]]
        if len(gs) > k:
            rest = gs[k:]
            out.append(f"\nAnd {len(rest)} smaller ({sum(g['missing'] or 0 for g in rest):,} items) in mcp-gaps.json.")
        out.append("")
    noted = [g for g in fd["noted"] if g["status"] != "gap"]
    if noted:
        out += ["Not asked, shown so the picture is whole:", ""]
        for st in ("boxes", "held", "searched", "derived", "unmeasured"):
            gs = [g for g in noted if g["status"] == st]
            if gs:
                out.append(f"- {NOT_ASKED[st]}: " + "; ".join(f"{g['source']} ({_n(g['old_count'])})" for g in gs[:12])
                           + ("; …" if len(gs) > 12 else ""))
        out.append("")
    if fd["closed"]:
        out += ["Closed (the records have landed): " + ", ".join(c["source"] or c["gap_id"] for c in fd["closed"]) + ".", ""]
    if fd.get("withdrawn"):
        out += ["Withdrawn (no longer asked as a backlog, nothing is said to have landed; anything still asked is named in brackets): "
                + "; ".join(f"{w['source'] or w['gap_id']} ({w['why']})" for w in fd["withdrawn"]) + ".", ""]
    out += ["How it is measured: an old document or page is held when the MCP holds the same address or the same "
            "content sha256. A register the old estate held as rows is compared by count; where the MCP has a corpus "
            "for it, its records are captured pages, not rows, so the count cannot say what is missing (shown as ?) "
            "and the provider is asked to say whether the corpus holds the whole register. The rows carry names, "
            "counts and years only; no record's content and no personal information."]
    return "\n".join(out) + "\n"


# ── reading (I/O) ────────────────────────────────────────────────────────────

def held_from_copy(conn) -> tuple:
    """(Held, cursors) from our copy of the MCP: every address of mcpsource.arrivals and mcpsource.files, every
    file hash a record promised; cursors: corpus -> records taken."""
    held = Held()
    with conn.cursor() as cur:
        cur.execute("SELECT corpus, url, NULL FROM mcpsource.arrivals WHERE url IS NOT NULL "
                    "UNION SELECT corpus, url, capture_sha256 FROM mcpsource.files")
        for corpus, url, sha in cur:
            held.add(corpus, url, sha)
        cursors = dict(conn.execute("SELECT corpus, cursor FROM mcpsource.cursors").fetchall())
    return held, cursors


def held_from_tail(client, corpora: list, cursors: dict, held: Held, page: int = 500, log=None) -> dict:
    """Records past our pull's cursor, metadata only, from the MCP's `records`: their keys into `held`.
    corpus -> records read."""
    read = {}
    for c in corpora:
        name, total = c["name"], int(c.get("records") or 0)
        cur = int(cursors.get(name) or 0)
        n = 0
        while cur < total:
            ans = client.call_retrying("records", {"corpus": name, "cursor": cur, "limit": page, "include_text": False})
            recs = (ans or {}).get("records") or []
            for r in recs:
                urls, shas = record_keys(r)
                for u in urls:
                    held.add(name, u)
                for s in shas:
                    held.add(name, None, s)
            nxt = (ans or {}).get("next_cursor")
            if not recs or nxt is None or nxt <= cur:
                break
            n += len(recs)
            cur = nxt
        read[name] = n
        if log and n:
            log(f"gaps: {name}: {n:,} records past our cursor read for their keys")
    return read


def measure(old_connect, v4_conn, client=None, inventory=None, log=print) -> tuple:
    """(gaps, mcp summary)."""
    held, cursors = held_from_copy(v4_conn)
    corpora = client.call_retrying("corpora", {}).get("corpora") if client else None
    if corpora is None:
        from support.mcpsource import freshness as F
        corpora = [{"name": k, "records": v.get("records")} for k, v in F.latest(v4_conn).items()]
        tail = {}
    else:
        tail = held_from_tail(client, corpora, cursors, held, log=log)
    records = {c["name"]: c.get("records") for c in corpora}
    how_mcp = ("the MCP's holdings are our pull's copy (mcpsource.arrivals, mcpsource.files)"
               + (" and the MCP's `records` past our cursor" if client else
                  "; records past our pull's cursor are not seen (run without --no-mcp to read them)"))
    gaps = []
    conns = {}

    def conn_for(name):
        if name not in conns:
            conns[name] = old_connect(name)
        return conns[name]

    for src in SOURCES:
        rows = conn_for(src.db).execute(src.sql).fetchall()
        if src.match == "count":
            gaps += gaps_of(src, tally_counts(rows), records.get(src.corpus) if src.corpus else None, how_mcp)
        else:
            dates = dates_held(held, src.corpus, src.date_pattern) if src.match == "date" else None
            gaps += gaps_of(src, tally(rows, held, src.match, dates), how_mcp=how_mcp)
        log(f"gaps: {src.id}: {len(rows):,} rows")
    news = conn_for("incoming_news")
    counts = news.execute(ARTICLE_COUNTS).fetchall()
    hosts = held.hosts()
    tags = sorted({t for t, _, _ in counts if any(host_of(t) == h or host_of(t).endswith("." + h) or
                                                  h.endswith("." + host_of(t)) for h in hosts)})
    urls_by_tag: dict = {}
    if tags:
        for tag, url, period in news.execute(ARTICLE_URLS, (tags, tags)).fetchall():
            urls_by_tag.setdefault(tag, []).append((url, period))
    gaps += article_gaps(counts, urls_by_tag, held, how_mcp)
    log(f"gaps: articles: {len(counts):,} tag-years, {len(tags)} tags matched by address")
    docs = news.execute(f"select url, sha256, {_year('created_at')}, source from documents").fetchall()
    gaps += document_gaps(docs, held, how_mcp)
    extra, out_ids = unmeasured(inventory, {s.id for s in SOURCES})
    gaps = [g for g in gaps if g["source_id"] not in out_ids and g["source_id"].split(":", 1)[-1] not in out_ids]
    gaps += extra
    for c in conns.values():
        c.close()
    mcp = {"corpora": len(corpora), "our_copy_cursors": cursors, "tail_read": tail, "records": records}
    return gaps, mcp


def _read_json(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write(text: str, path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="support.mcpsource.gaps")
    ap.add_argument("--print", action="store_true", help="print the page; write nothing")
    ap.add_argument("--no-mcp", action="store_true", help="our copy of the MCP only")
    ap.add_argument("--page", default=GAPS_MD)
    ap.add_argument("--json", default=GAPS_JSON)
    ap.add_argument("--inventory", default=INVENTORY)
    a = ap.parse_args(argv)
    from support import db
    client = None
    if not a.no_mcp:
        from support.mcpsource.client import Client
        client = Client()
    now = dt.datetime.now(dt.timezone.utc)
    with db.connect(db.READ_KEY, "querynz_v4") as v4:
        gaps, mcp = measure(lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10), v4, client,
                            _read_json(a.inventory), log=lambda s: print(s, file=sys.stderr, flush=True))
    fd = feed(gaps, now, previous=_read_json(a.json), mcp=mcp)
    text = page(fd, now)
    if a.print:
        print(text)
        return 0
    _write(json.dumps(fd, ensure_ascii=False, indent=1, sort_keys=True) + "\n", a.json)
    _write(text, a.page)
    print(f"gaps: {len(fd['gaps'])} asked, {len(fd['noted'])} noted, {len(fd['closed'])} closed; "
          f"{a.page}, {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
