"""The reading of one batch (step 7.2): named stages, each with its count; every item set aside says its stage and reason.

A Papers Past item is its article: the id the URL carries (`/newspapers/EP19040730.2.115.3`: paper code EP, issue date
30 July 1904, the article's place in the issue) is its key, and the paper and the date come from it. The title and the
whole text are kept as the dump holds them; nothing is read out of the text: no person, no claim, no name (hard limit 17).

    read(rows, batch, document, held=set())  -> Read(items, stages, catches)

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


def read(rows, batch: int, document: str, held=frozenset()) -> Read:
    out = Read()
    seen_reason = set()

    def aside(stage, r, reason):
        example = None
        if (stage, reason) not in seen_reason:      # the first failing example of each reason, kept whole
            seen_reason.add((stage, reason))
            example = {k: v for k, v in r.items() if not k.startswith("_")}
        out.catches.append((stage, str(r.get("id")), f"scraper_results line {r['_line']}", reason, example))

    rows = list(rows)
    n_in = len(rows)
    out.stages.append(("in", n_in, n_in, 0))

    stage, keep = "article id", []
    for r in rows:
        a = article_of(r.get("news_url"))
        if a is None:
            aside(stage, r, "the URL is not a Papers Past article id")
        else:
            keep.append((r, a))
    out.stages.append((stage, n_in, len(keep), n_in - len(keep)))

    stage, before, kept = "text", len(keep), []
    for r, a in keep:
        if not (r.get("text_content") or "").strip():
            aside(stage, r, f"the archive holds no text for it ({r.get('pipeline_status') or 'no status'})")
        else:
            kept.append((r, a))
    out.stages.append((stage, before, len(kept), before - len(kept)))

    stage, before, once, keys = "once", len(kept), [], set()
    for r, a in kept:
        if a[0] in keys:
            aside(stage, r, "a second row for an article already taken in this batch")
        else:
            keys.add(a[0])
            once.append((r, a))
    out.stages.append((stage, before, len(once), before - len(once)))

    for r, (key, paper, on) in once:
        text = r["text_content"]
        out.items.append({"key": key, "paper": paper, "published_on": on, "title": r.get("title"), "text": text,
                          "chars": len(text), "url": r["news_url"], "upstream_id": int(r["id"]),
                          "held_in_old": int(r["id"]) in held, "batch": batch, "document": document,
                          "place": f"scraper_results line {r['_line']}", "reader": READER})
    out.stages.append(("landed", len(once), len(out.items), 0))
    set_aside = sum(s[3] for s in out.stages)
    if n_in != len(out.items) + set_aside:
        raise RuntimeError(f"batch {batch} does not reconcile: {n_in} in, {len(out.items)} landed, {set_aside} set aside")
    return out
