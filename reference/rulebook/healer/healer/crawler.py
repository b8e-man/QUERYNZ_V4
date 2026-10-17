"""Common-sense crawler (Arthur 2026-08-14: "a system that samples the
graph and identifies obvious issues like I have found") — the standing
graph auditor, third layer of the healing system.

Finders sweep the EXISTING graph for the issue shapes Arthur surfaced by
hand; what they find flows into the same substrate the mint lane built:
mint_review queue -> LLM judge -> reversible execution through the
claim_graph.remediate gate -> verdict mirror in the Review tab for
sampled oversight. Two finder classes:

DETERMINISTIC (no LLM; the rule IS the proof, execution is immediate):
  - exec-role-place: ROLE claims binding a PLACE_BLIND_TITLES predicate
    to a place-typed object — the pre-R-G2 residue ("chief executive of
    Auckland", 3,918 measured). Healed by detach_claim_object: the edge
    goes, the claim and its evidence stay.
  - orphan entities: article-minted, zero references anywhere. The
    standing version of the item-e purge, but QUARANTINE (reversible)
    rather than delete — the crawler runs unattended.

LLM-JUDGED (queued as pattern 'crawler-*', judged here with a
TYPE-SANITY prompt, never the fragment prompt):
  - acronym-org: short all-caps names typed organisation with no
    register anchor (OCR = the Official Cash Rate, BYO). Verdict is the
    correct type; >= AUTO_BAND retypes through remediate.retype_entity
    (audited, writes the type override so future extractions bind
    correctly). 'organisation' verdicts clear; abstain clears.
  - type-multiplicity: a name carried by entities of 2+ types (Moana
    Pasifika person+facility+organisation). The judge classifies
    (distinct-entities-ok / mistyped / conflated) into the Review
    tab. Since stream S5 (2026-08-19) mistyped-duplicate verdicts
    DRAIN through merge_duplicates — verdict-backed reversible
    merges with deterministic target resolution. It rode run() from
    2026-08-19 to 2026-08-22, when ruling 31 removed it; B4b RESTARTED
    it IN run() behind the adversarial refuter (measured-gated, capped
    at MERGE_CAP/run — see the merge-actuator block in run()), and
    `crawler-merge` remains the CLI form (audit #44, 2026-08-30). Conflated
    (a split, not a merge) and distinct-ok stay observation-tier.

Every action is reversible, every verdict mirrors to the Review tab,
caps below keep a run bounded. Timer: querynz-crawler.timer (every 2 h, ruling 20).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
import re

from psycopg import Connection

from reviewer import model, settings   # sanctioned crossing: the LLM client
from .mint_lane import AUTO_BAND, VERDICTS_PATH, ensure_schema

log = logging.getLogger("healer.crawler")

FINDER_CAP = 500          # max findings a single run may queue per finder
# C235's own cap, measured rather than inherited. One tranche of 500 took
# 134.6 s on the live graph (18 folded, 482 quarantined) — about 0.27 s a row,
# because each disposition writes its audit row and a fold rewrites references.
# 1,024,328 rows at that rate is ~77 hours of work, so at FINDER_CAP it would
# take 170 days and at 2,000 it is ~9 minutes a run and clears in about six
# weeks. Raising it further is a load question about the canonical primary,
# which is Arthur's, not a measurement.
OCR_DEBRIS_CAP = 2000
DETACH_CAP = 2000         # max deterministic heals per run

TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string",
                    "enum": ["organisation", "concept", "place", "facility",
                             "person", "work", "abstain"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string", "maxLength": 500},
    },
    "required": ["verdict", "confidence", "reasoning"],
    "additionalProperties": False,
}

TYPE_SYSTEM = """You judge the TYPE of an entity in a New Zealand news
knowledge graph. The candidate is a short acronym or initialism currently
typed 'organisation' with no register anchor. Many are wrong: OCR is the
Official Cash Rate (a concept), GDP, CPI and OCR are economic measures,
BYO is a licensing concept. Others are genuinely organisations (ACC, MBIE,
NZTA, GCSB). Decide the correct type from the name and the evidence
sentences:
- organisation: an actual body that acts (agencies, companies, unions)
- concept: rates, indices, policies, licensing terms, abstract notions
- place / facility / person / work: as conventionally understood
- abstain: evidence insufficient — abstaining is correct when unsure.
Answer with the type alone plus two sentences of reasoning maximum."""

MULTI_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string",
                    "enum": ["distinct-entities-ok", "mistyped-duplicate",
                             "conflated", "abstain"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {"type": "string", "maxLength": 500},
    },
    "required": ["verdict", "confidence", "reasoning"],
    "additionalProperties": False,
}

MULTI_SYSTEM = """One name is carried by several entities of different
types in a New Zealand news knowledge graph. Judge the situation:
- distinct-entities-ok: genuinely different things share the name
  (a rugby team, a cultural concept and a venue can all be 'Moana
  Pasifika') — keeping them separate is correct
- mistyped-duplicate: they are the SAME thing and some copies carry a
  wrong type — they should eventually merge
- conflated: at least one of the entities is itself a mixture of
  different things (evidence spans clearly about different referents)
- abstain: cannot tell.
Two sentences of reasoning maximum."""


# ── deterministic finders ────────────────────────────────────────────────

def heal_exec_role_places(g: Connection) -> int:
    """Detach place objects from executive-title ROLE claims (pre-R-G2
    residue). The predicate list is the shared contract policy."""
    from claim_graph.contract import PLACE_BLIND_TITLES
    from claim_graph.remediate import detach_claim_object
    preds = tuple(f"is {t} of" for t in PLACE_BLIND_TITLES)
    rows = g.execute("""
        SELECT c.id FROM claims c
        JOIN entities o ON o.id = c.object_entity_id
        WHERE c.class = 'ROLE' AND o.type = 'place'
          AND c.predicate = ANY(%s)
        LIMIT %s""", (list(preds), DETACH_CAP)).fetchall()
    n = 0
    for r in rows:
        detach_claim_object(g, r["id"], "crawler:exec-role-place (R-G2 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_party_boundary(g: Connection) -> int:
    """C247 heal: LEADER claims bound to the COUNTRY where the sentence says
    "New Zealand First" — the party name cut at a word boundary before the
    claim was ever built.

    NER hands the cast `place:new zealand` over the first eleven characters of
    "New Zealand First's leader Winston Peters" and the appositive path binds
    the country. Measured 2026-09-20: 190 ROLE claims on the live graph, 164 of
    them leader-class — the product asserting that Winston Peters leads New
    Zealand. The extractor stopped producing them the same day (the cast-level
    split in `era4.party_boundary_at`); this is that rule applied in arrears to
    rows already minted, the way the R-G2 heal above is.

    LEADER-CLASS ONLY, and the narrowness is measured. The same sentence-level
    signal over the other predicates catches claims that are not this defect
    and one that is simply TRUE: "New Zealand, when former prime minister Helen
    Clark clung to New Zealand First support" is a correct claim about the
    country, and a heal that swept `is former prime minister of` would destroy
    it to reach eight rows.

    The edge goes; the OLD object name stays as object_text, not the party's.
    Six of the 164 are ACT leaders (Seymour, Whyte, Hide) whose sentences
    merely mention New Zealand First — writing the party in would swap one
    wrong object for another. The next era mints the right one.
    """
    from claim_graph.remediate import detach_claim_object
    rows = g.execute("""
        SELECT c.id FROM claims c
        JOIN entities o ON o.id = c.object_entity_id
        WHERE c.class = 'ROLE' AND o.type = 'place' AND o.name = 'New Zealand'
          AND c.predicate IN ('is leader of', 'was leader of', 'is deputy leader of')
          AND c.evidence_text LIKE %s
        LIMIT %s""", ("%New Zealand First%", DETACH_CAP)).fetchall()
    n = 0
    for r in rows:
        detach_claim_object(g, r["id"], "crawler:party-boundary (C247 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_anonymised_honorifics(g: Connection) -> int:
    """C252 heal: `<honorific> <initial>` entities minted before the guard
    listed their honorific.

    Measured 2026-09-20: 102 person entities of this shape, 8,381 subject
    claims, 2,696 object claims, 97,103 mentions. "Miss M." alone carried
    2,192 claims — every anonymised Miss M. in every tribunal decision the
    corpus holds, folded into one person who does not exist. These are the
    WHOLE POINT of a suppression order, and the mint guard already refused the
    shape; what it did not list was `miss`, `rev`, `hon`, `prof`, `justice` or
    `rt hon`, which is 101 of the 102.

    QUARANTINE, never delete, and never a rename: there is no deterministic
    recovery from an initial, so the only honest move is to take the entity
    out of the graph and leave the evidence where it is. The predicate is
    IMPORTED from the same lexicon the mint reads, so the heal and the guard
    can never disagree.
    """
    from claim_graph.remediate import quarantine_entity
    from reconciliation.lexicons import is_anonymised
    rows = g.execute("""
        SELECT id, name FROM entities
        WHERE type = 'person' AND quarantined_at IS NULL
          AND register_source IS NULL
          AND name ~* '^[A-Za-z.]+([ .]+[A-Za-z.]+)?[ .]+[A-Za-z]\\.?$'
        LIMIT %s""", (FINDER_CAP,)).fetchall()
    n = 0
    for r in rows:
        if not is_anonymised(r["name"]):
            continue
        quarantine_entity(g, r["id"], "crawler:anonymised-honorific (C252)")
        n += 1
        if n % 100 == 0:
            g.commit()
    g.commit()
    return n


def heal_ocr_debris(g: Connection) -> dict:
    """C235: entities carrying a glyph no writer could have typed.

    Measured 2026-09-20: 1,024,328 live entities, 250,606 of them typed
    `person` — the Papers-Past era minting broken type as people and companies.
    Two hand-read samples (60 person rows, 40 across all types) found debris in
    every one bar two real names wearing a stray caret.

    RECOVER OVER EXCLUDE, in that order. The glyphs are stripped first: where
    what is left is a well-formed name that ALREADY EXISTS as a live entity of
    the same type, this row is a mangled duplicate and it FOLDS into the real
    one ("William O'Brien^" into "William O'Brien"). Only where nothing is
    recovered is the row quarantined — reversible, never deleted.

    A name is "well-formed" here at its weakest useful reading: two or more
    tokens, each of two or more letters. "^^T^" strips to "T" and is refused,
    which is the point — the strip must not be allowed to INVENT a name.

    Returns what it did AND what is left, because a capped job that reports
    only its own cap is a measurement that cannot fail (queue 8's lesson, one
    function above).
    """
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import quarantine_entity
    from reconciliation.lexicons import OCR_IMPOSSIBLE, strip_ocr_debris
    klass = "[" + "".join("\\" + c for c in OCR_IMPOSSIBLE) + "]"
    rows = g.execute(f"""
        SELECT id, name, type FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND name ~ '{klass}'
        LIMIT %s""", (OCR_DEBRIS_CAP + 1,)).fetchall()
    more = len(rows) > OCR_DEBRIS_CAP
    rows = rows[:OCR_DEBRIS_CAP]
    folded = quarantined = 0
    for r in rows:
        base = strip_ocr_debris(r["name"])
        toks = base.split()
        keep = None
        if len(toks) >= 2 and all(len(t.strip(".,'-")) >= 2 for t in toks):
            hit = g.execute("""SELECT id FROM entities
                               WHERE name = %s AND type = %s AND id <> %s
                                 AND quarantined_at IS NULL
                               LIMIT 2""", (base, r["type"], r["id"])).fetchall()
            if len(hit) == 1:            # exactly one target, or abstain
                keep = hit[0]["id"]
        if keep is not None:
            # a refusal leaves the row ALONE — not quarantined. Quarantining it
            # would act on a pair a human ruled distinct, in the other direction.
            if merge_if_allowed(g, keep, r["id"], "crawler:ocr-debris-fold (C235)") is None:
                continue
            folded += 1
        else:
            quarantine_entity(g, r["id"], "crawler:ocr-debris (C235)")
            quarantined += 1
        if (folded + quarantined) % 100 == 0:
            g.commit()
    g.commit()
    total = g.execute(
        f"SELECT count(*) AS n FROM entities WHERE register_source IS NULL "
        f"AND quarantined_at IS NULL AND name ~ '{klass}'").fetchone()["n"]
    return {"folded": folded, "quarantined": quarantined, "left": total, "more": more}


def heal_glued_punctuation(g: Connection) -> int:
    """C241: prose glued to a name across punctuation the tokenizer kept.

    Measured 2026-09-20: 3,882 live entities match the seam shapes once OCR
    debris and abbreviations are excluded, and 1,243 of them carry a name the
    rule can recover deterministically ("release)Animal Policy International",
    "claims.16 Te Ururoa"). The other 2,639 abstain, most of them two NAMES run
    together — "Ray Archer)Hard", "Phototek)New Caledonia" — where the string
    holds no evidence for which one the entity is.

    A SINGLE-TOKEN recovery must fold, never rename. "sidehead)Today" recovers
    "Today", which is a word, not a name; renaming to it would trade a glued
    name for a bare one. Where an entity of that name already exists the fold
    is evidence that it IS a name; where none does, the row is left alone.
    """
    from reconciliation.lexicons import glued_punctuation, is_ocr_debris
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND name ~ '[a-zāēīōū)][).][A-ZĀĒĪŌŪ0-9]'
        LIMIT %s""", (FINDER_CAP,)).fetchall()
    n = 0
    for r in rows:
        if is_ocr_debris(r["name"]):
            continue                      # C235's class, disposed of there
        base = glued_punctuation(r["name"])
        if not base:
            continue
        if len(base.split()) < 2:
            twin = g.execute(
                "SELECT count(*) AS n FROM entities WHERE name = %s AND type = %s "
                "AND quarantined_at IS NULL AND id <> %s",
                (base, r["type"], r["id"])).fetchone()
            if twin["n"] != 1:
                continue                  # a bare word with nothing to fold into
        n += _dispose_stripped(g, r, base, "glued-punctuation")
        if n % 100 == 0:
            g.commit()
    g.commit()
    return n


