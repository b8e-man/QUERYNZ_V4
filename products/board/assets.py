"""The board's own files under /static/ (ruling 100): the vendored graph
library at pinned versions (static/README.md records where each came from,
its version and its sha256, its licence file beside it) and the board's own
script. Served by the board itself from its own folder, from a fixed list
and nothing else, so the page never asks anything off the box (hard limit
13; hard limit 10's spirit). Each address carries its file's hash, so the
long cache header never serves a stale file after a release."""
from __future__ import annotations

import functools
import hashlib
import os
import re

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
JS = "text/javascript; charset=utf-8"
TEXT = "text/plain; charset=utf-8"
#: every file /static/ answers for, with its content type; any other name is a 404
FILES = {
    "cola.min.js": JS,                  # WebCola 3.4.0, the force layout
    "webcola-name.js": JS,              # the board's: WebCola under the name cytoscape-cola looks for
    "cytoscape.min.js": JS,             # Cytoscape 3.34.0
    "cytoscape-cola.js": JS,            # cytoscape-cola 2.5.1
    "graph.js": JS,                     # the board's: the canvas beside the results (rulings 100, 108, 111)
    "chat.js": JS,                      # the board's: the chat pane's thread and question box (ruling 122)
    "table.js": JS,                     # the board's: a register table's row height and column widths (ruling 117 (3))
    "LICENSE.cytoscape": TEXT,
    "LICENSE.cytoscape-cola": TEXT,
    "LICENSE.webcola": TEXT,
}
#: the graph tab's scripts, in load order
SCRIPTS = ("cola.min.js", "webcola-name.js", "cytoscape.min.js", "cytoscape-cola.js", "graph.js")
CACHE = "public, max-age=31536000, immutable"


def read(name: str):
    """(bytes, content type) of a listed file, or None: never a path, never a listing."""
    if name not in FILES:
        return None
    with open(os.path.join(DIR, name), "rb") as f:
        return f.read(), FILES[name]


@functools.lru_cache(maxsize=None)
def version(name: str) -> str:
    return hashlib.sha256(read(name)[0]).hexdigest()[:12]


def url(name: str) -> str:
    return f"/static/{name}?v={version(name)}"


def tags() -> str:
    """The graph tab's script tags, in load order."""
    return "".join(f'<script src="{url(n)}"></script>' for n in SCRIPTS)


#: an address in a page or a script that is never asked for: the SVG namespace, a name and not a request
NAMESPACES = ("http://www.w3.org/2000/svg",)
_ADDRESS = re.compile(r"(?:https?:)?//[A-Za-z0-9.-]+\.[A-Za-z]{2,}[^\s\"'<>)]*|https?://[^\s\"'<>)]+")
_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def addresses(text: str, comments: bool = False) -> list:
    """Every absolute address in `text` (http, https, or protocol-relative)
    but the SVG namespace; `comments` false skips those inside a /* */
    comment, where the vendored files name their licences' homes."""
    spans = [] if comments else [m.span() for m in _COMMENT.finditer(text)]
    out = []
    for m in _ADDRESS.finditer(text):
        a = m.group(0)
        if a.startswith("//") and m.start() > 0 and text[m.start() - 1] in ":/":
            continue
        if any(a.startswith(n) for n in NAMESPACES) or any(s <= m.start() < e for s, e in spans):
            continue
        out.append(a)
    return out
