"""A template is a folder: `template.toml` (name, title, version, owner;
which published views it reads, each with its licence, attribution and
refresh; its sections in order; its known limits) and an optional
`rules.py` exporting `RULES`, a tuple of pure functions `(report) -> flag`.
The rules file is loaded by path, not imported, so a template folder under
`products/templates/` (step 5.2) needs no import of this module and the
one-way test stays simple. Before the file runs, the name `contract` is
bound in it to `products.report.contract`: the flag, the helpers over a
built report, the common rules and the presentation rules, reachable with
no import line (see that module). The common rules run for every template
unless its `template.toml` says `common_rules = false`.

What a template reads is all it is allowed to read (design: "A template
holds five things"). The builder passes the template's views to the walk,
and a section may draw only on those views; a template that names a view
the catalogue does not know is refused when loaded. A section draws on the
walk's buckets it names (`sources`; the walk runs only the buckets some
section names, so a template that wants an organisation start's officers
followed, the companies at its office, or the holding chain above it names
`officers`, `office` or `chain`, and `chain_depth` says how far), and may
keep only the start's own rows or only its people's (`own`), only
companies of some statuses (`statuses`), or only what changed between the
monthly files (`changed`).

A flag follows the old estate's contract (harvested from
data-layer/flags, as an idea): three statuses. `fired` must cite rows;
`clear` must name the sources it was checked against, because a green is
only "none in the sources held"; `blocked` must say why the check could
not run, and is never shown as clear."""
from __future__ import annotations

import importlib.util
import os
import tomllib
from dataclasses import dataclass, field

from products.report import catalogue as cat
from products.report import contract
from products.report.contract import flag  # noqa: F401  (the shape's own rules reach it here too)

HERE = os.path.dirname(os.path.abspath(__file__))
SHAPE_TEMPLATES = os.path.join(HERE, "templates")
USE_CASE_TEMPLATES = os.path.join(os.path.dirname(HERE), "templates")   # products/templates/<nn>-<name>/ (step 5.2)
STATUSES, SEVERITIES = contract.STATUSES, contract.SEVERITIES
BUCKETS = ("members", "confirmed", "near", "roles", "pointing", "second", "named", "officers", "office", "chain")   # walk.BUCKETS, held by a test
CHAIN_MAX = 4   # walk.LIMITS["chain"], held by a test


@dataclass(frozen=True)
class Section:
    name: str
    heading: str
    views: tuple                 # the published views it draws on (all in the template's reads)
    sources: tuple = ("members", "confirmed", "near", "roles", "pointing", "second", "named", "officers", "office", "chain")   # the walk's buckets it draws from
    not_held: tuple = ()         # registers it would read that no lane has published: the blank says so
    text: str = ""               # a line printed under the heading
    own: bool | None = None      # True: only rows of the start itself and rows that sit on it (or on its group); False: only the rest; None: both
    statuses: tuple = ()         # keep only rows whose `status` (a company's) is one of these, folded; rows with no status column pass
    changed: bool = False        # keep only rows that arrived or left between the monthly files held (and a company's earlier states), newest change first


@dataclass(frozen=True)
class Read:
    view: str
    licence: str
    attribution: str = ""
    refresh: str = ""


@dataclass(frozen=True)
class Template:
    name: str
    title: str
    version: str
    owner: str
    folder: str
    reads: tuple
    sections: tuple
    limits: tuple = ()
    depth: int = 2
    rules: tuple = field(default=(), compare=False)
    common_rules: bool = True     # the contract's COMMON_RULES run first; `common_rules = false` in template.toml opts out
    chain_depth: int = 0          # company holders of record followed up the chain from a company start (0: none; the walk caps it)

    @property
    def views(self) -> set:
        return {r.view for r in self.reads}

    @property
    def buckets(self) -> set:
        """The walk's buckets some section draws on: the walk runs no other."""
        return {b for s in self.sections for b in s.sources}


def _load_rules(folder: str) -> tuple:
    path = os.path.join(folder, "rules.py")
    if not os.path.exists(path):
        return ()
    spec = importlib.util.spec_from_file_location(f"qv4_template_rules_{os.path.basename(folder)}", path)
    mod = importlib.util.module_from_spec(spec)
    mod.contract = contract          # bound before the file runs: a template reaches the contract by this name, never by an import
    spec.loader.exec_module(mod)
    rules = getattr(mod, "RULES", ())
    for r in rules:
        if not callable(r):
            raise ValueError(f"{path}: RULES holds something that is not a function")
    return tuple(rules)


def load(folder: str) -> Template:
    with open(os.path.join(folder, "template.toml"), "rb") as f:
        t = tomllib.load(f)
    for k in ("name", "title", "version", "owner"):
        if not t.get(k):
            raise ValueError(f"{folder}: template.toml lacks {k}")
    reads = tuple(Read(r["view"], r.get("licence", ""), r.get("attribution", ""), r.get("refresh", "")) for r in t.get("reads", []))
    if not reads:
        raise ValueError(f"{folder}: a template names the published views it reads")
    for r in reads:
        if r.view not in cat.BY_NAME:
            raise ValueError(f"{folder}: reads pub.{r.view}, which the catalogue does not know")
        if not r.licence:
            raise ValueError(f"{folder}: pub.{r.view} is read without its licence terms stated")
    views = {r.view for r in reads}
    sections = []
    for s in t.get("sections", []):
        sv = tuple(s.get("views", []))
        outside = [x for x in sv if x not in views]
        if outside:
            raise ValueError(f"{folder}: section {s.get('name')} draws on {outside}, which the template does not read")
        for nh in s.get("not_held", []):
            if nh not in cat.NOT_HELD_NAME:
                raise ValueError(f"{folder}: section {s.get('name')} names {nh!r} as not held; the catalogue has no such register")
        sources = tuple(s.get("sources", Section.sources))
        unknown = [b for b in sources if b not in BUCKETS]
        if unknown:
            raise ValueError(f"{folder}: section {s.get('name')} draws on {unknown}, which the walk has no bucket for; the buckets are {BUCKETS}")
        own = s.get("own")
        if own is not None and not isinstance(own, bool):
            raise ValueError(f"{folder}: section {s.get('name')}: own is true or false")
        sections.append(Section(s["name"], s["heading"], sv, sources, tuple(s.get("not_held", [])), s.get("text", ""),
                                own, tuple(cat.fold(x) for x in s.get("statuses", [])), bool(s.get("changed", False))))
    if not sections:
        raise ValueError(f"{folder}: a template has sections")
    chain_depth = int(t.get("chain_depth", 0))
    if chain_depth < 0 or chain_depth > CHAIN_MAX:
        raise ValueError(f"{folder}: chain_depth is 0 to {CHAIN_MAX}")
    return Template(t["name"], t["title"], str(t["version"]), t["owner"], folder, reads, tuple(sections), tuple(t.get("limits", [])),
                    int(t.get("depth", 2)), _load_rules(folder), bool(t.get("common_rules", True)), chain_depth)


def folders() -> dict:
    """{name: folder} for every template on disk: the shape's own, then the use cases'."""
    out = {}
    for base in (SHAPE_TEMPLATES, USE_CASE_TEMPLATES):
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            path = os.path.join(base, d)
            if os.path.exists(os.path.join(path, "template.toml")):
                try:
                    with open(os.path.join(path, "template.toml"), "rb") as f:
                        out[tomllib.load(f)["name"]] = path
                except Exception:
                    continue
    return out


def by_name(name: str) -> Template:
    f = folders()
    if name not in f:
        raise KeyError(f"no template named {name!r}; have {sorted(f)}")
    return load(f[name])
