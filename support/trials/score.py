"""SCORING PER PAGE (plan step 3.7). Pure functions over texts, and a pass
over every stored reading of the page set that writes the scores to the
trial's scratch tables and prints the table per reader and shape.

    python -m support.trials score [--pass P] [--reader R]

The measures, as the plan states them:

- INVENTED TEXT. On a text page used as a key, any run of five or more
  words in the reading that is not on the page fails the page. On a true
  scan there is no page key, so invention is judged three ways: an amount
  no other reader produces that breaks the printed total; a row only one
  family of reader produces; a name matching the form's own printed example
  or instructions (`EXAMPLE_NAMES`).
- LOOPS. The same line three or more times in a row, where the key or the
  other readers show it once, fails the page. Genuinely repeated rows are
  not loops.
- AMOUNTS. Every money amount exact, to the cent: the key page's amounts
  all found, none added.
- TABLES. Row count: lines carrying an amount (the row-number column sits
  outside the border and readers disagree on it, so the count is of amount
  rows, not numbered rows). Column alignment comes from the text reader's
  rows (`rows.py`), the same for every page reader.
- COMPLETENESS. Which parts (A, B, C, D, E, F, G) the page names; a part
  not read is not a part that is zero.
- AGREEMENT. Where two readers from different families agree on a page's
  amounts, and where they differ.

Never prints page text; the stored scores are counts and booleans. A run
of invented words is recorded as its length, not its words.
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict

INVENTED_RUN = 5
LOOP_REPEATS = 3
# a grouped figure (15,000 / 25,000.00), a figure with cents (30.43), or a dollar figure ($30); the engine must not
# start one character early and take "$25" off "$25,000.00", so the dollar form may not be followed by a comma or point
MONEY = re.compile(r"(?<![\w.])\$?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2}|\$\s?\d+(?![\d,.]))(?![\d])")
PART_LABEL = re.compile(r"(?:TOTAL\s+FOR\s+)?PART\s+([A-G])\b", re.I)
TAG = re.compile(r"<[^>]+>")
WORD = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
# the form's own printed examples and instructions, which a reader may copy as if they were a donor
EXAMPLE_NAMES = ("john smith", "jane smith", "j smith", "abc limited", "xyz limited", "example", "sample")


def plain(text: str) -> str:
    """Markup out (HTML readers), entities decoded, whitespace kept per line."""
    t = TAG.sub(" ", text or "")
    t = html.unescape(t)
    return t


def words(text: str) -> list[str]:
    return WORD.findall(plain(text).lower())


def amounts(text: str) -> Counter:
    """Money amounts as cents, counted. A bare integer is not an amount: a
    year, a page number or a row number would swamp the measure."""
    out = Counter()
    for m in MONEY.finditer(plain(text)):
        s = m.group(1).replace("$", "").replace(" ", "").replace(",", "")
        if "." in s:
            whole, cents = s.split(".", 1)
            out[int(whole) * 100 + int(cents[:2].ljust(2, "0"))] += 1
        else:
            out[int(s) * 100] += 1
    return out


def ngrams(ws: list[str], n: int) -> set:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


SUPPORT = 3     # a word is on the page when it sits inside a three-word run the page also carries


def invented_runs(reading: str, key: str, n: int = INVENTED_RUN) -> list[int]:
    """Lengths of the maximal runs of at least n consecutive words in the
    reading that are not on the key page. A word is on the page when it
    sits inside a SUPPORT-word run the page carries (a single common word
    proves nothing; a misread word breaks only the runs through it)."""
    rw, kw = words(reading), words(key)
    if len(rw) < n:
        return []
    have = ngrams(kw, SUPPORT)
    supported = [False] * len(rw)
    for i in range(len(rw) - SUPPORT + 1):
        if tuple(rw[i:i + SUPPORT]) in have:
            for j in range(i, i + SUPPORT):
                supported[j] = True
    runs, run = [], 0
    for s in supported:
        if not s:
            run += 1
        else:
            if run >= n:
                runs.append(run)
            run = 0
    if run >= n:
        runs.append(run)
    return runs


def lines(text: str) -> list[str]:
    return [" ".join(l.split()).lower() for l in plain(text).splitlines() if l.strip()]


def loops(reading: str, key: str = None, others: list[str] = None, repeats: int = LOOP_REPEATS) -> list[int]:
    """Runs of the same line repeated `repeats` or more times in a row, where
    the key (or, with no key, every other reader) shows that line fewer
    times. Returns the run lengths."""
    ls = lines(reading)
    if not ls:
        return []
    refs = [Counter(lines(key))] if key is not None else [Counter(lines(o)) for o in (others or [])]
    out = []
    i = 0
    while i < len(ls):
        j = i
        while j < len(ls) and ls[j] == ls[i]:
            j += 1
        run = j - i
        if run >= repeats and len(ls[i]) >= 3:
            allowed = max([r.get(ls[i], 0) for r in refs] or [0])
            if allowed < run:
                out.append(run)
        i = j
    return out


def parts(text: str) -> set:
    return {m.group(1).upper() for m in PART_LABEL.finditer(plain(text))}


def amount_rows(text: str) -> int:
    return sum(1 for l in plain(text).splitlines() if MONEY.search(l))


def example_names(text: str) -> list[str]:
    t = " ".join(words(text))
    return [n for n in EXAMPLE_NAMES if n in t]


def score_page(reading: str, key: str = None, others: dict = None) -> dict:
    """One reading of one page against its key (a text page) or, with no
    key, against the other readers' readings (`others`: family → text)."""
    others = others or {}
    am = amounts(reading)
    out = {"chars": len(reading or ""), "words": len(words(reading)), "amount_rows": amount_rows(reading),
           "parts_found": "".join(sorted(parts(reading))), "example_names": len(example_names(reading)),
           "amounts_found": sum(am.values())}
    if key is not None:
        runs = invented_runs(reading, key)
        ka = amounts(key)
        missing = sum((ka - am).values())
        extra = sum((am - ka).values())
        out.update(has_key=True, invented_runs=len(runs), invented_longest=max(runs) if runs else 0,
                   invented_fail=bool(runs), loops=len(loops(reading, key)), loop_fail=bool(loops(reading, key)),
                   amounts_key=sum(ka.values()), amounts_missing=missing, amounts_extra=extra,
                   amounts_exact=(missing == 0 and extra == 0), parts_key="".join(sorted(parts(key))),
                   key_rows=amount_rows(key))
    else:
        other_texts = list(others.values())
        lp = loops(reading, None, other_texts)
        union = Counter()
        for t in other_texts:
            union |= amounts(t)
        lone = sum((am - union).values()) if other_texts else None
        out.update(has_key=False, invented_runs=None, invented_longest=None, invented_fail=None,
                   loops=len(lp), loop_fail=bool(lp), amounts_key=None, amounts_missing=None, amounts_extra=None,
                   amounts_exact=None, parts_key=None, key_rows=None, amounts_lone=lone)
    return out


