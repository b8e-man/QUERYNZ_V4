"""The lane's one figure against the outside world: the MCP's own counts,
corpus by corpus.

`corpora` gives each corpus's record count (its `ingest_cursor`); `measure`
gives, per corpus, `n_docs` and `corpus_words` (the whitespace words of
every record's `text`). Against these, for each of the seven corpora:

  taken      the pull's cursor (records taken, each an arrival or a catch line) at least 99% of the MCP's count
  read       every distinct document the pull landed is a record read, an older version or a set-aside line
  served     the records read that the MCP still serves, plus the pages set aside as blocked, equal the pull's
             cursor (each place holds one record)
  blocked    an archived page that is the site's refusal (read.BLOCKED, hard limit 6) is set aside: counted and
             stated on the line, never a failure; any other set-aside line is one
  measured   the MCP's n_docs against the cursor (at least 99%); its corpus_words against the words of the
             records' `text` the rows hold (`text_words`, served records only), within 1%
  clean      no pull catch line, no set-aside line, no row with a field the lane has no column for

And for the written questions:

  unique     every served question's number and year unique within its Parliament
  replies    the share of served questions with a reply at least REPLY_FLOOR: measured 27 October 2026 on
             the first full build, 683,517 of 683,524 (all but 7; the API's queue holds answered questions)

And over the published views (hard limit 15, ruling 102), with a second
pattern written apart from shapes.py, in Postgres's own regular
expressions, so a flag the load stopped setting cannot pass silently:

  flagged    each flag column's true count is stated, and equals the load's `address_flags` lines for it
  street     no text column of a view (every `text`, `varchar` or `jsonb` column, found by introspection, so a
             column added later is searched too) holds a house number and a street where its
             `<column>_names_address` flag is false or absent. The pattern runs over every row once, at the
             load, after the views are refreshed (load.stamp_scan, `street_scan`: per column the rows scanned,
             their load stamp and the count found); the check holds that stamp to the view (every text column
             stamped, the same rows and the same load, nothing found) and scans afresh a fixed sample, the
             SAMPLE rows of each view first by md5 of their key, as the proof the stamp is honest. A whole
             scan of every row took 1 min 55 s on 28 October 2026 (683,524 questions, 8,836 long pages) and
             the board gives a check 120 s, so the check never runs one

Run bare it answers about the live tables in querynz_v4 under the session
reader; a session's scratch proof passes --database, --schema,
--mcp-schema and --owner (the views of a proof are `<schema>.pub_parliament_*`,
load.views). Reads no private table. Prints figures only, never a value;
exits 1 on a failure.

    python -m registers.parliament.check [--database D --schema S --mcp-schema M --owner]
"""
import argparse
import sys

from support import mcpsource as M
from registers.parliament import capture, read

FLOOR = 0.99
WORDS_TOLERANCE = 0.01
REPLY_FLOOR = 0.99
TABLE = {c: "api_items" for c in capture.API_CORPORA}
TABLE.update({capture.WRITTEN_QUESTIONS: "written_questions", capture.WAYBACK: "wayback_pages"})
VIEWS = ("written_questions", "api_items", "wayback_pages")
FLAG = "_names_address"
SAMPLE = 5000           # rows of each view the check scans afresh; the load scans every row (load.stamp_scan)
# a house number and a street, as Postgres reads it (ARE): not after a letter, a digit or a unit's slash, nor after
# the word a highway's, a law's or a list's number follows; not a year; one to four capitalised words; the street's
# kind; and not the start of a company's name ("12 Sample Street Limited")
_KIND_WORDS = ("Street St Road Rd Avenue Ave Drive Dr Place Pl Crescent Cres Terrace Tce Lane Way Parade Highway Hwy "
               "Grove Close Court Ct Rise Quay Square Boulevard Esplanade Track Mews Heights Glade Row Loop Walk "
               "Promenade Strand Mall Circle Common Ridge Vale Downs Line Valley Hill View Green Gardens Park Point "
               "Reach Key").split()
