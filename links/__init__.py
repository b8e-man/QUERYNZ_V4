"""Links: the three tables, the three verdicts, the two trust settings
(plan 1.9; docs/contracts/links.md). Step 4.2 builds the rules.

- links: a pair of rows, the rule, the evidence, a grade (confirmed or near).
- decisions: a remembered ruling on a pair: same, not the same, contested.
  Each says who or what made it and on what evidence. Only ever added to.
- groups: rows gathered into people by following confirmed links, minus
  the decisions. Rebuilt whenever either table changes; edited by nobody.

Two settings are ruled from measurement and have a default until then:
`chain` (follow chains of confirmed links; a flagged group is contested
whole) and `steps` (a connection through more than one person is near,
never confirmed). They are settings, not code.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
TABLES_SQL = os.path.join(HERE, "tables.sql")
GRADES = ("confirmed", "near")
VERDICTS = ("same", "not the same", "contested")
MAKERS = re.compile(r"^(review-agent@\d+|correction:\S+|suppression:\S+|old-estate:\S+|person:\S+)$")

#: the two trust settings and their defaults (design: "Two settings are ruled from measurement")
SETTINGS = {
    "chain": "follow",            # follow | one-step: how far a chain of confirmed links is trusted
    "contested_group": "whole",   # whole: a group the watch flags is contested as a whole
    "steps": "near",              # near: a multi-step connection through more than one person is near
}


def tables_sql() -> str:
    with open(TABLES_SQL, encoding="utf-8") as f:
        return f.read()


def pair(a: str, b: str) -> tuple:
    """The ordered pair the tables store: the smaller key first."""
    if a == b:
        raise ValueError("a link joins two different rows")
    return (a, b) if a < b else (b, a)


def check_decision(verdict: str, made_by: str, made_on: dict) -> list:
    out = []
    if verdict not in VERDICTS:
        out.append(f"verdict must be one of {VERDICTS}")
    if not MAKERS.match(made_by or ""):
        out.append("made_by names who or what made it: review-agent@N, correction:ID, suppression:ID, old-estate:ID or person:NAME")
    if not isinstance(made_on, dict) or not made_on:
        out.append("made_on carries the evidence")
    return out
