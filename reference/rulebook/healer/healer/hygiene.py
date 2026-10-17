"""Entity-name whitespace hygiene — the STANDING pass for the T7.10 straggler
class (Muster 1 B4 tranche 3, 2026-08-29).

The graph's single largest historic defect was 38,309 entity names carrying
embedded newlines: v3/cast.py keys a cast entity on norm_form(surface) (whitespace
collapsed) but stored the RAW wrapped surface as the DISPLAY name, so a name that
wrapped a line-break kept the '\\n' — "St. James' Gazette" landed as
"St.\\nJames' Gazette". Clustering was never wrong; the display name was. Healed
to a handful; this lane keeps it at zero going forward.

A name that differs from its whitespace-collapsed form (embedded \\n\\r\\t, or
untrimmed edges) is renamed to the collapsed form through
`remediate.rename_entity` — pure cleanup, NOT an evidence-gated completion: the
new name is a strict whitespace-collapse of the current one, adds no information,
is reversible via entity_renames, and keeps the old surface as an alias (searches
still hit it). Deterministic, no LLM, no network.

    python -m healer.cli hygiene           # dry run (prints what would change)
    python -m healer.cli hygiene --apply    # rename + audit

STANDING: also runs each crawler cycle (crawler.run, R-G14, apply=True) so new
stragglers self-heal on the querynz-crawler cadence — this lane is the manual
handle on the same pass.
"""
from __future__ import annotations

import logging
import re

from psycopg import Connection

from claim_graph.remediate import rename_entity   # sanctioned crossing (see repair.py)

log = logging.getLogger("healer.hygiene")

# a display name is dirty if it carries a newline/CR/tab, or has untrimmed edges
_DIRTY_SQL = r"(name ~ '[\n\r\t]' OR name <> btrim(name))"
_WS = re.compile(r"\s+")


def clean_name(name: str) -> str:
    """Collapse every run of whitespace (newlines/tabs included) to a single
    space and trim the edges. The ONLY transform this lane applies."""
    return _WS.sub(" ", name).strip()


def heal_whitespace_names(g: Connection, apply: bool = False,
                          limit: int = 5000) -> dict:
    """Find live (non-quarantined) entities whose display name carries junk
    whitespace and normalise it through the audited rename gate. Caller need not
    commit — this commits when apply. Returns stats."""
    stats = {"dirty": 0, "renamed": 0, "skipped_empty": 0, "unchanged": 0}
    rows = g.execute(
        f"SELECT id, name, type FROM entities "
        f"WHERE {_DIRTY_SQL} AND quarantined_at IS NULL "
        f"ORDER BY id LIMIT %s", (limit,)).fetchall()
    stats["dirty"] = len(rows)
    for r in rows:
        cleaned = clean_name(r["name"])
        if not cleaned:                       # a name that is ALL whitespace: leave it
            stats["skipped_empty"] += 1        # (deletion is quarantine's call, not ours)
            continue
        if cleaned == r["name"]:               # dirty per SQL but stable under clean (shouldn't happen)
            stats["unchanged"] += 1
            continue
        log.info("%s #%d %r -> %r", r["type"], r["id"], r["name"], cleaned)
        if apply:
            rename_entity(g, r["id"], cleaned, "hygiene:whitespace-normalize",
                          evidence={"rule": "collapse-whitespace", "raw": r["name"]})
            stats["renamed"] += 1
    if apply:
        g.commit()
    return stats
