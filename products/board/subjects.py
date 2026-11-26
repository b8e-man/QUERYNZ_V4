"""A reading's subjects, as the board shows them (Arthur, 26 November 2026: "we can use the term "subjects" instead of
theme going forward").

Two kinds. The broad subjects are the IPTC Media Topic labels every news reading holds (`article.themes`, the field's
name in the readings already made). The specific subjects are what the article is about, named, each with its kind
(an event, a technology, a product or work, a law or bill, an issue or programme): the `subjects` section a reader from
`registers.news.read 6` on holds (docs/research/curation-plan.md, decision 5), each {name, kind, words, inferred}.
"""
from __future__ import annotations


def broad(got: dict) -> list[str]:
    th = ((got or {}).get("article") or {}).get("themes") or []
    return [str(x) for x in th if x]


def specific(got: dict) -> list[dict]:
    out = []
    for s in (got or {}).get("subjects") or []:
        if isinstance(s, dict) and (s.get("name") or "").strip():
            out.append({"name": s["name"].strip(), "kind": s.get("kind") or "", "words": s.get("words") or "",
                        "inferred": bool(s.get("inferred"))})
        elif isinstance(s, str) and s.strip():
            out.append({"name": s.strip(), "kind": "", "words": "", "inferred": False})
    return out


def names(got: dict) -> list[str]:
    """Every subject's name, the specific first, each once (case folded)."""
    seen, out = set(), []
    for n in [s["name"] for s in specific(got)] + broad(got):
        if n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out
