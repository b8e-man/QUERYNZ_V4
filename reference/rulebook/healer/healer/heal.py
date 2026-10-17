"""Claim-tier heals — Shane Jones demonstration (Arthur 2026-08-20:
"fix the shane jones one now so I can see what the applied fixes
look like"). The tier-2 arm of the claim-tier crawler, scoped to ONE
subject so the planning session can judge applied output before any
graph-wide run.

Doctrine: every heal is an evidence-gated REWRITE (never a delete),
convicted only where the claim's own cited sentence refutes it;
every rewrite lands in v3.claim_heals with the full before-state.
Revert is a replay of the audit table ONLY while the healed claim ids
still exist: an era's delete-and-replace re-mints every claim, so after
era 5 all 1,227 claim_heals rows point at claims that are gone (audit
A11, 2026-09-04) — the heal is re-derived by the next crawl, the ledger
is the record of what was judged, not a revert path. Pre-pass D5 decides
whether ledgers reference document+span instead (or a post-supersede
re-point phase). Unconvicted suspects stand —
they are the tier-3 (LLM re-read) residue, and their survival is
part of the demonstration.

Rules (subject: Shane Jones the politician, entity 3202143):
  R1 appositive-as-office   "NZ First minister Shane Jones" was
                            minted as minister OF the party ->
                            org-less minister mention
  R2 party-name truncation  object 'New Zealand'/'Zealand First'
                            where the evidence says 'New Zealand
                            First' -> re-point to the party entity
  R3 qualifier loss         'Associate ... Minister' in evidence,
                            qualifier dropped from the claim ->
                            'is associate minister of'
  R4 cabinet-as-org         'Cabinet minister' appositive ->
                            org-less minister mention
  R5 outlet crossover       'The Herald reports: MP ...' -> org-less
                            mp mention

    python -m healer.heal            # dry run (prints verdicts)
    python -m healer.heal --apply    # rewrite + audit

Moved out of `registers` 2026-08-22 (plan B0): that package's SPEC forbids
graph writes and its catalog guard was red for as long as this lived there.
`healer` is the service home B4 fills with mint_lane/crawler/repair.
"""
from __future__ import annotations

import sys

import psycopg
from psycopg.rows import dict_row

from claim_graph import store   # the graph writer's connection (search_path = v3)

SUBJECT = 3202143          # Shane Jones, person (the politician)
NZ_FIRST = 3201186         # dominant press entity for the party

DDL = """
CREATE TABLE IF NOT EXISTS v3.claim_heals (
    heal_id       bigserial PRIMARY KEY,
    claim_id      bigint NOT NULL,
    rule          text NOT NULL,
    old_predicate text,
    old_object_entity_id bigint,
    old_object_text text,
    new_predicate text,
    new_object_entity_id bigint,
    new_object_text text,
    evidence_excerpt text,
    healed_at     timestamptz NOT NULL DEFAULT now(),
    healed_by     text NOT NULL)
"""

