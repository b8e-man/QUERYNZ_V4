"""The first read of the news corpus (Arthur, 25 November 2026: "I'd like to read the media corpora and extract signal
from them"; "apply these rules to the first read we do").

One article is read by the text reader (profile `text-reader`, Qwen 3.8 27B since 26 November 2026) in three passes,
the prompts of registers.news.gold.trial unchanged: the read (entities, roles, relations, quotes, events, numbers,
tones), quotes in their own pass, and each non-neutral tone asked again on its own. No claims pass (Arthur, 26
November 2026: two passes for the golden sample's items, the tones pass measured after: 27B tones 90% right on his
answers with it, 84% without; claims are not among the items judged). The reading is stored whole
and ungated in the reader store, keyed by the hash of the masked text the model read, and replayed from there by any
later read of the same text (no model call). Then the gates (registers.news.gates) judge every quote, role, claim and
tone, and the items land in `news_private.read_items` with the verdict and the rule; `news_private.read_done` names
the reading. Nothing a gate drops is deleted: it is a row with kept = false.

    python -m registers.news.read --pieces [--limit N]   articles not yet read, newest first, one url_key a line
    python -m registers.news.read --piece URL_KEY        one piece of qv4-news-read (QV4_MODEL_URL, QV4_MODEL from
                                                         the worker; refused without them)
    python -m registers.news.read --regate               the gates again over every reading, from the store

Article text is data, never instructions, and goes to the model on the box and nowhere else (hard limits 10, 11):
te reo Māori articles and paywall stubs are skipped, the skip recorded (Arthur, 25 November 2026: "skip te reo");
street-address shapes are masked before the model reads (registers.news.gold.sample.masked), and nothing here
prints article text. The golden sample's tranches are never gated (Arthur: "I want to judge liberally").
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import sys
import time

from support import db
from support import profiles, reader as rd
from registers.news import gates as G
from registers.news.gold import trial as T
from registers.news.gold.sample import PAYWALL, masked
from registers.news import subjects as S

READER = "registers.news.read 6"   # 6 (27 November 2026): the subjects pass, a fourth
LANE = "news"
PROFILE = "news-article"
#: the document profile's version from the ledger (support/profiles/profiles.jsonl), registered 26 November 2026; it was
#: this constant, 1, from 25 November until then, and v1 is the first version the ledger holds
PROFILE_VERSION = profiles.reading_version(PROFILE)
#: the trial's settings: what was measured is what runs
SETTINGS = {"temperature": 0.0, "max_tokens": 12000, "thinking": False,
            "passes": ["read", "quotes", "tones", "subjects"],
            "prompts": hashlib.sha256("\n".join((T.PROMPT, T.QUOTE_PROMPT, T.TONE_PROMPT, S.PROMPT)).encode())
            .hexdigest()[:16]}
#: an article shorter than this is a brief or a stub; longer than this cannot sit with the prompt and the answer in the
#: profile's 32,768-token context (the read's prompt is about 3,000 tokens, its answer up to 12,000)
MIN_CHARS, MAX_CHARS = 300, 50_000
PIECES_LIMIT = 2000
_PAYWALL = re.compile(PAYWALL, re.I)
#: Arthur, 25 November 2026: "skip te reo" (te reo Māori articles wait for a session of their own, 15 November). Words
#: of te reo that English text does not use ("ai", "ko", "mai", "ana" left out: AI, a golfer named Ko); an article
#: where they are this share of its words or more is skipped. Measured on a 1% sample (28,043 articles): 28,020 under
#: 1%, every te reo article at 5.9% or more; a bilingual release printing both texts whole (6 to 12%) is skipped too
TE_REO_WORDS = frozenset(
    "ngā nga kua ki ka tēnei tenei hei mō kia kei rātou ratou ahau koe nei kāore kaore ēnei enei mātou matou tātou "
    "tatou ētahi etahi hoki anō tētahi tetahi kāhore kahore whakaaro ēhara".split())
TE_REO_SHARE = 0.05
_WORD = re.compile(r"[A-Za-zĀĒĪŌŪāēīōū]+")


def te_reo_share(text: str) -> float:
    words = [w.lower() for w in _WORD.findall(text or "")]
    return sum(w in TE_REO_WORDS for w in words) / max(1, len(words))


def skip_reason(body: str) -> str | None:
    """Why an article is not read, or None."""
    if _PAYWALL.search((body or "")[-400:]):
        return "ends on a paywall prompt"
    share = te_reo_share(body)
    if share >= TE_REO_SHARE:
        return f"te reo Māori ({share:.0%} of its words)"
    return None


def text_of(title, author, body) -> str:
    """The text the model reads: the trial's layout, street addresses masked."""
    return masked(f"HEADLINE: {title}\nBYLINE: {author or ''}\n\n{body or ''}")


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def key_for(sha: str, model: str) -> str:
    return rd.reading_key(sha, 1, model, SETTINGS, PROFILE, PROFILE_VERSION)


