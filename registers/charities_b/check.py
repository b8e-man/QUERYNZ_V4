"""The build's checks against what it read and against the register itself.

1. **Every row of every captured page is a typed row or a set-aside with
   its reason** (the reconciliation): every page the capture lists for a set
   is in the `pages` ledger, each page's rows equal its typed rows plus its
   catch-log lines, and the tables and the catch log hold exactly those.
2. **The register's own count on the capture day.** The feed's own count of
   each set at the start of its full pass (`$inlinecount`, in the capture's
   listing) against the rows the pass landed; and the register's count of
   registered charities, asked by the capture session on 20 October 2026 at
   about 07:30 NZDT (`REGISTER_COUNT`; the capture did not land that answer
   as a document, so the figure is its record's), against the registered
   charities held. The register moves while a pass runs, so a difference
   passes only when no larger than the organisations the register itself
   marks modified after the count was taken.
3. **The register's own resolution of the codes.** Its `vOrganisations` view
   names each charity's main sector, activity and beneficiary and its group;
   ours, resolved through the code lists, must give the same names wherever
   the view and the organisation were captured in the same state.

    python -m registers.charities_b.check [--schema scratch_charities_b_full] [--database querynz_v4_sample]

prints counts only and exits 1 when a check fails.
"""
import argparse
import collections
import datetime as dt
import json
import sys

from registers.charities_b import capture, load, read

REGISTER_COUNT = {"registered": 29265, "organisations": 46132,
                  "at": dt.datetime(2026, 10, 20, 7, 30, tzinfo=read.NZ),
                  "source": "the feed's $inlinecount for RegistrationStatus eq 'Registered', asked by the "
                            "charities-capture session (docs/status/charities.md, docs/merges/charities-capture-1.md)"}
TABLE_OF = {"Groups": "groups", "Organisations": "charities", "Officers": "officers", "AnnualReturn": "returns"}


def reconcile(conn, schema: str, listed: dict, shared: bool = False) -> list:
    """Problems, as plain lines; empty when every row is accounted for.
    `listed`: feed set → [sha256] the capture lists."""
    T = lambda t: load.table(schema, t, shared)
    out = []
    ledger = {r[0]: r[1:] for r in conn.execute(
        f"SELECT document, entity_set, rows, typed, set_aside, skipped FROM {T('pages')}")}
    for s, shas in listed.items():
        missing = [x for x in shas if x not in ledger]
        if missing:
            out.append(f"{s}: {len(missing)} listed page(s) not read")
    for sha, (s, rows, typed, aside, skipped) in ledger.items():
        if rows != typed + aside or skipped:
            out.append(f"{s} page {sha[:12]}: {rows} rows, {typed} typed + {aside} set aside, {skipped} passed over")
    by_set = collections.defaultdict(lambda: [0, 0])
    for s, rows, typed, aside, skipped in ledger.values():
        by_set[s][0] += typed
        by_set[s][1] += aside
    asides = dict(conn.execute(f"SELECT entity_set, count(*) FROM {T('set_aside')} GROUP BY 1").fetchall())
    codes = dict(conn.execute(f"SELECT code_list, count(*) FROM {T('codes')} GROUP BY 1").fetchall())
    for s, (typed, aside) in by_set.items():
        if s in TABLE_OF:
            held = conn.execute(f"SELECT count(*) FROM {T(TABLE_OF[s])}").fetchone()[0]
        else:
            held = codes.get(s, 0)
        if held != typed:
            out.append(f"{s}: the ledger says {typed} typed, the table holds {held}")
        if asides.get(s, 0) != aside:
            out.append(f"{s}: the ledger says {aside} set aside, the catch log holds {asides.get(s, 0)}")
    unreasoned = conn.execute(f"SELECT count(*) FROM {T('set_aside')} WHERE coalesce(reason, '') = '' "
                              "OR coalesce(stage, '') = ''").fetchone()[0]
    if unreasoned:
        out.append(f"{unreasoned} catch-log line(s) without a stage or a reason")
    return out


