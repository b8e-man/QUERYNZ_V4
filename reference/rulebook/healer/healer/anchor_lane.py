"""Anchor-audit lane (Arthur 2026-08-15: "can we hand the task you
describe to one of the LLM instances?" — the task being the register
panel's absurd-anchor spotting, mechanised).

Born from the NZTA find: NZ TALENT ALLIANCE LIMITED registered the
trading name "NZTA" and the gazetteer anchored the crown agency to a
shelf company. The C3 surname gate and the v0.6 multi-token restriction
never covered registered acronym trading names.

Mint-lane safety model, unchanged: reversible action only
(remediate.unanchor_entity — nzbn NULL + gazetteer blocklist, mentions/
claims untouched), AUTO_BAND calibration, every verdict mirrored to the
verdicts jsonl for Arthur's sampled read.

SCREEN is deterministic and cheap: an nzbn-anchored live entity is
suspect when its graph name shares ZERO content tokens with the register
entity name AND with every trading name registered under that NZBN.
Legitimate trading-name anchors ("Polynesian Taste" → VAVAU RESTAURANT
LIMITED, trading as Polynesian Taste) share tokens with a trading name
and never queue. JUDGE shows the model both sides — what the news says
about the graph entity vs who the register says the NZBN is — and asks
one question: same real-world organisation? EXECUTE de-anchors only
verdict='different' at >= AUTO_BAND; 'same' and abstain clear; the rest
park. Abstain is the design."""
from __future__ import annotations

import json
import logging
import os

from psycopg import Connection

from reviewer import model, settings   # sanctioned crossing: the LLM client

log = logging.getLogger("healer.anchor_lane")

AUTO_BAND = 0.9

DDL = """
CREATE TABLE IF NOT EXISTS anchor_review (
    entity_id     bigint PRIMARY KEY,
    name          text NOT NULL,
    type          text NOT NULL,
    nzbn          text NOT NULL,
    register_name text NOT NULL,
    status        text NOT NULL DEFAULT 'queued',
    verdict       text,
    confidence    real,
    reasoning     text,
    kind          text NOT NULL DEFAULT 'mislink',
    screened_at   timestamptz NOT NULL DEFAULT now(),
    judging_at    timestamptz,
    judged_at     timestamptz,
    actioned_at   timestamptz
);
CREATE INDEX IF NOT EXISTS anchor_review_status_idx ON anchor_review (status);
ALTER TABLE anchor_review ADD COLUMN IF NOT EXISTS judging_at timestamptz;
-- WHICH MODEL SAID SO (C454) — the same gap as mint_review's. NULL means not
-- recorded, never 'the default model'.
ALTER TABLE anchor_review ADD COLUMN IF NOT EXISTS model text;
ALTER TABLE anchor_review ADD COLUMN IF NOT EXISTS kind text NOT NULL DEFAULT 'mislink';
"""

VERDICTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), "var",
    "reviewer_verdicts", "anchor_lane_verdicts.jsonl")

# content-token overlap: generic corporate noise never counts as overlap
_STOP = {"limited", "ltd", "the", "of", "new", "zealand", "nz", "group",
         "holdings", "trust", "company", "and", "&", "te", "o", "a"}

SYSTEM = """You audit register anchors for a New Zealand news-entity graph.
An entity extracted from news carries an NZBN (register anchor) linking it
to a registered company. Sometimes the anchor is WRONG: a shelf company
registered a trading name (often an acronym) that coincides with a famous
organisation's name, and the matcher linked the famous organisation to the
shelf company.

You are shown BOTH sides. Decide whether the news entity and the
registered company are the SAME real-world organisation.

verdict:
- "same": the register row plausibly IS this organisation (including via a
  listed trading name).
- "different": the register row is clearly another business wearing a
  coinciding name — e.g. a crown agency or major institution anchored to a
  small private company with unrelated directors.
- "abstain": cannot tell from the evidence.

Confidence in [0,1]. A wrong de-anchor loses a good link, a wrong keep
poisons dossiers with another company's directors — be sure either way."""

