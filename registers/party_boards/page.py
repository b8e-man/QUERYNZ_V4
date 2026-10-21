"""A captured page as lines, with the markup each line sits in. No reading
happens here: this is the text layer of an HTML document, as the profile's
markers see it.

The bytes are what the capture stored: plain HTML, or HTML compressed with
gzip or zstandard (the Archive replays some pages with their transfer
encoding kept). The Archive's own toolbar, between its BEGIN and END
WAYBACK TOOLBAR comments, is not the party's page and is cut first.

A line is the text of one block of the page (a paragraph, a heading, a
table cell, a list item; a `<br>` ends a line, and `<small>` is a line of
its own, since a page prints a role in it beside a name). Inline markup
does not break a line, so 'S<span>ecretary:</span>' is one word. Each line
keeps the elements open at its first text (tag and classes, outermost
first) and the table row it sits in, so a profile can say "the name is the
h4, the role the span with class x".

    decode(data)     the page's text (str), or raises Undecodable
    lines(data)      [Line]
"""
import gzip
import re
from dataclasses import dataclass
from html.parser import HTMLParser

BLOCK = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "ul", "ol", "td", "th", "tr", "table", "tbody",
         "thead", "section", "article", "header", "footer", "main", "nav", "figure", "figcaption", "blockquote",
         "dt", "dd", "dl", "form", "aside", "small", "address", "pre", "hr", "label", "button", "option", "select"}
SKIP = {"script", "style", "noscript", "template", "svg", "iframe", "textarea"}
VOID = {"br", "img", "hr", "meta", "link", "input", "source", "wbr", "area", "base", "col", "embed", "param", "track"}
_TOOLBAR = re.compile(r"<!--\s*BEGIN WAYBACK TOOLBAR INSERT\s*-->.*?<!--\s*END WAYBACK TOOLBAR INSERT\s*-->", re.S | re.I)
_SPACE = re.compile(r"[\s ​‌‍﻿­]+")
ZSTD = b"\x28\xb5\x2f\xfd"


class Undecodable(ValueError):
    pass


@dataclass(frozen=True)
class Line:
    n: int                  # its place in the page, from 0
    text: str
    chain: tuple            # ((tag, (class, …)), …) outermost first, at the line's first text
    row: int                # the table row it sits in (a running count of <tr>), or -1

    def has(self, mark: str) -> bool:
        """`mark` is 'tag', '.class', 'tag.class' or '!mark' (not inside it):
        true when an element of the line's chain matches."""
        if mark.startswith("!"):
            return not self.has(mark[1:])
        tag, _, cls = mark.partition(".")
        return any((not tag or t == tag) and (not cls or cls in c) for t, c in self.chain)


def decode(data: bytes) -> str:
    try:
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        elif data[:4] == ZSTD:
            from compression import zstd
            data = zstd.decompress(data)
    except Exception as e:  # noqa: BLE001 - a broken stream is a drop-note, said with its reason
        raise Undecodable(f"compressed bytes that do not decompress ({type(e).__name__})") from e
    if b"\x00" in data[:2048]:
        raise Undecodable("binary bytes, not a page")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("cp1252", "replace")
    return _TOOLBAR.sub("", text)


class _Lines(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # [(tag, classes)]
        self.skip = 0
        self.buf = []
        self.buf_chain = None
        self.row = -1
        self.rows = 0
        self.out = []

    def flush(self):
        text = _SPACE.sub(" ", "".join(self.buf)).strip()
        if text:
            self.out.append(Line(len(self.out), text, self.buf_chain, self.row))
        self.buf, self.buf_chain = [], None

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            if tag not in VOID:
                self.skip += 1
            return
        if self.skip:
            return
        if tag in BLOCK or tag == "br":
            self.flush()
        if tag == "tr":
            self.row = self.rows
            self.rows += 1
        if tag in VOID:
            return
        classes = tuple((dict(attrs).get("class") or "").split())
        self.stack.append((tag, classes))

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK or tag == "br":
            if not self.skip:
                self.flush()

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip or tag in VOID:
            return
        if tag in BLOCK:
            self.flush()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if tag == "tr":
            self.row = -1

    def handle_data(self, data):
        if self.skip:
            return
        if self.buf_chain is None and data.strip():
            self.buf_chain = tuple(self.stack)
        if self.buf_chain is not None:
            self.buf.append(data)


def lines(data: bytes) -> list:
    p = _Lines()
    p.feed(decode(data))
    p.close()
    p.flush()
    return p.out
