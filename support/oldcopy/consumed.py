"""Has the new estate consumed the old one? (ruling 162, 10 November 2026)

The old estate's databases and trees stay in the off-site copy until the new estate is proven to hold everything in
them. This check is that proof, piece by piece, over every table of the three old databases (read live from their
catalogues, so a table added since stream I's inventory is seen) and every old tree the off-site copy sends:

  copied      a NEW or PARTLY table whose copy is caught up, with no failed batch left standing, and whose rows
              now count the same at the source and in the copy (the same leave_out, the same missing ranges)
  held        the inventory says the new estate holds it (HELD, with where); its own evidence, named
  let go      Arthur let it go: the off-site copy no longer sends it (ruling 164, the rebuildable public sets), or the
              inventory leaves it OUT (ruling 161)
  waiting     to be copied, not yet caught up, or its counts differ (the old jobs still write: a new row since)
  not held    nothing above: DERIVED with no ruling that lets it go, an old tree the copier does not walk, a table
              the inventory does not name. Each one blocks.

`ready` is true only when nothing is waiting or not held. It never stops the old off-site copy itself: that is
Arthur's word (hard limit 18), given on this proof.

    python -m support.oldcopy.consumed            measure, write <live>/checks/old-consumed.json, print the summary
    python -m support.oldcopy.consumed --print    measure and print, writing nothing

Reads only: the old databases through the read-only old login, querynz_v4's oldcopy ledger and copies through the
owner login (the copies are private). Prints names and counts, never a row (hard limit 11)."""
import argparse
import datetime as dt
import json
import os
import sys

from psycopg import sql

from support import db
from support.offsite import pieces as P
from support.oldcopy import INVENTORY, LEDGER, OLD_DATABASES, inventory
from support.oldcopy import files as F
from support.oldcopy import tables as T

LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
OUT_FILE = os.path.join(LIVE, "checks", "old-consumed.json")
DEST_DB = os.environ.get("QV4_OLDCOPY_DB") or db.LIVE
CLASSES = ("copied", "held", "let go", "waiting", "not held")
BLOCKING = ("waiting", "not held")


def old_tables(conn) -> list:
    """Every ordinary or partitioned table of an old database, outside the system schemas: (schema, table)."""
    return [tuple(r) for r in conn.execute(
        "SELECT n.nspname, c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE c.relkind IN ('r', 'p') AND NOT c.relispartition "
        "AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg_toast%' "
        "ORDER BY 1, 2").fetchall()]


def ledger_state(conn) -> dict:
    """piece -> {"caught_up", "rows", "failed_since_ok", "refused"} from the copier's ledger."""
    L = sql.Identifier(LEDGER)
    out = {}
    for piece, caught, rows in conn.execute(sql.SQL(
            "SELECT piece, bool_and(caught_up), sum(rows) FROM {}.cursors GROUP BY piece").format(L)):
        out[piece] = {"caught_up": bool(caught), "rows": int(rows or 0), "failed_since_ok": False, "refused": None}
    for piece, bad in conn.execute(sql.SQL(
            "SELECT piece, bool_or(NOT ok AND batch_id > COALESCE((SELECT max(b2.batch_id) FROM {}.batches b2 "
            "WHERE b2.piece = b.piece AND b2.ok), 0)) FROM {}.batches b GROUP BY piece").format(L, L)):
        out.setdefault(piece, {"caught_up": False, "rows": 0, "failed_since_ok": False, "refused": None})
        out[piece]["failed_since_ok"] = bool(bad)
    for piece, why in conn.execute(sql.SQL(
            "SELECT DISTINCT ON (piece) piece, why FROM {}.refusals ORDER BY piece, refusal_id DESC").format(L)):
        out.setdefault(piece, {"caught_up": False, "rows": 0, "failed_since_ok": False, "refused": None})
        out[piece]["refused"] = why
    conn.rollback()
    return out


def file_state(conn, ledger: str = LEDGER) -> dict:
    """store -> {"caught_up", "held": set of relative paths landed or held, "bad": paths failed or too big}."""
    L = sql.Identifier(ledger)
    out = {s: {"caught_up": bool(c), "held": set(), "bad": set()} for s, c in conn.execute(
        sql.SQL("SELECT store, caught_up FROM {}.file_cursors").format(L))}
    for store, rel, outcome in conn.execute(sql.SQL("SELECT store, old_path, outcome FROM {}.files").format(L)):
        st = out.setdefault(store, {"caught_up": False, "held": set(), "bad": set()})
        (st["held"] if outcome in F.HELD_OUTCOMES else st["bad"]).add(rel)
    conn.rollback()
    for st in out.values():
        st["bad"] -= st["held"]
    return out