SYSTEM_TWIN = """You judge whether a news organisation and a registered
company are the SAME organisation, for a New Zealand news-entity graph.

The news entity is UNANCHORED: the register matcher could not link it
(its name is made of common words, which the matcher deliberately
refuses). A candidate registered company exists whose name is the news
name plus a legal suffix. Coincidence is COMMON: "CROWN LIMITED" is not
the Crown, "WHITE HOUSE LIMITED" is not the White House, "ANZ LIMITED"
is not the bank (the bank is ANZ BANK NEW ZEALAND LIMITED). The
directors and registration details usually betray a coincidence
instantly.

verdict "same" ONLY when the registered company IS the organisation the
news writes about — its actual NZ operating or listed entity (e.g. THE
WAREHOUSE GROUP LIMITED for The Warehouse Group, AIR NEW ZEALAND
LIMITED for Air New Zealand). A mere local subsidiary of a global brand
(FACEBOOK NEW ZEALAND LIMITED for "Facebook" the platform) is
"different": the news means the global organisation, not the local
paperwork entity. Statutory/crown bodies written like companies are
"different" from any coincidental company. Default to "different" or
"abstain" when unsure — a wrong fold poisons a famous entity with a
stranger's directors."""

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"enum": ["same", "different", "abstain"]},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
    },
    "required": ["verdict", "confidence", "reasoning"],
}


def ensure_schema(g: Connection) -> None:
    g.execute(DDL)
    g.commit()


def _tokens(s: str) -> set[str]:
    import re
    return set(re.findall(r"[a-zāēīōū']+", s.lower())) - _STOP


def screen_twins(g: Connection, reg: Connection,
                 min_mentions: int = 10) -> int:
    """Queue the INVERSE class (Arthur's Warehouse Group find,
    2026-08-15): high-mention UNANCHORED orgs whose name + legal suffix
    matches exactly one live registered company. The generic-phrase gate
    rightly refuses these at extraction (all-common-word names); the
    judge decides fold-vs-coincidence with both sides on the table."""
    rows = g.execute("""
        SELECT e.id, e.name, p.n AS mentions
        FROM entities e JOIN entity_prominence p ON p.entity_id = e.id
        WHERE e.type='organisation' AND e.nzbn IS NULL
          AND e.register_source IS NULL AND e.quarantined_at IS NULL
          AND p.n >= %s
          AND NOT EXISTS (SELECT 1 FROM anchor_review a
                          WHERE a.entity_id = e.id)
        ORDER BY p.n DESC""", (min_mentions,)).fetchall()
    n = 0
    for r in rows:
        nm = r["name"].lower()
        cands = reg.execute("""
            SELECT nzbn, entity_name FROM entities
            WHERE lower(entity_name) IN (%s, %s, %s, %s)
              AND entity_status = 'Registered'""",
            (nm + " limited", nm + " ltd", nm + " (nz) limited",
             nm + " new zealand limited")).fetchall()
        if len(cands) != 1:
            continue
        g.execute("""
            INSERT INTO anchor_review (entity_id, name, type, nzbn,
                                       register_name, kind)
            VALUES (%s, %s, 'organisation', %s, %s, 'twin-fold')
            ON CONFLICT (entity_id) DO NOTHING""",
            (r["id"], r["name"], cands[0]["nzbn"], cands[0]["entity_name"]))
        n += 1
        if n % 500 == 0:
            g.commit()
    g.commit()
    return n


def screen(g: Connection, reg: Connection) -> int:
    """Queue suspects: anchored live entities whose name shares zero
    content tokens with the register name and every trading name."""
    rows = g.execute("""
        SELECT e.id, e.name, e.type, e.nzbn
        FROM entities e
        WHERE e.nzbn IS NOT NULL AND e.quarantined_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM anchor_review a
                          WHERE a.entity_id = e.id)""").fetchall()
    if not rows:
        return 0
    nzbns = list({r["nzbn"] for r in rows})
    regnames: dict[str, list[str]] = {}
    for chunk in range(0, len(nzbns), 5000):
        part = nzbns[chunk:chunk + 5000]
        for rr in reg.execute(
                "SELECT nzbn, entity_name FROM entities WHERE nzbn = ANY(%s)",
                (part,)).fetchall():
            regnames.setdefault(rr["nzbn"], []).append(rr["entity_name"])
        for rr in reg.execute(
                "SELECT nzbn, trading_name FROM bulk.companies_trading_name "
                "WHERE nzbn = ANY(%s)", (part,)).fetchall():
            regnames.setdefault(rr["nzbn"], []).append(rr["trading_name"])
    n = 0
    for r in rows:
        names = regnames.get(r["nzbn"])
        if not names:
            continue                      # nzbn not in this register copy
        gtok = _tokens(r["name"])
        if not gtok:
            continue
        if any(gtok & _tokens(nm) for nm in names):
            continue                      # shares a token somewhere — fine
        g.execute("""
            INSERT INTO anchor_review (entity_id, name, type, nzbn,
                                       register_name)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (entity_id) DO NOTHING""",
            (r["id"], r["name"], r["type"], r["nzbn"], names[0]))
        n += 1
        if n % 500 == 0:
            g.commit()
    g.commit()
    return n


