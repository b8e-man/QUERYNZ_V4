"""Post-mint review lane (Arthur 2026-08-14): heal issues shortly after
they reach the graph, automatically.

Arthur's ruling, verbatim: "there is no human. we need to find an
automatic solution. No waiting for me. We will just sample the work that
is performed and I will review it occasionally." So this lane runs on a
timer with no approval step. The safety model is:

  1. REVERSIBLE actions only — quarantine flips a column
     (claim_graph.remediate.quarantine_entity); nothing is deleted.
  2. Calibration bands — only >= AUTO_BAND confidence executes; below
     it the row is parked for the crawler / a second look.
  3. Sampled oversight — every verdict mirrors to
     var/reviewer_verdicts/mint_lane_verdicts.jsonl, which the Review
     tab already renders, so Arthur's occasional read costs nothing new.

Three passes, one cycle: SCREEN fresh mints against suspicion patterns,
JUDGE queued rows with the fragment-tier LLM prompt (reviewer.fragments
— Harlow-grounded, trap-aware), EXECUTE calibrated verdicts. Patterns
also serve as RULE-GAP DETECTORS: negation-prefix or article-led hits
should be zero under v3-det-1.2 — a hit means an era rule is leaking,
and the lane catches what the rule missed.

Truncated verdicts are never quarantined ("repaired, not deleted" — the
visible part IS a real name); they park as flagged-truncated for the
repair phase. Abstain clears — abstain is the design."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime

from psycopg import Connection

from reviewer import fragments, settings   # sanctioned crossing

log = logging.getLogger("healer.mint_lane")

AUTO_BAND = 0.9
# re-screen overlap: the poller looks this far behind its watermark so a
# mint that committed between snapshot and watermark write is never missed
OVERLAP = "1 hour"

DDL = """
CREATE TABLE IF NOT EXISTS mint_review (
    entity_id   bigint PRIMARY KEY,
    name        text NOT NULL,
    type        text NOT NULL,
    pattern     text NOT NULL,
    status      text NOT NULL DEFAULT 'queued',
    verdict     text,
    confidence  real,
    reasoning   text,
    screened_at timestamptz NOT NULL DEFAULT now(),
    judged_at   timestamptz,
    actioned_at timestamptz
);
CREATE INDEX IF NOT EXISTS mint_review_status_idx ON mint_review (status);
CREATE TABLE IF NOT EXISTS entity_quarantine (
    id            bigserial PRIMARY KEY,
    entity_id     bigint NOT NULL,
    name          text,
    type          text,
    reason        text NOT NULL,
    verdict       jsonb,
    quarantined_at timestamptz NOT NULL DEFAULT now(),
    reverted_at   timestamptz,
    revert_reason text
);
CREATE TABLE IF NOT EXISTS mint_lane_state (
    k text PRIMARY KEY,
    v timestamptz NOT NULL
);
-- repair-lane rename audit: reversal = restore old_name
CREATE TABLE IF NOT EXISTS entity_renames (
    id          bigserial PRIMARY KEY,
    entity_id   bigint NOT NULL,
    old_name    text NOT NULL,
    new_name    text NOT NULL,
    reason      text NOT NULL,
    evidence    jsonb,
    renamed_at  timestamptz NOT NULL DEFAULT now(),
    reverted_at timestamptz
);
-- crawler R-G2 heal audit: reversal = restore old_object_entity_id
CREATE TABLE IF NOT EXISTS claim_object_detachments (
    id                   bigserial PRIMARY KEY,
    claim_id             bigint NOT NULL,
    old_object_entity_id bigint NOT NULL,
    reason               text NOT NULL,
    detached_at          timestamptz NOT NULL DEFAULT now(),
    reverted_at          timestamptz
);
ALTER TABLE mint_review ADD COLUMN IF NOT EXISTS judging_at timestamptz;
-- WHICH MODEL SAID SO (C454, 2026-09-25). reviewer.model._judge_at has always
-- computed the SERVED model onto each verdict, with a comment explaining why
-- mixed-model corpora must stay separable — and the insert dropped it. So when
-- the gateway spent 37 hours answering chat with the page recogniser, the only
-- way to ask which of 32,279 entity judgments it made was to join a timestamp
-- against a separate audit file. A provenance field no table stores is a
-- comment. NULL means not recorded, never 'the default model'.
ALTER TABLE mint_review ADD COLUMN IF NOT EXISTS model text;
ALTER TABLE entities ADD COLUMN IF NOT EXISTS quarantined_at timestamptz;
-- the screen's window predicate; without it every pattern full-scans
CREATE INDEX IF NOT EXISTS entities_created_idx ON entities (created_at);
"""

# Suspicion patterns over fresh article-minted entities. Each is a SQL
# predicate on entities e; matching mints queue for the LLM. Ordered:
# the first matching pattern names the row.
PATTERNS = [
    # the 'Aoake Te' class — structure protects capitalised surfaces by
    # design, so the LLM is the instrument that can condemn them
    ("trailing-particle", r"""
        lower(substring(e.name from '\m([A-Za-zĀĒĪŌŪāēīōū]+)$'))
            IN ('te','ngā','nga','he','ka','o','ō','i','ki','ana','kei',
                'e','ko','nā','rā','mō','nō','mo','na','mā')"""),
    # census predicate: lowercase-led te reo prose that slipped structure
    ("lowercase-led", r"""
        e.name ~ '^[a-zāēīōū]'
        AND (e.name ~ '[āēīōū]'
             OR lower(e.name) ~ '\m(te|ngā|nga|ki|ana|kei|whaka)\M')"""),
    # rule-gap detectors: should be ZERO under v3-det-1.2
    ("negation-prefix", r"e.name ~* '^non[ -]'"),
    ("article-led", r"e.name ~ '^(a|an) [A-ZĀĒĪŌŪ]'"),
    # R-G4 extension (Arthur 2026-08-14, "we still have some non-maori
    # entities"): negation EMBEDDED mid-name is a mixed class — cohort
    # labels and headline fragments ("Māori / Non-Māori") beside real
    # things ("Nuclear Arms Non-Proliferation Treaty", register-live
    # "Non Fungible Labs Limited") — so unlike the prefix it is never
    # quarantined by structure; the LLM is the instrument
    ("embedded-negation", r"e.name ~* '\mnon[ -]' AND e.name !~* '^non[ -]'"),
    # leads batch (Arthur 2026-08-14) — three mixed classes structure cannot
    # condemn: a list is not an entity, but "Smith, Jones & Partners" is a
    # firm; a headline is not a person, but long legal names exist; a
    # possessive stub lost its noun, but McDonald's didn't
    ("comma-list", r"(e.name ~ ',.*,' OR e.name ~* ',[^,]* and ')"
                   r" AND e.type IN ('person', 'organisation')"),
    ("headline-prose", r"e.type = 'person' AND length(e.name) > 40"),
    ("possessive-stub", r"e.name ~ '''s$' AND e.name !~ ' '"),
    # leads batch 2 (2026-08-14) — mixed classes: 'John "Hondo" Smith' is
    # a nickname, 'Caitlyn "Jesus' is a cut quote; @handles may shadow real
    # entities; "Kate and Bob" is two people but "Marks and Spencer" is a
    # shop; "Former Prime Minister X" is a role wearing a name
    ("quoted-name", r"e.name LIKE '%%\"%%'"),
    ("at-handle", r"e.name ~ '^@'"),
    ("and-couple", r"e.type = 'person' AND e.name ~*"
                   r" '^[A-ZĀĒĪŌŪ][a-zāēīōū]+ and [A-ZĀĒĪŌŪ][a-zāēīōū]+$'"),
    ("role-led-person", r"e.type = 'person' AND e.name ~*"
                        r" '^(chief|deputy|acting|former|interim) '"),
    # leads batch 3 (2026-08-14) — mixed classes: "Picton Picton" is a
    # capture stutter but "Aka Aka" and "Duran Duran" are names; headline
    # verb-phrases hide real people (Will Hughes, Hamed Said)
    ("word-stutter", r"lower(e.name) ~ '\m(\w+) \1\M'"),
    ("verb-phrase", r"e.name ~* '.+\m(is|was|were|has|have|will|says|said|being)\M'"),
]

SCREEN_SQL = """
SELECT e.id, e.name, e.type
FROM entities e
WHERE e.register_source IS NULL
  AND e.quarantined_at IS NULL
  AND e.created_at > %(since)s
  AND ({pred})
