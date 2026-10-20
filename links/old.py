"""Copy the old estate's ledgers of judgments exactly as they are into
`links.old_decisions`, and map each to the new stable keys of the two rows
it was about, by content (plan 4.2; contract: links, 5).

    python -m links.old [--schema scratch_links] [--copy] [--map] [--promote]

The three ledgers (old database `nzbn_canonical`, read-only login):

| ledger                            | what it judged                                         | verdict here  |
| registers.roster_identity_folds   | two director records are one identity (rulings 216-218) | same          |
| registers.donor_anchors           | a donation row is a company (accept, by NZBN) or a      | same          |
|                                   | director identity (corroborated, by an arm)             |               |
| registers.review_verdicts         | Arthur's `hold` on a corroborated identity              | contested (the brief: the old "hold" is "contested") |

Every row of every version is copied (`copied` is the row as it is,
`old_id` is `<table>:<id>`). The ledgers are only ever added to, so each
build copies the rows the copy does not hold yet (those above its highest
old id, and any gap below it) and re-reads `withdrawn_at` and
`withdrawn_reason` on the rows it holds, the one thing the old estate
changes on a row (card: the links copy the old ledgers once and the check
counts them live). A row that names a pair is mapped; a row that names
none (abstain, no-match, reject, party-register) says so in `mapped_how`.

Only the old estate's last word is promoted into `links.decisions` as
`old-estate:<table>:<id>`: live folds; each donation's latest live anchor,
whatever its weights version (the old estate re-judges a donation at each
new version and keeps the older judgment as the record, so the latest
supersedes it; the latest is the highest id, never a version sorted as
text, which ranks 2.10 below 2.3); a live hold whose anchors at its
version are still applied (a hold binds to one version's reading, and a
new reading puts the card back in the old review). The versions seen are
recorded in the map's tally, with the version of the old table's latest
decision (card: the old estate's anchors moved to weights 2.3). A row that
cannot be mapped is counted and carded, never guessed.

The old row numbers changed nightly, so the map goes by content:
- an old director record (`public.director_roles.id`) → its name, company
  and appointment date → the one `pub.directors` row with that name on that
  company appointed that day;
- an old donation row → its return's file hash, donor, amount and year →
  the one `pub.party_return_donors`, `pub.candidate_return_donors` or
  `pub.disclosures` row (the candidate-returns lane published on 20 October);
- an accepted company → `companies:companies/<NZBN>`.
"""
from __future__ import annotations

import json
import re
import sys
import time

from keys import names as kn

import links

OLD_DB = "nzbn_canonical"
LEDGERS = {
    "roster_identity_folds": "SELECT * FROM registers.roster_identity_folds WHERE id = ANY(%s) ORDER BY id",
    "donor_anchors": "SELECT * FROM registers.donor_anchors WHERE id = ANY(%s) ORDER BY id",
    "review_verdicts": "SELECT * FROM registers.review_verdicts WHERE id = ANY(%s) ORDER BY id",
}
# what the old estate changes on a row of an append-only ledger: its withdrawal
LEDGER_STATE = "SELECT id, withdrawn_at, withdrawn_reason FROM registers.{table} ORDER BY id"
OLD_DIRECTOR_SQL = """
    SELECT coalesce(unique_identifier, id::text), full_name, source_nzbn, appointed_at::text FROM public.director_roles
    WHERE id::text = ANY(%s::text[]) OR unique_identifier = ANY(%s::text[])"""
# the old roster's person key: coalesce(unique_identifier, id::text); `id` is a uuid
_OLD_KEY = re.compile(r"^[0-9a-f-]{36}$|^[0-9]+$")
OLD_DONATION_SQL = {
    "party": "SELECT id, source_sha, year::text, party, donor_name, amount FROM registers.party_donations WHERE id = ANY(%s)",
    "candidate": "SELECT id, source_sha, election_year::text, candidate, donor_name, amount FROM registers.candidate_donations WHERE id = ANY(%s)",
    "disclosure": "SELECT id, source_sha, year_received::text, party, donor_name, amount FROM registers.donation_disclosures WHERE id = ANY(%s)",
}


def _json(v):
    return json.loads(json.dumps(v, default=str))


