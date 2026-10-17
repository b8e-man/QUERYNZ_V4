"""The crawler's other half: a retype that would mint junk quarantines instead
(T7.10, 2026-09-19).

The acronym-type-sanity judge is asked ONE question — "is this really an
organisation?" — and for `chief` it correctly answers "no, a concept". But "not
an organisation" and "therefore a concept" are different findings, and the
second one is not the judge's to make: `concept` is precisely the type the
caster refuses a bare role in. One verdict on 2026-09-09 wrote an
`entity_type_overrides` row that `claim_graph.consume` then applied on every
later extraction, re-minting an office with nobody in it each time.

Six overrides of this shape existed in the live graph — chair, head, ceo,
mayor, owner, chief — all from this one rule, all into person or concept.

`claim_graph.consume` now refuses them at the mint, which makes the existing
rows inert; this screen is what stops new ones being written. Both halves,
because a mint-guard without a screen leaves the damage and a screen without a
mint-guard leaves the door.
"""
from __future__ import annotations

import ast
import pathlib

from healer.crawler import _junk_after_retype


def test_a_retype_into_person_or_concept_of_a_bare_role_is_junk():
    assert _junk_after_retype("Chief", "concept") == "bare-role"
    assert _junk_after_retype("Mayor", "person") == "bare-role"
    assert _junk_after_retype("CEO", "concept") == "bare-role"


def test_a_legitimate_retype_is_untouched():
    assert _junk_after_retype("Fonterra", "organisation") is None
    assert _junk_after_retype("Waikato", "place") is None
    assert _junk_after_retype("Climate Change", "concept") is None


def test_it_delegates_rather_than_restating_the_rule():
    """One definition. A copy in the healer could drift from the one the graph
    actually enforces, and then the screen would pass what the mint refuses —
    which is the same class of bug as the leak itself."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "healer"
           / ("crawler" + ".py")).read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "_junk_after_retype")
    assert any(isinstance(n, ast.ImportFrom) and n.module == "claim_graph.consume"
               for n in ast.walk(fn)), "the screen must ask the graph's own guard"


def test_execute_screens_BEFORE_it_retypes():
    """Reading the source, because the ordering is the rule: a screen after the
    retype would record the judgement and then do it anyway."""
    src = (pathlib.Path(__file__).resolve().parents[1] / "healer"
           / ("crawler" + ".py")).read_text(encoding="utf-8")
    fn = next(n for n in ast.walk(ast.parse(src))
              if isinstance(n, ast.FunctionDef) and n.name == "execute")
    calls = [n.func.id for n in ast.walk(fn)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id in ("_junk_after_retype", "retype_entity")]
    assert calls, "neither call found — the screen or the retype has moved"
    assert calls.index("_junk_after_retype") < calls.index("retype_entity"), calls
