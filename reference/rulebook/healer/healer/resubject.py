"""Claim-tier RE-SUBJECTING rules — the first queue's per-claim half (plan
B4 T4, ruling 9, 2026-08-22). Two era-4 residue shapes where a claim's
SUBJECT is a fragment and the claim's own evidence names the person:

  R7 role-string-subject   subject 'National MP' / 'Labour MP' (a role
                           string minted as an entity) and the evidence
                           reads "National MP Greg Fleming ..." → the
                           claim is Greg Fleming's, if exactly ONE live
                           person carries that name.
  R8 surname-co-mention    subject is a single-token surname ('Ardern')
                           and the SAME DOCUMENT mentions exactly one
                           live person whose name ends in that surname
                           ('Jacinda Ardern') → the claim is theirs.
                           Same-document co-mention is the evidence;
                           prominence never decides (a lone 'Ardern' in
                           a document naming no Ardern stays put).

Doctrine as heal.py: an evidence-gated REWRITE, never a delete, ledgered
in claim_heals with the full before-state (old/new subject columns);
unconvicted claims stand and are counted. Dry run by default.

    python -m healer.cli resubject [--apply]
"""
from __future__ import annotations

import re

from psycopg import Connection

HEALER = "healer.resubject"

# role strings that were minted as entities; the person follows the role
ROLE_STRINGS = ("National MP", "Labour MP", "Green MP", "ACT MP", "NZ First MP",
                "National Party MP", "Labour Party MP")
_PERSON = r"([A-ZĀĒĪŌŪ][\w'’-]+(?: [A-ZĀĒĪŌŪ][\w'’-]+){1,2})"


def _r7_candidates(conn: Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT c.id, c.subject_entity_id, s.name AS subject, c.evidence_text
        FROM claims c JOIN entities s ON s.id = c.subject_entity_id
        WHERE s.name = ANY(%s) AND s.quarantined_at IS NULL
          AND c.evidence_text IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM claim_heals h WHERE h.claim_id = c.id
                          AND h.rule = 'R7-role-string-subject')""",
        (list(ROLE_STRINGS),)).fetchall()
    out = []
    for r in rows:
        m = re.search(re.escape(r["subject"]) + r"s?\s+" + _PERSON, r["evidence_text"])
        if not m:
            continue
        name = m.group(1)
        if name.split()[0].lower() in ("says", "said", "who", "for", "and", "has", "was"):
            continue
        persons = conn.execute("""
            SELECT id FROM entities WHERE lower(name) = lower(%s) AND name = %s AND type = 'person'
              AND quarantined_at IS NULL LIMIT 2""", (name, name)).fetchall()   # C355: indexed expression first
        if len(persons) != 1:
            continue                      # none or ambiguous: abstain
        out.append({"id": r["id"], "old": r["subject_entity_id"], "new": persons[0]["id"],
                    "excerpt": r["evidence_text"][:220], "rule": "R7-role-string-subject"})
    return out


# R8's scope in B4 is the NAMED residue (ruling 9: surname-only "Ardern",
# per claim). The general single-token-surname class convicts 138,153
# claims on the live graph (dry run 2026-08-22) — a rule an hour old does
# not open its execute band at that scale before its verdicts are sampled
# (LESSONS §5). `all_surnames=True` measures the general class; applying
# it is a later, sampled decision.
R8_SURNAMES = ("Ardern",)


def _r8_candidates(conn: Connection, all_surnames: bool = False) -> list[dict]:
    rows = conn.execute(r"""
        SELECT c.id, c.subject_entity_id, s.name AS surname, c.document_id, c.evidence_text
        FROM claims c JOIN entities s ON s.id = c.subject_entity_id
        WHERE s.quarantined_at IS NULL AND s.register_source IS NULL
          AND s.name ~ '^[A-ZĀĒĪŌŪ][a-zāēīōū''-]+$'
          AND (%s OR s.name = ANY(%s))
          AND s.type IN ('person', 'people', 'organisation')
          AND EXISTS (SELECT 1 FROM mentions m JOIN entities p ON p.id = m.entity_id
                      WHERE m.article_id = c.document_id AND p.type = 'person'
                        AND p.quarantined_at IS NULL AND p.id <> s.id
                        AND p.name ~ ('\s' || s.name || '$') AND p.name <> s.name)
          AND NOT EXISTS (SELECT 1 FROM claim_heals h WHERE h.claim_id = c.id
                          AND h.rule = 'R8-surname-co-mention')""",
        (all_surnames, list(R8_SURNAMES))).fetchall()
    out = []
    for r in rows:
        persons = conn.execute(r"""
            SELECT DISTINCT p.id FROM mentions m JOIN entities p ON p.id = m.entity_id
            WHERE m.article_id = %s AND p.type = 'person' AND p.quarantined_at IS NULL
              AND p.id <> %s AND p.name ~ ('\s' || %s || '$') LIMIT 2""",
            (r["document_id"], r["subject_entity_id"], re.escape(r["surname"]))).fetchall()
        if len(persons) != 1:
            continue                      # two Arderns in one document: abstain
        out.append({"id": r["id"], "old": r["subject_entity_id"], "new": persons[0]["id"],
                    "excerpt": (r["evidence_text"] or "")[:220], "rule": "R8-surname-co-mention"})
    return out


RULES = (("R7-role-string-subject", _r7_candidates),
         ("R8-surname-co-mention", _r8_candidates))


def run(conn: Connection, apply: bool = False, all_surnames: bool = False) -> dict:
    """Returns {rule: convicted count}. With apply: rewrites + ledgers.
    Caller commits. all_surnames widens R8 to every single-token surname
    — measure only; apply refuses it (sampled decision, not yet taken)."""
    if apply and all_surnames:
        raise ValueError("R8 over all surnames is measure-only until its verdicts are sampled")
    counts = {}
    for name, find in RULES:
        cands = find(conn, all_surnames) if name.startswith("R8") else find(conn)
        counts[name] = len(cands)
        if not apply:
            continue
        for c in cands:
            conn.execute("""
                INSERT INTO claim_heals (claim_id, rule, old_subject_entity_id, new_subject_entity_id,
                                         evidence_excerpt, healed_by)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (c["id"], name, c["old"], c["new"], c["excerpt"], HEALER))
            conn.execute("""
                UPDATE claims SET subject_entity_id = %s,
                       qualifiers = qualifiers || jsonb_build_object('healed', %s::text)
                WHERE id = %s""", (c["new"], name, c["id"]))
    return counts
