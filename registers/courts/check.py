"""The lane's check against the outside world (contract: the lane): the
MCP's courts corpus against what the lane made of it, and the reading's own
account.

  1. The count: every record of the corpus (the pull's arrivals, one per
     record id) is a `documents` row whose outcome is read, waiting on a
     reader (the page reader for a page with no text layer, the text reader
     for the model reading), set aside, or caught; a record in none fails,
     and so does a row read with no reading behind it (a judgment row, a case
     row or a sheet). The old listing's judgments the corpus lacks are
     counted as catch-log lines (stage `listing`), never rows.
  2. parsed / partial / unparsed, and the per-field missing counts.
  3. Suppression: judgments flagged and their kinds, names withheld; a
     published party name in a judgment under suppression (the Crown and a
     court-printed initial apart) fails; a model-read name on a document a
     suppression reaches (judges, counsel, agencies and the Crown apart)
     fails; a withheld name present in a published table fails.
  4. Every role a counsel line is "for" held by a party of the caption
     (`caption.roles_unaccounted`), re-read from the stored readings of a
     fixed sample of judgments: more than `ROLES_TOLERATED` short fails.

    account(conn, schema, shared=False)    dict
    python -m registers.courts.check [--schema courts] [--database querynz_v4] [--sample]

Read-only. Exit 1 on a failure.
"""
import sys

from registers.courts import capture
from registers.courts import load as L
from registers.courts import read as R

ROLES_TOLERATED = 2
ROLES_SAMPLE = 200          # judgments re-read for the counsel-role check (lessons: a check scans a fixed sample)


