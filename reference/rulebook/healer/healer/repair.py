"""Truncated-name repair lane (design: docs/TRUNCATED_REPAIR_DESIGN.md;
Arthur 2026-08-14: "build this and make it run automatically").

Repairs mint_review rows flagged `flagged-truncated` ("Greater
Wellington Te", "Te Rūnanga o" — real names cut mid-phrase; repaired,
never deleted). EVIDENCE-FIRST and fully mechanical this tranche — no
LLM: the completion must appear VERBATIM in the entity's own sighting
articles, starting exactly with the truncated surface.

  1. COMPLETE: scan the entity's articles for `<surface> <more name
     tokens>`; the winning completion needs >=2 independent articles,
     or 1 article + a register/govt_orgs exact-name hit (163 official
     Māori agency names are exactly this class).
  2. MERGE-PREFERRED: if an entity with the completed name exists (same
     type), merge the stub into it — subject to the register rule: a
     register-ambiguous name needs a corroborate tier.
  3. RENAME otherwise, through remediate.rename_entity (audited,
     reversible, old surface kept as an alias).
  4. No qualifying completion -> stays flagged. Honest stub.

Every action mirrors to the Review tab jsonl. Wired into the nightly
crawler cycle; run standalone via `reviewer repair`."""
from __future__ import annotations

import json
import logging
import os
import re

import psycopg
from psycopg.rows import dict_row

from reviewer import corroborate   # sanctioned crossing
from .mint_lane import VERDICTS_PATH

log = logging.getLogger("healer.repair")

REPAIR_CAP = 300           # rows per run
# C246 (2026-10-07): a row the repair lane could find no completion for was set
# to `repair-no-evidence` and NEVER LOOKED AT AGAIN — the select asked only for
# `flagged-truncated`. But the evidence is the CORPUS, which grows every day, so
# "no evidence today" is a measurement with a date on it and not a verdict.
# 7,001 rows sat in that state, 5,220 of them older than 30 days.
#
# THIRTY DAYS, and the re-queue gets only SPARE capacity. Both numbers come from
# the measurement rather than from feel: there are 2,298 live `flagged-truncated`
# rows against a cap of 300, so putting 5,220 re-queued rows in the same
# `ORDER BY screened_at` would starve genuinely new work for weeks. New rows are
# selected first and the re-queue tops the batch up only if the cap is unfilled,
# which makes it self-regulating: the backlog drains, then the old rows get
# re-asked.
REQUEUE_AFTER_DAYS = 30
MIN_ARTICLES = 2           # independent-evidence bar for a completion
# a completion continues in name-shaped tokens (capitalised or te reo
# particles/macron words), up to 6 more tokens
_CONT = r"((?:\s+(?:[A-ZĀĒĪŌŪ][\w'’\-]*|o|a|ki|te|ngā|nga|ō|ā))){1,6}"


def _backlog():
    """The backlog, or None — and None means the repair lane abstains entirely.

    Queue 8, 2026-09-19: this carried a loopback default, so a lane run without
    `V3_BACKLOG_DSN` did not abstain — it dialled node2's STANDBY. The two
    failures are now told apart, because "nobody told me where the backlog is"
    and "the backlog is down" call for different repairs. Raising here would be
    worse than either: `except Exception` does not catch `SystemExit`, so a
    refusal-by-exit would turn an abstaining lane into a crashing one.
    """
    dsn = os.environ.get("V3_BACKLOG_DSN")
    if not dsn:
        log.warning("V3_BACKLOG_DSN is not set — repair lane abstains entirely "
                    "(no default host: the unit's environment names the backlog)")
        return None
    try:
        return psycopg.connect(dsn, row_factory=dict_row)
    except Exception:   # noqa: BLE001
        log.warning("backlog unreachable at the DSN its environment names — repair lane abstains entirely")
        return None


def _article_texts(g, b, entity_id: int, cap: int = 12) -> list[str]:
    ids = [r["article_id"] for r in g.execute(
        "SELECT article_id FROM mentions WHERE entity_id=%s LIMIT %s",
        (entity_id, cap))]
    if not ids:
        return []
    return [r["text_content"] for r in b.execute(
        "SELECT text_content FROM articles WHERE id = ANY(%s::uuid[]) "
        "AND text_content IS NOT NULL", ([str(i) for i in ids],))]


def find_completion(g, b, reg, entity_id: int, surface: str) -> dict | None:
    """The longest completion supported by enough independent evidence."""
    rx = re.compile(re.escape(surface) + _CONT)
    votes: dict[str, int] = {}
    for text in _article_texts(g, b, entity_id):
        best = None
        for m in rx.finditer(text):
            cand = m.group(0).strip()
            if best is None or len(cand) > len(best):
                best = cand
        if best:
            votes[best] = votes.get(best, 0) + 1
    if not votes:
        return None
    cand, n = max(votes.items(), key=lambda kv: (kv[1], len(kv[0])))
    register_hit = False
    if reg is not None:
        # the register is a HELPER (correctness over coverage): twin
        # drift can strip a table from one box (govt_orgs missing on
        # node2, 2026-08-15, killed the drain) — degrade to no-hit,
        # never crash the lane
        try:
            register_hit = bool(
                reg.execute("SELECT 1 FROM persons WHERE lower(full_name)=lower(%s) "
                            "UNION ALL SELECT 1 FROM govt_orgs WHERE "
                            "lower(legal_name)=lower(%s) OR lower(maori_name)=lower(%s) "
                            "LIMIT 1", (cand, cand, cand)).fetchone())
        except psycopg.Error:
            log.warning("register lookup degraded (table missing or "
                        "register down) — completion votes stand alone")
            reg.rollback()
    if n >= MIN_ARTICLES or (n >= 1 and register_hit):
        return {"completion": cand, "articles": n, "register_hit": register_hit}
    return None


