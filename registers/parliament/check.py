"""The lane's one figure against the outside world: the MCP's own counts,
corpus by corpus.

`corpora` gives each corpus's record count (its `ingest_cursor`); `measure`
gives, per corpus, `n_docs` and `corpus_words` (the whitespace words of
every record's `text`). Against these, for each of the seven corpora:

  taken      the pull's cursor (records taken, each an arrival or a catch line) at least 99% of the MCP's count
  read       every distinct document the pull landed is a record read, an older version or a set-aside line
  served     the records read that the MCP still serves equal the pull's cursor (each place holds one record)
  measured   the MCP's n_docs against the cursor (at least 99%); its corpus_words against the words of the
             records' `text` the rows hold (`text_words`, served records only), within 1%
  clean      no pull catch line, no set-aside line, no row with a field the lane has no column for

And for the written questions:

  unique     every served question's number and year unique within its Parliament
  replies    the share of served questions with a reply at least REPLY_FLOOR: measured 27 October 2026 on
             the first full build, 683,517 of 683,524 (all but 7; the API's queue holds answered questions)

Run bare it answers about the live tables in querynz_v4 under the session
reader; a session's scratch proof passes --database, --schema,
--mcp-schema and --owner. Reads no private table. Prints figures only;
exits 1 on a failure.

    python -m registers.parliament.check [--database D --schema S --mcp-schema M --owner]
"""
import argparse
import sys

from support import mcpsource as M
from registers.parliament import capture

FLOOR = 0.99
WORDS_TOLERANCE = 0.01
REPLY_FLOOR = 0.99
TABLE = {c: "api_items" for c in capture.API_CORPORA}
TABLE.update({capture.WRITTEN_QUESTIONS: "written_questions", capture.WAYBACK: "wayback_pages"})


def held(conn, schema: str, mcp_schema: str) -> dict:
    """{corpus: figures} and, under `_wq`, the written questions' own."""
    q = lambda sql, *a: conn.execute(sql, a).fetchone()[0]  # noqa: E731
    out = {}
    for c, t in TABLE.items():
        where = " AND corpus = %s" if t == "api_items" else ""
        args = (c,) if t == "api_items" else ()
        out[c] = {
            "cursor": q(f"SELECT coalesce(max(cursor), 0) FROM {mcp_schema}.cursors WHERE corpus = %s", c),
            # places below the cursor: after the MCP removed records, the places past its new count keep old arrivals
            "arrivals": q(f"SELECT count(DISTINCT a.seq) FROM {mcp_schema}.arrivals a JOIN {mcp_schema}.cursors k "
                          "ON k.corpus = a.corpus WHERE a.corpus = %s AND a.seq < k.cursor", c),
            "documents": q(f"SELECT count(DISTINCT sha256) FROM {mcp_schema}.arrivals WHERE corpus = %s", c),
            "caught": q(f"SELECT count(*) FROM {mcp_schema}.catch WHERE corpus = %s AND resolved_at IS NULL", c),
            "records": q(f"SELECT count(*) FROM {schema}.{t} WHERE true{where}", *args),
            "served": q(f"SELECT count(*) FROM {schema}.{t} WHERE served{where}", *args),
            "older versions": q(f"SELECT count(*) FROM {schema}.files WHERE corpus = %s AND status = 'older version'", c),
            "files set aside": q(f"SELECT count(*) FROM {schema}.files WHERE corpus = %s AND status = 'set aside'", c),
            "set aside": q(f"SELECT count(*) FROM {schema}.set_aside WHERE item LIKE %s", f"{c} seq %")
                         + q(f"SELECT count(*) FROM {schema}.set_aside s JOIN {schema}.files f ON f.sha256 = s.item "
                             "WHERE f.corpus = %s", c),
            "fields unread": q(f"SELECT count(*) FROM {schema}.{t} WHERE cardinality(fields_unread) > 0{where}", *args),
            "words": q(f"SELECT coalesce(sum(text_words), 0) FROM {schema}.{t} WHERE served{where}", *args),
        }
    wq = f"{schema}.written_questions"
    out["_wq"] = {
        "served": q(f"SELECT count(*) FROM {wq} WHERE served"),
        "number repeated": q(f"SELECT coalesce(sum(n - 1), 0) FROM (SELECT count(*) n FROM {wq} WHERE served "
                             "GROUP BY parliament_number, question_year, question_number HAVING count(*) > 1) d"),
        "replied": q(f"SELECT count(*) FROM {wq} WHERE served AND reply_present"),
        "withdrawn": q(f"SELECT count(*) FROM {wq} WHERE NOT served"),
    }
    return out