def account(conn, schema: str = L.SCHEMA, shared: bool = False, mcp_schema: str = None) -> dict:
    t = lambda name: L.table(schema, name, shared)  # noqa: E731
    q = lambda sql, *a: conn.execute(sql, a).fetchall()  # noqa: E731
    out = {"failures": []}
    docs = q(f"SELECT key, document, kind, outcome, profile FROM {t('documents')}")
    out["records"] = len(docs)
    out["outcomes"] = dict(q(f"SELECT outcome, count(*) FROM {t('documents')} GROUP BY 1 ORDER BY 1"))
    out["profiles"] = dict(q(f"SELECT coalesce(profile, '(none)'), count(*) FROM {t('documents')} GROUP BY 1 ORDER BY 2 DESC"))
    allowed = {"read", R.WAIT_PAGES, R.WAIT_TEXT, "set aside", "caught"}
    for key, _, _, outcome, _ in docs:
        if outcome not in allowed:
            out["failures"].append(f"{key[-40:]}: outcome {outcome!r} is none of read, waiting, set aside, caught")
    # a record the pull took that the lane has no row for
    if mcp_schema or not shared:
        ms = mcp_schema or capture.MCP_SCHEMA
        held = conn.execute("SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'arrivals'", (ms,)).fetchone()
        if held:
            taken = q(f"SELECT count(DISTINCT record_id) FROM {ms}.arrivals WHERE corpus = %s", capture.CORPUS)[0][0]
            out["taken by the pull"] = taken
            if taken != len(docs):
                out["failures"].append(f"the pull took {taken} records, the lane has {len(docs)} document rows")
    # a row read has its reading: a judgment, a case, or a sheet (citation, case numbers or a date read)
    judged = {r[0] for r in q(f"SELECT document FROM {t('judgments')}")}
    cased = {r[0] for r in q(f"SELECT document FROM {t('cases')}")}
    sheets = {r[0] for r in q(f"SELECT document FROM {t('documents')} WHERE outcome IN ('read', %s) AND "
                              f"(citation IS NOT NULL OR cardinality(case_numbers) > 0 OR dated IS NOT NULL OR summary IS NOT NULL)", R.WAIT_TEXT)}
    for key, doc, kind, outcome, profile in docs:
        if outcome in ("read", R.WAIT_TEXT):
            if profile in R.JUDGMENT_SLUGS and doc not in judged:
                out["failures"].append(f"{key[-40:]}: a judgment read with no judgment row")
            elif profile == R.CASE_PAGE and doc not in cased:
                out["failures"].append(f"{key[-40:]}: a case page read with no case row")
    out["sheets with a fact read"] = len(sheets)
    # a document is its bytes: a file under several records is read once, each record's row carrying the reading
    out["records sharing a file"] = q(f"SELECT count(*) - count(DISTINCT document) FROM {t('documents')} WHERE document IS NOT NULL")[0][0]
    for sha, n in q(f"SELECT document, count(*) FROM {t('cases')} GROUP BY 1 HAVING count(*) > 1") + \
            q(f"SELECT document, count(*) FROM {t('judgments')} GROUP BY 1 HAVING count(*) > 1"):
        out["failures"].append(f"{sha[:12]}…: a file read {n} times")
    aside = q(f"SELECT stage, count(*) FROM {t('set_aside')} GROUP BY 1 ORDER BY 1")
    out["set aside"] = dict(aside)
    out["status"] = dict(q(f"SELECT status, count(*) FROM {t('judgments')} GROUP BY 1 ORDER BY 1"))
    out["courts"] = dict(q(f"SELECT coalesce(court, '?'), count(*) FROM {t('judgments')} GROUP BY 1 ORDER BY 2 DESC"))
    out["missing"] = dict(q(f"SELECT m, count(*) FROM {t('judgments')}, unnest(missing) m GROUP BY 1 ORDER BY 1"))
    for col in ("registry", "judges", "heading", "hearing"):
        out["missing"][f"{col} (not printed or not read)"] = q(f"SELECT count(*) FROM {t('judgments')} WHERE {col} IS NULL")[0][0]
    out["missing"]["outcome (none in the orders)"] = q(f"SELECT count(*) FROM {t('judgments')} WHERE outcome = '{{}}'")[0][0]
    out["parties"] = dict(zip(("parties", "withheld", "anonymised", "crown", "low"), q(
        f"SELECT count(*), count(*) FILTER (WHERE withheld), count(*) FILTER (WHERE anonymised), "
        f"count(*) FILTER (WHERE crown), count(*) FILTER (WHERE confidence = 'low') FROM {t('judgment_parties')}")[0]))
    out["people"] = dict(zip(("names", "withheld", "persons", "bodies", "documents"), q(
        f"SELECT count(*), count(*) FILTER (WHERE withheld), count(*) FILTER (WHERE kind = 'person'), "
        f"count(*) FILTER (WHERE kind = 'body'), count(DISTINCT document) FROM {t('people')}")[0]))
    out["people"].update(dict(q(f"SELECT role, count(*) FROM {t('people')} GROUP BY 1 ORDER BY 2 DESC")))
    out["cases"] = dict(zip(("cases", "with a citation", "with a judgment date", "with a hearing date", "links", "links to a held document"), q(
        f"SELECT count(*), count(citation), count(date_of_judgment), count(date_of_hearing), "
        f"(SELECT count(*) FROM {t('case_links')}), (SELECT count(linked_document) FROM {t('case_links')}) FROM {t('cases')}")[0]))
    out["suppression"] = {"judgments flagged": q(f"SELECT count(*) FROM {t('judgments')} WHERE suppression")[0][0],
                          "names withheld": out["parties"]["withheld"], "model-read names withheld": out["people"]["withheld"],
                          "cases withheld": q(f"SELECT count(*) FROM {t('cases')} WHERE suppression")[0][0],
                          **dict(q(f"SELECT k, count(*) FROM {t('judgments')}, unnest(suppression_kinds) k GROUP BY 1 ORDER BY 1"))}
    leaked = q(f"SELECT p.key FROM {t('judgment_parties')} p JOIN {t('judgments')} j ON j.key = p.judgment "
               "WHERE j.suppression AND p.name IS NOT NULL AND NOT p.crown AND NOT p.anonymised")
    for (k,) in leaked:
        out["failures"].append(f"{k[:12]}…{k[64:]}: a name published in a judgment under suppression")
    # a model-read name on a document a suppression reaches: the judgment's own, or a document of its citation or case
    reach = q(f"""
        WITH s AS (SELECT document, citation, case_slug FROM {t('judgments')} WHERE suppression)
        SELECT n.key FROM {t('people')} n
         WHERE n.name IS NOT NULL AND n.role NOT IN ('judge', 'counsel', 'agency')
           AND (n.document IN (SELECT document FROM s)
                OR (n.citation IS NOT NULL AND n.citation IN (SELECT citation FROM s WHERE citation IS NOT NULL))
                OR (n.case_slug IS NOT NULL AND n.case_slug IN (SELECT case_slug FROM s WHERE case_slug IS NOT NULL)))
           AND upper(n.name) !~ %s""", R.caption.CROWN.pattern)
    for (k,) in reach:
        out["failures"].append(f"{k[:12]}…{k[64:]}: a model-read name published on a document a suppression reaches")
    shown = q(f"SELECT count(*) FROM {t('judgment_parties')} WHERE withheld AND (name IS NOT NULL OR capacity IS NOT NULL)")[0][0]
    shown += q(f"SELECT count(*) FROM {t('people')} WHERE withheld AND name IS NOT NULL")[0][0]
    shown += q(f"SELECT count(*) FROM {t('cases')} WHERE withheld IS NOT NULL AND case_name IS NOT NULL")[0][0]
    if shown:
        out["failures"].append(f"{shown} withheld names still in a published table")
    orders = q(f"SELECT count(*) FROM {t('suppression_orders')}")[0][0] if _exists(conn, t("suppression_orders")) else 0
    out["suppression"]["orders in the ledger"] = orders
    short = roles_short(conn, schema, shared)
    out["roles short"] = len(short)
    if len(short) > ROLES_TOLERATED:
        out["failures"].append(f"{len(short)} judgments whose counsel lines name a role no party holds (tolerated {ROLES_TOLERATED})")
    return out