def heal_article_led(g: Connection) -> int:
    """R-G3 heal for the pre-rules stratum ('a Winston Churchill', 'a
    Fire and Emergency New Zealand' — the era-3 drain ran v3-det-1.0/1.1
    before the article rule landed). Deterministic, the extractor's own
    rule applied in arrears: strip the lowercase article; if exactly ONE
    live same-type node carries the base name, fold into it (alias
    preserved, reversible); if none exists, rename (audited, old surface
    kept). Two or more base candidates = ambiguous — abstain and leave
    the row for the mint-lane screen's LLM. Persons are skipped
    outright (the register rule owns person identity)."""
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity
    rows = g.execute(r"""
        WITH stripped AS (
            SELECT id, name, type,
                   regexp_replace(name, '^(a|an) ', '') AS base
            FROM entities
            WHERE register_source IS NULL AND quarantined_at IS NULL
              AND type <> 'person'
              AND name ~ '^(a|an) [A-ZĀĒĪŌŪ]'
        ),
        candidates AS (
            SELECT s.id AS lose, s.name AS lname, s.type, s.base,
                   count(b.id) AS n_base, min(b.id) AS keep
            FROM stripped s
            LEFT JOIN entities b ON b.name = s.base AND b.type = s.type
                 AND b.quarantined_at IS NULL AND b.id <> s.id
            GROUP BY s.id, s.name, s.type, s.base
        )
        SELECT lose, lname, type, base, n_base, keep
        FROM candidates WHERE n_base <= 1
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        if r["n_base"] == 1:
            if merge_if_allowed(g, r["keep"], r["lose"],
                                "crawler:article-led-fold (R-G3 heal)") is None:
                continue                  # refused: neither fold nor rename
        else:
            rename_entity(g, r["lose"], r["base"],
                          "crawler:article-led-rename (R-G3 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_negation_prefix(g: Connection) -> int:
    """R-G4 heal for the pre-rules stratum: 'non-X' is never an entity —
    the extractor drops these at mint now; existing ones quarantine
    (reversible, audited), same disposition the rule would have given
    them at birth."""
    from claim_graph.remediate import quarantine_entity
    rows = g.execute(r"""
        SELECT id FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND name ~* '^non[ -]'
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        quarantine_entity(g, r["id"], "crawler:negation-prefix (R-G4 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_definite_article(g: Connection) -> int:
    """R-G7 heal (Arthur's leads batch, 2026-08-14): 'The High Court' and
    'High Court' must be ONE node. The C5 mint strip (2026-07-31) stopped
    new the-doubles and the alias fold rewrote the keys, but the-named
    ENTITY nodes were never folded — 3,531 live pairs on the serving
    graph. Same machinery as R-G3: strip, fold when exactly one live
    same-type base exists, rename when none, abstain on 2+. THE_NAMES
    (the measured The-IS-the-name allowlist) is protected; persons are
    skipped (register rule owns person identity)."""
    from claim_graph.contract import THE_NAMES
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity
    rows = g.execute(r"""
        WITH stripped AS (
            SELECT id, name, type,
                   regexp_replace(name, '^the ', '', 'i') AS base
            FROM entities
            WHERE register_source IS NULL AND quarantined_at IS NULL
              AND type <> 'person'
              AND name ~* '^the [A-Za-zĀĒĪŌŪāēīōū]'
              AND lower(name) <> ALL(%s)
        ),
        candidates AS (
            SELECT s.id AS lose, s.name AS lname, s.type, s.base,
                   count(b.id) AS n_base, min(b.id) AS keep
            FROM stripped s
            LEFT JOIN entities b ON b.name = s.base AND b.type = s.type
                 AND b.quarantined_at IS NULL AND b.id <> s.id
            GROUP BY s.id, s.name, s.type, s.base
        )
        SELECT lose, lname, type, base, n_base, keep
        FROM candidates WHERE n_base <= 1
        LIMIT %s""", (list(THE_NAMES), DETACH_CAP)).fetchall()
    n = 0
    for r in rows:
        if r["n_base"] == 1:
            if merge_if_allowed(g, r["keep"], r["lose"],
                                "crawler:definite-article-fold (R-G7 heal)") is None:
                continue                  # refused: neither fold nor rename
        else:
            rename_entity(g, r["lose"], r["base"],
                          "crawler:definite-article-rename (R-G7 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


# R-G8: trailing caption-credit grammar. The colon/paren form is structural
# ("X (Photo: Supplied", "X Photo: Supplied") — no real name ends that way;
# the bare-word form is restricted to photo/photograph/supplied (video,
# image, picture alone are real name material: Blockbuster Video).
_CAPTION_TAIL = re.compile(
    r"(?i)(?:(?:\s*[|(•]\s*)?(?:photos?|photograph|images?|pictures?|video)?"
    r"\s*:\s*supplied\)?\s*$"
    r"|\s+(?:photos?|photograph):?\s*$"
    r"|\s+supplied\)?\s*$)")


def heal_caption_credit(g: Connection) -> int:
    """R-G8 heal (Arthur's leads batch, 2026-08-14): a caption credit is
    not part of a name — "Bill English Photo: Supplied" is Bill English
    plus caption glue. Strip the credit tail; fold into the bare node
    when exactly one live same-type base exists, rename otherwise; a
    base too short to be a name (empty, or single-token person)
    quarantines as caption debris."""
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import quarantine_entity, rename_entity
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND name ~* '([|(•]\s*)?(photos?|photograph|images?|pictures?|video)?\s*:\s*supplied\)?\s*$|[ ](photos?|photograph):?\s*$|[ ]supplied\)?\s*$'
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        base = _CAPTION_TAIL.sub("", r["name"]).strip(" |(•").strip()
        if _dispose_stripped(g, r, base, "caption-credit (R-G8 heal)"):
            n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def _dispose_stripped(g, row, base: str, rule: str) -> bool:
    """Shared R-G8/9/10 disposition: fold into the unique live same-type
    twin, rename when none exists, abstain on 2+, quarantine a base too
    short to be a name (empty, or single-token person). Returns True only
    when an ACTION was taken — abstains and no-op strips must not count,
    or a drain loop reads its own recurrence as progress (found live
    2026-08-14: an abstaining row re-selects every pass forever)."""
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import quarantine_entity, rename_entity
    if base == row["name"]:
        return False        # strip was a no-op — never rename to itself
    toks = base.split()
    if not toks or (row["type"] == "person" and len(toks) < 2):
        quarantine_entity(g, row["id"], f"crawler:{rule}-debris")
        return True
    # C355 (2026-09-07): lower(name) is the indexed expression on v3.entities
    # (27 M rows); `name = %s` alone was a full scan per call
    twin = g.execute("""
        SELECT array_agg(id) AS ids FROM entities
        WHERE lower(name) = lower(%s) AND name = %s AND type = %s AND quarantined_at IS NULL
          AND id <> %s""", (base, base, row["type"], row["id"])).fetchone()
    ids = twin["ids"] or []
    if len(ids) == 1:
        if merge_if_allowed(g, ids[0], row["id"], f"crawler:{rule}-fold") is None:
            return False              # refused, so this row was NOT handled
        return True
    if not ids:
        rename_entity(g, row["id"], base, f"crawler:{rule}-rename")
        return True
    return False  # 2+ same-name twins: ambiguous — abstain (multiplicity lane)


# R-G9: leading list/attribution junk — bullets, dashes, orphan quotes.
# "• Accenture" is Accenture; "— Phil Goff" is Phil Goff's pull-quote credit.
_LEAD_JUNK = re.compile(r"^(?:[•·*–—-]\s+|[‘’'\"]\s*)+")
# R-G10: trailing function words / dangling connectors — the English cousin
# of the trailing-particle class ("North End Health Centre and",
# "Institute for Governance and", "Lone Star Cafe and Bar in") — plus
# parenthetical status suffixes ("X Limited (in liquidation)").
_TAIL_FUNC = re.compile(
    r"(?i)(?:\s+(?:of|for|at|to|in|on|by|with|and|or|the|a|an)"
    r"|\s*\(?(?:in )?(?:liquidation|receivership|administration)\)?"
    r"|\s*[,&;:/–—-])+\s*$")


def heal_lead_junk(g: Connection) -> int:
    """R-G9 heal (leads batch 2, Arthur 2026-08-14): list bullets,
    attribution dashes and orphan quotes are markup, not name."""
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND (name ~ '^[•·*–—-] ' OR name ~ '^[''"‘’]')
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        base = _LEAD_JUNK.sub("", r["name"]).strip()
        # a fully-quoted 'Name' keeps its closing quote once the opener
        # goes — drop the orphan tail quote too
        base = re.sub(r"[‘’'\"]\s*$", "", base).strip()
        if _dispose_stripped(g, r, base, "lead-junk (R-G9 heal)"):
            n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_trailing_function_word(g: Connection) -> int:
    """R-G10 heal (leads batch 2): a name ending in a function word was
    cut mid-phrase — strip to the last content word, then the shared
    disposition decides."""
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND (name ~* '[ ](of|for|at|to|in|on|by|with|and|or|the|a|an)$'
               OR name ~ '[,&;:/–—-]\s*$')
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        base = _TAIL_FUNC.sub("", r["name"]).strip()
        if _dispose_stripped(g, r, base,
                             "trailing-function-word (R-G10 heal)"):
            n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_orthography_twins(g: Connection) -> int:
    """Era catch-up folds for orthographic doubles: a macron twin folds
    into the MACRONNED node (register orthography canonical — the
    acceptance:macron-twin-fold rule applied as a standing heal), and a
    case twin (JOHN SMITH / John Smith) folds into the mixed-case node.
    Only exact 1-1 same-type pairs; anything else abstains."""
    from claim_graph.identity_refusals import merge_if_allowed
    n = 0
    # macron twins: keep macronned, lose the plain-ascii spelling
    rows = g.execute(r"""
        WITH m AS (SELECT id, name, type,
                          translate(lower(name), 'āēīōū', 'aeiou') AS folded
                   FROM entities
                   WHERE name ~ '[āēīōūĀĒĪŌŪ]' AND quarantined_at IS NULL)
        SELECT m.id AS keep, min(e.id) AS lose, count(e.id) AS n_twin
        FROM m JOIN entities e
          ON lower(e.name) = m.folded AND e.type = m.type
         AND e.id <> m.id AND e.quarantined_at IS NULL
         AND e.register_source IS NULL
        GROUP BY m.id HAVING count(e.id) = 1
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    lost: set[int] = set()
    for r in rows:
        # two macron variants can fold to the same plain spelling — the
        # second pair's lose is already merged away; skip, don't crash
        if r["lose"] in lost or r["keep"] in lost:
            continue
        if merge_if_allowed(g, r["keep"], r["lose"],
                            "crawler:macron-twin-fold (register orthography canonical)") is None:
            continue                  # refused: `lose` is still live, so not in `lost`
        lost.add(r["lose"])
        n += 1
        if n % 200 == 0:
            g.commit()
    # case twins: keep the mixed-case spelling, lose ALL-CAPS/all-lower
    rows = g.execute(r"""
        WITH t AS (SELECT lower(name) AS ln, type
                   FROM entities
                   WHERE register_source IS NULL AND quarantined_at IS NULL
                   GROUP BY 1, 2
                   HAVING count(*) = 2 AND count(DISTINCT name) = 2)
        SELECT min(e.id) FILTER (WHERE e.name <> upper(e.name)
                                   AND e.name <> lower(e.name)) AS keep,
               min(e.id) FILTER (WHERE e.name = upper(e.name)
                                    OR e.name = lower(e.name)) AS lose
        FROM t JOIN entities e
          ON lower(e.name) = t.ln AND e.type = t.type
         AND e.quarantined_at IS NULL AND e.register_source IS NULL
        GROUP BY t.ln, t.type
        HAVING count(*) FILTER (WHERE e.name <> upper(e.name)
                                  AND e.name <> lower(e.name)) = 1
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    for r in rows:
        if r["keep"] and r["lose"]:
            if merge_if_allowed(g, r["keep"], r["lose"],
                                "crawler:case-twin-fold") is None:
                continue
            n += 1
            if n % 200 == 0:
                g.commit()
    g.commit()
    return n


def heal_url_fragments(g: Connection) -> int:
    """R-G11 heal (leads batch 3): no real entity name contains a URL
    protocol or www. prefix — capture artifacts, quarantined. Bare
    domains ("interest.co.nz") are spared: outlets legitimately go by
    their domain."""
    from claim_graph.remediate import quarantine_entity
    rows = g.execute(r"""
        SELECT id FROM entities
        WHERE register_source IS NULL AND quarantined_at IS NULL
          AND (name ~* 'https?://' OR name ~* '\mwww\.')
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    for r in rows:
        quarantine_entity(g, r["id"], "crawler:url-fragment (R-G11 heal)")
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


# R-G12: leading role titles are not part of a person's name. Multi-word
# titles first so "Prime Minister" wins over "Minister". Bare military
# ranks (Major, General) are DELIBERATELY absent — they are real names.
_ROLE_TITLES = (
    "deputy prime minister", "prime minister", "associate minister",
    "deputy mayor", "detective sergeant", "detective inspector",
    "detective constable", "associate professor", "vice-chancellor",
    "minister", "mayor", "judge", "justice", "detective", "sergeant",
    "inspector", "constable", "superintendent", "commissioner",
    "professor", "coach", "captain", "president", "premier", "chancellor",
    "dame", "sir",
    # B4 first queue (ruling 9): the "Rt Hon twins" — 107 entities on
    # 2026-08-22, the honorific minted as part of the name
    "rt hon", "hon",
)
_ROLE_PREFIX = re.compile(
    r"(?i)^(?:" + "|".join(_ROLE_TITLES) + r")\s+")


def _close_quietly(conn) -> None:
    """Close a register connection a heal opened, on every exit path (queue 8,
    2026-09-17 — audit 2026-09-14: `heal_role_title_prefix` never closed its
    register connection, and the post-nominal fold / anchor lane closed
    theirs only on the happy path: one register connection leaked per cycle)."""
    if conn is None:
        return
    try:
        conn.close()
    except Exception:  # noqa: BLE001 — closing is best effort; the leak is what matters
        pass


def heal_role_title_prefix(g: Connection) -> int:
    """R-G12 heal (leads batch 3): "Prime Minister Chris Hipkins" is
    Chris Hipkins wearing his job. R-G5's guarded person-fold shape:
    strip the title; fold ONLY into a namesake-unique live person, and
    when the register holds >=2 persons with the base name the fold
    additionally needs a corroborator tier. No base -> rename (title
    off, identity unchanged). Ambiguous -> abstain."""
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity
    from reviewer import corroborate   # sanctioned crossing
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE type = 'person' AND register_source IS NULL
          AND quarantined_at IS NULL
          AND name ~* %s
        LIMIT %s""",
        ("^(" + "|".join(_ROLE_TITLES) + ") [A-ZĀĒĪŌŪ]", DETACH_CAP),
        ).fetchall()
    reg = corroborate.register_conn()   # closed in `finally` (audit 2026-09-14: leaked per cycle)
    n = 0
    try:
        for r in rows:
            base = _ROLE_PREFIX.sub("", r["name"]).strip()
            if base == r["name"] or len(base.split()) < 2 \
                    or not base[:1].isupper():
                continue
            twins = g.execute("""
                SELECT array_agg(id) AS ids FROM entities
                WHERE lower(name) = lower(%s) AND name = %s AND type = 'person' AND quarantined_at IS NULL
                  AND id <> %s""", (base, base, r["id"])).fetchone()["ids"] or []   # C355: indexed expression first
            if len(twins) > 1:
                continue                      # namesake-ambiguous — abstain
            if len(twins) == 1:
                if corroborate.register_namesakes(reg, base) >= 2 and \
                        not corroborate.corroborated(
                            g, reg, r["id"], twins[0], r["name"], base):
                    continue                  # register rule: needs a witness
                if merge_if_allowed(g, twins[0], r["id"],
                                    "crawler:role-title-fold (R-G12 heal)") is None:
                    continue
            else:
                rename_entity(g, r["id"], base,
                              "crawler:role-title-rename (R-G12 heal)")
            n += 1
            if n % 200 == 0:
                g.commit()
        g.commit()
    finally:
        _close_quietly(reg)
    return n


# ── B4 first queue (ruling 9, 2026-08-22) ────────────────────────────────

_MAORI_LETTERS = set("aeiouhkmnprtwgāēīōū")   # g only inside 'ng' — checked below
TRAILING_REPEAT_REFUSED: list[int] = []       # per-run trap-refusal counts (measured, never silent)


def _maori_spellable(tok: str) -> bool:
    """True when the token is spellable in the Māori alphabet (a e i o u h k
    m n p r t w, ng, wh, macrons). The trailing-repeat shape ("Jacinda
    Ardern Ardern") collides head-on with REDUPLICATED Māori names (Te Heu
    Heu, Paki Paki, Kiri Kiri — the top matches of a naive rule, measured
    2026-08-22); a duplicate token that could be te reo is a TRAP and the
    heal refuses it. Over-refusing an English name that happens to be
    Māori-spellable (Worth) is the cheap side of the error."""
    t = tok.lower()
    if not t or any(ch not in _MAORI_LETTERS for ch in t):
        return False
    # 'g' must be part of 'ng'; 'wh' is fine as letters
    return all(t[i - 1] == "n" for i, ch in enumerate(t) if ch == "g" and i > 0) and not t.startswith("g")


def heal_trailing_repeat(g: Connection) -> int:
    """"Jacinda Ardern Ardern" → "Jacinda Ardern": a person name of 3+ tokens
    whose last token repeats the one before it. Disposition via the shared
    R-G8/9/10 shape (fold into the unique live twin, rename when none,
    abstain on 2+). REFUSES when the duplicated token is Māori-spellable
    (reduplication is a feature of the language, not a doubling error);
    refusals are counted in TRAILING_REPEAT_REFUSED."""
    rows = g.execute(r"""
        SELECT id, name, type FROM entities
        WHERE type = 'person' AND register_source IS NULL AND quarantined_at IS NULL
          AND name ~ '^(\S+\s+){2,}\S+$'
          AND name ~ '\m(\w{2,})\s+\1$'
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = refused = 0
    for r in rows:
        toks = r["name"].split()
        if len(toks) < 3 or toks[-1].lower() != toks[-2].lower():
            continue
        if _maori_spellable(toks[-1]):
            refused += 1
            continue
        base = " ".join(toks[:-1])
        if _dispose_stripped(g, r, base, "trailing-repeat"):
            n += 1
            if n % 200 == 0:
                g.commit()
    g.commit()
    TRAILING_REPEAT_REFUSED.append(refused)
    return n


def heal_role_string_entities(g: Connection) -> int:
    """'National MP' / 'Labour MP' minted as organisation/person entities
    (ruling 9: 1,060 / 1,693 mentions on 2026-08-22). The string IS a
    position, so the entity is RETYPED to `position` through the
    remediation gate (ledgered, reversible, writes the type override);
    its mentions stay — correctly typed now — and the claims whose
    evidence names the actual MP are re-subjected by resubject.R7. The
    plan's "→ 0" was written as "no longer a false organisation", not
    "no mentions": a mention of the role string is a true mention."""
    from claim_graph.remediate import retype_entity
    from .resubject import ROLE_STRINGS
    rows = g.execute("""
        SELECT id, name, type FROM entities
        WHERE name = ANY(%s) AND type <> 'position' AND quarantined_at IS NULL
          AND register_source IS NULL""", (list(ROLE_STRINGS),)).fetchall()
    n = 0
    for r in rows:
        retype_entity(g, r["id"], "position", reason="crawler:role-string-position (B4 first queue)")
        n += 1
    g.commit()
    return n


_CONJ = re.compile(r"^(\S+ \S+(?: \S+)?) (?:and|&) (\S+ \S+(?: \S+)?)$")


def conjunction_halves(name: str) -> tuple[str, str] | None:
    """'Jacinda Ardern and Grant Robertson' → both halves, each 2-3 tokens;
    None for single-token halves (Simon and Garfunkel is one act)."""
    m = _CONJ.match(name)
    if not m:
        return None
    a, b = m.group(1), m.group(2)
    if not (a[:1].isupper() and b[:1].isupper()):
        return None
    return a, b


def find_conjunctions(g: Connection) -> int:
    """Queue person mints shaped 'A B and C D' for the tier-3 re-read
    (pattern crawler-conjunction). The judge decides two-people /
    one-person / not-a-person; execute() splits the two-people verdicts
    through claim_graph.split (ruling 10)."""
    rows = g.execute(r"""
        SELECT e.id, e.name, e.type FROM entities e
        WHERE e.type = 'person' AND e.register_source IS NULL AND e.quarantined_at IS NULL
          AND e.name ~ '^\S+ \S+( \S+)? (and|&) \S+ \S+( \S+)?$'
          AND NOT EXISTS (SELECT 1 FROM mint_review mr WHERE mr.entity_id = e.id)
        ORDER BY (SELECT count(*) FROM mentions m WHERE m.entity_id = e.id) DESC
        LIMIT %s""", (CONJUNCTION_CAP,)).fetchall()
    n = 0
    for r in rows:
        if conjunction_halves(r["name"]) is None:
            continue
        cur = g.execute("""
            INSERT INTO mint_review (entity_id, name, type, pattern)
            VALUES (%s,%s,%s,'crawler-conjunction')
            ON CONFLICT (entity_id) DO NOTHING""", (r["id"], r["name"], r["type"]))
        n += cur.rowcount
    g.commit()
    return n


CONJUNCTION_LABELS = ["two-people", "one-person", "not-a-person"]
# A tier-3 verdict is a 6-round tool loop on the 2-slot agent lane, not a
# single-shot call on the 24-slot fleet (measured 2026-08-22: the fleet
# judges ~120 single-shot cases per 10 min at concurrency 16). 40 per
# cycle keeps the 2-hour cadence honest; the rate is measured at B4's
# close (plan B3b) before the cap moves.
CONJUNCTION_CAP = 40
# a split MINTS entities, so it takes a higher band than retype/quarantine:
# hand-read of the first 36 live splits (2026-08-22) found ~8/13 of the
# 0.90 verdicts wrong ('Claire King Allen & Unwin Pea' = a publisher,
# 'Shunhua Ding: Drugs and Human Health' = a book) and the 0.95+ ones
# right; those 13 were reverted through the ledger. 0.90 two-people parks.
CONJUNCTION_SPLIT_BAND = 0.95



def _re_read(case: dict, labels: list[str], **kw):
    """The tier-3 tool-loop judge (research.crawler_judge) — graph reads
    only, abstain-capable. Indirected so tests can script it.

    NETWORK DOCTRINE, enforced in code: the research loop posts to
    LLM_API_URL (query.agent.API), and the fleet env file was found
    carrying a non-loopback value on 2026-08-22. This lane calls the
    local model only; a non-loopback endpoint is refused before any
    call is made (the judge logs it and the row is reclaimed later)."""
    # the research loop resolves its endpoint from LLM_API_URL at import
    # (query.agent.API) and has DEFAULTED TO LOOPBACK since 211d32e — so the
    # check judges the RESOLVED url, not the raw env (audit A30: "unset =
    # cloud" was a false premise that refused every run with the default)
    if "post" not in kw:
        from modelgate import client as modelclient   # B10 T3b: the one loopback rule
        from query.agent import API as _research_api
        why = modelclient.endpoint_refusal(_research_api, "research")
        if why:
            raise RuntimeError(f"tier-3 re-read refused: {why}")
    from research.crawler_judge import re_read   # sanctioned crossing (B3/B4)
    return re_read(case, labels, **kw)


def _conjunction_set_path() -> str:
    return os.environ.get("B4_CONJUNCTION_SET", os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))), "var", "audits", "b4-conjunction-set.json"))


def _freeze_conjunction(row: dict, status: str) -> None:
    """The acceptance set the plan cites was never enumerated; it is
    FROZEN here as the judged verdicts accumulate, before each split."""
    path = _conjunction_set_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = []
    data.append({"entity_id": row["entity_id"], "name": row["name"], "verdict": row["verdict"],
                 "confidence": row["confidence"], "status": status})
    with open(path, "w") as f:
        json.dump(data, f, indent=1)


def heal_the_names_bare_twins(g: Connection) -> int:
    """R-G7 twin-fold, the other end (Arthur's Warehouse find, 2026-08-15):
    the THE_NAMES allowlist protects "The X" from the article strip, but
    NER leaves the determiner outside the span often enough that a bare
    "X" twin grows beside it (era-3 "Warehouse": 1,363 mentions). For each
    allowlist entry: a live bare same-type node folds into its unique live
    "The X" twin; no twin and organisation-typed -> rename to the The-form;
    two-plus twins -> abstain. Bounded by the curated 101 names. Mint end:
    strip_leading_article re-attaches The under era 3 (v3-det-1.9)."""
    from claim_graph.contract import THE_NAMES
    from claim_graph.identity_refusals import merge_if_allowed
    from claim_graph.remediate import rename_entity
    n = 0
    for full in THE_NAMES:
        bare = full[4:]
        rows = g.execute("""
            SELECT id, name, type FROM entities
            WHERE lower(name)=%s AND quarantined_at IS NULL
              AND register_source IS NULL""", (bare,)).fetchall()
        for r in rows:
            twins = g.execute("""
                SELECT id FROM entities
                WHERE lower(name)=%s AND type=%s AND quarantined_at IS NULL
                  AND id<>%s""", (full, r["type"], r["id"])).fetchall()
            if len(twins) == 1:
                if merge_if_allowed(g, twins[0]["id"], r["id"],
                                    "crawler:the-names-bare-fold (R-G7 heal)") is not None:
                    n += 1
            elif not twins and r["type"] == "organisation":
                rename_entity(g, r["id"], "The " + r["name"],
                              "crawler:the-names-bare-rename (R-G7 heal)")
                n += 1
            if n and n % 100 == 0:
                g.commit()
    g.commit()
    return n


def heal_comma_composites(g: Connection) -> int:
    """R-G13 heal (verdict mining, 2026-08-15): an entity whose name is a
    two-plus-comma enumeration where EVERY segment already exists as a live
    entity is a capture composite, not an entity — the signal already lives
    on the segments ("Spark, Kiwibank, Fisher & Paykel Appliances").
    Quarantine the composite. Enumerations whose segments are NOT all known
    stay with the comma-list LLM screen — that population judged ~50/50
    debris/real, so no deterministic call is safe there. Same rule at the
    mint end: cast.py splits/refuses at v3-det-1.8. Actions only; keyset
    pagination because most selected rows are correctly left alone."""
    from claim_graph.contract import comma_name_segments
    from claim_graph.remediate import quarantine_entity
    n, last_id = 0, 0
    while True:
        rows = g.execute(r"""
            SELECT id, name FROM entities
            WHERE register_source IS NULL AND quarantined_at IS NULL
              AND name ~ ',.*,' AND id > %s
            ORDER BY id LIMIT %s""", (last_id, DETACH_CAP)).fetchall()
        if not rows:
            break
        for r in rows:
            last_id = r["id"]
            segs = comma_name_segments(r["name"])
            if not segs:
                continue
            wanted = list({s.lower() for s in segs})
            known = g.execute(
                "SELECT count(DISTINCT lower(name)) c FROM entities "
                "WHERE quarantined_at IS NULL AND lower(name) = ANY(%s) "
                "AND id <> %s", (wanted, r["id"])).fetchone()["c"]
            if known == len(wanted):
                quarantine_entity(g, r["id"],
                                  "crawler:comma-composite (R-G13 heal)")
                n += 1
                if n % 200 == 0:
                    g.commit()
        g.commit()
    return n


def heal_ampersand_twins(g: Connection) -> int:
    """'Johnson & Johnson' and 'Johnson and Johnson' are one node —
    fold the article-minted spelling into its twin (register-sourced
    twin preferred as keeper, else the more-mentioned side). Exact 1-1
    same-type pairs only; the merge keeps the other spelling as alias."""
    from claim_graph.identity_refusals import merge_if_allowed
    rows = g.execute(r"""
        SELECT a.id AS amp, b.id AS spelled,
               (a.register_source IS NOT NULL) AS amp_reg,
               (b.register_source IS NOT NULL) AS spelled_reg
        FROM entities a
        JOIN entities b ON lower(replace(a.name, ' & ', ' and ')) = lower(b.name)
             AND b.type = a.type AND b.id <> a.id AND b.quarantined_at IS NULL
        WHERE a.name LIKE '%% & %%' AND a.quarantined_at IS NULL
          AND NOT (a.register_source IS NOT NULL
                   AND b.register_source IS NOT NULL)
        LIMIT %s""", (DETACH_CAP,)).fetchall()
    n = 0
    lost: set[int] = set()
    for r in rows:
        if r["amp"] in lost or r["spelled"] in lost:
            continue
        # keeper: the register-sourced side, else the older node
        if r["amp_reg"] or (not r["spelled_reg"] and r["amp"] < r["spelled"]):
            keep, lose = r["amp"], r["spelled"]
        else:
            keep, lose = r["spelled"], r["amp"]
        if merge_if_allowed(g, keep, lose, "crawler:ampersand-twin-fold") is None:
            continue                  # refused: `lose` is still live
        lost.add(lose)
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def heal_eponym_retype(g: Connection) -> int:
    """R-G6 heal for the pre-rules stratum (Arthur 2026-08-14, the Edmund
    Hillary find): an institution wearing a person's name is not the
    person. Deterministic retype — the trailing noun names the correct
    type (EPONYM_SUFFIX_TYPES, corpus-seeded); person-typed article
    entities ending in one retype through the entity_type_changes ledger.
    The punctuation guard skips compound debris ("Lisa Pragar / Occupy
    Garnet Road", "silken firm tofu ¼ cup") — that is quarantine-class,
    not retype-class, and stays for the screens. Retype only: a retyped
    twin standing beside a same-name node of the same type is the
    type-multiplicity lane's fold decision, not this heal's."""
    from claim_graph.contract import EPONYM_SUFFIX_TYPES
    from claim_graph.remediate import retype_entity
    rows = g.execute(r"""
        WITH heads AS (
            SELECT id, name,
                   lower(rtrim(substring(name from '([A-Za-zĀĒĪŌŪāēīōū.]+)$'),
                               '.')) AS head
            FROM entities
            WHERE type = 'person' AND register_source IS NULL
              AND quarantined_at IS NULL
              AND name ~ ' ' AND name !~ '[/()•*0-9¼½¾]'
        )
        SELECT id, name, head FROM heads WHERE head = ANY(%s)
        """, (list(EPONYM_SUFFIX_TYPES),)).fetchall()
    n = 0
    for r in rows:
        # same healed-away race guard as execute(): a concurrent lane may
        # have merged/quarantined the row since selection
        try:
            retype_entity(g, r["id"], EPONYM_SUFFIX_TYPES[r["head"]],
                          "crawler:eponym-retype (R-G6 heal)")
        except LookupError:
            g.rollback()
            continue
        n += 1
        if n % 200 == 0:
            g.commit()
    g.commit()
    return n


def quarantine_orphans(g: Connection) -> dict:
    """Article-minted entities with zero references anywhere — the
    standing, REVERSIBLE version of the item-e purge.

    Queue 8, 2026-09-19: this returns a DICT now, because the int it used to
    return could not answer the only question anyone asks of it. The finder is
    capped at FINDER_CAP per run, so it logged "orphans quarantined 500" on 34
    consecutive runs across a week — a number that reads identically whether
    501 rows remain or five million, making progress, stall and disaster
    indistinguishable from outside. Nothing was wrong: it had cleared 110,794
    of 216,880 since 2026-08-09 and was about half way. But establishing that
    took a seven-minute census, three wrong answers, and a question from Arthur.

    So a run now says what is LEFT as well as what it did. `more` comes free —
    fetch cap+1 rows and see whether the extra one is there — and `total` is
    one count, so the trend is provable from the log alone. A capped job that
    reports only its own cap is a measurement that cannot fail, which is to say
    not a measurement."""
    from claim_graph.remediate import quarantine_entity
    rows = g.execute("""
        SELECT e.id FROM entities e
        WHERE e.register_source IS NULL AND e.quarantined_at IS NULL
          AND NOT EXISTS (SELECT 1 FROM mentions m WHERE m.entity_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM claims c
                          WHERE c.subject_entity_id = e.id OR c.object_entity_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM claim_entities ce WHERE ce.entity_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM entity_keys k WHERE k.entity_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM entity_key_proposals p WHERE p.entity_id = e.id)
          AND NOT EXISTS (SELECT 1 FROM watchlist_entities w WHERE w.entity_id = e.id)
        LIMIT %s""", (FINDER_CAP + 1,)).fetchall()
    more = len(rows) > FINDER_CAP          # the cap+1 row: there is a tail
    n = 0
    for r in rows[:FINDER_CAP]:
        quarantine_entity(g, r["id"], "crawler:zero-reference-orphan")
        n += 1
    g.commit()
    # THIS FINDER'S OWN TOTAL, not every quarantine in the graph (queue 8,
    # 2026-09-19). T7.50 judges "is this drain moving?" by watching the total
    # rise, and the first cut counted EVERY quarantined entity — 223,990 rows
    # across a dozen rules. Another rule working hard would have masked an
    # orphan stall completely, which is the one thing the arm exists to catch.
    total = g.execute("SELECT count(*) c FROM entity_quarantine "
                      "WHERE reason = %s AND reverted_at IS NULL",
                      ("crawler:zero-reference-orphan",)).fetchone()["c"]
    out = {"quarantined": n, "more": more, "total_quarantined": total,
           "cap": FINDER_CAP,
           "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    _write_finder_state("orphans", out)
    return out


FINDER_STATE = os.path.join("var", "audits", "crawler_finders" + "." + "json")


def _write_finder_state(finder: str, out: dict) -> None:
    """One line of state per capped finder, where the board can read it.

    The board cannot run a census every morning — that took seven minutes — so
    T7.50 reads THIS instead: a finder that has said "more remain" for a
    fortnight while its total has not moved is a drain that has stalled, and
    someone should look. A file rather than a table, because this is telemetry
    about the lane, not a fact about the graph."""
    import json
    path = os.path.join(os.environ.get("QUERYNZ_REPO", os.getcwd()), FINDER_STATE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        state = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                state = json.load(f)
        hist = state.get(finder, {}).get("history", [])
        hist = (hist + [{"at": out["at"], "quarantined": out["quarantined"],
                         "more": out["more"], "total": out["total_quarantined"]}])[-200:]
        state[finder] = {**out, "history": hist}
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=1)
        os.replace(tmp, path)
    except OSError as e:        # telemetry never breaks the lane it measures
        log.warning("could not write finder state: %s", e)


def heal_post_nominals(g: Connection) -> int:
    """R-G5 heal (Anne Norman CNZM): a person node whose name is BASE +
    post-nominal honours merges into the existing BASE person node —
    deterministic, alias preserved by merge, reversible via revert_merge."""
    from claim_graph.identity_refusals import merge_if_allowed
    rows = g.execute(r"""
        WITH suffixed AS (
            SELECT id, name, trim(regexp_replace(name,
                '([,\s]+(ONZ|GNZM|KNZM|DNZM|CNZM|ONZM|MNZM|QSM|QSO|KStJ|JP|KC|QC))+$',
                '')) AS base
            FROM entities
            WHERE type = 'person' AND quarantined_at IS NULL
              AND name ~ '([,\s]+(ONZ|GNZM|KNZM|DNZM|CNZM|ONZM|MNZM|QSM|QSO|KStJ|JP|KC|QC))+$'
        ),
        -- FALSE-FOLD GUARD (Arthur 2026-08-14: "register occurrences
        -- without a corroborator"): fold ONLY when the base name is
        -- carried by exactly ONE live person node — with two, the fold
        -- would pick an identity by accident. Ambiguous cases abstain
        -- and stay for the corroborator tier (repair lane).
        -- Aggregated in ONE pass: the correlated per-row form of this
        -- guard seq-scanned all persons per candidate (an 80-minute
        -- statement that convoyed the whole estate, found live).
        namesakes AS (
            SELECT name, count(*) AS n FROM entities
            WHERE type = 'person' AND quarantined_at IS NULL
            GROUP BY name
        )
        SELECT s.id AS lose, b.id AS keep, s.name AS lname, b.name AS bname
        FROM suffixed s
        JOIN entities b ON b.type = 'person' AND b.quarantined_at IS NULL
         AND b.name = s.base
        JOIN namesakes c ON c.name = b.name AND c.n = 1
        WHERE s.id <> b.id
        LIMIT %s""", (FINDER_CAP,)).fetchall()
    # REGISTER RULE (Arthur 2026-08-14): name alone never combines
    # register occurrences. If the register holds >=2 persons with the
    # base name, the fold additionally needs a corroborator — any tier
    # in reviewer.corroborate (media shared article / register shared
    # org / shared registered office).
    from reviewer import corroborate   # sanctioned crossing
    reg = corroborate.register_conn()
    n = 0
    try:
        for r in rows:
            if corroborate.register_namesakes(reg, r["bname"]) >= 2:
                tier = corroborate.corroborated(
                    g, reg, r["lose"], r["keep"], r["lname"], r["bname"])
                if tier is None:
                    log.info("fold ABSTAINED (register namesakes, no corroborator): %r",
                             r["lname"])
                    continue
                reason = f"crawler:post-nominal-fold (R-G5, {tier})"
            else:
                reason = "crawler:post-nominal-fold (R-G5)"
            if merge_if_allowed(g, r["keep"], r["lose"], reason) is None:
                continue
            log.info("post-nominal fold: %r -> %r", r["lname"], r["bname"])
            n += 1
    finally:
        _close_quietly(reg)     # every exit path, not only the happy one
    g.commit()
    return n


# ── LLM-judged finders ───────────────────────────────────────────────────

def find_acronym_orgs(g: Connection) -> int:
    """Queue short unregistered all-caps organisations for type sanity."""
    rows = g.execute(r"""
        SELECT e.id, e.name, e.type FROM entities e
        WHERE e.register_source IS NULL AND e.quarantined_at IS NULL
          AND e.type = 'organisation'
          AND e.name ~ '^[A-Z][A-Za-z&+]{1,4}$'
          AND NOT EXISTS (SELECT 1 FROM mint_review mr WHERE mr.entity_id = e.id)
        ORDER BY (SELECT count(*) FROM mentions m WHERE m.entity_id = e.id) DESC
        LIMIT %s""", (FINDER_CAP,)).fetchall()
    n = 0
    for r in rows:
        cur = g.execute("""
            INSERT INTO mint_review (entity_id, name, type, pattern)
            VALUES (%s,%s,%s,'crawler-acronym-org')
            ON CONFLICT (entity_id) DO NOTHING""",
            (r["id"], r["name"], r["type"]))
        n += cur.rowcount
    g.commit()
    return n


def find_type_multiplicity(g: Connection) -> int:
    """Queue one representative per multi-typed name (observation tier)."""
    rows = g.execute("""
        WITH multi AS (
            SELECT lower(name) AS lname
            FROM entities
            WHERE register_source IS NULL AND quarantined_at IS NULL
            GROUP BY lower(name)
            HAVING count(DISTINCT type) >= 2
               AND sum((SELECT count(*) FROM mentions m
                        WHERE m.entity_id = entities.id)) >= 20
        )
        SELECT DISTINCT ON (lower(e.name)) e.id, e.name, e.type
        FROM entities e JOIN multi ON lower(e.name) = multi.lname
        WHERE NOT EXISTS (SELECT 1 FROM mint_review mr WHERE mr.entity_id = e.id)
        ORDER BY lower(e.name), e.id
        LIMIT %s""", (FINDER_CAP,)).fetchall()
    n = 0
    for r in rows:
        cur = g.execute("""
            INSERT INTO mint_review (entity_id, name, type, pattern)
            VALUES (%s,%s,%s,'crawler-type-multiplicity')
            ON CONFLICT (entity_id) DO NOTHING""",
            (r["id"], r["name"], r["type"]))
        n += cur.rowcount
    g.commit()
    return n


# ── judge + execute ──────────────────────────────────────────────────────

def _evidence(g: Connection, entity_id: int, cap: int = 3) -> list[str]:
    rows = g.execute("""
        SELECT evidence_text FROM model_claims   -- B10 T2: the gate
        WHERE (subject_entity_id = %s OR object_entity_id = %s)
          AND evidence_text IS NOT NULL LIMIT %s""",
        (entity_id, entity_id, cap)).fetchall()
    return [r["evidence_text"][:300] for r in rows]


def _mirror(row: dict) -> None:
    os.makedirs(os.path.dirname(VERDICTS_PATH), exist_ok=True)
    with open(VERDICTS_PATH, "a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _worker_connect(g: Connection) -> Connection:
    """Sibling of the caller's connection (reviewer.graph_handle.sibling_connection):
    works on a raw connection or the ReconnectingGraph the CLI passes."""
    from reviewer.graph_handle import sibling_connection
    return sibling_connection(g)


def build_prompt(lg: Connection, r: dict) -> tuple[str, str, dict]:
    """The one-shot judge's (system, user, schema) for a crawler row —
    acronym-org and type-multiplicity. ONE builder, used by judge() and by
    the B4b dense-validation pass (R3a), so the second model re-judges
    exactly the prompt the fleet would build today; conjunctions are the
    tool-loop re-read and have no one-shot prompt."""
    if r["pattern"] == "crawler-acronym-org":
        lines = [f"CANDIDATE: {r['name']!r} (currently typed organisation)"]
        ev = _evidence(lg, r["entity_id"])
        lines += ([f"EVIDENCE:"] + [f"  - {t}" for t in ev]) if ev else \
                 ["No claims attach (mention-only)."]
        return TYPE_SYSTEM, "\n".join(lines), TYPE_SCHEMA
    if r["pattern"] == "crawler-type-multiplicity":
        sibs = lg.execute("""
            SELECT type, (SELECT count(*) FROM mentions m
                          WHERE m.entity_id = e.id) AS mentions
            FROM entities e WHERE lower(e.name) = lower(%s)
              AND quarantined_at IS NULL""", (r["name"],)).fetchall()
        if len(sibs) > 40:
            # mega-ambiguous names ('EU': 4,946 siblings) — the
            # per-entity list blows the 16k slot and 400s the
            # judge deterministically (found live 2026-08-17);
            # aggregate by type, which is what the judge weighs
            agg: dict[str, list[int]] = {}
            for s in sibs:
                t = agg.setdefault(s["type"], [0, 0])
                t[0] += 1
                t[1] += s["mentions"]
            share = ", ".join(
                f"{k} ×{v[0]} ({v[1]} mentions total)"
                for k, v in sorted(agg.items()))
        else:
            share = ", ".join(
                f"{s['type']} ({s['mentions']} mentions)" for s in sibs)
        lines = [f"NAME: {r['name']!r}",
                 "ENTITIES sharing it: " + share]
        ev = _evidence(lg, r["entity_id"])
        if ev:
            lines += ["EVIDENCE (one entity's):"] + [f"  - {t}" for t in ev]
        return MULTI_SYSTEM, "\n".join(lines), MULTI_SCHEMA
    raise ValueError(f"no one-shot prompt for pattern {r['pattern']!r}")


def judge(g: Connection, limit: int = 100, concurrency: int = 6) -> int:
    """Judge queued crawler findings with the pattern-appropriate prompt."""
    from concurrent.futures import ThreadPoolExecutor
    rows = g.execute("""
        WITH pick AS (
            SELECT entity_id FROM mint_review WHERE status='queued'
              AND pattern LIKE 'crawler-%%'
            -- the capped conjunction queue (CONJUNCTION_CAP/cycle) is
            -- judged FIRST: oldest-first alone left it behind 4,793
            -- older backlog rows forever (found live 2026-08-22)
            ORDER BY (pattern = 'crawler-conjunction') DESC, screened_at
            LIMIT %s
            FOR UPDATE SKIP LOCKED)
        UPDATE mint_review m SET status='judging', judging_at=now()
        FROM pick WHERE m.entity_id = pick.entity_id
        RETURNING m.entity_id, m.name, m.type, m.pattern""",
        (limit,)).fetchall()
    g.commit()

    def _one(r):
        # OWN connection per worker: the threads previously shared g's
        # transaction, and a failing worker's rollback could silently
        # erase the main thread's not-yet-committed verdict UPDATE
        # (audit find 2026-08-17). Reads here, writes only on g in the
        # main thread — no shared transaction state.
        lg = _worker_connect(g)
        try:
            if r["pattern"] == "crawler-acronym-org":
                system, user, schema = build_prompt(lg, r)
                v = model.judge(system, user, schema=schema)
            elif r["pattern"] == "crawler-conjunction":
                # tier-3: the tool-loop re-read decides from the graph's own
                # evidence whether 'A B and C D' is two people (ruling 10)
                verdict, _meta = _re_read(
                    {"entity_id": r["entity_id"], "name": r["name"], "type": r["type"],
                     "pattern": r["pattern"],
                     "question": "Is this one entity really TWO people named together "
                                 "(a conjunction mint), ONE person, or not a person at all?"},
                    CONJUNCTION_LABELS)
                v = {"verdict": verdict["verdict"], "confidence": verdict["confidence"],
                     "reasoning": verdict.get("reasoning", ""), "model_reasoning": ""}
            else:   # crawler-type-multiplicity
                system, user, schema = build_prompt(lg, r)
                v = model.judge(system, user, schema=schema)
            v["confidence"] = min(max(float(v["confidence"]), 0.0), 1.0)
            return r, v
        except Exception as e:  # noqa: BLE001 — one bad case never stops a run
            log.warning("crawler judge %s failed: %s", r["entity_id"], e)
            return r, None
        finally:
            try:
                lg.close()
            except Exception:   # noqa: BLE001
                pass

    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        for r, v in ex.map(_one, rows):
            if v is None:
                continue
            g.execute("""
                UPDATE mint_review SET verdict=%s, confidence=%s, reasoning=%s,
                       status='judged', judged_at=now()
                WHERE entity_id=%s""",
                (v["verdict"], v["confidence"], v["reasoning"], r["entity_id"]))
            g.commit()
            _mirror({"id": r["entity_id"], "name": r["name"], "type": r["type"],
                     "pattern": r["pattern"], "verdict": v["verdict"],
                     "confidence": v["confidence"], "reasoning": v["reasoning"],
                     "model": v.get("model") or settings.LLM_MODEL,
                     "tier": "crawler", "prompt_version": "crawler-v1"})
            n += 1
    return n


def _junk_after_retype(name: str, new_type: str) -> str | None:
    """Would the graph's own mint guard refuse this name AT THE NEW TYPE?

    One import, no restatement: `claim_graph.consume` asks the caster's
    predicates the same question when it applies a type override, and this is
    that function. A second copy of the rule here would be a rule that can
    drift from the one it is meant to enforce."""
    from claim_graph.consume import _junk_for_type
    return _junk_for_type(name, new_type)


def execute(g: Connection) -> dict:
    """Act on judged crawler findings. Retype only; observations park."""
    from claim_graph.remediate import quarantine_entity, retype_entity

    # entities_type_check, verbatim — a verdict on a shared mint_review
    # row can come from ANOTHER lane's judge (2026-08-15 crash: 'Men'
    # carried mint-lane's 'debris' under a crawler pattern, and the raw
    # retype hit the check constraint). Junk quarantines; only real
    # graph types retype; anything else parks.
    graph_types = {"person", "organisation", "place", "facility",
                   "people", "work", "event", "case", "programme",
                   "instrument", "concept", "position", "industry",
                   "enterprise", "profession"}
    stats = {"retyped": 0, "cleared": 0, "observed": 0, "parked": 0}
    rows = g.execute("""
        SELECT entity_id, name, type, verdict, confidence, pattern
        FROM mint_review WHERE status='judged' AND pattern LIKE 'crawler-%'
        """).fetchall()
    for r in rows:
        v, conf = r["verdict"], r["confidence"] or 0
        if r["pattern"] == "crawler-acronym-org":
            if v in ("organisation", "abstain"):
                status = "cleared"
                stats["cleared"] += 1
            elif conf >= AUTO_BAND:
                # a heal may have merged/quarantined the entity after the
                # verdict queued (same race as mint_lane) — record 'gone',
                # never let one vanished row kill the drain
                try:
                    if v == "debris":
                        quarantine_entity(
                            g, r["entity_id"],
                            f"crawler:judged-debris {conf:.2f}")
                        status = "quarantined"
                        stats["quarantined"] = stats.get("quarantined", 0) + 1
                    elif v not in graph_types:
                        status = "parked"
                        stats["parked"] += 1
                    elif _junk_after_retype(r["name"], v):
                        # A RETYPE MUST NOT CREATE WHAT THE MINT GUARD REFUSES
                        # (queue 8, 2026-09-19 — T7.10). The judge is asked "is
                        # this really an organisation?", so for `chief` it
                        # correctly answers "no, a concept" — and `concept` is
                        # exactly the type the caster refuses a bare role in.
                        # The retype wrote a `entity_type_overrides` row, which
                        # consume applies on every later extraction, so one
                        # verdict on 2026-09-09 kept re-minting an office with
                        # nobody in it.
                        #
                        # "Not an organisation" and "therefore a concept" are
                        # different findings, and the judge is only asked the
                        # first. Debris is the honest reading, and it is what
                        # the same loop already does for an explicit `debris`
                        # verdict — reversible, ledgered, the entity kept.
                        quarantine_entity(
                            g, r["entity_id"],
                            f"crawler:retype-would-mint-junk {conf:.2f}")
                        status = "quarantined"
                        stats["quarantined"] = stats.get("quarantined", 0) + 1
                    else:
                        retype_entity(g, r["entity_id"], v,
                                      reason=f"crawler:acronym-type-sanity {conf:.2f}")
                        status = "retyped"
                        stats["retyped"] += 1
                except LookupError:
                    g.rollback()
                    status = "gone"
                    stats["gone"] = stats.get("gone", 0) + 1
            else:
                status = "parked"
                stats["parked"] += 1
        elif r["pattern"] == "crawler-conjunction":
            # ruling 10: a two-people verdict at the auto band SPLITS through
            # claim_graph.split — both halves get every mention article and
            # every claim (a conjunction sentence is about both); the source
            # is quarantined by the gate. The judged row is frozen into the
            # acceptance set BEFORE the split so the set exists independently
            # of what the split did.
            if v == "two-people" and conf >= CONJUNCTION_SPLIT_BAND:
                halves = conjunction_halves(r["name"])
                if halves is None:
                    status = "parked"; stats["parked"] += 1
                else:
                    from claim_graph.split import split_entity
                    arts = [str(x["article_id"]) for x in g.execute(
                        "SELECT article_id FROM mentions WHERE entity_id=%s", (r["entity_id"],)).fetchall()]
                    cids = [x["id"] for x in g.execute(
                        "SELECT id FROM claims WHERE subject_entity_id=%s OR object_entity_id=%s",
                        (r["entity_id"], r["entity_id"])).fetchall()]
                    _freeze_conjunction(r, "split")
                    try:
                        split_entity(g, r["entity_id"],
                                     [{"name": h, "type": "person", "article_ids": arts, "claim_ids": cids}
                                      for h in halves],
                                     reason=f"crawler:conjunction-split {conf:.2f}")
                        status = "split"; stats["split"] = stats.get("split", 0) + 1
                    except (ValueError, LookupError) as e:
                        g.rollback()
                        log.warning("conjunction split %s refused: %s", r["entity_id"], e)
                        status = "parked"; stats["parked"] += 1
            elif v == "not-a-person" and conf >= AUTO_BAND:
                # a paid verdict that the 'person' is furniture, an
                # advert phrase or an implement: junk quarantines through
                # the gate (reversible), as the acronym lane's debris
                # does; parking it threw the verdict away (found live
                # 2026-08-22: 24 of the first 31 verdicts)
                _freeze_conjunction(r, "quarantined")
                try:
                    quarantine_entity(g, r["entity_id"],
                                      f"crawler:conjunction-not-a-person {conf:.2f}")
                    status = "quarantined"
                    stats["quarantined"] = stats.get("quarantined", 0) + 1
                except LookupError:
                    g.rollback()
                    status = "gone"; stats["gone"] = stats.get("gone", 0) + 1
            elif v in ("one-person", "abstain"):
                status = "cleared"; stats["cleared"] += 1
            else:
                status = "parked"; stats["parked"] += 1
        else:                        # type-multiplicity: observation tier
            status = "observed"
            stats["observed"] += 1
        g.execute("UPDATE mint_review SET status=%s, actioned_at=now() "
                  "WHERE entity_id=%s", (status, r["entity_id"]))
        g.commit()
    return stats


MACRON_FOLD = "translate(%s, 'āēīōūĀĒĪŌŪ', 'aeiouAEIOU')"
DOMINANCE = 0.75          # C7's mention-dominance keeper threshold
# B4b (2026-08-22): the drain is back in run() BEHIND the adversarial
# refuter, capped per run. 40 × the 2-hour cadence ≈ 480/day, under
# ruling 31's 500/day concern, and sized to the 401 pending rows.
MERGE_CAP = 40
# a junk name ('4fd', '7/u', '2.20pm', '18S4') is not an identity question
# — no refuter call is spent on it; the pair parks as junk
_JUNK_NAME = re.compile(r"^(?:[^A-Za-z]*[A-Za-z]){0,2}[^A-Za-z]*$|^\d{1,2}[.:]\d{2}\s*[ap]m$", re.I)

_REFUTATIONS_DDL = """
CREATE TABLE IF NOT EXISTS merge_refutations (
    id          bigserial PRIMARY KEY,
    entity_id   bigint NOT NULL,
    kept_id     bigint NOT NULL,
    loser_id    bigint NOT NULL,
    basis       text NOT NULL,
    verdict     text NOT NULL,
    confidence  real,
    reasoning   text,
    evidence    jsonb,
    urls        jsonb,
    merge_id    bigint,
    refuted_at  timestamptz NOT NULL DEFAULT now()
)"""


def ensure_refuter_schema(g: Connection) -> None:
    """The refuter's ledger: every verdict with its reasoning, evidence and
    the URLs fetched — question-time lookup recorded as an AUDIT row, never
    as a claim (terminal architecture). Healer lifecycle table."""
    g.execute(_REFUTATIONS_DDL)
    g.commit()


#: ANCHORED TO THE REPO, not to the caller (C260, 2026-10-06). This default
#: was relative, so the gate's answer depended on `os.getcwd()`: from the repo
#: it authorised the drain, from anywhere else it returned "no full refuter gate
#: run recorded" and the drain skipped, politely, forever. It worked only
#: because `querynz-crawler.service` and the era orchestrator both happen to
#: run with the repo as their working directory — a correctness resting on a
#: coincidence of configuration. The env override is kept: the gate script and
#: every test here point this at a fixture directory.
GATE_GLOB = os.environ.get("B4B_GATE_GLOB", os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))), "var", "audits",
    "b4b-refuter-gate-*.json"))


def _artifact_age_days(path: str) -> int | None:
    """Days since the gate run, from the artifact's own UTC stamp.

    From the FILENAME, not the mtime: these files get copied between boxes
    and an mtime would then report the copy as a fresh measurement. Reckoned
    in UTC on both sides because the stamps carry `Z`.
    """
    m = re.search(r"(\d{4}-\d{2}-\d{2})T\d{6}Z", os.path.basename(path))
    if not m:
        return None
    try:
        ran = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (datetime.now(timezone.utc).date() - ran).days


#: the sentinel prefix; `refuter_measured` refuses it outright rather than comparing it
_UNLOADABLE = "unloadable:"


def _judgment_fingerprint() -> str:
    """The live refuter's fingerprint, or a sentinel that can never match.

    IMPORTED LAZILY AND NEVER ALLOWED TO PASS. `research.merge_refuter` pulls in the
    query layer and the web tools, so importing it at module scope would make the
    healer depend on them to answer a question about an artifact. If it cannot be
    imported at all, the honest answer is not "fingerprints match" — it is a value
    that fails the comparison, because a refuter we cannot load is one we certainly
    cannot authorise (#ffe697: a gate whose subject is absent must not pass politely).
    """
    try:
        from research.merge_refuter import judgment_fingerprint
        return judgment_fingerprint()
    except Exception as exc:                                  # noqa: BLE001
        return f"{_UNLOADABLE}{type(exc).__name__}"


def refuter_measured() -> tuple[bool, str]:
    """MEASURED BEFORE TRUSTED (plan B4b): the drain runs only while the
    newest FULL gate artifact (ops/b4b_refuter_gate.py over the frozen
    labelled set; smoke runs with --limit/--only never count) says
    `passed`. No artifact, or a failed one, and the refuter is unmeasured
    — the timer run skips the drain and says why.

    THE REASON STRING STATES THE ARTIFACT'S AGE (C260, 2026-10-06), because
    this function is what the journal and the era record quote and it read
    identically whether the measurement was taken today or six weeks ago. On
    2026-10-06 the authorising artifact was **45 days old** and nothing said
    so; `merge_refuter.py` had been committed to three times since (all three
    endpoint plumbing, so the judgment it measured was in fact unchanged — but
    nothing checked that either). Refusing on a CHANGED refuter needs a fresh
    gate run against the frozen labelled set and is C513; this makes the gap
    visible, which is the precondition for anyone noticing it.
    """
    import glob
    full = []
    for path in sorted(glob.glob(GATE_GLOB)):
        try:
            with open(path) as f:
                d = json.load(f)
        except (OSError, ValueError):
            continue
        if not d.get("limit") and not d.get("only"):
            full.append((path, d))
    if not full:
        return False, "no full refuter gate run recorded"
    path, d = full[-1]
    r = d.get("rates", {})
    age = _artifact_age_days(path)
    stamp = f"{os.path.basename(path)} ({age}d old)" if age is not None else \
            f"{os.path.basename(path)} (age unknown — no stamp in the name)"
    if not d.get("passed"):
        # SAY WHAT THE NUMBER CAN SUPPORT (C540/C532, 2026-10-09). This string is
        # what the journal and the era record quote, and "catch=0.769" reads like
        # a finding about the refuter. It is not: the catch denominator is 13
        # `different` cases, so 0.80 is not an achievable value (the real bar is
        # 11/13 = 0.846), one case moves the rate 7.7 points, and the 95% interval
        # at 10/13 is [0.497, 0.918] — which overlaps August's PASSING 11/13
        # [0.578, 0.957] almost entirely. Six verdicts moved between those two runs
        # in BOTH directions on an identical judgment fingerprint. The drain still
        # fails closed, which is right; what this sentence must not do is send the
        # next reader to improve a rate that cannot be measured.
        res = d.get("resolution") or {}
        tail = ""
        if res.get("catch_denominator"):
            tail = (f" — {res.get('catch_refuted')}/{res['catch_denominator']} different "
                    f"cases, one case = {res.get('catch_step')}, 95% CI "
                    f"{res.get('catch_ci95')}; {res.get('threshold')} is "
                    f"{'' if res.get('threshold_is_achievable') else 'NOT '}achievable on "
                    f"this denominator (effective bar {res.get('effective_threshold')}), and "
                    f"{res.get('n_different_for_half_width_0_05')} cases would be needed to "
                    f"measure it to +/-0.05. The set is the work, not the rate")
        return False, (f"{stamp} FAILED catch={r.get('catch')} "
                       f"false_refute={r.get('false_refute')}{tail}")
    # C513: AND IT MUST BE A MEASUREMENT OF THE REFUTER THAT WOULD RUN. A passing
    # artifact authorises the judgment it measured, not whatever has replaced it.
    live = _judgment_fingerprint()
    recorded = d.get("judgment_fingerprint")
    if live.startswith(_UNLOADABLE):
        # A SENTINEL MUST NOT BE ABLE TO AGREE WITH ITSELF. Comparing two
        # "unloadable:ImportError" strings would authorise the drain on the strength of
        # the refuter being unavailable — refused explicitly instead, with its own
        # message, because "I could not look" is a third state and not a mismatch.
        return False, (f"{stamp} passed, but the live refuter did not import "
                       f"({live}) — nothing can be authorised against a refuter that "
                       f"cannot be loaded")
    if recorded != live:
        return False, (
            f"{stamp} passed, but it measured a DIFFERENT refuter: artifact "
            f"{recorded or 'carries no fingerprint (written before C513)'} vs live "
            f"{live}. The drain fails closed — re-authorise with one full "
            f"`ops/b4b_refuter_gate.py` run over the frozen labelled set")
    return True, (f"{stamp} catch={r.get('catch')} false_refute={r.get('false_refute')} "
                  f"fp={live}")


def _refute(pair: dict, **kw) -> tuple[dict, dict]:
    """The adversarial merge refuter (research.merge_refuter) — graph reads
    + robots-absolutist web tools, refutation only. Indirected so tests
    script it. Refuses a non-loopback model endpoint before any call."""
    from research.merge_refuter import endpoint_refusal, refute
    if "post" not in kw:
        why = endpoint_refusal()
        if why:
            raise RuntimeError(f"merge refuter refused: {why}")
    return refute(pair, **kw)


def merge_duplicates(g: Connection, cap: int = 500) -> dict:
    """R3 merge actuator (stream S5, 2026-08-19): drain 'observed'
    mistyped-duplicate verdicts as verdict-backed MERGES. The judge's
    verdict is a diagnosis naming no keeper — what this adds is
    deterministic TARGET RESOLUTION, then the one true merge gate
    (claim_graph.merge_entities: full payload, revertible in-era).

    THE VERDICT NAMES NO DIRECTION (first-tranche lesson, 14 merges
    reverted 2026-08-19: the queued row is the NAME's representative,
    sometimes the correctly-typed side — 'Armida Salsiah Alisjahbana'
    person nearly folded into its incidental org twin). Direction is
    resolved from evidence, never from which node was queued:
      - pair case only (judged + exactly ONE live different-typed
        folded-same-name sibling); n-node names park for a later tier
      - exactly one side register-anchored → the anchor keeps (C7's
        single-anchor-is-authority); both anchored → park
      - neither anchored → mention dominance ≥ {DOMINANCE} of the
        pair keeps (C7's threshold); no dominant side → park.
    Judged-node gates: still exists, type unchanged since judgment,
    not quarantined. Executor refusals (enterprise loser, bad pair)
    park; vanished rows record 'gone'.

    Arthur sampled the mirror and passed it (2026-08-19, in session)
    — rides the daily crawler cadence (run(), cap 500/run) alongside
    the CLI verb for manual tranches."""
    from claim_graph.merge import merge_entities

    ensure_refuter_schema(g)
    rows = g.execute("""
        SELECT entity_id, name, type, confidence FROM mint_review
        WHERE status='observed' AND pattern='crawler-type-multiplicity'
          AND verdict='mistyped-duplicate' AND confidence >= %s
        ORDER BY confidence DESC LIMIT %s""",
        (AUTO_BAND, cap)).fetchall()
    stats = {"merged": 0, "parked": 0, "gone": 0, "refuted": 0, "junk": 0}
    fold = MACRON_FOLD % "lower(name)"

    def _m(eid: int) -> int:
        row = g.execute("SELECT coalesce(sum(n_mentions), 0) AS m "
                        "FROM mentions WHERE entity_id=%s",
                        (eid,)).fetchone()
        return row["m"]

    for r in rows:
        why, keeper, loser = "", None, None
        judged = g.execute(
            "SELECT id, name, type, register_source, quarantined_at "
            "FROM entities WHERE id=%s", (r["entity_id"],)).fetchone()
        if judged is None:
            status = "gone"
        elif _JUNK_NAME.match(r["name"] or ""):
            status, why = "junk", "junk name — no identity question, refuter not spent"
        elif judged["type"] != r["type"]:
            status, why = "parked", "type drifted since judgment"
        elif judged["quarantined_at"] is not None:
            status, why = "parked", "judged node quarantined"
        else:
            cands = g.execute(f"""
                SELECT id, name, type, register_source FROM entities
                WHERE {fold} = {MACRON_FOLD % 'lower(%s)'}
                  AND id <> %s AND type <> %s
                  AND quarantined_at IS NULL""",
                (r["name"], r["entity_id"], r["type"])).fetchall()
            if not cands:
                status = "gone"
            elif len(cands) > 1:
                status, why = "parked", f"{len(cands) + 1}-node name"
            else:
                sib = cands[0]
                j_anc = judged["register_source"] is not None
                s_anc = sib["register_source"] is not None
                if j_anc and s_anc:
                    status, why = "parked", "both anchored"
                elif j_anc:
                    keeper, loser, basis = judged, sib, "anchor"
                elif s_anc:
                    keeper, loser, basis = sib, judged, "anchor"
                else:
                    mj, ms = _m(judged["id"]), _m(sib["id"])
                    total = mj + ms
                    if total and max(mj, ms) / total >= DOMINANCE:
                        keeper, loser = ((judged, sib) if mj > ms
                                         else (sib, judged))
                        basis = f"dominance {max(mj, ms)}/{total}"
                    else:
                        status, why = "parked", (
                            f"no dominant side ({mj} vs {ms})")
        if keeper is not None:
            # B4b: the refuter gets the LAST word before the gate. Its job is
            # to break the merge; "not-refuted" is a failed attempt, not a
            # confirmation — the verdict-backed merge still owns the decision.
            pair = {"a_id": keeper["id"], "a_name": keeper["name"], "a_type": keeper["type"],
                    "b_id": loser["id"], "b_name": loser["name"], "b_type": loser["type"],
                    "basis": f"mistyped-duplicate {r['confidence']:.2f} {basis}"}
            verdict, meta = _refute(pair)
            ref_id = g.execute(
                "INSERT INTO merge_refutations (entity_id, kept_id, loser_id, basis, verdict, "
                "confidence, reasoning, evidence, urls) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (r["entity_id"], keeper["id"], loser["id"], pair["basis"], verdict["verdict"],
                 verdict.get("confidence"), verdict.get("reasoning"),
                 json.dumps(verdict.get("evidence", [])), json.dumps(meta.get("urls", [])))).fetchone()["id"]
            g.commit()
            if verdict["verdict"] == "refuted":
                status, why = "refuted", f"refuted: {(verdict.get('reasoning') or '')[:140]}"
                keeper = None
            elif verdict["verdict"] != "not-refuted":
                status, why = "parked", f"refuter {verdict['verdict']}: {(verdict.get('reasoning') or '')[:120]}"
                keeper = None
        if keeper is not None:
            try:
                mid = merge_entities(
                    g, keeper["id"], loser["id"],
                    f"crawler:mistyped-duplicate {r['confidence']:.2f} "
                    f"{basis} refuter:not-refuted {verdict.get('confidence', 0):.2f}")
                g.execute("UPDATE merge_refutations SET merge_id=%s WHERE id=%s", (mid, ref_id))
                status = "merged"
                _mirror({"tier": "crawler-merge",
                         "entity_id": r["entity_id"],
                         "name": r["name"],
                         "kept_id": keeper["id"],
                         "kept_type": keeper["type"],
                         "loser_id": loser["id"],
                         "loser_type": loser["type"],
                         "confidence": r["confidence"],
                         "basis": basis, "merge_id": mid})
            except ValueError as e:
                g.rollback()
                status, why = "parked", str(e)[:120]
            except LookupError:
                g.rollback()
                status = "gone"
        if status != "merged":
            _mirror({"tier": "crawler-merge", "entity_id": r["entity_id"],
                     "name": r["name"], "judged_type": r["type"],
                     "confidence": r["confidence"], "status": status,
                     "why": why})
        stats[status] += 1
        g.execute("UPDATE mint_review SET status=%s, actioned_at=now() "
                  "WHERE entity_id=%s", (status, r["entity_id"]))
        g.commit()
    return stats


def run(g: Connection, judge_limit: int = 100,
        concurrency: int = 6) -> None:
    ensure_schema(g)
    # a judge failure (JSON error, 400) leaves its row in 'judging' and
    # judge() only picks 'queued' — without this the drain loop's
    # queued==0 exit strands them unjudged (found live 2026-08-17,
    # same reclaim mint_lane.run has had all along)
    g.execute("""
        UPDATE mint_review SET status='queued', judging_at=NULL
        WHERE status='judging' AND pattern LIKE 'crawler-%%'
          AND judging_at < now() - interval '30 minutes'""")
    g.commit()
    d1 = heal_exec_role_places(g)
    d1b = heal_party_boundary(g)
    d1c = heal_anonymised_honorifics(g)
    log.info("anonymised-honorific entities quarantined (C252): %d", d1c)
    d1d = heal_ocr_debris(g)
    log.info("OCR-debris entities (C235): folded %d, quarantined %d, %d left",
             d1d["folded"], d1d["quarantined"], d1d["left"])
    d1e = heal_glued_punctuation(g)
    log.info("glued-punctuation names healed (C241): %d", d1e)
    # The re-read lane (Arthur 2026-09-21). Every heal above reads the NAME;
    # this one reads the SOURCE DOCUMENT, which is the only place the evidence
    # for the glued class actually lives. It runs AFTER the name-only heals so
    # it only ever sees what they could not decide.
    try:
        from .reread import run_reread
        rr = run_reread(g)
        log.info("re-read against source documents: read %d, recovered %d, "
                 "quarantined %d, abstained %d (no document for %d)",
                 rr["read"], rr["recovered"], rr["discarded"], rr["abstained"], rr["no_document"])
    except Exception:   # noqa: BLE001 — a lane that cannot read documents must
        log.exception("re-read lane failed; the rest of the cycle stands")
    log.info("party-boundary leader claims detached (C247): %d", d1b)
    d2 = quarantine_orphans(g)
    d3 = heal_post_nominals(g)
    log.info("post-nominal folds: %d", d3)
    d4 = heal_article_led(g)
    d5 = heal_negation_prefix(g)
    log.info("article-led healed: %d, negation-prefix quarantined: %d", d4, d5)
    d6 = heal_eponym_retype(g)
    d7 = heal_definite_article(g)
    d8 = heal_caption_credit(g)
    log.info("eponym retypes (R-G6): %d, definite-article healed (R-G7): %d, "
             "caption credits healed (R-G8): %d", d6, d7, d8)
    d9 = heal_lead_junk(g)
    d10 = heal_trailing_function_word(g)
    d11 = heal_orthography_twins(g)
    log.info("lead-junk (R-G9): %d, trailing-function-word (R-G10): %d, "
             "orthography twins: %d", d9, d10, d11)
    d12 = heal_url_fragments(g)
    d13 = heal_role_title_prefix(g)
    d14 = heal_ampersand_twins(g)
    d15 = heal_comma_composites(g)
    d16 = heal_the_names_bare_twins(g)
    log.info("url-fragments (R-G11): %d, role-title (R-G12): %d, "
             "ampersand twins: %d, comma composites (R-G13): %d, "
             "THE_NAMES bare twins (R-G7): %d", d12, d13, d14, d15, d16)
    d17 = heal_trailing_repeat(g)
    d18 = heal_role_string_entities(g)
    log.info("trailing-repeat doubles healed: %d (Māori-reduplication refusals: %d); "
             "role-string entities retyped to position: %d",
             d17, TRAILING_REPEAT_REFUSED[-1] if TRAILING_REPEAT_REFUSED else 0, d18)
    from . import hygiene
    d19 = hygiene.heal_whitespace_names(g, apply=True)["renamed"]
    log.info("whitespace-normalized (T7.10 hygiene, R-G14): %d", d19)
    f1 = find_acronym_orgs(g)
    f2 = find_type_multiplicity(g)
    f3 = find_conjunctions(g)
    log.info("conjunction persons queued for the tier-3 re-read: %d", f3)
    log.info("crawler finders: exec-role-place healed %d, orphans quarantined %d%s "
             "(%s quarantined in all), acronym-orgs queued %d, type-multiplicity queued %d",
             d1, d2["quarantined"],
             " AT THE CAP — MORE REMAIN," if d2["more"] else " — backlog clear,",
             f"{d2['total_quarantined']:,}", f1, f2)
    n = judge(g, judge_limit, concurrency=concurrency)
    x = execute(g)
    log.info("crawler judged %d, executed %s", n, x)
    # merge actuator (S5/R3): STOPPED by ruling 31 (2026-08-22) while
    # nothing refuted it; RESTARTED in B4b behind the adversarial refuter
    # (every pair goes verdict → target resolution → refuter → gate),
    # capped at MERGE_CAP per run. tests/test_crawler_no_merge_in_run.py
    # asserts the gated form.
    measured, why = refuter_measured()
    if not measured:
        log.warning("merge drain skipped — refuter unmeasured: %s", why)
    else:
        try:
            m = merge_duplicates(g, cap=MERGE_CAP)
            log.info("merge drain (refuter-gated by %s, cap %d): %s", why, MERGE_CAP, m)
        except RuntimeError as e:      # refuter refused (endpoint) — no drain, say so
            log.warning("merge drain skipped: %s", e)
    # anchor-audit lane (2026-08-15): register-anchor sanity rides the
    # crawler cadence; skipped cleanly when the register copy is down
    try:
        from psycopg.rows import dict_row
        from reviewer import corroborate
        from . import anchor_lane
        reg = corroborate.register_conn()
        if reg is not None:
            try:
                reg.row_factory = dict_row
                anchor_lane.run(g, reg, judge_limit=50)
            finally:
                _close_quietly(reg)
    except Exception as e:  # noqa: BLE001 — the audit never blocks the drain
        log.warning("anchor lane skipped: %s", e)
    from . import repair
    log.info("repair lane: %s", repair.run(g))