def ledger_changes(held: dict, theirs: list) -> tuple:
    """`held`: old id → (withdrawn_at, withdrawn_reason) as the copy holds
    them; `theirs`: (id, withdrawn_at, withdrawn_reason) from the old table.
    → (ids to copy, {id: (withdrawn_at, withdrawn_reason)} to re-read, ids
    held that the old table no longer has)."""
    missing, changed, seen = [], {}, set()
    for oid, w_at, w_why in theirs:
        oid = int(oid)
        seen.add(oid)
        now = (_json(w_at), w_why)
        if oid not in held:
            missing.append(oid)
        elif tuple(held[oid]) != now:
            changed[oid] = now
    return sorted(missing), changed, sorted(set(held) - seen)


def copy_ledgers(old, conn, s: str, log=print) -> dict:
    """Bring the copy of the three ledgers level with the old database:
    every row it does not hold yet, exactly as it is, and the withdrawal
    re-read on every row it holds."""
    t0 = time.monotonic()
    out = {}
    for table, sql in LEDGERS.items():
        held = {int(r[0]): (r[1], r[2]) for r in conn.execute(
            f"""SELECT split_part(old_id, ':', 2), copied->'withdrawn_at', copied->>'withdrawn_reason'
                FROM {s}.old_decisions WHERE source = %s""", (table,)).fetchall()}
        missing, changed, gone = ledger_changes(held, old.execute(LEDGER_STATE.format(table=table)).fetchall())
        n = 0
        with conn.cursor() as w:
            for i in range(0, len(missing), 5000):
                cur = old.execute(sql, (missing[i:i + 5000],))
                cols = [d.name for d in cur.description]
                for r in cur.fetchall():
                    row = dict(zip(cols, r))
                    w.execute(f"""INSERT INTO {s}.old_decisions (old_id, copied, source)
                                  VALUES (%s, %s::jsonb, %s) ON CONFLICT (old_id) DO NOTHING""",
                              (f"{table}:{row['id']}", json.dumps(_json(row)), table))
                    n += 1
            w.executemany(f"""UPDATE {s}.old_decisions SET copied = copied || jsonb_build_object('withdrawn_at', %s::jsonb, 'withdrawn_reason', %s::text)
                              WHERE old_id = %s""",
                          [(json.dumps(w_at), w_why, f"{table}:{oid}") for oid, (w_at, w_why) in changed.items()])
        out[table] = {"held": len(held), "copied": n, "withdrawal_re_read": len(changed), "gone_from_the_old_table": len(gone)}
        log(f"links.old: {table}: {json.dumps(out[table])} ({time.monotonic() - t0:.0f} s)")
    conn.commit()
    return out


def _fold(s: str) -> str:
    return " ".join(kn.fold_diacritics(s or "").lower().split())


def director_map(old, conn, s: str, ids: list) -> dict:
    """old director_roles id → (new ref | None, how)."""
    out = {}
    ids = sorted({str(i) for i in ids if _OLD_KEY.match(str(i))})
    old_rows = {}
    for i in range(0, len(ids), 5000):
        for oid, name, nzbn, appointed in old.execute(OLD_DIRECTOR_SQL, (ids[i:i + 5000], ids[i:i + 5000])).fetchall():
            old_rows[oid] = (name, nzbn, appointed)
    for oid in ids:
        if oid not in old_rows:
            out[oid] = (None, "the old director record no longer exists in the old database")
            continue
        name, nzbn, appointed = old_rows[oid]
        found = conn.execute(f"""SELECT ref FROM {s}.rows WHERE view = 'directors' AND entity_ref = %s
                                 AND upper(name_filed) = upper(%s) AND (started_on::text = %s::text OR (started_on IS NULL AND %s::text IS NULL))""",
                             (links.ref("companies", f"companies/{nzbn}"), name, appointed, appointed)).fetchall()
        if len(found) == 1:
            out[oid] = (found[0][0], "name, company and appointment date")
        elif not found:
            loose = conn.execute(f"""SELECT ref FROM {s}.rows WHERE view = 'directors' AND entity_ref = %s AND upper(name_filed) = upper(%s)""",
                                 (links.ref("companies", f"companies/{nzbn}"), name)).fetchall()
            if len(loose) == 1:
                out[oid] = (loose[0][0], "name and company (the appointment date differs or is missing)")
            else:
                out[oid] = (None, f"no published director row carries this name on this company ({len(loose)} by name alone)")
        else:
            out[oid] = (None, f"{len(found)} published director rows carry this name on this company on that day")
    return out