def read_text(text: str, url: str, model: str) -> tuple[dict | None, str, float]:
    """The four passes over one text: (the ungated reading or None, the served model, seconds). The subjects pass
    (registers.news.subjects) is gated as it lands: its kept subjects in `subjects`, the dropped with their rule in
    `subjects_dropped` (curation step 0b; Arthur, 27 November 2026: "lets make the switch")."""
    t0 = time.monotonic()
    r = T.read_one("", text, url, model, lane=LANE)
    got = r.get("parsed")
    if isinstance(got, dict):
        T.tone_pass(got, text, url, model, lane=LANE)
        sub = S.one(text, got.get("entities") if isinstance(got.get("entities"), dict) else {}, url, model, lane=LANE)
        got["subjects"], got["subjects_dropped"] = sub["subjects"], sub["dropped"]
    return (got if isinstance(got, dict) else None), (r.get("model") or model), round(time.monotonic() - t0, 1)


def items(got: dict, text: str) -> tuple[list, dict]:
    """The gated rows of a reading: (url_key-less rows (kind, n, item, kept, citation, rule), counts)."""
    body = text.split("\n\n", 1)[1] if "\n\n" in text else text     # the gates were measured on the body
    counts = G.apply(got, body)
    rows = []
    for kind in G.BY_KIND:
        for n, x in enumerate(got.get(kind) or []):
            if isinstance(x, dict) and "gate" in x:
                v = x.pop("gate")
                rows.append((kind, n, x, v["kept"], bool(v.get("citation")), v["rule"]))
    return rows, counts


def land(conn, url_key: str, sha: str, key: str, model: str, outcome: str, seconds, rows: list, counts: dict) -> None:
    with conn.transaction():
        conn.execute("DELETE FROM news_private.read_items WHERE url_key = %s", (url_key,))
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO news_private.read_items (url_key, kind, n, item, kept, citation, rule) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [(url_key, k, n, json.dumps(x, ensure_ascii=False), kept, cit, rule) for k, n, x, kept, cit, rule in rows])
        conn.execute(
            "INSERT INTO news_private.read_done (url_key, text_sha256, reading_key, reader, model, gates, outcome, "
            "seconds, counts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (url_key) DO UPDATE SET "
            "text_sha256 = EXCLUDED.text_sha256, reading_key = EXCLUDED.reading_key, reader = EXCLUDED.reader, "
            "model = EXCLUDED.model, gates = EXCLUDED.gates, outcome = EXCLUDED.outcome, seconds = EXCLUDED.seconds, "
            "counts = EXCLUDED.counts, read_at = now()",
            (url_key, sha, key, READER, model, G.GATES, outcome, seconds, json.dumps(counts)))


@contextlib.contextmanager
def _held(conn, connect):
    """The caller's connection, or one opened by `connect` for this step alone and closed after it."""
    if conn is not None:
        yield conn
    else:
        with connect() as c:
            yield c