_NOT_AFTER = ("Highway highway Hwy SH No No. no. Act Regulations Rule Order Notice Section section Schedule schedule "
              "Part part Clause clause Reg Route route Question question Bill bill Level level Alert alert Phase phase "
              "Stage stage Tranche").split()
STREET_SQL = (r"(?<![[:alnum:]_/.,-])"
              + "(?<!(?:" + "|".join(w.replace(".", r"\.") for w in _NOT_AFTER) + r") )"
              + r"(?!(?:18|19|20)[0-9]{2}\M)[0-9]{1,4}[A-Za-z]?(?:\s*[-/]\s*[0-9]{1,4}[A-Za-z]?)?,?\s+"
              + r"(?:[A-Z][[:alnum:]_'’.-]*\s+){1,4}"
              + "(?:" + "|".join(sorted({w for k in _KIND_WORDS for w in (k, k.upper())}, key=len, reverse=True)) + r")\M"
              + r"(?![\s,]*(?:[A-Z(][[:alnum:]_'’&().-]*\s+){0,4}(?:Limited|Ltd|LIMITED|LTD|Incorporated|Inc)\M)")


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
                             "WHERE f.corpus = %s AND s.reason <> %s", c, read.BLOCKED),
            "blocked": q(f"SELECT count(*) FROM {schema}.set_aside s JOIN {schema}.files f ON f.sha256 = s.item "
                         "WHERE f.corpus = %s AND s.reason = %s", c, read.BLOCKED),
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


def view_name(schema: str, v: str) -> tuple:
    """(schema, view) of a published view: `pub.parliament_<v>` live, `<schema>.pub_parliament_<v>` in a proof."""
    return ("pub", f"parliament_{v}") if schema == "parliament" else (schema, f"pub_parliament_{v}")


def texts_of(conn, vs: str, vn: str) -> tuple:
    """(every column, the text columns) of a view, by introspection."""
    cols = conn.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = %s "
                        "AND table_name = %s ORDER BY ordinal_position", (vs, vn)).fetchall()
    return [c for c, _ in cols], [c for c, t in cols if t in ("text", "character varying", "jsonb")]


def street_counts(conn, vs: str, vn: str, sample: int = None) -> tuple:
    """(rows read, {text column: rows holding a street with its flag false or absent}) over the view, or over
    its first `sample` rows by md5 of the key (a fixed sample: the same rows while the keys stay)."""
    names, texts = texts_of(conn, vs, vn)
    parts = ["count(*)"]
    for c in texts:
        f = c + FLAG
        parts.append(f'count(*) FILTER (WHERE "{c}"::text ~ %(p)s'
                     + (f' AND NOT coalesce("{f}", false))' if f in names else ")"))
    where = (f' WHERE key IN (SELECT key FROM "{vs}"."{vn}" ORDER BY md5(key) LIMIT %(n)s)'
             if sample is not None else "")
    row = conn.execute(f'SELECT {", ".join(parts)} FROM "{vs}"."{vn}"{where}',
                       {"p": STREET_SQL, "n": sample}).fetchone()
    return row[0], dict(zip(texts, row[1:]))


