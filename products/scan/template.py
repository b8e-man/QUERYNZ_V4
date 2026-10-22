"""A scan template is a folder under products/scan/templates/<name>/ holding
`template.toml`: the question in words; the published views it reads, each
with its licence, attribution and refresh; the join it makes, as a chain
of steps; its known limits; its owner and version. A template is data: no
code runs from it. What it reads is all it is allowed to read (design: "A
template holds five things"): a step on a view the template does not list
is refused when loaded, and a column no view has is refused by the check.

The steps. The first names the view (or views: one scan asked of each,
the lines carrying which) every row starts from. Each later step names
the view it lands on and how it gets there:

  by = "row"     a column of this row equals a column of the next (`on =
                 [here, there]`): a director's company, a notice's company.
                 The register's own structure; it never lowers a grade.
  by = "person"  the next row is the same person as this one, by the links:
                 under the chains setting "follow", the rows of the group
                 (pub.groups) this row is in, contested when the watch
                 flagged the group; under "direct", a confirmed link between
                 the two rows themselves. Both rows must be rows pub.names
                 carries (`person_row` in the catalogue).
  by = "link"    a link of one named rule between this row and the next
                 (`rule = "organisation-name@1"`), or of any of several
                 (`rule = ["full-name@1", "name-only@1"]`), graded as the
                 link is: a near rule gives a near line, with the link's
                 own reason.
  by = "name"    a name column of this row and one of the next are the same
                 text once folded (lower case, macrons off, a legal ending
                 such as Limited off, letters and digits only): `on = [name
                 here, name there]`. With `number = [here, there]`, two rows
                 that both carry the number join by it alone (confirmed) and
                 never by name; otherwise by name alone (near, with the
                 reason). Every row there under the same name is a line of
                 its own; with `namesakes = true` (the rows there are each
                 one body, as the companies register's are) each such line
                 is marked as one of its namesakes.

A row or name step may be `optional = true`: a row with nothing to join
there is still listed, the step shown as "none found in" the view; every
step after an optional one is optional too.

A step may filter (`where = { in_latest = true, role_status = ["current"] }`:
equality, a list, a boolean or null; nothing else) and name columns to
carry into the line (`columns`); a name column is shown suppressed with
the row; an address-shaped column is refused."""
from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass

from products.scan import views as cat

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, "templates")
BYS = ("row", "person", "link", "name")
OPTIONAL_BYS = ("row", "name")
MAX_STEPS = 6


@dataclass(frozen=True)
class Step:
    view: str                    # the view this step lands on (the first step: the first of `views`)
    label: str                   # the word the list heads this step's columns with
    by: str = ""                 # "" for the first step; row | person | link
    on: tuple = ()               # (column here, column there) for a row step
    rule: str = ""               # the link rule for a link step (several: joined with ", ")
    where: tuple = ()            # ((column, value), ...): value a scalar, a list, a bool or None
    columns: tuple = ()          # columns carried into the line beside the title, dates and citation
    views: tuple = ()            # the first step only: every view the scan starts from
    number: tuple = ()           # a name step: (number column here, number column there)
    optional: bool = False       # a row or name step: a row with nothing to join is listed, the step "none found in"
    rules: tuple = ()            # a link step: every rule it follows
    namesakes: bool = False      # a name step: several rows there under one name are namesakes, and each line says so

    @property
    def fold_note(self) -> str:
        if not self.number:
            return "by name"
        return f"by {'charity number' if 'charit' in ' '.join(self.number) else 'business number'} or by name"


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
    question: str
    join: str
    version: str
    owner: str
    folder: str
    reads: tuple
    steps: tuple
    limits: tuple = ()

    @property
    def views(self) -> set:
        return {r.view for r in self.reads}

    @property
    def person_steps(self) -> int:
        return sum(1 for s in self.steps if s.by == "person")

    @property
    def uses_links(self) -> bool:
        return any(s.by in ("person", "link") for s in self.steps)

    def starts(self) -> tuple:
        return self.steps[0].views


def _columns(folder: str, step_name: str, cols) -> tuple:
    out = []
    for c in cols or ():
        if not cat.COLUMN.match(str(c)):
            raise ValueError(f"{folder}: step {step_name}: {c!r} is not a column name")
        if cat.ADDRESS_COLUMN.search(str(c)):
            raise ValueError(f"{folder}: step {step_name}: {c!r} is address-shaped; no list carries one (hard limit 15)")
        out.append(str(c))
    return tuple(out)


def _where(folder: str, step_name: str, where) -> tuple:
    out = []
    for c, val in (where or {}).items():
        if not cat.COLUMN.match(str(c)):
            raise ValueError(f"{folder}: step {step_name}: where names {c!r}, not a column name")
        if isinstance(val, dict) or (isinstance(val, list) and any(isinstance(x, (dict, list)) for x in val)):
            raise ValueError(f"{folder}: step {step_name}: where {c} is a value, a list of values, a boolean or null")
        out.append((str(c), tuple(val) if isinstance(val, list) else val))
    return tuple(out)


