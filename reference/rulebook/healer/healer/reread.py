"""The re-read lane — go back to the document the surface came from.

Arthur, 2026-09-21, on C241's abstains:

    "for these kind of errors we need a pipeline to return to the document,
     identify the glued name and find the actual name for extraction. This
     pipeline should be used for all obvious extraction debris and artifacts
     that we have taxonomised."

Every other heal in this file's neighbour reads the NAME. This one reads the
SOURCE. That is the whole difference, and it is what lets it answer questions
no string rule can:

    Dokyun Kim (Laing Properties)Dokyun delivered an outstanding performance

`Laing Properties)Dokyun` was minted as a person. The name is `Dokyun Kim`,
which is on neither side of the seam; no rule reading the string could have
reached it, and the card's honest abstention was the best a string rule had.

MEASURED 2026-09-21 over 2,359 of C241's abstained rows, each re-read against
its own document:

    24.3%  acted on          (the card acted on none of them)
    18.8%  ocr-garble        quarantined: no token in them is a word
     2.8%  footnote-marker   quarantined: prose carrying a note number
     2.7%  RECOVERED         a name the document supports, 63 rows
    73.2%  abstained still   and they stay exactly as they are

The taxonomy is `reconciliation.defects` — one home for the classes and for
what each needs the document to show. This module is the machinery only: find
candidates, fetch the document once per article, ask the taxonomy, dispose
through the same audited, reversible gate every other heal uses.

THE LANE REMEMBERS WHAT IT READ. `v3.reread_log` holds one row per entity
looked at, abstentions included, and candidates exclude what is already there.
Without it 73% of the work would re-select every cycle and the lane would
re-read the same 1,700 rows forever without reaching the rest — the trap
recorded on `_dispose_stripped` in 2026-08-14, one layer up.

NO DOCUMENT, NO READING. Where `V3_BACKLOG_DSN` is unset or unreachable the
lane abstains entirely rather than falling back on the string, which is the
one thing it exists not to do.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from psycopg import Connection

from reconciliation import defects
from .mint_lane import VERDICTS_PATH
from .repair import _backlog          # one home for where the documents live

log = logging.getLogger("healer.reread")

REREAD_CAP = 400           # entities re-read per run
DOC_CAP = 400_000          # a document longer than this is read to here only

DDL = """
CREATE TABLE IF NOT EXISTS reread_log (
    entity_id  bigint PRIMARY KEY,
    surface    text        NOT NULL,
    defect     text        NOT NULL,
    verdict    text        NOT NULL,
    recovered  text,
    because    text,
    article_id uuid,
    read_at    timestamptz NOT NULL DEFAULT now()
);
"""

# The prefilter is deliberately wider than the taxonomy: SQL picks the shapes
# an index can reach, `defects.classify` decides which class (or none).
_CANDIDATES = r"""
    SELECT e.id, e.name, e.type
    FROM entities e
    WHERE e.register_source IS NULL AND e.quarantined_at IS NULL
      AND (e.name ~ '[a-zāēīōū)][).][A-ZĀĒĪŌŪ0-9]'
           OR e.name ~ '\.[0-9]{1,4}$'
           -- strpos, not a LIKE pattern: psycopg scans a parameterised
           -- statement for placeholders and rejects a per-cent sign followed
           -- by anything but s, b or t -- INSIDE COMMENTS TOO, which is how
           -- the first version of this comment broke the query it explained.
           OR strpos(e.name, '@') > 0)
      AND NOT EXISTS (SELECT 1 FROM reread_log l WHERE l.entity_id = e.id)
    LIMIT %s
"""


def ensure_schema(g: Connection) -> None:
    # Same fast path as the mint lane's, and for the same reason: CREATE TABLE
    # IF NOT EXISTS still asks for ACCESS EXCLUSIVE, and asking every cycle
    # puts that request behind any long reader on a 27 M-row table.
    if g.execute("SELECT to_regclass('reread_log') IS NOT NULL AS ok").fetchone()["ok"]:
        g.commit()
        return
    g.execute(DDL)
    g.commit()


def _mention(g: Connection, entity_id: int) -> dict | None:
    """One sighting: the article this surface was read out of, and where.

    Lowest offset first, which is the earliest sighting in the piece — a name
    is introduced in full before it is shortened, so the earliest mention is
    the one most likely to sit beside the evidence."""
    return g.execute(
        "SELECT article_id, first_char FROM mentions WHERE entity_id = %s "
        "ORDER BY first_char NULLS LAST LIMIT 1", (entity_id,)).fetchone()


def _mirror(row: dict, reading: defects.Reading, article_id) -> None:
    """Every action reaches the Review tab, as every other lane's does."""
    try:
        with open(VERDICTS_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(),
                "lane": "reread", "entity_id": row["id"], "surface": row["name"],
                "defect": reading.defect, "verdict": reading.verdict,
                "recovered": reading.name, "because": reading.because,
                "article_id": str(article_id) if article_id else None,
            }) + "\n")
    except OSError:     # the mirror is an audit convenience, never a gate
        log.warning("reread: verdict mirror unwritable")


def run_reread(g: Connection, cap: int = REREAD_CAP) -> dict:
    """Re-read one tranche. Returns the counts, so a caller can log them."""
    from claim_graph.remediate import quarantine_entity
    from .crawler import _dispose_stripped

    b = _backlog()
    if b is None:
        log.warning("reread lane abstains entirely: no document source")
        return {"read": 0, "recovered": 0, "discarded": 0, "abstained": 0, "no_document": 0}

    ensure_schema(g)
    rows = g.execute(_CANDIDATES, (cap,)).fetchall()
    docs: dict = {}
    out = {"read": 0, "recovered": 0, "discarded": 0, "abstained": 0, "no_document": 0}
    for r in rows:
        if defects.classify(r["name"]) is None:
            continue                       # the prefilter is wider than the taxonomy
        m = _mention(g, r["id"])
        aid = m["article_id"] if m else None
        if aid not in docs:
            got = b.execute("SELECT text_content FROM articles WHERE id = %s",
                            (aid,)).fetchone() if aid else None
            docs[aid] = ((got or {}).get("text_content") or "")[:DOC_CAP]
        doc = docs[aid]
        reading = defects.read(r["name"], doc, (m or {}).get("first_char") or -1)
        out["read"] += 1
        if not doc:
            out["no_document"] += 1
        acted = False
        if reading.verdict == defects.RECOVER:
            # the same disposition every other heal uses: fold into the one
            # live twin, rename when there is none, abstain on two or more
            acted = _dispose_stripped(g, r, reading.name, f"reread:{reading.defect}")
            out["recovered"] += acted
        elif reading.verdict == defects.DISCARD:
            quarantine_entity(g, r["id"], f"reread:{reading.defect}")
            out["discarded"] += 1
            acted = True
        if not acted:
            out["abstained"] += 1
        g.execute("""INSERT INTO reread_log (entity_id, surface, defect, verdict,
                                             recovered, because, article_id)
                     VALUES (%s, %s, %s, %s, %s, %s, %s)
                     ON CONFLICT (entity_id) DO NOTHING""",
                  (r["id"], r["name"], reading.defect or "unclassified",
                   reading.verdict if acted else defects.ABSTAIN,
                   reading.name or None, reading.because, aid))
        if acted:
            _mirror(r, reading, aid)
        if out["read"] % 100 == 0:
            g.commit()
    g.commit()
    return out