"""

# ALWAYS the repo's var/ — deliberately independent of V3_VAR_DIR
# (a fleet cache concern): the Review tab reads this directory, and the
# mirror IS Arthur's sampling surface. Found live: the fleet env's
# V3_VAR_DIR sent the first 14 verdicts to /home/user/var-era3 where no
# UI would ever show them (2026-08-14).
VERDICTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), "var",
    "reviewer_verdicts", "mint_lane_verdicts.jsonl")


def ensure_schema(g: Connection) -> None:
    # Fast path: once every object exists, running the DDL again is not
    # free — ALTER TABLE / CREATE IF NOT EXISTS take ACCESS EXCLUSIVE
    # requests that queue behind any long reader and then stall every
    # entities/mint_review user behind THEM (estate-wide lock convoy,
    # found live 2026-08-14: one fold-audit scan + this DDL froze both
    # fleets and the judges for 80 minutes).
    done = g.execute("""
        SELECT (SELECT count(*) FROM pg_attribute
                WHERE attrelid = to_regclass('mint_review')
                  AND attname = 'judging_at' AND NOT attisdropped)
             + (SELECT count(*) FROM pg_attribute
                WHERE attrelid = to_regclass('entities')
                  AND attname = 'quarantined_at' AND NOT attisdropped)
             + (to_regclass('entity_quarantine') IS NOT NULL)::int
             + (to_regclass('mint_lane_state') IS NOT NULL)::int
             + (to_regclass('entity_renames') IS NOT NULL)::int
             + (to_regclass('claim_object_detachments') IS NOT NULL)::int
             + (to_regclass('entities_created_idx') IS NOT NULL)::int AS n""").fetchone()
    if done["n"] == 7:
        g.commit()
        return
    g.execute(DDL)
    g.commit()


def _register_allow() -> set[str]:
    """The era-rules item-c allowlist: real register names shaped like
    guard targets ('Mandy Te'). Never queued — queuing them wastes LLM
    cycles and creates the only path to a wrong condemnation."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "extractor", "extractor", "data",
        "maori_register_allowlist.txt")
    try:
        with open(path) as f:
            return {l.strip() for l in f if l.strip() and not l.startswith("#")}
    except OSError:
        return set()


