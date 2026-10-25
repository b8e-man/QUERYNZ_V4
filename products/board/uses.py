"""The use cases tab (ruling 87): the plan's table of use cases, read at
render time from the copy of the repository the board runs from (found from
this file, so the release copy shows the release copy's plan), each row with
what the data holds for it today:

- the scan templates built for it: `products/scan/templates/*/template.toml`
  read as data files from disk, never imported (the one-way rule binds
  imports and queries of another module's inside; a product's published
  files are read as text). A template names its use case in `use_case`
  where it carries one, else in its `owner` line, "(use case 9)";
- the registers the plan's reference names for it (`not-held.md`, the one
  reference table with a use-case column), each held or not held by whether
  a published view of the board's register for it is present in `pub`
  (`catalogue.REFERENCE_REGISTERS` maps the reference's words to registers).

Pure but for `read_*`, which read files; nothing is written."""
from __future__ import annotations

import glob
import os
import re
import tomllib

from products.board import catalogue as cat

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TABLE = os.path.join("docs", "plan", "reference", "registers-and-use-cases", "the-sixteen-use-cases.md")
NOT_HELD = os.path.join("docs", "plan", "reference", "registers-and-use-cases", "not-held.md")
TEMPLATES = os.path.join("products", "scan", "templates", "*", "template.toml")
COLUMNS = ("number", "name", "who", "question", "shape", "step")


def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_table(text: str) -> list:
    """The use cases in the plan's order: a dict per row whose first cell is a number."""
    out = []
    for line in (text or "").splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) >= len(COLUMNS) and re.fullmatch(r"\d+", cells[0]):
            out.append(dict(zip(COLUMNS, cells[:len(COLUMNS)])))
    return out


def parse_not_held(text: str) -> list:
    """[(source, (use case numbers…))] from the reference's not-held table."""
    out = []
    for line in (text or "").splitlines():
        cells = _cells(line) if line.lstrip().startswith("|") else []
        if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("- ") and cells[0] != "Source":
            nums = tuple(re.findall(r"\b(\d+)\b", cells[1]))
            if nums:
                out.append((cells[0], nums))
    return out


def use_case_of(t: dict) -> tuple:
    """The use case numbers a template names: its `use_case` field, else its owner line's "(use case N)"."""
    x = t.get("use_case")
    if isinstance(x, int):
        return (str(x),)
    if isinstance(x, (list, tuple)):
        return tuple(str(n) for n in x)
    return tuple(re.findall(r"use case (\d+)", str(t.get("owner") or "")))


def read_text(rel: str, repo: str = REPO):
    try:
        with open(os.path.join(repo, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def read_templates(repo: str = REPO) -> list:
    """[{'name', 'title', 'uses': (numbers…)}] for every scan template on disk, by name."""
    out = []
    for p in sorted(glob.glob(os.path.join(repo, TEMPLATES))):
        try:
            with open(p, "rb") as f:
                t = tomllib.load(f)
        except (OSError, tomllib.TOMLDecodeError):
            continue
        out.append({"name": t.get("name") or os.path.basename(os.path.dirname(p)), "title": t.get("title") or "", "uses": use_case_of(t)})
    return out


def registers_for(source: str) -> tuple:
    for words, regs in cat.REFERENCE_REGISTERS.items():
        if source.startswith(words):
            return regs
    return ()


def held_of(registers: tuple, held_views: set) -> list:
    """[(register, plain name, held?)] for the board's registers named."""
    plain = dict(cat.REGISTERS) | dict(cat.NOT_HELD)
    return [(r, plain.get(r, r), any(v.name in held_views for v in cat.views_of(r))) for r in registers]


def rows(table: str, not_held: str, templates: list, held_views: set) -> list:
    """The tab's rows: the plan's columns, then 'templates' and 'registers'
    [(source, [(register, plain, held)])], in the plan's order."""
    sources = parse_not_held(not_held or "")
    out = []
    for uc in parse_table(table):
        n = uc["number"]
        out.append({**uc, "templates": [t for t in templates if n in t["uses"]],
                    "registers": [(s, held_of(registers_for(s), held_views)) for s, nums in sources if n in nums]})
    return out