def _mirror(row: dict) -> None:
    os.makedirs(os.path.dirname(VERDICTS_PATH), exist_ok=True)
    with open(VERDICTS_PATH, "a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def select_batch(g) -> tuple[list, int]:
    """The run's rows, newest work first: (rows, how many were re-queued).

    Extracted so the SELECTION can be tested without performing a repair — the
    priority rule below is the whole of C246 and it is not visible from the
    outside of `run()`.
    """
    rows = g.execute("""
        SELECT mr.entity_id, mr.name, mr.type FROM mint_review mr
        JOIN entities e ON e.id = mr.entity_id AND e.quarantined_at IS NULL
        WHERE mr.status = 'flagged-truncated'
        ORDER BY mr.screened_at LIMIT %s""", (REPAIR_CAP,)).fetchall()
    # SPARE CAPACITY ONLY. New work is never displaced: with 2,298 live
    # `flagged-truncated` rows against a cap of 300, putting 5,220 re-queued rows
    # into the same ORDER BY would starve genuinely new rows for weeks. So the
    # re-queue tops the batch up and nothing more, which self-regulates — the
    # backlog drains, then the aged rows get re-asked.
    spare = REPAIR_CAP - len(rows)
    if spare <= 0:
        return list(rows), 0
    again = g.execute("""
        SELECT mr.entity_id, mr.name, mr.type FROM mint_review mr
        JOIN entities e ON e.id = mr.entity_id AND e.quarantined_at IS NULL
        WHERE mr.status = 'repair-no-evidence'
          AND mr.actioned_at < now() - make_interval(days => %s)
        ORDER BY mr.actioned_at LIMIT %s""",
        (REQUEUE_AFTER_DAYS, spare)).fetchall()
    return list(rows) + list(again), len(again)


def run(g) -> dict:
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity
    stats = {"merged": 0, "renamed": 0, "no_evidence": 0, "abstained": 0,
             "requeued": 0}
    b = _backlog()
    if b is None:
        return stats
    reg = corroborate.register_conn()
    rows, requeued = select_batch(g)
    stats["requeued"] = requeued
    for r in rows:
        found = find_completion(g, b, reg, r["entity_id"], r["name"])
        if found is None:
            g.execute("UPDATE mint_review SET status='repair-no-evidence', "
                      "actioned_at=now() WHERE entity_id=%s", (r["entity_id"],))
            g.commit()
            stats["no_evidence"] += 1
            continue
        cand = found["completion"]
        target = g.execute("""
            SELECT id, name FROM entities WHERE lower(name)=lower(%s)
              AND type=%s AND quarantined_at IS NULL AND id<>%s""",
            (cand, r["type"], r["entity_id"])).fetchone()
        action = None
        if target:
            # merge-preferred, under the register rule
            tier = "register-unique"
            if corroborate.register_namesakes(reg, cand) >= 2:
                tier = corroborate.corroborated(
                    g, reg, r["entity_id"], target["id"], r["name"], cand)
            if tier is None:
                g.execute("UPDATE mint_review SET status='repair-abstained', "
                          "actioned_at=now() WHERE entity_id=%s", (r["entity_id"],))
                g.commit()
                stats["abstained"] += 1
                action = "abstained"
            elif merge_if_allowed(g, target["id"], r["entity_id"],
                                  f"repair:truncated-merge ({tier})") is None:
                # C428: a human ruled these two names distinct. The row is
                # ABSTAINED, not repaired — a truncation that cannot be folded
                # to its twin is exactly the case this lane already abstains on.
                g.execute("UPDATE mint_review SET status='repair-abstained', "
                          "actioned_at=now() WHERE entity_id=%s", (r["entity_id"],))
                g.commit()
                stats["abstained"] += 1
                action = "abstained (identity refusal)"
            else:
                g.execute("UPDATE mint_review SET status='repaired-merged', "
                          "actioned_at=now() WHERE entity_id=%s", (r["entity_id"],))
                g.commit()
                stats["merged"] += 1
                action = f"merged->{target['id']} ({tier})"
        else:
            rename_entity(g, r["entity_id"], cand,
                          "repair:truncated-rename", evidence=found)
            g.execute("UPDATE mint_review SET status='repaired-renamed', "
                      "actioned_at=now() WHERE entity_id=%s", (r["entity_id"],))
            g.commit()
            stats["renamed"] += 1
            action = "renamed"
        if action and action != "abstained":
            _mirror({"id": r["entity_id"], "name": r["name"], "type": r["type"],
                     "pattern": "repair-truncated", "verdict": action,
                     "confidence": 1.0,
                     "reasoning": f"completion {cand!r}: {found['articles']} article(s), "
                                  f"register_hit={found['register_hit']}",
                     "model": "mechanical", "tier": "repair",
                     "prompt_version": "repair-mechanical-v1"})
    if hasattr(b, "close"):
        b.close()
    if reg is not None:
        reg.close()
    return stats
