"""The lane's one figure against the outside world: the MCP's own counts.

`corpora` gives the parliament-diaries corpus's record count (its
`ingest_cursor`); `measure` gives `n_docs` (the records it counts) and
`corpus_words` (the whitespace words of every record's `text`: 4,764,189 on
27 October, the same as the 208,464 entries' `text_words`). Against these:

  taken      the pull's cursor at least 99% of the MCP's count, every record taken an arrival or a catch line
  read       every distinct document the pull landed is an entry, an older version or a set-aside line
  measured   the MCP's n_docs against the records taken (at least 99%); its corpus_words against the words of
             the entries' `text` (within 1%)
  releases   every release's entries counted: each release's `entries` is the entries that name it, they sum
             to the entries, and each release names one minister
  clean      no pull catch line, no set-aside line, no entry with a field the lane has no column for

Stated, never a failure: the release's withholdings (entries and fields), the
entries each flag marks (`location_names_home`, `location_street_only`,
`meeting_names_address`, `attendees_names_address`: counted, never
printed; a product applies hard limit 15 by them, ruling 102), the releases with no PDF
address or no month, the entries before 2019, and the ministers named
against the House's `pub.members`. That last is by the register's own title
words only ("Rt Hon", "Hon", "Dr", "KC" taken off the name as released), then
`keys.names.person_key` against the published `name_key`: exact or not at all,
counted, never matched by looking. pub.members holds the 2020 and 2023
Parliaments, so a minister who left before 2020 is counted as not found. Nothing
is written: the match is a count, not a link.

Run bare it answers about the live tables in querynz_v4 under the session
reader; a session's scratch proof passes --database, --schema, --mcp-schema
and --owner. Prints figures only; exits 1 on a failure.

    python -m registers.ministers_diaries.check [--database D --schema S --mcp-schema M --owner]
"""
import argparse
import re
import sys

from keys import names as N
from support import mcpsource as M
from registers.ministers_diaries.read import FLAGS

CORPUS = "parliament-diaries"
FLOOR = 0.99
WORDS_TOLERANCE = 0.01
TITLE_WORDS = re.compile(r"^(?:(?:rt\.?\s+hon|hon|dr)\.?\s+)+|[\s,]+kc\.?$", re.I)


def held(conn, schema: str, mcp_schema: str) -> dict:
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
    return {
        "cursor": q(f"SELECT coalesce(max(cursor), 0) FROM {mcp_schema}.cursors WHERE corpus = %s", CORPUS),
        "arrivals": q(f"SELECT count(DISTINCT seq) FROM {mcp_schema}.arrivals WHERE corpus = %s", CORPUS),
        "documents": q(f"SELECT count(DISTINCT sha256) FROM {mcp_schema}.arrivals WHERE corpus = %s", CORPUS),
        "caught": q(f"SELECT count(*) FROM {mcp_schema}.catch WHERE corpus = %s AND resolved_at IS NULL", CORPUS),
        "entries": q(f"SELECT count(*) FROM {schema}.entries"),
        "releases": q(f"SELECT count(*) FROM {schema}.releases"),
        "older versions": q(f"SELECT count(*) FROM {schema}.files WHERE status = 'older version'"),
        "files set aside": q(f"SELECT count(*) FROM {schema}.files WHERE status = 'set aside'"),
        "set aside": q(f"SELECT count(*) FROM {schema}.set_aside"),
        "fields unread": q(f"SELECT count(*) FROM {schema}.entries WHERE cardinality(fields_unread) > 0"),
        "words": q(f"SELECT coalesce(sum(text_words), 0) FROM {schema}.entries"),
        "release entries": q(f"SELECT coalesce(sum(entries), 0) FROM {schema}.releases"),
        "releases miscounted": q(f"SELECT count(*) FROM {schema}.releases r LEFT JOIN (SELECT release, count(*) n "
                                 f"FROM {schema}.entries GROUP BY release) e ON e.release = r.key "
                                 "WHERE coalesce(e.n, 0) <> r.entries"),
        "entries with no release": q(f"SELECT count(*) FROM {schema}.entries e WHERE NOT EXISTS "
                                     f"(SELECT 1 FROM {schema}.releases r WHERE r.key = e.release)"),
        "releases naming more than one minister": q(f"SELECT count(*) FROM {schema}.releases WHERE ministers_named <> 1"),
        # stated
        "ministers": q(f"SELECT count(DISTINCT minister) FROM {schema}.entries"),
        "entries with a withholding": q(f"SELECT count(*) FROM {schema}.entries WHERE withheld <> '{{}}'"),
        "withheld fields": q(f"SELECT coalesce(sum(cardinality(withheld)), 0) FROM {schema}.entries"),
        **{f: q(f"SELECT count(*) FROM {schema}.entries WHERE {f}") for f in FLAGS},
        "releases with no PDF address": q(f"SELECT count(*) FROM {schema}.releases WHERE pdf_url IS NULL"),
        "releases with no month": q(f"SELECT count(*) FROM {schema}.releases WHERE month IS NULL"),
        "entries before 2019": q(f"SELECT count(*) FROM {schema}.entries WHERE entry_on < '2019-01-01'"),
    }


