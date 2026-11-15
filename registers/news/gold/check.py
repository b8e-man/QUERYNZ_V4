"""Hold the golden labels to the text: every span a label types must be in the article, character for character.

    python -m registers.news.gold.check [--tranche 1]

The same check the reader's output faces (plan step 4). Text is compared after the masking `sample.show` applies,
so a label never carries what a session never saw. Prints each span that is not found, and a count.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from registers.news.gold.sample import HERE, T, _conn, masked


def spans(d: dict):
    """(where, text) for every value a label says is verbatim."""
    for k, e in d["entities"].items():
        for f in e["forms"]:
            yield f"entity {k}", f
    for r in d["roles"]:
        if r["bound_by"] != "unbound" or r["role"]:
            yield "role", r["role"]
    for x in d["descriptors"]:
        yield "descriptor", x["text"]
    for q in d["quotes"]:
        yield "quote", q["text"]
        if q.get("speaker_as_printed"):
            yield "speaker", q["speaker_as_printed"]
    for n in d["numbers"]:
        yield "number", n["text"]
    for s in d["sentiment"]:
        yield "sentiment", s["evidence"]
    for r in d["relations"]:
        yield "relation", r["says"]


def norm(s: str) -> str:
    return " ".join((s or "").split())


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    labels = sorted((HERE / "labels").glob("*.json"))
    missing = total = 0
    with _conn() as c:
        for f in labels:
            d = json.loads(f.read_text())
            row = c.execute(f"SELECT title, author, text_content FROM {T} WHERE id = %s", (d["id"],)).fetchone()
            text = norm(masked("\n".join(x or "" for x in row)))
            for where, s in spans(d):
                total += 1
                if norm(s) not in text:
                    missing += 1
                    print(f"{f.stem[:8]} {where}: {s[:90]!r}")
    print(f"{len(labels)} labels, {total} spans, {missing} not found in their article")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