def _case(g: Connection, reg: Connection, r: dict) -> str | None:
    """Build the both-sides prompt, or None when the register no longer
    holds the NZBN (a rebuilt copy can drop rows the screen saw — the
    row is then 'gone', not an error)."""
    surfaces = g.execute("""
        SELECT surface_form, count(*) n FROM mentions
        WHERE entity_id=%s AND surface_form IS NOT NULL
        GROUP BY 1 ORDER BY n DESC LIMIT 5""", (r["entity_id"],)).fetchall()
    n_mentions = g.execute(
        "SELECT count(*) n FROM mentions WHERE entity_id=%s",
        (r["entity_id"],)).fetchone()["n"]
    evidence = g.execute("""
        SELECT evidence_text FROM model_claims WHERE subject_entity_id=%s   -- B10 T2: the gate
          AND evidence_text IS NOT NULL AND length(evidence_text) > 40
        ORDER BY id DESC LIMIT 3""", (r["entity_id"],)).fetchall()
    core = reg.execute("""
        SELECT id, entity_name, entity_type, entity_status,
               registered_at::date::text AS registered_at
        FROM entities WHERE nzbn=%s""", (r["nzbn"],)).fetchone()
    if core is None:
        return None
    rid = core["id"]
    directors = [d["full_name"] for d in reg.execute("""
        SELECT full_name FROM director_roles
        WHERE entity_id=%s AND ceased_at IS NULL AND NOT suppressed
        LIMIT 5""", (rid,)).fetchall()]
    trading = [t["trading_name"] for t in reg.execute("""
        SELECT trading_name FROM bulk.companies_trading_name
        WHERE nzbn=%s LIMIT 8""", (r["nzbn"],)).fetchall()]
    lines = [
        f"NEWS ENTITY: {r['name']!r} (type {r['type']}, "
        f"{n_mentions} news mentions)",
        "Seen in print as: " + ", ".join(
            f"{s['surface_form']!r}×{s['n']}" for s in surfaces),
    ]
    for ev in evidence:
        lines.append(f"  news evidence: {ev['evidence_text'][:220]}")
    lines += [
        "",
        f"REGISTER ROW it is anchored to (NZBN {r['nzbn']}):",
        f"  {core['entity_name']} · {core['entity_type']} · "
        f"{core['entity_status']} · registered {core['registered_at']}",
        f"  directors: {', '.join(directors) or '(none listed)'}",
        f"  trading names: {', '.join(trading) or '(none)'}",
        "",
        "Same real-world organisation?",
    ]
    return "\n".join(lines)


def judge(g: Connection, reg: Connection, limit: int = 200,
          concurrency: int = 6) -> int:
    from concurrent.futures import ThreadPoolExecutor
    rows = g.execute("""
        WITH pick AS (
            SELECT entity_id FROM anchor_review WHERE status='queued'
            ORDER BY screened_at LIMIT %s
            FOR UPDATE SKIP LOCKED)
        UPDATE anchor_review a SET status='judging', judging_at=now()
        FROM pick WHERE a.entity_id = pick.entity_id
        RETURNING a.entity_id, a.name, a.type, a.nzbn, a.kind""",
        (limit,)).fetchall()
    g.commit()
    os.makedirs(os.path.dirname(VERDICTS_PATH), exist_ok=True)

    # prompts build on THIS thread — workers touch only the LLM edge, so
    # no worker ever commits/rolls back the shared connections under the
    # main loop's writes (review 2026-08-15: a worker rollback landing
    # between the status write and its commit discarded the judged row)
    cases = []
    for r in rows:
        try:
            prompt = _case(g, reg, r)
            g.commit()
            reg.commit()
        except Exception as e:  # noqa: BLE001 — one case never stops a run
            log.warning("entity %s case build failed: %s", r["entity_id"], e)
            for c in (g, reg):
                try:
                    c.rollback()
                except Exception:  # noqa: BLE001
                    pass
            g.execute("UPDATE anchor_review SET status='queued' "
                      "WHERE entity_id=%s", (r["entity_id"],))
            g.commit()
            continue
        if prompt is None:      # register no longer holds the NZBN
            g.execute("UPDATE anchor_review SET status='gone', "
                      "actioned_at=now() WHERE entity_id=%s",
                      (r["entity_id"],))
            g.commit()
            continue
        cases.append((r, prompt))

    def _one(case):
        r, prompt = case
        try:
            system = SYSTEM_TWIN if r["kind"] == "twin-fold" else SYSTEM
            v = model.judge(system, prompt, schema=SCHEMA)
            v["confidence"] = min(max(float(v["confidence"]), 0.0), 1.0)
            return r, v
        except Exception as e:  # noqa: BLE001
            log.warning("entity %s judge failed: %s", r["entity_id"], e)
            return r, None

    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        with open(VERDICTS_PATH, "a") as fh:
            for r, v in ex.map(_one, cases):
                if v is None:
                    g.execute("UPDATE anchor_review SET status='queued' "
                              "WHERE entity_id=%s", (r["entity_id"],))
                    g.commit()
                    continue
                g.execute("""
                    UPDATE anchor_review SET verdict=%s, confidence=%s,
                           reasoning=%s, status='judged', judged_at=now(),
                           model=%s
                    WHERE entity_id=%s""",
                    (v["verdict"], v["confidence"], v["reasoning"],
                     v.get("model") or settings.LLM_MODEL, r["entity_id"]))
                g.commit()
                fh.write(json.dumps({
                    "id": r["entity_id"], "name": r["name"],
                    "type": r["type"], "nzbn": r["nzbn"],
                    "pattern": f"anchor-{r['kind']}", "verdict": v["verdict"],
                    "confidence": v["confidence"],
                    "reasoning": v["reasoning"],
                    "model": v.get("model") or settings.LLM_MODEL,
                    "tier": "anchor-lane", "prompt_version": "anchor-v1",
                }, ensure_ascii=False) + "\n")
                fh.flush()
                n += 1
    return n


