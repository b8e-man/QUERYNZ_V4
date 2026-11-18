"""The news reader's golden sample: choosing the articles (Arthur, 15 November 2026: "you should hand label some,
make your own golden sample do some extraction, then give me some to label and I'll check yours").

    python -m registers.news.gold.sample choose --tranche 1        # writes registers/news/gold/tranche-1.json
    python -m registers.news.gold.sample show ARTICLE_ID            # one article, street addresses masked

Reads the old copy's articles (old_incoming_news_private.articles), newest first, read-only. A tranche is a fixed
list of article ids with the reason each was chosen; the labels (registers/news/gold/labels/) are typed by a person
and never regenerated. `show` masks every street-address shape before the text reaches a session (hard limit 11).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = "old_incoming_news_private.articles"
HOST = r"split_part(regexp_replace(news_url, '^https?://(www\.)?', ''), '/', 1)"
#: a stub that ends at a paywall prompt is never sampled (Arthur, 17 November 2026: two of tranche 2's Newsroom
#: articles were the opening paragraph only, from the old copy collected before the provider had his logins)
PAYWALL = (r"(14-day free trial|free trial now|Subscribe to (continue|read)|subscribers? only|Already a subscriber|"
           r"Premium (content|article)|Sign in to (continue|read)|Unlock this (story|article))")
RECENT = ("post_date > now() - interval '60 days' AND length(text_content) BETWEEN 600 AND 20000"
          f" AND right(text_content, 400) !~* '{PAYWALL}'")

#: articles per site and per hard case. Tranches 1-4 took 2 and 1 (32 articles, up to 17 questions each); from tranche 5
#: more articles and fewer questions each (Arthur, 18 November 2026: "it is important for you to bring me fresh
#: articles"), so 7 and 2 (94 articles, at most questions.PER_ARTICLE each)
PER_SITE, PER_SEED = 7, 2
#: from tranche 6, 140 questions one an article (questions.QUOTA) out of the articles that give a usable tone, so more
#: are read than asked
PER_SITE_6, PER_SEED_6 = 25, 3

#: the commonest news sites of the last sixty days (te reo sites wait for their own session)
SITES = ["scoop.co.nz", "stuff.co.nz", "rnz.co.nz", "odt.co.nz", "1news.co.nz", "nzherald.co.nz", "newsroom.co.nz",
         "businessdesk.co.nz", "interest.co.nz", "farmersweekly.co.nz"]

#: ten for the hard cases the plan names (docs/research/news-reader-plan.md)
SEEDS = [
    ("the-warehouse-company", "text_content ~ 'The Warehouse (Group|Ltd|chief|said|has|is|will|stores?)'"),
    ("warehouse-the-word", "text_content ~* '\\ma warehouse\\M' AND text_content !~ 'The Warehouse'"),
    ("several-chief-executives", "(length(text_content) - length(replace(text_content, 'chief executive', ''))) / 15 >= 3"),
    ("former-and-acting", "text_content ~* '(former|acting|interim|outgoing) (chief executive|chair|ceo|director|minister)'"),
    ("sport", "categories && array['sport', 'Sport', 'sports']"),
    ("entertainment", "categories && array['entertainment', 'Entertainment', 'Culture', 'culture', 'lifestyle']"),
    ("cannot-be-named", "text_content ~* '(cannot be named|name suppression|interim suppression)'"),
    ("hamilton-a-person", "text_content ~ '\\m[A-Z][a-z]+ Hamilton\\M(?! (City|Council|Airport|Gardens|Park|East|West|North|Lake))' AND text_content !~ 'Hamilton (City|Council)'"),
    ("police-release", f"{HOST} = 'police.govt.nz'"),
    ("live-blog", "title ~* '(\\mlive\\M|as it happened)'"),
    ("wire-story", "text_content ~ '(\\(AP\\)|\\mReuters\\M|\\mAAP\\M|Associated Press)'"),
    ("opinion", "categories && array['opinion', 'Opinion', 'comment', 'Comment', 'columnists']"),
]

ADDRESS = re.compile(
    r"\b\d{1,5}[A-Za-z]?(?:/\d{1,5})?\s+(?:[A-Z][a-zA-Zāēīōū'’-]+\s+){1,3}"
    r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Terrace|Tce|Lane|Ln|Way|Close|Grove|Parade|"
    r"Highway|Hwy|Quay|Boulevard|Blvd|Court|Ct|Rise|View|Heights|Square|Esplanade|Mews)\b\.?")


def masked(text: str) -> str:
    """Every street-address shape replaced, so no home address is printed into a session."""
    return ADDRESS.sub("[street address]", text or "")


def _conn():
    from support import db
    c = db.connect()
    c.execute("SET default_transaction_read_only = on")
    return c


def _order(seed: str) -> str:
    """A fixed, reproducible order within a bucket: by a hash of the id and the tranche's seed, among the newest."""
    return f"md5(id::text || '{seed}')"