def screen(g: Connection) -> dict:
    """Queue fresh suspicious mints. Watermark advances to now() each
    run; OVERLAP re-covers the write window and the PK absorbs rerun
    duplicates."""
    row = g.execute("SELECT v FROM mint_lane_state WHERE k='watermark'").fetchone()
    since = row["v"] if row else datetime(2026, 8, 14)
    allow = _register_allow()
    stats: dict[str, int] = {}
    for pattern, pred in PATTERNS:
        rows = g.execute(
            SCREEN_SQL.format(pred=pred) + " AND e.created_at > %(since)s - interval '" + OVERLAP + "'",
            {"since": since}).fetchall()
        n = 0
        for r in rows:
            if r["name"].lower() in allow:
                continue
            cur = g.execute("""
                INSERT INTO mint_review (entity_id, name, type, pattern)
                VALUES (%s,%s,%s,%s) ON CONFLICT (entity_id) DO NOTHING""",
                (r["id"], r["name"], r["type"], pattern))
            n += cur.rowcount
        stats[pattern] = n
    g.execute("""
        INSERT INTO mint_lane_state (k, v) VALUES ('watermark', now())
        ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v""")
    g.commit()
    return stats


def judge(g: Connection, limit: int = 200, concurrency: int = 6) -> int:
    """LLM-judge queued rows with the fragment-tier prompt; mirror every
    verdict to the Review tab's jsonl. Concurrency 6 against the local
    llama-server's parallel slots (same pattern as fragments
    .annotate_file — sequential measured 15 s/verdict, 2026-08-14);
    psycopg3 serialises the shared connection, verdicts land as they
    finish (kill-safe)."""
    from concurrent.futures import ThreadPoolExecutor
    # atomic batch claim (FOR UPDATE SKIP LOCKED — the extraction queue's
    # pattern): parallel judge processes, one per GPU, share the queue
    # without double-judging. A killed judge's rows revert via the stale
    # reset in run().
    # fragment-prompt rows ONLY — crawler findings (pattern 'crawler-*')
    # carry different questions and are judged by reviewer/crawler.py
    rows = g.execute("""
        WITH pick AS (
            SELECT entity_id FROM mint_review WHERE status='queued'
              AND pattern NOT LIKE 'crawler-%%'
            ORDER BY screened_at LIMIT %s
            FOR UPDATE SKIP LOCKED)
        UPDATE mint_review m SET status='judging', judging_at=now()
        FROM pick WHERE m.entity_id = pick.entity_id
        RETURNING m.entity_id, m.name, m.type, m.pattern""",
        (limit,)).fetchall()
    g.commit()
    os.makedirs(os.path.dirname(VERDICTS_PATH), exist_ok=True)

    def _one(r):
        ent = {"id": r["entity_id"], "name": r["name"], "type": r["type"],
               "claims": 0}
        try:
            v = fragments.judge_name(g, ent)
            g.commit()      # close the per-case read transaction
            return r, v
        except Exception as e:  # noqa: BLE001 — one bad case never stops a run
            log.warning("entity %s failed: %s", r["entity_id"], e)
            try:
                g.rollback()
            except Exception:   # noqa: BLE001
                pass
            return r, None

    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        with open(VERDICTS_PATH, "a") as fh:
            for r, v in ex.map(_one, rows):
                if v is None:
                    continue
                g.execute("""
                    UPDATE mint_review SET verdict=%s, confidence=%s,
                           reasoning=%s, status='judged', judged_at=now(),
                           model=%s
                    WHERE entity_id=%s""",
                    (v.get("verdict"), v.get("confidence"), v.get("reasoning"),
                     v.get("model") or settings.LLM_MODEL, r["entity_id"]))
                g.commit()
                fh.write(json.dumps({
                    "id": r["entity_id"], "name": r["name"], "type": r["type"],
                    "pattern": r["pattern"], "verdict": v.get("verdict"),
                    "confidence": v.get("confidence"),
                    "reasoning": v.get("reasoning"),
                    "model": v.get("model") or settings.LLM_MODEL,
                    "tier": "mint-lane", "prompt_version": "fragment-tier1-v1",
                }, ensure_ascii=False) + "\n")
                fh.flush()
                n += 1
    return n