# each rule: (name, conviction SQL for eligible+convicted claims,
# dict of field -> new value; None means SET NULL)
_OBJ = "coalesce(oe.name, c.object_text)"
RULES = [
    ("R1-appositive-as-office",
     f"""c.predicate = 'is minister of'
         AND (c.object_entity_id = {NZ_FIRST}
              OR {_OBJ} IN ('New Zealand', 'Zealand First'))
         AND (c.evidence_text ~*
                  '(new zealand|nz)[ -]first[^.]{{0,40}}minister[s]?[^.]{{0,3}}shane jones'
              OR c.evidence_text ~*
                  'shane jones[^.]{{0,30}}(new zealand|nz)[ -]first[^.]{{0,20}}minister')
         AND c.evidence_text !~* 'minister (of|for) (new zealand|nz)[ -]first'""",
     {"predicate": "is minister", "object_entity_id": None,
      "object_text": None}),
    ("R2-party-name-truncation",
     f"""c.predicate IN ('is mp of', 'is leader of', 'is member of',
                         'is deputy leader of')
         AND {_OBJ} IN ('New Zealand', 'Zealand First')
         AND c.evidence_text ~* '(new zealand|nz)[ -]first'""",
     {"object_entity_id": NZ_FIRST, "object_text": None}),
    # qualifier rules demand NAME ADJACENCY: 'Associate ... Minister
    # Shane Jones' (or the reversed appositive) — a sentence naming
    # a DIFFERENT associate minister alongside Jones must not
    # convict (dry-run finding: Chris Bishop, claim 10295673)
    ("R3-qualifier-loss",
     r"""c.predicate = 'is minister of'
         AND (c.evidence_text ~*
                  'associate [a-z -]{0,30}minister[s]?[^.]{0,3}shane jones'
              OR c.evidence_text ~*
                  'shane jones[^.]{0,30}associate minister')""",
     {"predicate": "is associate minister of"}),
    ("R4-cabinet-as-org",
     f"""c.predicate ~* 'minister' AND {_OBJ} = 'Cabinet'
         AND (c.evidence_text ~*
                  'cabinet minister[s]?[^.]{{0,3}}shane jones'
              OR c.evidence_text ~*
                  'shane jones[^.]{{0,20}}cabinet minister')""",
     {"predicate": "is minister", "object_entity_id": None,
      "object_text": None}),
    # runs AFTER R2 so re-pointed party claims also get the
    # qualifier restored ('New Zealand First deputy leader Shane
    # Jones' -> is deputy leader of, the predicate-flattening
    # sibling from the issues ledger)
    ("R6-deputy-qualifier",
     r"""c.predicate = 'is leader of'
         AND c.object_entity_id IS NOT NULL
         AND (c.evidence_text ~*
                  'deputy leader[s]?[^.]{0,3}shane jones'
              OR c.evidence_text ~*
                  'shane jones[^.]{0,30}deputy leader')""",
     {"predicate": "is deputy leader of"}),
    ("R5-outlet-crossover",
     f"""c.predicate = 'is mp of' AND {_OBJ} = 'Herald'
         AND c.evidence_text ~* '\\mherald\\M'
         AND c.evidence_text !~* 'mp (of|for)[^.]{{0,15}}herald'""",
     {"predicate": "is mp", "object_entity_id": None,
      "object_text": None}),
]

SELECT = f"""
SELECT c.id, c.predicate, c.object_entity_id, c.object_text,
       {_OBJ} AS obj_name, left(c.evidence_text, 220) AS excerpt
FROM v3.claims c LEFT JOIN v3.entities oe ON oe.id = c.object_entity_id
WHERE c.subject_entity_id = {SUBJECT} AND c.class = 'ROLE'
  AND ({{cond}})
ORDER BY c.id
"""


def run(apply: bool) -> None:
    healer = "healer.heal (was registers.heal demo 2026-08-20)"
    with store.connect() as conn:
        conn.execute(DDL)
        total = 0
        for name, cond, sets in RULES:
            rows = conn.execute(SELECT.format(cond=cond)).fetchall()
            print(f"\n{name}: {len(rows)} convicted")
            for r in rows[:2]:
                print(f"  #{r['id']} [{r['predicate']} | "
                      f"{r['obj_name']}]  «{r['excerpt']}»")
            if not (apply and rows):
                continue
            for r in rows:
                new_pred = sets.get("predicate", r["predicate"])
                new_oid = sets.get("object_entity_id",
                                   r["object_entity_id"])
                new_otext = sets.get("object_text", r["object_text"])
                conn.execute(
                    """INSERT INTO v3.claim_heals (claim_id, rule,
                       old_predicate, old_object_entity_id,
                       old_object_text, new_predicate,
                       new_object_entity_id, new_object_text,
                       evidence_excerpt, healed_by)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (r["id"], name, r["predicate"],
                     r["object_entity_id"], r["object_text"],
                     new_pred, new_oid, new_otext, r["excerpt"],
                     healer))
                conn.execute(
                    """UPDATE v3.claims SET predicate = %s,
                       object_entity_id = %s, object_text = %s,
                       qualifiers = qualifiers ||
                           jsonb_build_object('healed', %s::text)
                       WHERE id = %s""",
                    (new_pred, new_oid, new_otext, name, r["id"]))
            total += len(rows)
        if apply:
            conn.commit()
            print(f"\nAPPLIED {total} heals (audit: claim_heals)")
        else:
            print("\nDRY RUN — nothing written "
                  "(--apply to rewrite + audit)")


if __name__ == "__main__":
    run("--apply" in sys.argv)