def choose(tranche: int) -> list:
    picked, seen = [], set()
    for earlier in range(1, tranche):           # never an article an earlier tranche already holds
        f = HERE / f"tranche-{earlier}.json"
        if f.exists():
            seen |= {a["id"] for a in json.loads(f.read_text())["articles"]}
    import difflib
    with _conn() as c:
        # from tranche 6, nor one whose title or opening is near one already held (Arthur, 18 November 2026: "some of
        # these articles are the same again": a newsletter rerun under a new title, a weekly round-up in new numbers)
        held = []
        if tranche >= 6 and seen:
            held = [(t or "", o or "") for t, o in c.execute(
                f"SELECT lower(title), left(regexp_replace(coalesce(text_content,''),'\\s+',' ','g'), 300) FROM {T} "
                "WHERE id::text = ANY(%s)", (list(seen),)).fetchall()]

        def near(title, opening):
            return any(difflib.SequenceMatcher(None, title, t).ratio() > 0.6
                       or difflib.SequenceMatcher(None, opening, o).ratio() > 0.45 for t, o in held)

        def take(where, n, why):
            rows = c.execute(f"SELECT id::text, {HOST}, title, post_date, "
                             f"left(regexp_replace(coalesce(text_content,''),'\\s+',' ','g'), 300) FROM {T} WHERE {RECENT} AND {where} "
                             f"ORDER BY {_order(f't{tranche}-{why}')} LIMIT {n * 4}").fetchall()
            got = 0
            for r in rows:
                if r[0] in seen or got == n:
                    continue
                if tranche >= 6:
                    if near((r[2] or "").lower(), r[4] or ""):
                        continue
                    held.append(((r[2] or "").lower(), r[4] or ""))
                seen.add(r[0]); got += 1
                picked.append({"id": r[0], "site": r[1], "title": r[2], "post_date": r[3].isoformat() if r[3] else None,
                               "why": why})
            if got < n:
                print(f"short: {why} {got} of {n}", file=sys.stderr)
        for s in SITES:
            take(f"{HOST} = '{s}'", (PER_SITE_6 if tranche >= 6 else PER_SITE if tranche >= 5 else 2), f"site:{s}")
        news = " OR ".join(f"{HOST} = '{x}'" for x in SITES + ["thespinoff.co.nz", "sunlive.co.nz", "pmn.co.nz", "times.co.nz", "police.govt.nz"])
        for why, where in SEEDS:
            take(f"({where}) AND ({news})", (PER_SEED_6 if tranche >= 6 else PER_SEED if tranche >= 5 else 1), f"case:{why}")
    out = {"tranche": tranche, "source": T, "chosen_by": "registers.news.gold.sample", "articles": picked}
    (HERE / f"tranche-{tranche}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    return picked


def show(article_id: str) -> str:
    with _conn() as c:
        r = c.execute(f"SELECT title, author, news_url, categories, post_date, text_content FROM {T} WHERE id = %s",
                      (article_id,)).fetchone()
    if not r:
        return "no such article"
    title, author, url, cats, date, text = r
    sha = hashlib.sha256((text or "").encode()).hexdigest()
    return (f"id {article_id}\ntitle {masked(title)}\nauthor {author}\nurl {url}\ncategories {cats}\ndate {date}\n"
            f"text_sha256 {sha}\nchars {len(text or '')}\n---\n{masked(text)}")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["choose"]:
        n = int(argv[argv.index("--tranche") + 1]) if "--tranche" in argv else 1
        for p in choose(n):
            print(p["why"], p["site"], p["post_date"], (p["title"] or "")[:80])
        return 0
    if argv[:1] == ["show"] and len(argv) == 2:
        print(show(argv[1]))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