def agreement(a: str, b: str) -> dict:
    """Two readings of one page: the amounts they share and where they differ."""
    aa, ab = amounts(a), amounts(b)
    shared = sum((aa & ab).values())
    return {"shared": shared, "only_a": sum((aa - ab).values()), "only_b": sum((ab - aa).values()),
            "agree": (aa == ab) and bool(aa)}


# ── the pass over stored readings ────────────────────────────────────────────

def stored_readings(sha256: str, root: str = None) -> list[dict]:
    """Every reading of one document in the reader store (as dicts)."""
    from support import reader as rd
    root = root or rd.STORE
    out = []
    for p in sorted(glob.glob(os.path.join(root, sha256[:2], sha256, "*.json"))):
        try:
            with open(p, encoding="utf-8") as f:
                out.append(json.load(f))
        except (OSError, ValueError):
            continue
    return out


SCORE_TABLE = """
CREATE SCHEMA IF NOT EXISTS scratch_trial;
CREATE TABLE IF NOT EXISTS scratch_trial.page_scores (
    key text PRIMARY KEY, document text, page int, reader text, model text, level text, dpi int, pass text,
    shape text, kind text, has_key boolean, chars int, words int, amount_rows int, key_rows int,
    parts_found text, parts_key text, example_names int, invented_runs int, invented_longest int, invented_fail boolean,
    loops int, loop_fail boolean, amounts_key int, amounts_found int, amounts_missing int, amounts_extra int,
    amounts_exact boolean, amounts_lone int, at timestamptz NOT NULL DEFAULT now()
);
GRANT USAGE ON SCHEMA scratch_trial TO qv4_read;
GRANT SELECT ON ALL TABLES IN SCHEMA scratch_trial TO qv4_read;
ALTER DEFAULT PRIVILEGES IN SCHEMA scratch_trial GRANT SELECT ON TABLES TO qv4_read;
"""