def shown(conn, schema: str, shared: bool = False) -> dict:
    """{view: {"rows": n, "loaded": the rows' load stamp, "flagged": {column: n}, "lines": {column: n},
    "sampled": n, "street unflagged": {column: n in the sample}, "scan": {column: (rows, loaded, found)}}}.
    shared: the sample's schema, where the lane's tables carry its name (load.table)."""
    pre = f"{schema}.parliament_" if shared else f"{schema}."
    q = lambda sql, *a: conn.execute(sql, a).fetchall()  # noqa: E731
    stamped = q("SELECT to_regclass(%s)", f"{pre}street_scan")[0][0] is not None     # none before the first load
    out = {}
    for v in VIEWS:
        vs, vn = view_name(schema, v)
        names, _ = texts_of(conn, vs, vn)
        flags = [c for c in names if c.endswith(FLAG)]
        row = conn.execute(f'SELECT count(*), max(loaded_at), '
                           + ", ".join([f'count(*) FILTER (WHERE "{f}")' for f in flags] or ["0"])
                           + f' FROM "{vs}"."{vn}"').fetchone()
        sampled, unflagged = street_counts(conn, vs, vn, SAMPLE)
        lines = dict(q(f"SELECT column_name, count(*) FROM {pre}address_flags WHERE table_name = %s "
                       "GROUP BY column_name", v))
        scan = {c: (n, at, found) for c, n, at, found in
                (q(f"SELECT column_name, rows, loaded_at, found FROM {pre}street_scan WHERE view_name = %s", v)
                 if stamped else [])}
        out[v] = {"rows": row[0], "loaded": row[1], "flagged": {f[:-len(FLAG)]: n for f, n in zip(flags, row[2:])},
                  "lines": lines, "sampled": sampled, "street unflagged": unflagged, "scan": scan}
    return out


def judge_shown(s: dict) -> list:
    out = []
    for v, x in s.items():
        if not x["flagged"]:
            out.append(f"{v}: the view carries no `{FLAG}` flag")
        for c, n in x["flagged"].items():
            if n != x["lines"].get(c, 0):
                out.append(f"{v}.{c}: {n} rows flagged but {x['lines'].get(c, 0)} address_flags lines")
        if not x["scan"]:
            out.append(f"{v}: the load's whole scan has no line for the view (load.stamp_scan)")
        flag = lambda c: f"`{c}{FLAG}` false" if c in x["flagged"] else "no flag beside the column"  # noqa: E731
        for c, n in x["street unflagged"].items():
            if n:
                out.append(f"{v}.{c}: {n} rows hold a street address with {flag(c)}")
            if c not in x["scan"]:
                if x["scan"]:
                    out.append(f"{v}.{c}: the load's whole scan has no line for the column")
                continue
            rows, at, found = x["scan"][c]
            if (rows, at) != (x["rows"], x["loaded"]):
                out.append(f"{v}.{c}: the load's whole scan read {rows} rows of another load, not the "
                           f"{x['rows']} the view holds")
            elif found:
                out.append(f"{v}.{c}: {found} rows hold a street address with {flag(c)} (the load's whole scan)")
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
        if x["served"] + x["blocked"] != x["cursor"] - x["caught"]:
            out.append(f"{c}: {x['served']} records the MCP still serves and {x['blocked']} blocked for "
                       f"{x['cursor'] - x['caught']} places taken")
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
        conn.execute("SET statement_timeout = '60s'")        # the pattern over a fixed sample, never every row
        s = shown(conn, a.schema)
    o = outside(M.Client())
    fails = judge(h, o) + judge_shown(s)
    for c in capture.CORPORA:
        print(f"parliament: {c}: held " + ", ".join(f"{k} {v}" for k, v in h[c].items())
              + "; the MCP " + ", ".join(f"{k} {v}" for k, v in o[c].items()))
    w = h["_wq"]
    print("parliament: written questions " + ", ".join(f"{k} {v}" for k, v in w.items())
          + (f", replied share {w['replied'] / w['served']:.2%}" if w["served"] else ""))
    for v, x in s.items():
        print(f"parliament: {v}: {x['rows']} rows; names an address by shape: "
              + ", ".join(f"{c} {n}" for c, n in x["flagged"].items())
              + f"; a street with no flag: {sum(x['street unflagged'].values())} in a fixed sample of "
              f"{x['sampled']}, {sum(f for _, _, f in x['scan'].values())} in the load's whole scan of "
              f"{min((n for n, _, _ in x['scan'].values()), default=0)}")
    for f in fails:
        print("parliament: FAIL " + f)
    print("parliament: " + ("green" if not fails else f"red, {len(fails)} failure(s)"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