def donation_map(old, conn, s: str, anchors: list) -> dict:
    """old anchor id → (new donation ref | None, how), through the old
    donation row's content where its id still resolves to the same donor
    name, else the donor name alone where exactly one published row carries it."""
    out = {}
    by_source: dict = {}
    for a in anchors:
        if a.get("source") in OLD_DONATION_SQL:
            by_source.setdefault(a["source"], []).append(a)
        else:
            out[f"donor_anchors:{a['id']}"] = (None, "the old row names no source table (a ledger version before the content key)")
    for source, rows in by_source.items():
        old_rows = {}
        ids = sorted({int(a["donation_id"]) for a in rows})
        for i in range(0, len(ids), 5000):
            for oid, sha, year, receiver, donor, amount in old.execute(OLD_DONATION_SQL[source], (ids[i:i + 5000],)).fetchall():
                old_rows[oid] = (sha, year, receiver, donor, amount)
        for a in rows:
            key = f"donor_anchors:{a['id']}"
            view = {"party": "party_return_donors", "candidate": "candidate_return_donors", "disclosure": "disclosures"}[source]
            orow = old_rows.get(int(a["donation_id"]))
            if orow and _fold(orow[3]) == _fold(a["donor_name"]):
                sha, year, receiver, donor, amount = orow
                found = conn.execute(f"""SELECT r.ref FROM {s}.rows r WHERE r.view = %s AND lower(r.name_filed) = lower(%s)
                                         AND (r.document = %s OR extract(year FROM r.started_on)::text = %s)""",
                                     (view, donor, sha, str(year))).fetchall()
                if len(found) == 1:
                    out[key] = (found[0][0], "donor, and the return's file hash or year")
                    continue
                if len(found) > 1 and amount is not None:
                    exact = _by_amount(conn, s, view, [f[0] for f in found], amount)
                    if len(exact) == 1:
                        out[key] = (exact[0], "donor, year and amount")
                        continue
                    out[key] = (None, f"{len(found)} published rows carry this donor in that return; the amount does not single one out")
                    continue
                if not found:
                    out[key] = (None, "no published row carries this donor in that return (the return may be set aside or not read)")
                    continue
            found = conn.execute(f"SELECT ref FROM {s}.rows WHERE view = %s AND lower(name_filed) = lower(%s)", (view, a["donor_name"])).fetchall()
            if len(found) == 1:
                out[key] = (found[0][0], "the donor name alone: exactly one published row carries it (the old row number no longer resolves)")
            elif not found:
                out[key] = (None, "no published row carries this donor name, and the old row number no longer resolves")
            else:
                out[key] = (None, f"{len(found)} published rows carry this donor name and the old row number no longer resolves")
    return out


_DONOR_TABLES = {"party_return_donors": ("pub.party_return_donors", "party_returns"),
                 "candidate_return_donors": ("pub.candidate_return_donors", "candidate_returns"),
                 "disclosures": ("pub.disclosures", "disclosures")}


def _by_amount(conn, s: str, view: str, refs: list, amount) -> list:
    table, register = _DONOR_TABLES[view]
    return [r[0] for r in conn.execute(f"""SELECT %s || ':' || key FROM {table} WHERE %s || ':' || key = ANY(%s) AND amount = %s""",
                                       (register, register, refs, amount)).fetchall()]


def _id(oid: str) -> int:
    return int(oid.split(":", 1)[1])


def applied_anchors(anchors: list) -> tuple:
    """The old estate's last word on each donation. `anchors`: (old_id,
    copied). → ({old_id: None when applied, else why not}, the versions
    seen). A donation is its stable content key (`source`, `row_key`); the
    latest is the highest old id among its live judgments (old ids rise
    with `decided_at`); no version is named here."""
    latest: dict = {}
    for oid, c in anchors:
        if not c.get("withdrawn_at") and c.get("row_key"):
            k = (c.get("source"), c["row_key"])
            if k not in latest or _id(oid) > _id(latest[k]):
                latest[k] = oid
    by_oid = dict(anchors)
    out, versions = {}, {}
    for oid, c in anchors:
        v = versions.setdefault(c.get("weights_version"), {"rows": 0, "live": 0, "applied": 0})
        v["rows"] += 1
        if c.get("withdrawn_at"):
            out[oid] = "withdrawn"
            continue
        v["live"] += 1
        if not c.get("row_key"):
            # a ledger version before the content key (1.0, 1.1): which later
            # judgment re-judged its donation cannot be told, so it is not the word
            out[oid] = "names no donation key (a ledger version before the content key)"
            continue
        top = latest[(c.get("source"), c["row_key"])]
        if top == oid:
            out[oid] = None
            v["applied"] += 1
        else:
            out[oid] = f"superseded by {top} (weights {by_oid[top].get('weights_version')})"
    newest = max(anchors, key=lambda a: _id(a[0]))[1].get("weights_version") if anchors else None
    return out, {"latest_decision_version": newest, "versions": dict(sorted(versions.items(), key=lambda kv: str(kv[0])))}