def execute(g: Connection) -> dict:
    """Act on calibrated verdicts. Reversible actions only."""
    from claim_graph import remediate
    stats = {"quarantined": 0, "flagged_truncated": 0, "cleared": 0,
             "parked": 0}
    rows = g.execute("""
        SELECT entity_id, name, verdict, confidence, reasoning, pattern
        FROM mint_review WHERE status='judged'
          AND pattern NOT LIKE 'crawler-%'""").fetchall()
    for r in rows:
        v, conf = r["verdict"], r["confidence"] or 0
        if v == "debris" and conf >= AUTO_BAND:
            try:
                remediate.quarantine_entity(
                    g, r["entity_id"], f"mint-lane:{r['pattern']}",
                    verdict={"verdict": v, "confidence": conf,
                             "reasoning": r["reasoning"]})
            except LookupError:
                # a deterministic heal folded the entity away while its
                # verdict sat queued (race found live 2026-08-14) — the
                # verdict is moot, not an error
                g.rollback()
                status = "gone"
                stats["gone"] = stats.get("gone", 0) + 1
                g.execute("""
                    UPDATE mint_review SET status=%s, actioned_at=now()
                    WHERE entity_id=%s""", (status, r["entity_id"]))
                g.commit()
                continue
            status = "quarantined"
            stats["quarantined"] += 1
        elif v == "truncated" and conf >= AUTO_BAND:
            status = "flagged-truncated"     # repaired, not deleted
            stats["flagged_truncated"] += 1
        elif v in ("real_name", "abstain"):
            status = "cleared"               # abstain is the design
            stats["cleared"] += 1
        else:
            status = "parked"                # low confidence: crawler's job
            stats["parked"] += 1
        g.execute("""
            UPDATE mint_review SET status=%s, actioned_at=now()
            WHERE entity_id=%s""", (status, r["entity_id"]))
        g.commit()
    return stats


def run(g: Connection, judge_limit: int = 200,
        concurrency: int = 6) -> None:
    ensure_schema(g)
    # a judge that died mid-batch left rows in 'judging'; after 30 min they
    # are nobody's — re-offer them
    g.execute("""
        UPDATE mint_review SET status='queued', judging_at=NULL
        WHERE status='judging' AND judging_at < now() - interval '30 minutes'""")
    g.commit()
    s = screen(g)
    log.info("mint-lane screen: %s", s)
    n = judge(g, judge_limit, concurrency=concurrency)
    log.info("mint-lane judged: %d", n)
    x = execute(g)
    log.info("mint-lane executed: %s", x)