def bare(name: str) -> str:
    """The name as released with the register's own title words taken off."""
    return TITLE_WORDS.sub("", N.squash(name)).strip(" ,")


def ministers_against_members(ministers: list, member_keys: set) -> dict:
    """How many of the ministers, by name as released, find a member's
    `name_key` exactly once their title words are off."""
    found = [m for m in ministers if N.person_key(bare(m)) in member_keys]
    return {"ministers named": len(ministers), "found in pub.members": len(found),
            "not found": len(ministers) - len(found)}


def outside(client) -> dict:
    listing = client.call_retrying("corpora", {})
    c = next(x for x in listing["corpora"] if x["name"] == CORPUS)
    cell = next(x for x in client.call_retrying("measure", {"keywords": ["minister"], "corpora_filter": [CORPUS]})
                ["cells"] if x["corpus"] == CORPUS)
    return {"records": c.get("ingest_cursor", c.get("records")), "n_docs": cell["n_docs"],
            "corpus_words": cell["corpus_words"]}


def judge(h: dict, o: dict) -> list:
    """The failures, as plain lines."""
    out = []
    if h["cursor"] < FLOOR * o["records"]:
        out.append(f"taken: the pull holds {h['cursor']} of the MCP's {o['records']} records (floor {FLOOR:.0%})")
    if h["arrivals"] + h["caught"] != h["cursor"]:
        out.append(f"taken: {h['arrivals']} arrivals and {h['caught']} catch lines for a cursor of {h['cursor']}")
    if h["entries"] + h["older versions"] + h["files set aside"] != h["documents"]:
        out.append(f"read: {h['documents']} documents but {h['entries']} entries, {h['older versions']} older "
                   f"versions and {h['files set aside']} set aside")
    if h["cursor"] < FLOOR * o["n_docs"]:
        out.append(f"measured: the MCP measures {o['n_docs']} records, the pull holds {h['cursor']}")
    if o["corpus_words"] and abs(h["words"] - o["corpus_words"]) > WORDS_TOLERANCE * o["corpus_words"] \
            and h["cursor"] >= o["n_docs"]:
        out.append(f"measured: the MCP counts {o['corpus_words']} words, the entries hold {h['words']}")
    if h["release entries"] != h["entries"]:
        out.append(f"releases: the releases count {h['release entries']} entries, the entries are {h['entries']}")
    for k in ("releases miscounted", "entries with no release", "releases naming more than one minister"):
        if h[k]:
            out.append(f"releases: {h[k]} {k}")
    for k in ("caught", "set aside", "fields unread"):
        if h[k]:
            out.append(f"clean: {h[k]} {k}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.ministers_diaries.check")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default="ministers_diaries")
    ap.add_argument("--mcp-schema", default="mcpsource")
    ap.add_argument("--members-database", default="querynz_v4", help="where pub.members is read (the session reader)")
    ap.add_argument("--owner", action="store_true", help="the owner login (a scratch schema the reader cannot see)")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY if a.owner else db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        h = held(conn, a.schema, a.mcp_schema)
        ministers = [r[0] for r in conn.execute(f"SELECT DISTINCT minister FROM {a.schema}.entries "
                                                "WHERE minister IS NOT NULL ORDER BY 1")]
    with db.connect(db.READ_KEY, a.members_database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        member_keys = {r[0] for r in conn.execute("SELECT DISTINCT name_key FROM pub.members WHERE name_key IS NOT NULL")}
    m = ministers_against_members(ministers, member_keys)
    o = outside(M.Client())
    fails = judge(h, o)
    print("ministers_diaries: held " + ", ".join(f"{k} {v}" for k, v in h.items()))
    print("ministers_diaries: against pub.members by title words only " + ", ".join(f"{k} {v}" for k, v in m.items()))
    print("ministers_diaries: the MCP " + ", ".join(f"{k} {v}" for k, v in o.items()))
    for f in fails:
        print("ministers_diaries: FAIL " + f)
    print("ministers_diaries: " + ("green" if not fails else f"red, {len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