def map_all(old, conn, s: str, log=print) -> dict:
    """Fill row_a, row_b, verdict and mapped_how on every copied row."""
    t0 = time.monotonic()
    tally: dict = {}
    rows = conn.execute(f"SELECT old_id, source, copied FROM {s}.old_decisions ORDER BY old_id").fetchall()
    folds = [(oid, c) for oid, src, c in rows if src == "roster_identity_folds"]
    anchors = [(oid, c) for oid, src, c in rows if src == "donor_anchors"]
    verdicts = [(oid, c) for oid, src, c in rows if src == "review_verdicts"]
    # directors named anywhere
    director_ids = set()
    for _, c in folds:
        director_ids.update([c["kept_key"], c["folded_key"]])
    for _, c in anchors:
        if c.get("band") == "corroborated":
            pk = (c.get("features") or {}).get("person_key")
            if pk:
                director_ids.add(str(pk))
    for _, c in verdicts:
        director_ids.add(str(c["card_key"]))
    dmap = director_map(old, conn, s, [i for i in director_ids if _OLD_KEY.match(str(i))])
    log(f"links.old: {len(director_ids)} old director records, {sum(1 for v in dmap.values() if v[0])} mapped ({time.monotonic() - t0:.0f} s)")
    updates = []
    for oid, c in folds:
        a, how_a = dmap.get(str(c["kept_key"]), (None, "not a director record"))
        b, how_b = dmap.get(str(c["folded_key"]), (None, "not a director record"))
        verdict = "same"
        if a and b and a != b:
            ra, rb = links.pair(a, b)
            how = f"both records mapped ({how_a}; {how_b})"
        else:
            ra = rb = None
            how = f"kept: {how_a}; folded: {how_b}" if not (a and b) else "both records map to one published row"
        if c.get("withdrawn_at"):
            how = f"withdrawn in the old estate ({c.get('withdrawn_reason') or 'no reason given'}); not applied. " + how
        updates.append((ra, rb, verdict, how, oid))
    applied, seen = applied_anchors(anchors)
    tally["donor_anchors_versions"] = seen
    pair_anchors = [c for _, c in anchors if c.get("band") in ("accept", "corroborated")]
    donmap = donation_map(old, conn, s, pair_anchors)
    for oid, c in anchors:
        band = c.get("band")
        if band not in ("accept", "corroborated"):
            updates.append((None, None, None, f"names no second row (band {band})", oid))
            continue
        d, how_d = donmap.get(oid, (None, "no donation row found"))
        if band == "accept":
            other, how_o = (links.ref("companies", f"companies/{c['matched_nzbn']}"), "the accepted NZBN") if c.get("matched_nzbn") else (None, "no NZBN on the accept")
        else:
            pk = str((c.get("features") or {}).get("person_key") or "")
            other, how_o = dmap.get(pk, (None, "the corroborated identity names no director record"))
        if d and other:
            ra, rb = links.pair(d, other)
            how = f"donation: {how_d}; other: {how_o}"
        else:
            ra = rb = None
            how = f"donation: {how_d}; other: {how_o}"
        if applied[oid]:
            how = (applied[oid] if applied[oid].startswith(("withdrawn", "superseded")) else f"superseded: {applied[oid]}") \
                + " in the old estate; not applied. " + how
        updates.append((ra, rb, "same", how, oid))
    # verdicts: hold → contested, on the pair the corroborated anchor at that version named
    anchor_by_pk: dict = {}
    for oid, c in anchors:
        if c.get("band") == "corroborated" and not c.get("withdrawn_at"):
            pk = str((c.get("features") or {}).get("person_key") or "")
            anchor_by_pk.setdefault((pk, c.get("weights_version")), []).append(oid)
    anchor_rows = {u[4]: u for u in updates}
    latest_verdict: dict = {}
    for oid, c in verdicts:
        if not c.get("withdrawn_at"):
            k = str(c["card_key"])
            if k not in latest_verdict or _id(oid) > _id(latest_verdict[k]):
                latest_verdict[k] = oid
    for oid, c in verdicts:
        cands = anchor_by_pk.get((str(c["card_key"]), c.get("weights_version")), [])
        live = [x for x in cands if applied.get(x) is None]
        mapped = [anchor_rows[x] for x in live if anchor_rows.get(x) and anchor_rows[x][0]]
        if mapped:
            ra, rb = mapped[0][0], mapped[0][1]
            how = f"the corroborated anchor this hold read ({live[0]}); {len(mapped)} of {len(live)} applied anchors on the identity map"
        else:
            ra = rb = None
            how = (f"the identity's {len(live)} applied anchors at {c.get('weights_version')} map to no pair" if live
                   else "no corroborated anchor at that version carries this identity key")
        if c.get("withdrawn_at"):
            how = "withdrawn in the old estate; not applied. " + how
        elif latest_verdict.get(str(c["card_key"])) != oid:
            how = f"superseded by {latest_verdict[str(c['card_key'])]} in the old estate; not applied. " + how
        elif cands and not live:
            how = (f"superseded in the old estate: every anchor this hold read at {c.get('weights_version')} "
                   "was judged again since; not applied. " + how)
        updates.append((ra, rb, "contested", how, oid))
    with conn.cursor() as w:
        w.executemany(f"UPDATE {s}.old_decisions SET row_a = %s, row_b = %s, verdict = %s, mapped_how = %s WHERE old_id = %s", updates)
    conn.commit()
    for ra, rb, v, how, oid in updates:
        src = oid.split(":")[0]
        t = tally.setdefault(src, {"rows": 0, "name a pair": 0, "mapped": 0, "unmapped": 0, "not applied": 0})
        t["rows"] += 1
        if v:
            t["name a pair"] += 1
            t["mapped" if ra else "unmapped"] += 1
            if how.startswith(("withdrawn", "superseded")):
                t["not applied"] += 1
    tally["seconds"] = round(time.monotonic() - t0, 1)
    log(f"links.old: mapped: {json.dumps(tally)}")
    return tally


