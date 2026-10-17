"""The template's contract (plan 1.9; docs/contracts/template.md).

A shape is built once; a use case is a template on it. A template holds
five things, and `validate` refuses one that lacks any:

  reads        the published tables it reads, each with its licence terms,
               the attribution it requires and how often it is refreshed.
               This is also all it is allowed to read (never the inside of a
               lane; the one-way test holds that in code)
  sections     in order; a section headed "articles mentioning" retrieves
               and asserts nothing
  rules        its own warning flags and patterns
  known_limits the page that tells the reader what the product cannot see
  owner, version

A template is data, kept as `products/templates/<name>.json`; the shape
renders it. Every figure links to its document; a blank says whether it
means "none found" or "not held"; a total states what it leaves out; an
unreadable name is shown as unreadable; a figure read from pixels is marked.
"""
import json
import os
import re
from dataclasses import dataclass, field

SHAPES = ("published-site", "subject-report", "register-scan", "archive-search", "board")
REFRESH = ("daily", "weekly", "monthly", "on-change", "never")
_PUB = re.compile(r"^pub\.[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class Read:
    table: str          # pub.<view>
    licence: str        # the terms the data came under
    attribution: str    # '' when none is required
    refresh: str        # one of REFRESH


@dataclass(frozen=True)
class Template:
    name: str
    shape: str
    use_case: int
    reads: tuple
    sections: tuple
    rules: tuple
    known_limits: str
    owner: str
    version: int
    settings: dict = field(default_factory=dict)


def validate(t: Template) -> list:
    out = []
    if t.shape not in SHAPES:
        out.append(f"shape must be one of {SHAPES}")
    if not t.reads:
        out.append("a template names the published tables it reads")
    for r in t.reads:
        if not _PUB.match(r.table):
            out.append(f"{r.table}: a template reads only pub.* views")
        if r.refresh not in REFRESH:
            out.append(f"{r.table}: refresh must be one of {REFRESH}")
        if not r.licence:
            out.append(f"{r.table}: its licence terms are stated")
    if not t.sections:
        out.append("a template has sections, in order")
    if not t.known_limits.strip():
        out.append("a template has a known-limits page")
    if not t.owner:
        out.append("a template has an owner")
    if t.version < 1:
        out.append("version from 1")
    return out


def load(path: str) -> Template:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    reads = tuple(Read(**r) for r in d.get("reads", []))
    return Template(name=d["name"], shape=d["shape"], use_case=int(d["use_case"]), reads=reads,
                    sections=tuple(d.get("sections", [])), rules=tuple(d.get("rules", [])),
                    known_limits=d.get("known_limits", ""), owner=d.get("owner", ""), version=int(d.get("version", 0)),
                    settings=d.get("settings", {}))


def all_templates(folder: str = None) -> list:
    folder = folder or os.path.dirname(os.path.abspath(__file__))
    return [load(os.path.join(folder, f)) for f in sorted(os.listdir(folder)) if f.endswith(".json")]