def load(folder: str) -> Template:
    with open(os.path.join(folder, "template.toml"), "rb") as f:
        t = tomllib.load(f)
    for k in ("name", "title", "question", "join", "version", "owner"):
        if not t.get(k):
            raise ValueError(f"{folder}: template.toml lacks {k}")
    if not t["question"].rstrip().endswith("?"):
        raise ValueError(f"{folder}: the question is a question, ending in '?'")
    reads = tuple(Read(r["view"], r.get("licence", ""), r.get("attribution", ""), r.get("refresh", "")) for r in t.get("reads", []))
    if not reads:
        raise ValueError(f"{folder}: a scan names the published views it reads")
    for r in reads:
        if r.view not in cat.BY_NAME:
            raise ValueError(f"{folder}: reads pub.{r.view}, which the catalogue does not know")
        if not r.licence:
            raise ValueError(f"{folder}: pub.{r.view} is read without its licence terms stated")
    views = {r.view for r in reads}
    raw = t.get("steps", [])
    if not raw or len(raw) > MAX_STEPS:
        raise ValueError(f"{folder}: a scan has one to {MAX_STEPS} steps")
    steps = []
    for i, s in enumerate(raw):
        name = s.get("label") or f"step {i + 1}"
        if i == 0:
            starts = tuple(s["views"]) if s.get("views") else ((s["view"],) if s.get("view") else ())
            if not starts:
                raise ValueError(f"{folder}: the first step names the view (or views) every row starts from")
            if s.get("by") or s.get("optional"):
                raise ValueError(f"{folder}: the first step is where the scan starts; it has no `by` and is not optional")
            for v in starts:
                if v not in views:
                    raise ValueError(f"{folder}: step {name} starts from pub.{v}, which the template does not read")
            steps.append(Step(starts[0], str(name), "", (), "", _where(folder, name, s.get("where")), _columns(folder, name, s.get("columns")), starts))
            continue
        v = s.get("view")
        if v not in views:
            raise ValueError(f"{folder}: step {name} lands on pub.{v}, which the template does not read")
        by = s.get("by")
        if by not in BYS:
            raise ValueError(f"{folder}: step {name}: by is one of {BYS}, not {by!r}")
        on, rule, rules, number = (), "", (), ()
        if by in ("row", "name"):
            on = tuple(s.get("on") or ())
            if len(on) != 2 or not all(cat.COLUMN.match(str(c)) for c in on):
                raise ValueError(f"{folder}: step {name}: a {by} step names `on = [column here, column there]`")
            if any(cat.ADDRESS_COLUMN.search(str(c)) for c in on):
                raise ValueError(f"{folder}: step {name}: joins on an address-shaped column (hard limit 15)")
        if by == "name":
            number = tuple(s.get("number") or ())
            if number and (len(number) != 2 or not all(cat.COLUMN.match(str(c)) for c in number)):
                raise ValueError(f"{folder}: step {name}: a name step's `number = [column here, column there]`")
        elif s.get("number") or "namesakes" in s:
            raise ValueError(f"{folder}: step {name}: only a name step names a number or its namesakes")
        namesakes = s.get("namesakes", False)
        if not isinstance(namesakes, bool):
            raise ValueError(f"{folder}: step {name}: namesakes is true or false")
        elif by == "person":
            prev = steps[-1].view
            if not (cat.BY_NAME[v].person_row and cat.BY_NAME[prev].person_row):
                raise ValueError(f"{folder}: step {name}: a person step joins two rows pub.names carries; pub.{prev} to pub.{v} is not that")
        elif by == "link":
            raw = s.get("rule")
            rules = tuple(str(x) for x in raw) if isinstance(raw, list) else ((str(raw),) if raw else ())
            if not rules or not all("@" in x for x in rules) or len(set(rules)) != len(rules):
                raise ValueError(f"{folder}: step {name}: a link step names the rule (or rules), as the links publish it (name@version)")
            rule = ", ".join(rules)
        optional = s.get("optional", False)
        if not isinstance(optional, bool):
            raise ValueError(f"{folder}: step {name}: optional is true or false")
        if optional and by not in OPTIONAL_BYS:
            raise ValueError(f"{folder}: step {name}: only a row or name step may be optional")
        if steps[-1].optional and not optional:
            raise ValueError(f"{folder}: step {name}: follows an optional step, so it is optional too")
        steps.append(Step(v, str(name), by, on, rule, _where(folder, name, s.get("where")), _columns(folder, name, s.get("columns")),
                          (), number, optional, rules, namesakes))
    labels = [s.label for s in steps]
    if len(set(labels)) != len(labels):
        raise ValueError(f"{folder}: every step has its own label")
    return Template(t["name"], t["title"], t["question"].strip(), t["join"].strip(), str(t["version"]), t["owner"], folder, reads, tuple(steps),
                    tuple(t.get("limits", [])))


def folders(base: str = TEMPLATES) -> dict:
    out = {}
    if not os.path.isdir(base):
        return out
    for d in sorted(os.listdir(base)):
        path = os.path.join(base, d)
        if os.path.exists(os.path.join(path, "template.toml")):
            out[d] = path
    return out


def by_name(name: str, base: str = TEMPLATES) -> Template:
    f = folders(base)
    if name not in f:
        raise KeyError(f"no scan named {name!r}; have {sorted(f)}")
    t = load(f[name])
    if t.name != name:
        raise ValueError(f"{f[name]}: the folder is {name!r} but template.toml says {t.name!r}")
    return t