def execute(g: Connection) -> dict:
    """Act on calibrated verdicts. De-anchor only; reversible (nzbn is
    re-settable and the blocklist row is deletable)."""
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity, unanchor_entity
    stats = {"deanchored": 0, "folded": 0, "cleared": 0, "parked": 0}
    rows = g.execute("""
        SELECT entity_id, name, nzbn, verdict, confidence, kind
        FROM anchor_review WHERE status='judged'""").fetchall()
    for r in rows:
        v, conf = r["verdict"], r["confidence"] or 0
        if r["kind"] == "twin-fold":
            if v == "same" and conf >= AUTO_BAND:
                twin = g.execute("""
                    SELECT id FROM entities WHERE nzbn=%s
                      AND quarantined_at IS NULL""", (r["nzbn"],)).fetchone()
                if twin is None or twin["id"] == r["entity_id"]:
                    status = "parked"
                    stats["parked"] += 1
                else:
                    try:
                        # register node keeps identity (nzbn, register
                        # provenance); news display name wins the label
                        if merge_if_allowed(g, twin["id"], r["entity_id"],
                                            "anchor-lane:twin-fold "
                                            f"{conf:.2f}") is None:
                            # C428: refused. The rename must not run either —
                            # relabelling the register node with the news name
                            # of an entity it was NOT folded with would put one
                            # person's name on another's register identity.
                            status = "parked"
                            stats["parked"] += 1
                        else:
                            rename_entity(g, twin["id"], r["name"],
                                          "anchor-lane:twin-fold-display")
                            status = "folded"
                            stats["folded"] += 1
                    except LookupError:
                        g.rollback()
                        status = "gone"
                        stats["gone"] = stats.get("gone", 0) + 1
            elif v in ("different", "abstain"):
                status = "cleared"
                stats["cleared"] += 1
            else:
                status = "parked"
                stats["parked"] += 1
            g.execute("""
                UPDATE anchor_review SET status=%s, actioned_at=now()
                WHERE entity_id=%s""", (status, r["entity_id"]))
            g.commit()
            continue
        if v == "different" and conf >= AUTO_BAND:
            try:
                unanchor_entity(
                    g, r["entity_id"],
                    reason=f"anchor-lane:acronym-mislink {conf:.2f} "
                           f"(entity {r['entity_id']} {r['name']!r})")
                status = "deanchored"
                stats["deanchored"] += 1
            except LookupError:
                g.rollback()
                status = "gone"           # healed away or already de-anchored
                stats["gone"] = stats.get("gone", 0) + 1
        elif v in ("same", "abstain"):
            status = "cleared"
            stats["cleared"] += 1
        else:
            status = "parked"
            stats["parked"] += 1
        g.execute("""
            UPDATE anchor_review SET status=%s, actioned_at=now()
            WHERE entity_id=%s""", (status, r["entity_id"]))
        g.commit()
    return stats


def run(g: Connection, reg: Connection, judge_limit: int = 200) -> None:
    ensure_schema(g)
    # stale revert (mint-lane recovery half): a killed judge leaves rows
    # 'judging' forever, and screen()'s NOT EXISTS would never requeue them
    g.execute("""
        UPDATE anchor_review SET status='queued'
        WHERE status='judging' AND judging_at < now() - interval '30 min'""")
    g.commit()
    s = screen(g, reg) + screen_twins(g, reg)
    j = judge(g, reg, judge_limit)
    x = execute(g)
    log.info("anchor lane: screened %d, judged %d, executed %s", s, j, x)
