"""The reading of one batch (step 7.2): named stages, each with its count; every item set aside says its stage and reason.

A Papers Past item is its article: the id the URL carries (`/newspapers/EP19040730.2.115.3`: paper code EP, issue date
30 July 1904, the article's place in the issue) is its key, and the paper and the date come from it. The title and the
whole text are kept as the dump holds them; nothing is read out of the text: no person, no claim, no name (hard limit 17).

    read(rows, batch, document, held=set())  -> Read(items, stages, catches)
    Reading(batch, document).take(row) ... .finish()    the same, one row at a time

Stages, in order: `in` (the rows the capture took), `article id` (the URL is a Papers Past article id), `text` (the dump
holds text for it; the archive's own MIGRATION_ERROR rows hold none), `once` (one item per article id), `landed`.
"""
import datetime as dt
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

READER = "registers.papers_past.read 1"
ARTICLE = re.compile(r"^/newspapers/([A-Za-z]+)(\d{8})((?:\.\d+)+)/?$")


@dataclass
class Read:
    items: list = field(default_factory=list)
    stages: list = field(default_factory=list)    # (stage, in, out, set aside)
    catches: list = field(default_factory=list)   # (stage, item, place, reason, example or None)


def article_of(url: str):
    """(key, paper, date or None) for a Papers Past article URL, or None."""
    m = ARTICLE.match(urlsplit(url or "").path)
    if not m:
        return None
    paper, ymd, rest = m.groups()
    try:
        on = dt.date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:]))
    except ValueError:
        on = None
    return f"{paper}{ymd}{rest}", paper, on


class Reading:
    """The stages applied one row at a time, so a batch of a million is never held whole: `take(row)` returns the item
    or None (set aside, with its catch); `finish()` closes the stage counts and checks the batch reconciles."""

    def __init__(self, batch: int, document: str, held=frozenset(), keep_text: bool = True, dedupe: bool = True,
                 seen_reasons=()):
        """dedupe=False leaves the `once` stage to the caller (the streaming load lets the catalogue's key refuse a
        second row, so no set of every key is held); seen_reasons: the reasons whose first example is already kept."""
        self.batch, self.document, self.held, self.keep_text, self.dedupe = batch, document, held, keep_text, dedupe
        self.out = Read()
        self.n = {"in": 0, "article id": 0, "text": 0, "once": 0}
        self.n_catches = 0
        self.keys, self._seen = set(), set(seen_reasons)

    def _aside(self, stage, r, reason):
        example = None
        if (stage, reason) not in self._seen:          # the first failing example of each reason, kept whole
            self._seen.add((stage, reason))
            example = {k: v for k, v in r.items() if not k.startswith("_")}
        self.out.catches.append((stage, str(r.get("id")), f"scraper_results line {r['_line']}", reason, example))
        self.n_catches += 1

    def take(self, r):
        self.n["in"] += 1
        a = article_of(r.get("news_url"))
        if a is None:
            return self._aside("article id", r, "the URL is not a Papers Past article id")
        self.n["article id"] += 1
        if not (r.get("text_content") or "").strip():
            return self._aside("text", r, f"the archive holds no text for it ({r.get('pipeline_status') or 'no status'})")
        self.n["text"] += 1
        key, paper, on = a
        if self.dedupe:
            if key in self.keys:
                return self._aside("once", r, "a second row for an article already taken in this batch")
            self.keys.add(key)
        self.n["once"] += 1
        text = r["text_content"]
        it = {"key": key, "paper": paper, "published_on": on, "title": r.get("title"), "text": text,
              "chars": len(text), "url": r["news_url"], "upstream_id": int(r["id"]),
              "held_in_old": int(r["id"]) in self.held, "batch": self.batch, "document": self.document,
              "place": f"scraper_results line {r['_line']}", "line": r["_line"], "reader": READER}
        if self.keep_text:
            self.out.items.append(it)
        return it

    def drain(self) -> list:
        """The catches since the last drain, forgotten here (a chunk's, for its COPY)."""
        out, self.out.catches = self.out.catches, []
        return out

    def finish(self) -> Read:
        n = self.n
        self.out.stages = [("in", n["in"], n["in"], 0),
                           ("article id", n["in"], n["article id"], n["in"] - n["article id"]),
                           ("text", n["article id"], n["text"], n["article id"] - n["text"]),
                           ("once", n["text"], n["once"], n["text"] - n["once"]),
                           ("landed", n["once"], n["once"], 0)]
        set_aside = sum(s[3] for s in self.out.stages)
        if n["in"] != n["once"] + set_aside or self.n_catches != set_aside:
            raise RuntimeError(f"batch {self.batch} does not reconcile: {n['in']} in, {n['once']} landed, "
                               f"{set_aside} set aside, {self.n_catches} catches")
        return self.out


def read(rows, batch: int, document: str, held=frozenset()) -> Read:
    r = Reading(batch, document, held)
    for row in rows:
        r.take(row)
    return r.finish()