def _exists(conn, name: str) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL", (name,)).fetchone()[0]


def roles_short(conn, schema: str, shared: bool = False, limit: int = ROLES_SAMPLE) -> list:
    """Judgments whose counsel lines name a role no party holds, re-read from
    the stored text-layer readings of a fixed sample (by md5 of the key; the
    counsel lines are never stored)."""
    from support import reader as rd
    from support.docread.read import TEXT_MODEL
    from registers.courts import caption
    store, out = rd.Store(), []
    rows = conn.execute(f"SELECT key, document, profile, profile_version, caption_shape FROM {L.table(schema, 'judgments', shared)} "
                        f"ORDER BY md5(key) LIMIT %s", (limit,)).fetchall()
    for key, doc, slug, version, shape in rows:
        try:
            texts = {p: store.get(rd.reading_key(doc, p, TEXT_MODEL, {"tool": "pdftotext -layout"}, slug, version)).text
                     for p in (1, 2)}
        except rd.MissingReading:
            continue
        j = caption.Judgment(counsel_roles=caption._counsel_roles(texts[1] + "\n" + texts[2]), caption_shape=shape)
        j.parties = [caption.Party(name="", role=r[0], position=0, block=0) for r in conn.execute(
            f"SELECT role FROM {L.table(schema, 'judgment_parties', shared)} WHERE judgment = %s", (key,))]
        if caption.roles_unaccounted(j):
            out.append(key)
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else L.SCHEMA
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    shared = "--sample" in argv
    from support import db
    with db.connect(db.OWNER_KEY if shared or schema != L.SCHEMA else db.READ_KEY, database) as conn:
        conn.execute("SET statement_timeout = '120s'")
        out = account(conn, schema, shared)
    print(f"corpus {capture.CORPUS}: {out['records']} records" + (f" ({out['taken by the pull']} taken by the pull)" if "taken by the pull" in out else ""))
    for k in ("outcomes", "profiles", "set aside", "status", "courts", "missing", "parties", "people", "cases", "suppression"):
        print(f"{k}: " + ", ".join(f"{a} {b}" for a, b in out[k].items()))
    print(f"sheets with a fact read: {out['sheets with a fact read']}; records sharing a file: {out['records sharing a file']}; "
          f"roles short: {out['roles short']} (tolerated {ROLES_TOLERATED})")
    for f in out["failures"]:
        print("FAIL " + f)
    return 1 if out["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