def run(pass_name: str = None, reader_name: str = None, conn=None, log=print) -> list[dict]:
    from support.docread import pages as pg
    from support.trials import pageset, readers
    rows_out = []
    by_reader_shape = defaultdict(lambda: Counter())
    for doc in pageset.load():
        rs = [r for r in stored_readings(doc["sha256"]) if r.get("read_from") == "pixels"
              and (r.get("reader", "").startswith("support.trials") or r.get("reader", "").startswith("support.scheduler.reread"))]
        for r in rs:                      # the re-read job's page-1 readings (qv4-reread-pages) count as a pass of their own
            if r.get("reader", "").startswith("support.scheduler.reread"):
                r.setdefault("checks", {})["trial_pass"] = "reread"
        if pass_name:
            rs = [r for r in rs if (r.get("checks") or {}).get("trial_pass") == pass_name]
        if not rs:
            continue
        data = None
        by_page = defaultdict(list)
        for r in rs:
            by_page[r["page"]].append(r)
        selected = {p["page"]: p for p in doc["selected_pages"]}
        for page, group in sorted(by_page.items()):
            is_text = selected.get(page, {}).get("read_from") == "text"
            key = None
            if is_text:
                data = data or pageset.read_bytes(doc["sha256"])
                key = pg.page_text(data, page)
            fam = {}
            for r in group:
                rd_ = next((x for x in readers.READERS.values() if x.model == r["model"]), None)
                fam.setdefault(rd_.family if rd_ else r["model"], r["text"])
            for r in group:
                rd_ = next((x for x in readers.READERS.values() if x.model == r["model"]), None)
                if reader_name and (rd_ is None or rd_.name != reader_name):
                    continue
                others = {f: t for f, t in fam.items() if f != (rd_.family if rd_ else r["model"])}
                s = score_page(r["text"], key, others)
                rec = {"key": f"{doc['sha256']}/p{page}/{r['profile']}@{r['profile_version']}/{r['model']}/"
                              f"{json.dumps(r['settings'], sort_keys=True)[:0]}{_settings_hash(r['settings'])}",
                       "document": doc["sha256"], "page": page, "reader": rd_.name if rd_ else r["model"], "model": r["model"],
                       "level": (r.get("settings") or {}).get("level"), "dpi": (r.get("settings") or {}).get("dpi"),
                       "pass": (r.get("checks") or {}).get("trial_pass"), "shape": doc["shape"], "kind": doc["kind"], **s}
                rows_out.append(rec)
                c = by_reader_shape[(rec["reader"], "text-key" if s["has_key"] else doc["shape"])]
                c["pages"] += 1
                c["invented_fail"] += int(bool(s.get("invented_fail")))
                c["loop_fail"] += int(bool(s.get("loop_fail")))
                c["amounts_exact"] += int(bool(s.get("amounts_exact")))
                c["amounts_lone"] += int(s.get("amounts_lone") or 0)
                c["example_names"] += int(s.get("example_names") or 0)
    if conn is not None:
        conn.execute(SCORE_TABLE)
        cols = ["key", "document", "page", "reader", "model", "level", "dpi", "pass", "shape", "kind", "has_key", "chars", "words",
                "amount_rows", "key_rows", "parts_found", "parts_key", "example_names", "invented_runs", "invented_longest",
                "invented_fail", "loops", "loop_fail", "amounts_key", "amounts_found", "amounts_missing", "amounts_extra",
                "amounts_exact", "amounts_lone"]
        for rec in rows_out:
            conn.execute(f"INSERT INTO scratch_trial.page_scores ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) "
                         f"ON CONFLICT (key) DO UPDATE SET " + ", ".join(f"{c} = EXCLUDED.{c}" for c in cols[1:]) + ", at = now()",
                         [rec.get(c) for c in cols])
    log(f"{'reader':24s} {'shape':17s} {'pages':>5s} {'invented':>8s} {'loops':>5s} {'exact$':>6s} {'lone$':>5s} {'example':>7s}")
    for (reader, shape), c in sorted(by_reader_shape.items()):
        log(f"{reader:24s} {shape:17s} {c['pages']:5d} {c['invented_fail']:8d} {c['loop_fail']:5d} {c['amounts_exact']:6d} "
            f"{c['amounts_lone']:5d} {c['example_names']:7d}")
    return rows_out


def _settings_hash(settings: dict) -> str:
    from support.reader import settings_hash
    return settings_hash(settings)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pass_name = reader_name = None
    i = 0
    while i < len(argv):
        if argv[i] == "--pass":
            pass_name = argv[i + 1]
            i += 2
        elif argv[i] == "--reader":
            reader_name = argv[i + 1]
            i += 2
        else:
            i += 1
    conn = None
    try:
        import support.db as db
        conn = db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True)
    except Exception as e:  # noqa: BLE001
        print(f"score: no database ({type(e).__name__}); printing only", file=sys.stderr)
    rows = run(pass_name, reader_name, conn=conn)
    print(f"score: {len(rows)} page readings scored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