def outside(client) -> dict:
    listing = client.call_retrying("corpora", {})
    cells = client.call_retrying("measure", {"keywords": ["minister"], "corpora_filter": list(capture.CORPORA)})["cells"]
    out = {}
    for c in capture.CORPORA:
        rec = next((x for x in listing["corpora"] if x["name"] == c), None)
        cell = next((x for x in cells if x["corpus"] == c), None)
        out[c] = {"records": rec.get("ingest_cursor", rec.get("records")) if rec else None,
                  "n_docs": cell["n_docs"] if cell else None, "corpus_words": cell["corpus_words"] if cell else None}
    return out


def judge(h: dict, o: dict) -> list:
    """The failures, as plain lines."""
    out = []
    for c in capture.CORPORA:
        x, y = h[c], o.get(c) or {}
        if not y.get("records"):
            out.append(f"{c}: the MCP no longer lists the corpus")
            continue
        if x["cursor"] < FLOOR * y["records"]:
            out.append(f"{c}: taken {x['cursor']} of the MCP's {y['records']} records (floor {FLOOR:.0%})")
        if x["arrivals"] + x["caught"] != x["cursor"]:
            out.append(f"{c}: {x['arrivals']} places arrived and {x['caught']} caught for a cursor of {x['cursor']}")
        if x["records"] + x["older versions"] + x["files set aside"] != x["documents"]:
            out.append(f"{c}: read {x['documents']} documents but {x['records']} records, {x['older versions']} "
                       f"older versions and {x['files set aside']} set aside")
        if x["served"] != x["cursor"] - x["caught"]:
            out.append(f"{c}: {x['served']} records the MCP still serves for {x['cursor'] - x['caught']} places taken")
        if y.get("n_docs") is not None and x["cursor"] < FLOOR * y["n_docs"]:
            out.append(f"{c}: the MCP measures {y['n_docs']} documents, the pull holds {x['cursor']}")
        if y.get("corpus_words") and x["cursor"] >= (y.get("n_docs") or 0) \
                and abs(x["words"] - y["corpus_words"]) > WORDS_TOLERANCE * y["corpus_words"]:
            out.append(f"{c}: the MCP counts {y['corpus_words']} words, the rows hold {x['words']}")
        for k in ("caught", "set aside", "fields unread"):
            if x[k]:
                out.append(f"{c}: {x[k]} {k}")
    w = h["_wq"]
    if w["number repeated"]:
        out.append(f"written questions: {w['number repeated']} served rows repeat a number and year within a Parliament")
    if w["served"] and w["replied"] < REPLY_FLOOR * w["served"]:
        out.append(f"written questions: {w['replied']} of {w['served']} replied ({w['replied'] / w['served']:.1%}), "
                   f"below {REPLY_FLOOR:.0%}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers.parliament.check")
    ap.add_argument("--database", default="querynz_v4")
    ap.add_argument("--schema", default="parliament")
    ap.add_argument("--mcp-schema", default="mcpsource")
    ap.add_argument("--owner", action="store_true", help="the owner login (a scratch schema the reader cannot see)")
    a = ap.parse_args(argv)
    from support import db
    with db.connect(db.OWNER_KEY if a.owner else db.READ_KEY, a.database) as conn:
        conn.execute("SET statement_timeout = '60s'")
        h = held(conn, a.schema, a.mcp_schema)
    o = outside(M.Client())
    fails = judge(h, o)
    for c in capture.CORPORA:
        print(f"parliament: {c}: held " + ", ".join(f"{k} {v}" for k, v in h[c].items())
              + "; the MCP " + ", ".join(f"{k} {v}" for k, v in o[c].items()))
    w = h["_wq"]
    print("parliament: written questions " + ", ".join(f"{k} {v}" for k, v in w.items())
          + (f", replied share {w['replied'] / w['served']:.2%}" if w["served"] else ""))
    for f in fails:
        print("parliament: FAIL " + f)
    print("parliament: " + ("green" if not fails else f"red, {len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