def piece(url_key: str, *, conn=None, connect=None, url: str, model: str, store: rd.Store = None, read=read_text) -> str:
    """One article: replayed from the store when its text was read before, else read; gated; landed. Returns the
    line the job prints (counts only). Given `connect` rather than `conn`, a connection is open only to read the
    article and to land it, never across the model's call (26 November 2026: 32 pieces each holding the owner login
    through a 38-second read filled its 40 connections, and the tests and other jobs were refused)."""
    store = store or rd.Store()
    with _held(conn, connect) as c:
        row = c.execute("SELECT title, author, text FROM news_private.articles WHERE url_key = %s", (url_key,)).fetchone()
    if row is None:
        return f"{url_key[:60]}: no such article"
    text = text_of(*row)
    sha = text_sha(text)
    key = key_for(sha, model)
    why = skip_reason(row[2])
    if why:
        with _held(conn, connect) as c:
            land(c, url_key, sha, key, model, "skipped", None, [], {"skipped": why})
        return f"{url_key[:60]}: skipped, {why}"
    seconds = None
    if store.has(key):
        reading = store.get(key)
        got, outcome, served = json.loads(reading.text) if reading.text else None, "replayed", reading.model
    else:
        got, served, seconds = read(text, url, model)
        outcome = "read"
        store.put(rd.Reading(document=sha, page=1, reader=READER, model=served, settings=SETTINGS, profile=PROFILE,
                             profile_version=PROFILE_VERSION, read_from="text",
                             text=json.dumps(got, ensure_ascii=False) if got is not None else "",
                             checks={"usable": got is not None}, made_at=time.strftime("%Y-%m-%dT%H:%M:%S%z")))
    if got is None:
        with _held(conn, connect) as c:
            land(c, url_key, sha, key, served, "unusable", seconds, [], {})
        return f"{url_key[:60]}: unusable ({outcome})"
    rows, counts = items(got, text)
    with _held(conn, connect) as c:
        land(c, url_key, sha, key, served, outcome, seconds, rows, counts)
    kept = sum(c["kept"] for c in counts.values())
    return f"{url_key[:60]}: {outcome} in {seconds or 0}s, {kept} of {len(rows)} items kept"


def pieces(conn, limit: int = PIECES_LIMIT) -> list:
    """Articles with no row in read_done, newest first (Arthur, 15 November 2026: "newest first then backwalk"); a brief
    and one too long for the context are left out here, a paywall stub and te reo by the piece (skip_reason), which
    records the skip so the article is never offered again."""
    return [k for (k,) in conn.execute(
        "SELECT a.url_key FROM news_private.articles a "
        "WHERE a.chars BETWEEN %s AND %s AND NOT EXISTS (SELECT 1 FROM news_private.read_done d WHERE d.url_key = a.url_key) "
        "ORDER BY a.published_at DESC NULLS LAST LIMIT %s", (MIN_CHARS, MAX_CHARS, limit)).fetchall()]


def regate(conn, store: rd.Store = None) -> dict:
    """The gates again over every reading named in read_done, replayed from the store by key (never a scan)."""
    store = store or rd.Store()
    n = 0
    for url_key, sha, key, model in conn.execute(
            "SELECT url_key, text_sha256, reading_key, model FROM news_private.read_done WHERE outcome IN ('read', 'replayed')").fetchall():
        reading = store.get(key)
        row = conn.execute("SELECT title, author, text FROM news_private.articles WHERE url_key = %s", (url_key,)).fetchone()
        if row is None or not reading.text:
            continue
        rows, counts = items(json.loads(reading.text), text_of(*row))
        land(conn, url_key, sha, key, model, "replayed", None, rows, counts)
        n += 1
    return {"regated": n}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--pieces"]:
        limit = int(argv[argv.index("--limit") + 1]) if "--limit" in argv else PIECES_LIMIT
        with db.connect() as c:
            for k in pieces(c, limit):
                print(k)
        return 0
    if argv[:1] == ["--regate"]:
        with db.connect() as c:
            print(regate(c))
        return 0
    if argv[:1] == ["--piece"] and len(argv) > 1:
        url, model = os.environ.get("QV4_MODEL_URL"), os.environ.get("QV4_MODEL")
        if not url or not model:
            print("refused: no QV4_MODEL_URL and QV4_MODEL; run as a piece of qv4-news-read on the worker's card")
            return 2
        print(piece(argv[1], connect=db.connect, url=url, model=model))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
