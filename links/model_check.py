"""Every name a text reader's model gave is printed in its own document, or its row is set aside (Arthur, 1 November
2026: "are you comfortable that we arent polluting the graph?" ... "do those things").

A model's name enters `links.rows` only when the document it cites prints it: the name and the document's text are
normalised the same way as the name pass's (links.sightings.norm: macrons folded, lower case, every run of other than a
letter or digit one space) and the name must occur whole, on word boundaries. Measured read-only before it was built
(60 documents a view): beehive 0.9% not printed, hansard 0.3%, parliament 1.4%, courts 3.2%; what it catches is "Mr
Hall's uncle", "design company", "Ministers Reti", a court's name the document never prints.

`links.model_name_checks` holds one verdict per (view, document, name), so a document's text is opened once, ever; a
refill checks only the pairs it has not seen. A document whose text cannot be opened gives printed NULL and its rows
are set aside under their own reason, never let through.
"""
from __future__ import annotations

import collections

from links import sightings as S
from links.rows import MODEL_VIEWS

DDL = """
CREATE TABLE IF NOT EXISTS {s}.model_name_checks (
    view        text NOT NULL,
    document    text NOT NULL,
    name        text NOT NULL,
    printed     boolean,
    checked_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (view, document, name)
);
"""
LANE = {"beehive_people": "beehive", "hansard_people": "hansard", "court_people": "courts"}
NOT_PRINTED = "a model's name not printed in its document"
NOT_OPENED = "a model's name whose document text was not opened"


def printed(name: str, text_norm: str) -> bool:
    """`name` occurs whole in a text already normalised and padded with a space each side."""
    n = S.norm(name)
    return bool(n) and f" {n} " in text_norm


def text_for(conn, view: str, document: str) -> str:
    if view in LANE:
        return S.text_of(conn, LANE[view], document)
    # parliament_people: a written question or an archived page, by which view holds the document
    t = S.text_of(conn, "parliament-questions", document)
    return t or S.text_of(conn, "parliament-wayback", document)


#: the views whose document text is a column of a published view: fetched for many documents at once (4 November 2026: the
#: one-document lookups of pub.parliament_written_questions, which has no index on `document`, each scanned the view's 1.35
#: million rows, and 63,256 new parliament documents stopped the nightly build at its deadline)
BULK = {"parliament_people": (
    "SELECT document, concat_ws(E'\\n\\n', title, question_text, reply_text) FROM pub.parliament_written_questions "
    "WHERE document = ANY(%s)",
    "SELECT document, text FROM pub.parliament_wayback_pages WHERE document = ANY(%s) AND coalesce(text, '') <> ''")}
BULK_BATCH = 20000


def bulk_texts(conn, view: str, documents: list) -> dict:
    """{document: text} for the documents of a BULK view, a batch of documents per query (the first view holding one
    wins, as text_for reads them)."""
    out = {}
    for sql in BULK.get(view, ()):
        want = [d for d in documents if d not in out]
        for i in range(0, len(want), BULK_BATCH):
            for d, t in conn.execute(sql, (want[i:i + BULK_BATCH],)).fetchall():
                if t and d not in out:
                    out[d] = t
    return out


def check_view(conn, reader, view: str, sql: str, schema: str = "links", log=print) -> dict:
    """Check every (document, name) of `view` (its links.rows source query `sql`) not checked before. Returns counts."""
    assert view in MODEL_VIEWS, view
    conn.execute(DDL.format(s=schema))
    seen = {(d, n) for d, n in conn.execute(f"SELECT document, name FROM {schema}.model_name_checks WHERE view = %s",
                                            (view,)).fetchall()}
    todo = collections.defaultdict(set)
    with reader.cursor(name=f"links_model_check_{view}") as cur:
        cur.itersize = 20000
        cur.execute(sql)
        for r in cur:
            name, document = r[1], r[7]
            if name and document and (document, name) not in seen:
                todo[document].add(name)
    out = {"documents": len(todo), "names": 0, "not_printed": 0, "not_opened": 0}
    rows = []
    pre = bulk_texts(reader, view, sorted(todo)) if view in BULK else {}
    for document, names in todo.items():
        try:
            # a BULK view's document found in neither view has no text: the bulk read looked in both
            text = f" {S.norm(pre.get(document, '') if view in BULK else text_for(reader, view, document))} "
            ok = text.strip() != ""
        except Exception:  # noqa: BLE001 — a document that cannot be opened sets its names aside, never through
            ok = False
        for name in names:
            verdict = printed(name, text) if ok else None
            rows.append((view, document, name, verdict))
            out["names"] += 1
            if verdict is False:
                out["not_printed"] += 1
            elif verdict is None:
                out["not_opened"] += 1
    if rows:
        with conn.cursor() as w, w.copy(f"COPY {schema}.model_name_checks (view, document, name, printed) FROM STDIN") as cp:
            for r in rows:
                cp.write_row(r)
    log(f"links.model_check: {view}: {out}")
    return out


def set_aside(conn, view: str, schema: str = "links") -> dict:
    """{(document, name): reason} for the view's pairs that may not enter links.rows."""
    return {(d, n): (NOT_PRINTED if p is False else NOT_OPENED)
            for d, n, p in conn.execute(f"SELECT document, name, printed FROM {schema}.model_name_checks "
                                        "WHERE view = %s AND printed IS NOT TRUE", (view,)).fetchall()}