def promote(conn, s: str, log=print) -> dict:
    """The old estate's last word, mapped, into `<schema>.decisions` as
    `old-estate:<table>:<id>`, once each (decisions are only ever added to:
    a row already there is left alone)."""
    rows = conn.execute(f"""
        SELECT old_id, row_a, row_b, verdict, copied, mapped_how FROM {s}.old_decisions
        WHERE row_a IS NOT NULL AND verdict IS NOT NULL
          AND mapped_how NOT LIKE 'withdrawn%%' AND mapped_how NOT LIKE 'superseded%%'
          AND NOT EXISTS (SELECT 1 FROM {s}.decisions d WHERE d.made_by = 'old-estate:' || old_id)
        ORDER BY old_id""").fetchall()
    n = 0
    with conn.cursor() as w:
        for oid, a, b, v, copied, how in rows:
            evidence = {"old_table": oid.split(":")[0], "old_id": oid, "mapped_how": how,
                        "old_rule": copied.get("rule"), "old_band": copied.get("band"), "old_verdict": copied.get("verdict"),
                        "old_evidence": copied.get("evidence") or copied.get("features") or {}}
            errs = links.check_decision(v, f"old-estate:{oid}", evidence)
            if errs:
                raise ValueError(f"{oid}: {errs}")
            w.execute(f"INSERT INTO {s}.decisions (row_a, row_b, verdict, made_by, made_on, made_at) VALUES (%s, %s, %s, %s, %s::jsonb, %s)",
                      (a, b, v, f"old-estate:{oid}", json.dumps(evidence, default=str), copied.get("decided_at")))
            n += 1
    conn.commit()
    log(f"links.old: promoted {n} decisions")
    return {"promoted": n}


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    steps = [a for a in ("--copy", "--map", "--promote") if a in argv] or ["--copy", "--map", "--promote"]
    out = {}
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn, db.connect(db.OLD_READ_KEY, OLD_DB) as old:
        conn.execute("SET statement_timeout = 0")
        old.execute("SET statement_timeout = '300s'")
        conn.execute(links.ddl(s))
        conn.commit()
        if "--copy" in steps:
            out["copy"] = copy_ledgers(old, conn, s)
        if "--map" in steps:
            out["map"] = map_all(old, conn, s)
        if "--promote" in steps:
            out["promote"] = promote(conn, s)
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