def judge_store(store, state, walk=F.walk, sniff=F.sniff) -> tuple:
    """(class, why) for one copied store: every wanted file now on disk is in the ledger as landed or held."""
    if state is None:
        return "waiting", "not walked yet"
    if not state["caught_up"]:
        return "waiting", "its walk is not caught up"
    missing = 0
    for rel in walk(store.root, None, store.exclude):
        kind, _ = sniff(os.path.join(store.root, rel), rel)
        if F.wanted(kind, store.html, store.every_kind) and rel not in state["held"]:
            missing += 1
    if state["bad"]:
        return "not held", f"{len(state['bad'])} files failed or too big, e.g. {sorted(state['bad'])[0]}"
    if missing:
        return "waiting", f"{missing} files on disk not yet in the ledger (written since the walk)"
    return "copied", f"{len(state['held'])} files, every wanted one in the ledger"


def counts_agree(src, dst, spec) -> tuple:
    """(source rows, copied rows) over the spec's ranges and leave_out, both counted now."""
    cat = T.catalogue(src, spec.schema, spec.table, spec.key)
    cat["leave_out"] = tuple(spec.leave_out)
    src_rel = T._ident(spec.schema, spec.table)
    dst_rel = T._ident(T.dest_schema(spec.database), T.dest_table(spec.schema, spec.table))
    n_src = n_dst = 0
    for lo, hi in spec.ranges:
        q = "SELECT count(*) FROM {} WHERE {}"
        with src.transaction():
            n_src += src.execute(sql.SQL(q).format(src_rel, T._where(cat, lo, hi))).fetchone()[0]
        n_dst += dst.execute(sql.SQL(q).format(dst_rel, T._where(cat, lo, hi))).fetchone()[0]
    dst.rollback()
    return int(n_src), int(n_dst)


SUPERSET_MAX_ROWS = 2_000_000


def rows_missing(src, dst, spec, schema: str = None) -> int:
    """How many of the source's distinct rows (spec's ranges and leave_out) are not in the copy, row by row: md5 of
    each row's copied columns on both sides, the rows the copier's own whole-table measure hashes. For a copy that holds
    more rows than the source, which drops rows the copy keeps."""
    cat = T.catalogue(src, spec.schema, spec.table, spec.key)
    cat["leave_out"] = tuple(spec.leave_out)
    src_rel = T._ident(spec.schema, spec.table)
    dst_rel = T._ident(schema or T.dest_schema(spec.database), T.dest_table(spec.schema, spec.table))
    q = "SELECT DISTINCT md5(s::text) FROM (SELECT {} FROM {} WHERE {}) s"
    want = set()
    for lo, hi in spec.ranges:
        with src.transaction():
            want |= {r[0] for r in src.execute(sql.SQL(q).format(T._cols(cat), src_rel, T._where(cat, lo, hi)))}
    if not want:
        return 0
    held = dst.execute(sql.SQL("SELECT count(DISTINCT m) FROM (SELECT md5(s::text) AS m FROM (SELECT {} FROM {}) s) h "
                               "WHERE m = ANY(%s)").format(T._cols(cat), dst_rel), (list(want),)).fetchone()[0]
    dst.rollback()
    return len(want) - int(held)


def judge_table(database, schema, table, entry, spec, led, count, missing=None) -> tuple:
    """(class, why) for one old table. `entry` is its inventory row or None; `spec` its inventory.Table when
    copied; `led` its ledger state or None; `count()` gives (source, copy) rows now, called only when needed."""
    fate, fate_why = P.fate(database, schema, table)
    status = (entry or {}).get("status")
    if spec is not None:
        if led is None:
            return "waiting", "not copied yet"
        if led["refused"] and not led["caught_up"]:
            return "not held", f"the copier refused it: {led['refused']}"
        if led["failed_since_ok"]:
            return "waiting", "its last batch failed its check"
        if not led["caught_up"]:
            return "waiting", f"{led['rows']} rows copied, not caught up"
        n_src, n_dst = count()
        if n_dst > n_src and missing is not None:
            if n_src > SUPERSET_MAX_ROWS:
                return "waiting", (f"{n_dst} rows in the copy, {n_src} at the source (the source dropped rows): too "
                                   f"many to compare row by row")
            gone = missing()
            if gone:
                return "waiting", f"{gone} of the source's {n_src} rows not in the copy (changed since the copy)"
            return "copied", (f"every one of the source's {n_src} rows is in the copy, which keeps {n_dst - n_src} "
                              f"more the source has since dropped")
        if n_src != n_dst:
            return "waiting", f"{n_src} rows at the source now, {n_dst} in the copy (new rows since)"
        return "copied", f"{n_dst} rows, the counts agree"
    if status == "HELD":
        return "held", f"in {entry.get('held_in') or 'the new estate'} (stream I's evidence)"
    if status == "OUT":
        return "let go", "OUT in the inventory"
    if fate == P.OUT:
        return "let go", f"not sent off-site: {fate_why}"
    if entry is None:
        return "not held", "not in stream I's inventory (added since?)"
    if status == "DERIVED":
        return "not held", f"DERIVED ({entry.get('note') or 'built from other tables'}), not copied and not let go"
    return "not held", f"inventory status {status!r}, not copied"


