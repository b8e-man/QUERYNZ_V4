"""The lane's one figure against the outside world: the MCP's own counts.

`corpora` gives the beehive corpus's record count (its `ingest_cursor`);
`measure` gives, for the corpus, `n_docs` (the documents it counts) and
`corpus_words` (the whitespace words of every record's `text`: measured
26 October, 38,122,105 against the 38,169,497 the first pull's texts hold). Against these:

  taken      the pull's cursor (records taken, each an arrival or a catch line) at least 99% of the MCP's count
  read       every distinct document the pull landed is a release, an older version or a set-aside line
  measured   the MCP's n_docs against the records taken (at least 99%); its corpus_words against the words
             of the MCP records' `text` the releases hold (`text_words`), within 1%
  clean      no pull catch line, no set-aside line, no release with a field the lane has no column for, and no
             model-made field the record names outside topics and quotes

Run bare it answers about the live tables in querynz_v4 under the session
reader (lesson: a lane check run bare answers about the live tables); a
session's scratch proof passes --database, --schema and --mcp-schema.
Prints figures only; exits 1 on a failure.

    python -m registers.beehive.check [--database D --schema S --mcp-schema M]
"""
import argparse
import sys

from support import mcpsource as M

FLOOR = 0.99
WORDS_TOLERANCE = 0.01


def held(conn, schema: str, mcp_schema: str) -> dict:
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
    return {
        "cursor": q(f"SELECT coalesce(max(cursor), 0) FROM {mcp_schema}.cursors WHERE corpus = 'beehive'"),
        "arrivals": q(f"SELECT count(DISTINCT seq) FROM {mcp_schema}.arrivals WHERE corpus = 'beehive'"),
        "documents": q(f"SELECT count(DISTINCT sha256) FROM {mcp_schema}.arrivals WHERE corpus = 'beehive'"),
        "caught": q(f"SELECT count(*) FROM {mcp_schema}.catch WHERE corpus = 'beehive' AND resolved_at IS NULL"),
        "releases": q(f"SELECT count(*) FROM {schema}.releases WHERE mcp_document IS NOT NULL"),
        "captured only": q(f"SELECT count(*) FROM {schema}.releases WHERE mcp_state = 'captured only'"),
        "old estate releases": q(f"SELECT count(*) FROM {schema}.releases WHERE origin = 'old estate'"),
        "old estate only": q(f"SELECT count(*) FROM {schema}.releases WHERE mcp_document IS NULL"),
        "older versions": q(f"SELECT count(*) FROM {schema}.files WHERE status = 'older version'"),
        "set aside": q(f"SELECT count(*) FROM {schema}.set_aside"),
        "files set aside": q(f"SELECT count(*) FROM {schema}.files WHERE status = 'set aside'"),
        "fields unread": q(f"SELECT count(*) FROM {schema}.releases WHERE cardinality(fields_unread) > 0"),
        "annotated outside": q(f"SELECT count(*) FROM {schema}.releases WHERE annotation_fields <> '{{}}' "
                               "AND NOT annotation_fields <@ ARRAY['topics', 'quotes']"),
        "words": q(f"SELECT coalesce(sum(text_words), 0) FROM {schema}.releases WHERE mcp_document IS NOT NULL"),
    }


def outside(client) -> dict:
    listing = client.call_retrying("corpora", {})
    c = next(x for x in listing["corpora"] if x["name"] == "beehive")
    cell = next(x for x in client.call_retrying("measure", {"keywords": ["minister"], "corpora_filter": ["beehive"]})
                ["cells"] if x["corpus"] == "beehive")
    return {"records": c.get("ingest_cursor", c.get("records")), "n_docs": cell["n_docs"],
            "corpus_words": cell["corpus_words"]}


def judge(h: dict, o: dict) -> list:
    """The failures, as plain lines."""
    out = []
    if h["cursor"] < FLOOR * o["records"]:
        out.append(f"taken: the pull holds {h['cursor']} of the MCP's {o['records']} records (floor {FLOOR:.0%})")
    if h["arrivals"] + h["caught"] != h["cursor"]:
        out.append(f"taken: {h['arrivals']} arrivals and {h['caught']} catch lines for a cursor of {h['cursor']}")
    if h["releases"] + h["older versions"] + h["files set aside"] != h["documents"]:
        out.append(f"read: {h['documents']} documents but {h['releases']} releases, {h['older versions']} older "
                   f"versions and {h['files set aside']} set aside")
    if h["cursor"] < FLOOR * o["n_docs"]:
        out.append(f"measured: the MCP measures {o['n_docs']} documents, the pull holds {h['cursor']}")
    if o["corpus_words"] and abs(h["words"] - o["corpus_words"]) > WORDS_TOLERANCE * o["corpus_words"] \
            and h["cursor"] >= o["n_docs"]:
        out.append(f"measured: the MCP counts {o['corpus_words']} words, the releases hold {h['words']}")
    for k in ("caught", "set aside", "fields unread", "annotated outside"):
        if h[k]:
            out.append(f"clean: {h[k]} {k}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.beehive.check")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default="beehive")
    ap.add_argument("--mcp-schema", default="mcpsource")
    ap.add_argument("--owner", action="store_true", help="the owner login (a scratch schema the reader cannot see)")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY if a.owner else db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        h = held(conn, a.schema, a.mcp_schema)
    o = outside(M.Client())
    fails = judge(h, o)
    print("beehive: held " + ", ".join(f"{k} {v}" for k, v in h.items()))
    print("beehive: the MCP " + ", ".join(f"{k} {v}" for k, v in o.items()))
    for f in fails:
        print("beehive: FAIL " + f)
    print("beehive: " + ("green" if not fails else f"red, {len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
