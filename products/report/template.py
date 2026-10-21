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

A template may declare the reader's settings its rules read (`[[params]]`:
`name`, `kind`, `default`, `means`), so the page can offer them, the
command line can set them (`--set name=value`) and the builder can refuse
one the template did not declare. The builder puts each under its name in
`report["params"]` and, so a rule reads it the way it reads
`report["since"]`, under its own name on the report too; the first is the
construction template's `window_days`.

A flag follows the old estate's contract (harvested from
data-layer/flags, as an idea): three statuses. `fired` must cite rows;
`clear` must name the sources it was checked against, because a green is
only "none in the sources held"; `blocked` must say why the check could
not run, and is never shown as clear."""
from __future__ import annotations

import datetime as dt
import importlib.util
import os
import re
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
PARAM_KINDS = ("integer", "text", "date")   # what a declared parameter's value is read as
#: names a parameter may not take: the report's own keys, and the page's and the command line's own arguments
RESERVED_PARAMS = frozenset({"template", "title", "version", "owner", "reads", "ref", "as_of", "built_at", "since", "new", "cannot_say", "found",
                             "why", "subject", "group", "sections", "flags", "hubs", "citations", "walk", "limits", "not_held", "views_not_published",
                             "problems", "members", "params", "params_declared", "format", "m", "saved", "set", "html", "superseded_not_held"})
PARAM_NAME = re.compile(r"^[a-z][a-z0-9_]{0,39}$")


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
class Param:
    name: str                    # the key a rule reads on the report (`report["window_days"]`) and the page's and command line's name for it
    kind: str                    # integer | text | date: what the value is read as; a value that does not read is passed as given, and the rule says so
    default: object = None       # the value when the reader sets none (None: the rule treats it as not set)
    means: str = ""              # what it means, in the reader's words, shown on the form and in the memo


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
    params: tuple = ()            # the reader's settings the template's rules read, declared so a surface can offer and refuse them
    superseded_not_held: tuple = ()   # (key, register) for each not-held key the template cites that a lane has since published

    @property
    def param_names(self) -> tuple:
        return tuple(p.name for p in self.params)

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
    sections, superseded = [], []
    for s in t.get("sections", []):
        sv = tuple(s.get("views", []))
        outside = [x for x in sv if x not in views]
        if outside:
            raise ValueError(f"{folder}: section {s.get('name')} draws on {outside}, which the template does not read")
        not_held = []
        for nh in s.get("not_held", []):
            if nh in cat.SUPERSEDED_NOT_HELD:   # a register a lane published after the template named it: the template loads, and the report says so
                if (nh, cat.SUPERSEDED_NOT_HELD[nh]) not in superseded:
                    superseded.append((nh, cat.SUPERSEDED_NOT_HELD[nh]))
                continue
            if nh not in cat.NOT_HELD_NAME:
                raise ValueError(f"{folder}: section {s.get('name')} names {nh!r} as not held; the catalogue has no such register")
            not_held.append(nh)
        sources = tuple(s.get("sources", Section.sources))
        unknown = [b for b in sources if b not in BUCKETS]
        if unknown:
            raise ValueError(f"{folder}: section {s.get('name')} draws on {unknown}, which the walk has no bucket for; the buckets are {BUCKETS}")
        own = s.get("own")
        if own is not None and not isinstance(own, bool):
            raise ValueError(f"{folder}: section {s.get('name')}: own is true or false")
        sections.append(Section(s["name"], s["heading"], sv, sources, tuple(not_held), s.get("text", ""),
                                own, tuple(cat.fold(x) for x in s.get("statuses", [])), bool(s.get("changed", False))))
    if not sections:
        raise ValueError(f"{folder}: a template has sections")
    chain_depth = int(t.get("chain_depth", 0))
    if chain_depth < 0 or chain_depth > CHAIN_MAX:
        raise ValueError(f"{folder}: chain_depth is 0 to {CHAIN_MAX}")
    params = []
    for p in t.get("params", []):
        name = str(p.get("name") or "")
        if not PARAM_NAME.match(name) or name in RESERVED_PARAMS:
            raise ValueError(f"{folder}: a parameter is named {name!r}; a name is lower-case letters, digits and underscores, and not one of the report's own keys")
        if name in {x.name for x in params}:
            raise ValueError(f"{folder}: the parameter {name} is declared twice")
        if p.get("kind") not in PARAM_KINDS:
            raise ValueError(f"{folder}: the parameter {name} has kind {p.get('kind')!r}; the kinds are {PARAM_KINDS}")
        if not p.get("means"):
            raise ValueError(f"{folder}: the parameter {name} says nothing about what it means")
        default = p.get("default")
        if default is not None and read_param(p["kind"], default) is None:
            raise ValueError(f"{folder}: the parameter {name}'s default {default!r} is not a {p['kind']}")
        params.append(Param(name, p["kind"], default, str(p["means"])))
    return Template(t["name"], t["title"], str(t["version"]), t["owner"], folder, reads, tuple(sections), tuple(t.get("limits", [])),
                    int(t.get("depth", 2)), _load_rules(folder), bool(t.get("common_rules", True)), chain_depth, tuple(params), tuple(superseded))


def read_param(kind: str, value):
    """The value as its kind reads it, or None when it does not read: an
    integer from digits (a sign allowed), a date from YYYY-MM-DD, text as
    given and stripped. A bool is never an integer."""
    if value is None or isinstance(value, bool):
        return None
    s = str(value).strip()
    if kind == "integer":
        try:
            return int(s)
        except ValueError:
            return None
    if kind == "date":
        try:
            return dt.date.fromisoformat(s).isoformat()
        except ValueError:
            return None
    return s if s else None


def params_for(t: Template, given: dict | None) -> tuple:
    """(values, declared) for a template and what the reader gave: `values`
    is {name: value} for every declared parameter (the reading of what was
    given, the given text itself when it does not read as its kind so the
    rule can say so, or the default); `declared` lists each with its kind,
    meaning, default, what was given and whether it read. A name the
    template does not declare is refused."""
    given = {k: v for k, v in (given or {}).items() if v not in (None, "")}
    unknown = sorted(set(given) - set(t.param_names))
    if unknown:
        raise KeyError(f"the template {t.name} declares no parameter named {', '.join(unknown)}; it declares {list(t.param_names) or 'none'}")
    values, declared = {}, []
    for p in t.params:
        raw = given.get(p.name)
        if raw is None:
            value, read, source = p.default, True, "default"
        else:
            value = read_param(p.kind, raw)
            read = value is not None
            value, source = (value if read else str(raw).strip()), "given"
        values[p.name] = value
        declared.append({"name": p.name, "kind": p.kind, "means": p.means, "default": p.default, "value": value, "given": raw, "source": source, "read": read})
    return values, tuple(declared)


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