def counts(conn, schema: str, capture_conn, read_bytes, shared: bool = False) -> dict:
    """The held copy against the register's own counts (check 2)."""
    T = lambda t: load.table(schema, t, shared)
    out = {"sets": {}}
    for s in ("Organisations", "Officers", "AnnualReturn", "Groups"):
        st = capture.stated(capture_conn, s)
        if st is None:
            out["sets"][s] = {"held": None}
            continue
        stated, landed, started, finished = st
        out["sets"][s] = {"stated_at_pass_start": stated, "landed": landed,
                          "pass": f"{started.isoformat(timespec='minutes')} to {finished.isoformat(timespec='minutes')}",
                          "typed": conn.execute(f"SELECT count(*) FROM {T(TABLE_OF[s])}").fetchone()[0],
                          "set_aside": conn.execute(f"SELECT count(*) FROM {T('set_aside')} WHERE entity_set = %s "
                                                    "AND stage <> 'supersede'", (s,)).fetchone()[0]}
    at = REGISTER_COUNT["at"]
    typed_reg, typed_after = conn.execute(
        f"SELECT count(*) FILTER (WHERE status = 'Registered'), count(*) FILTER (WHERE source_modified_at >= %s) "
        f"FROM {T('charities')}", (at,)).fetchone()
    aside_reg = aside_after = 0
    places = collections.defaultdict(set)
    for doc, place in conn.execute(f"SELECT document, place FROM {T('set_aside')} WHERE entity_set = 'Organisations' "
                                   "AND stage <> 'supersede'"):
        places[doc].add(place)
    for doc, want in places.items():
        for r in read.parse_page(read_bytes(doc))[1]:
            if f"OrganisationId={r['OrganisationId']}" in want:
                aside_reg += read.text(r.get("RegistrationStatus")) == "Registered"
                m = read.feed_moment(r.get("ModifiedOn"))
                aside_after += bool(m and m >= at)
    held = typed_reg + aside_reg
    moved = typed_after + aside_after
    diff = held - REGISTER_COUNT["registered"]
    out["registered"] = {"register_on_capture_day": REGISTER_COUNT["registered"],
                         "register_asked_at": at.isoformat(timespec="minutes"), "held": held, "typed": typed_reg,
                         "set_aside": aside_reg, "difference": diff, "modified_after_the_count": moved,
                         "ok": abs(diff) <= moved}
    return out


def resolution(conn, schema: str, v_pages: list, read_bytes, shared: bool = False) -> dict:
    """Ours against the register's own `vOrganisations` names (check 3)."""
    T = lambda t: load.table(schema, t, shared)
    ours = {r[0]: r[1:] for r in conn.execute(
        f"SELECT organisation_id, main_sector, main_activity, main_beneficiary, group_name, source_modified_at "
        f"FROM {T('charities')}")}
    fields = ("MainSectorName", "MainActivityName", "MainBeneficiaryName", "GroupName")
    out = collections.Counter()
    seen = set()
    for sha in reversed(v_pages):
        for r in read.parse_page(read_bytes(sha))[1]:
            oid = r["OrganisationId"]
            if oid in seen or oid not in ours:
                continue
            seen.add(oid)
            mine = ours[oid]
            if read.feed_moment(r.get("ModifiedOn")) != mine[4]:
                out["moved between the two captures"] += 1
                continue
            out["compared"] += 1
            for i, f in enumerate(fields):
                if read.text(r.get(f)) != mine[i]:
                    out[f"{f} differs"] += 1
    out["not in the view"] = len(set(ours) - seen)
    return dict(out)


def figures(conn, schema: str, capture_conn, read_bytes, shared: bool = False) -> dict:
    listed = load.listings(capture_conn)
    lines = reconcile(conn, schema, listed, shared)
    c = counts(conn, schema, capture_conn, read_bytes, shared)
    v = resolution(conn, schema, [s for s, _, _ in capture.listing(capture_conn, "vOrganisations")], read_bytes, shared)
    differs = sum(n for k, n in v.items() if k.endswith("differs"))
    return {"reconciles": not lines, "problems": lines, "counts": c, "resolution": v,
            "ok": not lines and c["registered"]["ok"] and differs == 0 and v.get("compared", 0) > 0}


def main(argv=None) -> int:
    from support import db
    from support.docstore.landing import read_bytes
    ap = argparse.ArgumentParser(prog="python -m registers.charities_b.check")
    ap.add_argument("--schema", default=load.SCRATCH)
    ap.add_argument("--database", default="querynz_v4_sample")
    a = ap.parse_args(argv)
    with db.connect(db.READ_KEY, "querynz_v4") as src, db.connect(db.OWNER_KEY, a.database) as conn:
        src.execute("SET statement_timeout = '60s'")
        conn.execute("SET statement_timeout = '60s'")
        f = figures(conn, a.schema, src, read_bytes)
    print(json.dumps(f, indent=1, default=str))
    print("charities_b: check " + ("green" if f["ok"] else "RED"))
    return 0 if f["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
