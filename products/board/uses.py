"""The use cases tab (ruling 87): the plan's table of use cases, read at
render time from the copy of the repository the board runs from (found from
this file, so the release copy shows the release copy's plan), each row with
what the data holds for it today:

- the templates built for it, on their shape (ruling 89): the subject
  report's `products/templates/*/template.toml` (step 5.2) and the scan's
  `products/scan/templates/*/template.toml`, read as data files from disk,
  never imported (the one-way rule binds imports and queries of another
  module's inside; a product's published files are read as text). A
  template names its use case in `use_case` where it carries one, else in
  its `owner` line, "(use case 9)", else in its folder's leading two
  digits, `02-legal`;
- the use case's interface, opened in a new browser tab (ruling 89): the
  report server's form for its template, the scan server's page for each
  of its templates, the site preview for Follow the Money; one with none
  says what holds it (`HELD`). The servers' addresses are `bases`, the one
  place their ports and the hostname rule live;
- the registers the plan's reference names for it (`not-held.md`, the one
  reference table with a use-case column), each held or not held by whether
  a published view of the board's register for it is present in `pub`
  (`catalogue.REFERENCE_REGISTERS` maps the reference's words to registers).

Pure but for `read_*`, which read files; nothing is written."""
from __future__ import annotations

import glob
import os
import re
import socket
import tomllib
import urllib.parse

from products.board import catalogue as cat

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TABLE = os.path.join("docs", "plan", "reference", "registers-and-use-cases", "the-sixteen-use-cases.md")
NOT_HELD = os.path.join("docs", "plan", "reference", "registers-and-use-cases", "not-held.md")
#: the templates on disk by shape, read as files: (glob, shape as the tab says it, the server that opens it)
TEMPLATES = (
    (os.path.join("products", "templates", "*", "template.toml"), "Subject report", "report"),
    (os.path.join("products", "scan", "templates", "*", "template.toml"), "Register scan", "scan"),
)
#: ruling 89: the server each interface is on, the environment name that overrides its address, and its port; with
#: no override the host is the board request's own Host header, so a reader on another box reaches it (never 127.0.0.1)
SERVERS = {"report": ("QV4_REPORT_URL", 8440), "scan": ("QV4_SCAN_URL", 8450), "site": ("QV4_SITE_URL", 8430)}
#: a use case whose shape is a published site opens the site preview
SITE_SHAPE = "Published site"
#: a use case with no interface yet, and what holds it (rulings 79 and 63)
HELD = {"15": "held: ruling 79 (no document reading until node1 returns)",
        "16": "held: ruling 63 (step 7)", "17": "held: ruling 63 (step 7)"}
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


def use_case_of(t: dict, folder: str = "") -> tuple:
    """The use case numbers a template names: its `use_case` field, else its
    owner line's "(use case N)", else its folder's leading two digits."""
    x = t.get("use_case")
    if isinstance(x, int):
        return (str(x),)
    if isinstance(x, (list, tuple)):
        return tuple(str(n) for n in x)
    owned = tuple(re.findall(r"use case (\d+)", str(t.get("owner") or "")))
    if owned:
        return owned
    m = re.match(r"(\d\d)-", os.path.basename(folder or ""))
    return (str(int(m.group(1))),) if m else ()


def read_text(rel: str, repo: str = REPO):
    try:
        with open(os.path.join(repo, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def read_templates(repo: str = REPO) -> list:
    """[{'name', 'title', 'uses': (numbers…), 'shape', 'server', 'folder'}] for every
    template on disk, the subject report's then the scan's, each by folder."""
    out = []
    for pattern, shape, server in TEMPLATES:
        for p in sorted(glob.glob(os.path.join(repo, pattern))):
            folder = os.path.dirname(p)
            try:
                with open(p, "rb") as f:
                    t = tomllib.load(f)
            except (OSError, tomllib.TOMLDecodeError):
                continue
            out.append({"name": t.get("name") or os.path.basename(folder), "title": t.get("title") or "",
                        "uses": use_case_of(t, folder), "shape": shape, "server": server,
                        "folder": os.path.relpath(folder, repo)})
    return out


def bases(host: str = "", env=None) -> dict:
    """{server: base address} (ruling 89): the environment's `QV4_*_URL` where
    set, else http://<the request's own host>:<port>."""
    env = os.environ if env is None else env
    name = (host or "").strip()
    name = name[:name.find("]") + 1] if name.startswith("[") else name.partition(":")[0]   # the port off; an IPv6 literal kept whole
    name = name or socket.gethostname()
    return {k: (env.get(var) or f"http://{name}:{port}").rstrip("/") for k, (var, port) in SERVERS.items()}


def href_of(t: dict, base: dict) -> str:
    """The address that opens a template's interface: the report's form with
    the template chosen (`/?template=`), or the scan's page (`/scan/<name>`)."""
    q = urllib.parse.quote(t["name"], safe="")
    return f"{base['report']}/?template={q}" if t["server"] == "report" else f"{base['scan']}/scan/{q}"


def interface(uc: dict, base: dict) -> tuple:
    """(links [(label, href)], what holds it): its templates' pages in order,
    the site preview for a published site, else the hold."""
    if uc["number"] in HELD:
        return [], HELD[uc["number"]]
    if uc["shape"].startswith(SITE_SHAPE):
        return [("site preview", base["site"] + "/")], ""
    links = [(t["name"], href_of(t, base)) for t in uc["templates"]]
    return links, "" if links else "no interface built"


def registers_for(source: str) -> tuple:
    for words, regs in cat.REFERENCE_REGISTERS.items():
        if source.startswith(words):
            return regs
    return ()


def held_of(registers: tuple, held_views: set) -> list:
    """[(register, plain name, held?)] for the board's registers named."""
    plain = dict(cat.REGISTERS) | dict(cat.NOT_HELD)
    return [(r, plain.get(r, r), any(v.name in held_views for v in cat.views_of(r))) for r in registers]


def rows(table: str, not_held: str, templates: list, held_views: set, base: dict = None) -> list:
    """The tab's rows: the plan's columns, then 'templates', 'registers'
    [(source, [(register, plain, held)])], and 'links' [(label, href)] with
    'held', what holds a use case with none, in the plan's order."""
    sources = parse_not_held(not_held or "")
    base = base or bases()
    out = []
    for uc in parse_table(table):
        n = uc["number"]
        r = {**uc, "templates": [t for t in templates if n in t["uses"]],
             "registers": [(s, held_of(registers_for(s), held_views)) for s, nums in sources if n in nums]}
        r["links"], r["held"] = interface(r, base)
        out.append(r)
    return out