def uncovered(root: str, store_roots, listdir=os.listdir) -> list:
    """The entries directly under `root` that no store covers (a store's root is the entry or lies above it); an
    entry with a store somewhere below it but not at it is reported too, since only part of it is walked."""
    roots = [r.rstrip("/") for r in store_roots]
    try:
        names = sorted(listdir(root))
    except OSError:
        return []
    out = []
    for n in names:
        p = os.path.join(root, n)
        if any(p == r or p.startswith(r + "/") for r in roots):
            continue
        out.append(n + (" (partly: a store lies inside it)" if any(r.startswith(p + "/") for r in roots) else ""))
    return out


def judge_trees(inv: dict, fstate: dict, listdir=os.listdir, judge=judge_store) -> list:
    """The old trees the off-site copy sends: each inventory store under one is copied (its walk caught up), held or
    OUT; a tree with no store of the inventory under it, or with files outside its stores, is not held."""
    stores = inv.get("stores") or []
    out = []
    for name, (root, fate, why, _excl) in sorted(P.TREES.items()):
        if not root.startswith(P.OLD_REPO) or fate == P.OUT:
            continue
        under = [s for s in stores if (s.get("root") or "").startswith(root.rstrip("/") + "/") or s.get("root") == root]
        if not under:
            out.append({"piece": f"tree:{name}", "class": "not held",
                        "why": f"{why}: no store of the inventory covers it, so nothing copies it"})
            continue
        copied = {x.name: x for x in inventory.stores(inv)[0]}
        for s in under:
            st = str(s.get("status") or "").upper()
            sname = s.get("name")
            if sname in copied:
                c = judge(copied[sname], fstate.get(sname))
            elif st == "HELD":
                c = ("held", f"in {s.get('held_in') or 'the new estate'} (stream I's evidence)")
            elif st == "OUT":
                c = ("let go", "OUT in the inventory")
            else:
                c = ("not held", f"inventory status {st!r}")
            out.append({"piece": f"tree:{name}/{sname}", "class": c[0], "why": c[1]})
        rest = uncovered(root, [s.get("root") or "" for s in under], listdir)
        if rest:
            out.append({"piece": f"tree:{name} (outside its stores)", "class": "not held",
                        "why": f"{len(rest)} entries no inventory store covers: " + ", ".join(rest[:12])})
    return out


def measure(old_connect, dst, inv, log=print) -> dict:
    todo, _skipped = inventory.tables(inv, OLD_DATABASES)
    specs = {t.piece: t for t in todo}
    entries = {f"{t['database']}:{t.get('schema') or 'public'}.{t['table']}": t for t in inv.get("tables") or []}
    led = ledger_state(dst)
    rows = []
    for database in OLD_DATABASES:
        with old_connect(database) as src:
            src = T.prepare_source(src)
            for schema, table in old_tables(src):
                piece = f"{database}:{schema}.{table}"
                spec = specs.get(piece)
                cls, why = judge_table(database, schema, table, entries.get(piece), spec, led.get(piece),
                                       lambda: counts_agree(src, dst, spec), lambda: rows_missing(src, dst, spec))
                rows.append({"piece": piece, "class": cls, "why": why})
        log(f"consumed: {database}: {sum(1 for r in rows if r['piece'].startswith(database + ':'))} tables")
    rows += judge_trees(inv, file_state(dst))
    by = {c: sum(1 for r in rows if r["class"] == c) for c in CLASSES}
    return {"schema": 1, "made": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "ready": not any(by[c] for c in BLOCKING), "counts": by, "pieces": rows}


def summary(rep: dict) -> str:
    lines = [f"old estate consumed: {'READY' if rep['ready'] else 'not ready'}; "
             + ", ".join(f"{c} {n}" for c, n in rep["counts"].items())]
    for c in BLOCKING:
        for r in [r for r in rep["pieces"] if r["class"] == c][:40]:
            lines.append(f"  {c}: {r['piece']}: {r['why']}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m support.oldcopy.consumed")
    ap.add_argument("--print", action="store_true", help="measure and print, writing nothing")
    ap.add_argument("--inventory", default=INVENTORY)
    a = ap.parse_args(argv)
    inv = inventory.load(a.inventory)
    with db.connect(db.OWNER_KEY, DEST_DB, connect_timeout=10) as dst:
        T.prepare_dest(dst)
        rep = measure(lambda name: db.connect(db.OLD_READ_KEY, name, connect_timeout=10), dst, inv)
    print(summary(rep))
    if not a.print:
        os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
        tmp = OUT_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rep, f, indent=1)
        os.replace(tmp, OUT_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
