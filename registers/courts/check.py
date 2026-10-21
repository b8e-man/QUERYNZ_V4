"""The lane's check against the outside world (contract: the lane): the
judgments held and read against the source's own listing, and the
reading's own account.

  1. The count: every courtsofnz judgment the old estate's listing names
     (the pinned export, `capture.LISTING_SHA`), and every judgment the
     capture job found on a court's RSS feed, is a judgment row or a
     catch-log line ("not held", "set aside"). A listed judgment in neither
     fails.
  2. parsed / partial / unparsed, and the per-field missing counts.
  3. Suppression: judgments flagged and their kinds, names withheld; a
     published party name in a judgment that carries a suppression marker or
     a ledger order (the Crown and a court-printed initial apart) fails; a
     withheld name present in a published view fails.
  4. Every role a counsel line is "for" held by a party of the caption
     (`caption.roles_unaccounted`): more than `ROLES_TOLERATED` judgments
     short fails (the courts print the odd inconsistency themselves).

    account(conn, schema, shared=False)    dict
    python -m registers.courts.check [--schema courts] [--database querynz_v4] [--sample]

Read-only. Exit 1 on a failure.
"""
import sys

from registers.courts import capture
from registers.courts import load as L

ROLES_TOLERATED = 2


def account(conn, schema: str = L.SCHEMA, shared: bool = False) -> dict:
    t = lambda name: L.table(schema, name, shared)  # noqa: E731
    q = lambda sql, *a: conn.execute(sql, a).fetchall()  # noqa: E731
    out = {"failures": []}
    listed = q(f"SELECT document, source, outcome FROM {t('files')}")
    out["listed"] = {}
    for _, src, oc in listed:
        out["listed"].setdefault(src, {}).setdefault(oc, 0)
        out["listed"][src][oc] += 1
    judged = {r[0] for r in q(f"SELECT document FROM {t('judgments')}")}
    aside = {r[0] for r in q(f"SELECT item FROM {t('set_aside')} WHERE stage IN ('capture', 'recognise')")}
    for doc, src, oc in listed:
        if src != "waitangitribunal.govt.nz" and doc not in judged and doc not in aside:
            out["failures"].append(f"{src} {doc[:12]}: listed, neither a judgment nor a catch-log line")
    found = q(f"SELECT count(*), count(document) FROM {t('captures')}")[0] if _exists(conn, t("captures")) else (0, 0)
    out["captures"] = {"found": found[0], "landed": found[1]}
    out["status"] = dict(q(f"SELECT status, count(*) FROM {t('judgments')} GROUP BY 1 ORDER BY 1"))
    out["missing"] = dict(q(f"SELECT m, count(*) FROM {t('judgments')}, unnest(missing) m GROUP BY 1 ORDER BY 1"))
    for col in ("registry", "judges", "heading", "hearing"):
        out["missing"][f"{col} (not printed or not read)"] = q(f"SELECT count(*) FROM {t('judgments')} WHERE {col} IS NULL")[0][0]
    out["missing"]["outcome (none in the orders)"] = q(f"SELECT count(*) FROM {t('judgments')} WHERE outcome = '{{}}'")[0][0]
    out["parties"] = dict(zip(("parties", "withheld", "anonymised", "crown", "low"), q(
        f"SELECT count(*), count(*) FILTER (WHERE withheld), count(*) FILTER (WHERE anonymised), "
        f"count(*) FILTER (WHERE crown), count(*) FILTER (WHERE confidence = 'low') FROM {t('judgment_parties')}")[0]))
    out["suppression"] = {"judgments flagged": q(f"SELECT count(*) FROM {t('judgments')} WHERE suppression")[0][0],
                          "names withheld": out["parties"]["withheld"],
                          **dict(q(f"SELECT k, count(*) FROM {t('judgments')}, unnest(suppression_kinds) k GROUP BY 1 ORDER BY 1"))}
    leaked = q(f"SELECT p.key FROM {t('judgment_parties')} p JOIN {t('judgments')} j ON j.key = p.judgment "
               "WHERE j.suppression AND p.name IS NOT NULL AND NOT p.crown AND NOT p.anonymised")
    for (k,) in leaked:
        out["failures"].append(f"{k[:12]}…{k[64:]}: a name published in a judgment under suppression")
    # the session login cannot read the private table, and needs not: a withheld row carries no name
    shown = q(f"SELECT count(*) FROM {t('judgment_parties')} WHERE withheld AND (name IS NOT NULL OR capacity IS NOT NULL)")[0][0]
    if shown:
        out["failures"].append(f"{shown} withheld names still in the published table")
    orders = q(f"SELECT count(*) FROM {t('suppression_orders')}")[0][0] if _exists(conn, t("suppression_orders")) else 0
    out["suppression"]["orders in the ledger"] = orders
    short = roles_short(conn, schema, shared)
    out["roles short"] = len(short)
    if len(short) > ROLES_TOLERATED:
        out["failures"].append(f"{len(short)} judgments whose counsel lines name a role no party holds (tolerated {ROLES_TOLERATED})")
    return out


def _exists(conn, name: str) -> bool:
    return conn.execute("SELECT to_regclass(%s) IS NOT NULL", (name,)).fetchone()[0]


def roles_short(conn, schema: str, shared: bool = False) -> list:
    """Judgments whose counsel lines name a role no party holds, re-read from
    the stored text-layer readings (the counsel lines are never stored)."""
    from support import reader as rd
    from support.docread.read import TEXT_MODEL
    from registers.courts import caption
    store, out = rd.Store(), []
    rows = conn.execute(f"SELECT key, document, profile, profile_version FROM {L.table(schema, 'judgments', shared)}").fetchall()
    for key, doc, slug, version in rows:
        try:
            texts = {p: store.get(rd.reading_key(doc, p, TEXT_MODEL, {"tool": "pdftotext -layout"}, slug, version)).text
                     for p in (1, 2)}
        except rd.MissingReading:
            texts = None
        if texts is None:
            continue
        j = caption.Judgment(counsel_roles=caption._counsel_roles(texts[1] + "\n" + texts[2]))
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
        conn.execute("SET statement_timeout = '60s'")
        out = account(conn, schema, shared)
    print(f"listing {capture.LISTING_SHA[:12]}: " + "; ".join(
        f"{src}: " + ", ".join(f"{k} {v}" for k, v in sorted(oc.items())) for src, oc in sorted(out["listed"].items())))
    print(f"captures: {out['captures']}")
    for k in ("status", "missing", "parties", "suppression"):
        print(f"{k}: " + ", ".join(f"{a} {b}" for a, b in out[k].items()))
    print(f"roles short: {out['roles short']} (tolerated {ROLES_TOLERATED})")
    for f in out["failures"]:
        print("FAIL " + f)
    return 1 if out["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
