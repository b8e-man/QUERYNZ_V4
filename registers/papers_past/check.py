"""The lane's outside check (step 8.6): a batch against the old estate's own copy of Papers Past (`incoming_news.articles`,
read-only): every item the old copy holds by its upstream id carries the same title and the same URL; the batch's
stages reconcile (items in equal items landed plus set aside); and a sample of the items reads back from the store's
files on /mnt/hdd2 with the sha256 and the length the catalogue holds.

    python -m registers.papers_past.check --schema papers_past|staging_… [--database querynz_v4]    exits 1 on failure
"""
import sys


def against_old(items: list, old: dict) -> list:
    """items: [{upstream_id, title, url, held_in_old}]; old: {upstream_id: (title, url)}. The problems, as plain lines."""
    out = []
    for it in items:
        o = old.get(it["upstream_id"])
        if it["held_in_old"] and o is None:
            out.append(f"{it['upstream_id']} is marked held in the old estate, which does not hold it")
        if o is not None:
            if (o[0] or "") != (it["title"] or ""):
                out.append(f"{it['upstream_id']}: the title differs from the old estate's copy")
            if o[1] != it["url"]:
                out.append(f"{it['upstream_id']}: the URL differs from the old estate's copy")
    return out


def reconciles(stages: list) -> list:
    """stages: [(seq, stage, in, out, set aside)] of one batch, in order."""
    out = []
    if not stages:
        return ["no stages recorded"]
    first = stages[0][2]
    aside = sum(s[4] for s in stages if not s[1].endswith("(measured)"))
    landed = [s for s in stages if s[1] == "landed"]
    if not landed:
        return ["no landed stage"]
    if first != landed[0][3] + aside:
        out.append(f"{first} in, {landed[0][3]} landed, {aside} set aside: does not reconcile")
    for a, b in zip(stages, stages[1:]):
        if not b[1].endswith("(measured)") and a[3] != b[2]:
            out.append(f"stage {b[1]} took {b[2]} in, the stage before it put {a[3]} out")
    return out


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    schema = argv[argv.index("--schema") + 1] if "--schema" in argv else "papers_past"
    database = argv[argv.index("--database") + 1] if "--database" in argv else "querynz_v4"
    from support import db
    why = []
    from registers.papers_past.load import URL, read_back
    with db.connect(db.OWNER_KEY, database) as conn:
        conn.execute("SET statement_timeout = '300s'")
        items = [dict(zip(("upstream_id", "title", "url", "held_in_old"), r)) for r in
                 conn.execute(f"SELECT upstream_id, title, coalesce(url, %s || key), held_in_old FROM {schema}.items",
                              (URL,)).fetchall()]
        for (batch, sdir) in conn.execute(f"SELECT batch, store FROM {schema}.batches ORDER BY 1").fetchall():
            why += [f"batch {batch}: {w}" for w in read_back(conn, schema, sdir, 200)]
        for (batch,) in conn.execute(f"SELECT DISTINCT batch FROM {schema}.stages ORDER BY 1").fetchall():
            why += [f"batch {batch}: {w}" for w in reconciles(conn.execute(
                f"SELECT seq, stage, items_in, items_out, set_aside FROM {schema}.stages WHERE batch = %s ORDER BY seq",
                (batch,)).fetchall())]
    with db.connect(db.OLD_READ_KEY, "incoming_news", connect_timeout=10) as c:
        c.execute("SET statement_timeout = '120s'")
        c.execute("SET default_transaction_read_only = on")
        ids, old = [it["upstream_id"] for it in items], {}
        for i in range(0, len(ids), 100_000):
            old.update({r[0]: (r[1], r[2]) for r in c.execute(
                "SELECT upstream_id, title, news_url FROM articles WHERE upstream_id = ANY(%s)", (ids[i:i + 100_000],)).fetchall()})
    why += against_old(items, old)
    print(f"papers_past: {len(items)} items, {len(old)} held in the old estate, {sum(1 for it in items if it['held_in_old'])} marked so")
    for w in why[:50]:
        print("FAILS " + w)
    return 1 if why else 0


if __name__ == "__main__":
    sys.exit(main())
