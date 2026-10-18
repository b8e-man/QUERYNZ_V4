"""SCORING PER PAGE (plan step 3.7). Pure functions over texts, and a pass
over every stored reading of the page set that writes the scores to the
trial's scratch tables and prints the table per reader and shape.

    python -m support.trials score [--pass P] [--reader R]     the page stage (below)
    python -m support.trials score --rows                      the rows stage: amounts and tables after the text reader
    python -m support.trials score --levels                    the twenty-page comparison of two compression levels

The measures, as the plan states them, and what pass one taught about
the free key (a text page's own layer):

- INVENTED TEXT. On a text page used as a key, any run of five or more
  words in the reading that is not on the page fails the page. "On the
  page" is judged against the layer in BOTH of pdftotext's orderings
  (layout and raw: a two-column form reads in a different order in each),
  and a run counts only when at least two of its words of four or more
  letters are nowhere on the page at all (page words out of order are not
  invention). The layer is a PARTIAL key where the document carries form
  fields (pdftotext prints a field's label and not its typed value), where
  the page's fonts are a scanner's OCR layer (`CIDFont+F…`: the key is
  itself a reading), where a page-sized image sits under the text, or
  where the layer is garbage; a run another family of reader also reads
  is text the layer lacked, not invention; a run on a partial key that no
  other family has read yet is UNDECIDED, never a failure. On a true scan
  there is no page key, so invention is judged three ways: an amount no
  other reader produces that breaks the printed total (the rows stage); a
  row only one family of reader produces (the rows stage); a name
  matching the form's own printed example (`EXAMPLE_NAMES`).
- LOOPS. The same line three or more times in a row, where the key or the
  other readers show it fewer times, fails the page; so does the same
  amount token twelve or more times in a row WITHIN one line (GLM-OCR
  loops sideways on an empty expense table). Genuinely repeated rows are
  not loops.
- AMOUNTS. Every money amount exact, to the cent: the key page's amounts
  all found, none added (complete keys only).
- TABLES. Row count: lines carrying an amount (the row-number column sits
  outside the border and readers disagree on it). Column alignment comes
  from the text reader's rows (`rows.py`), the same for every page reader.
- COMPLETENESS. Which parts (A to G) the page names; a part not read is
  not a part that is zero.
- AGREEMENT. Where two readers agree on a page's amounts, and where they
  differ, every pair, with the families named.

Never prints page text; the stored scores are counts and booleans. A run
of invented words is recorded as its length, not its words.
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

INVENTED_RUN = 5
LOOP_REPEATS = 3
LINE_LOOP = 12        # the same amount token this many times in a row on ONE line
ABSENT_WORDS = 2      # a run is new text only when this many of its words of 4+ letters are nowhere on the page
SUPPORT = 3           # a word is on the page when it sits inside a three-word run the page also carries
OTHER_SUPPORT = 0.5   # a run is text the key lacked when this share of its words sit in another family's reading
# a grouped figure (15,000 / 25,000.00), a figure with cents (30.43), or a dollar figure ($30); the engine must not
# start one character early and take "$25" off "$25,000.00", so the dollar form may not be followed by a comma or point
MONEY = re.compile(r"(?<![\w.])\$?(\d{1,3}(?:,\d{3})+(?:\.\d{2})?|\d+\.\d{2}|\$\s?\d+(?![\d,.]))(?![\d])")
PART_LABEL = re.compile(r"(?:TOTAL\s+FOR\s+)?PART\s+([A-G])\b", re.I)
TAG = re.compile(r"<[^>]+>")
WORD = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")
# the form's own printed examples, which a reader may copy as if they were a donor (names only: "example" and
# "sample" are words of the instructions on every form)
EXAMPLE_NAMES = ("john smith", "jane smith", "j smith", "abc limited", "xyz limited")
OCR_FONT = re.compile(r"^(CIDFont\+F\d+|\*|GlyphLessFont|Glyphless)", re.I)
# printed on every Commission form as an image (its logo), so never in a text layer and never invented
PAGE_FURNITURE = "electoral commission te kaitiaki take kōwhiri kowhiri"


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


def _keys(key) -> list[str]:
    if key is None:
        return []
    return [key] if isinstance(key, str) else [k for k in key if k]


def supported_mask(rw: list[str], texts: list[str]) -> list[bool]:
    """Which words of a reading sit inside a SUPPORT-word run that any of
    the texts carries."""
    have = set()
    for t in texts:
        have |= ngrams(words(t), SUPPORT)
    supported = [False] * len(rw)
    for i in range(len(rw) - SUPPORT + 1):
        if tuple(rw[i:i + SUPPORT]) in have:
            for j in range(i, i + SUPPORT):
                supported[j] = True
    return supported


def unsupported_runs(rw: list[str], texts: list[str], n: int = INVENTED_RUN) -> list[list[str]]:
    """The maximal runs of at least n consecutive reading words that no
    text supports."""
    if len(rw) < n:
        return []
    runs, run = [], []
    for w, s in zip(rw, supported_mask(rw, texts)):
        if not s:
            run.append(w)
        else:
            if len(run) >= n:
                runs.append(run)
            run = []
    if len(run) >= n:
        runs.append(run)
    return runs


def bag(texts: list[str]) -> set:
    out = set(words(PAGE_FURNITURE))
    for t in texts:
        out |= set(words(t))
    return out


def new_text(run: list[str], page_bag: set, absent: int = ABSENT_WORDS) -> bool:
    """A run is new text when at least `absent` of its words of four or
    more letters are nowhere on the page; page words out of order are
    not invention."""
    return sum(1 for w in run if len(w) >= 4 and w not in page_bag) >= absent


def invention(reading: str, key, others: list[str] = None, n: int = INVENTED_RUN) -> dict:
    """The runs of at least n reading words not on the key page: `runs`
    (lengths) are invented; `key_lacked` (lengths) are runs another
    reader of a different family also reads, so the key lacked them."""
    keys = _keys(key)
    rw = words(reading)
    if len(rw) < n:
        return {"runs": [], "key_lacked": []}
    page_bag = bag(keys)
    runs, lacked = [], []
    other_mask = supported_mask(rw, list(others or [])) if others else None
    sup = supported_mask(rw, keys)
    starts = []       # each unsupported run's position in the reading
    i = 0
    while i < len(rw):
        if not sup[i]:
            j = i
            while j < len(rw) and not sup[j]:
                j += 1
            if j - i >= n:
                starts.append((i, j))
            i = j
        else:
            i += 1
    for (i, j) in starts:
        run = rw[i:j]
        if not new_text(run, page_bag):
            continue
        if other_mask is not None and sum(other_mask[i:j]) >= OTHER_SUPPORT * (j - i):
            lacked.append(j - i)
        else:
            runs.append(j - i)
    return {"runs": runs, "key_lacked": lacked}


def invented_runs(reading: str, key, n: int = INVENTED_RUN) -> list[int]:
    """Lengths of the invented runs against the key alone."""
    return invention(reading, key, None, n)["runs"]


def lines(text: str) -> list[str]:
    return [" ".join(l.split()).lower() for l in plain(text).splitlines() if l.strip()]


def longest_token_run(line: str) -> int:
    """The longest run of the same amount token in a row within one line."""
    toks = [m.group(0) for m in MONEY.finditer(line)]
    best = run = 0
    for i, t in enumerate(toks):
        run = run + 1 if i and toks[i - 1] == t else 1
        best = max(best, run)
    return best


def loops(reading: str, key=None, others: list[str] = None, repeats: int = LOOP_REPEATS, line_loop: int = LINE_LOOP) -> list[int]:
    """Runs of the same line repeated `repeats` or more times in a row, and
    the same amount token `line_loop` or more times in a row inside one
    line, where the key (or, with no key, every other reader) shows fewer.
    Returns the run lengths."""
    ls = lines(reading)
    if not ls:
        return []
    keys = _keys(key)
    ref_texts = keys if keys else list(others or [])
    refs = [Counter(lines(t)) for t in ref_texts]
    ref_line_run = max([max([longest_token_run(l) for l in lines(t)] or [0]) for t in ref_texts] or [0])
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
    for l in ls:
        r = longest_token_run(l)
        if r >= line_loop and r > ref_line_run:
            out.append(r)
    return out


def parts(text: str) -> set:
    return {m.group(1).upper() for m in PART_LABEL.finditer(plain(text))}


def amount_rows(text: str) -> int:
    return sum(1 for l in plain(text).splitlines() if MONEY.search(l))


def example_names(text: str, key=None) -> list[str]:
    """The form's printed example names found in the reading; on a key
    page, only those the key does not carry itself."""
    t = " ".join(words(text))
    k = " ".join(words(" ".join(_keys(key)))) if key is not None else ""
    return [n for n in EXAMPLE_NAMES if n in t and n not in k]


# ── the free key's quality ───────────────────────────────────────────────────

def page_keys(data: bytes, page: int) -> list[str]:
    """The text layer in both orderings: layout (as the profile's reader
    sees it) and raw (content-stream order)."""
    from support.docread import pages as pg
    out = [pg.page_text(data, page)]
    try:
        r = subprocess.run(["pdftotext", "-q", "-raw", "-f", str(page), "-l", str(page), "-", "-"],
                           input=data, capture_output=True, timeout=120)
        if r.returncode == 0:
            out.append(r.stdout.decode("utf-8", "replace"))
    except (OSError, subprocess.SubprocessError):
        pass
    return out


def document_has_form(data: bytes) -> bool:
    """Whether the document carries form fields (pdfinfo's `Form:` line):
    pdftotext prints a field's label and never its typed value."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(data)
            f.flush()
            info = subprocess.run(["pdfinfo", f.name], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return any(l.startswith("Form:") and "none" not in l.lower() for l in info.splitlines())


def page_fonts(data: bytes, page: int) -> list[str]:
    try:
        r = subprocess.run(["pdffonts", "-f", str(page), "-l", str(page), "-"], input=data, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    return [l.split()[0] for l in r.stdout.decode("utf-8", "replace").splitlines()[2:] if l.strip()]


def page_big_images(data: bytes, page: int, side: int = 1000) -> int:
    try:
        r = subprocess.run(["pdfimages", "-list", "-f", str(page), "-l", str(page), "-"], input=data, capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return 0
    n = 0
    for line in r.stdout.decode("utf-8", "replace").splitlines()[2:]:
        f = line.split()
        if len(f) > 4 and f[2] == "image":
            try:
                if int(f[3]) >= side and int(f[4]) >= side:
                    n += 1
            except ValueError:
                pass
    return n


def key_quality(data: bytes, page: int, keys: list[str], has_form: bool = None) -> dict:
    """Why a text page's layer is, or is not, a complete key. `partial`
    names the first reason, or is None."""
    layer = keys[0] if keys else ""
    w = words(layer)
    fonts = page_fonts(data, page)
    q = {"form": document_has_form(data) if has_form is None else bool(has_form),
         "ocr_font": any(OCR_FONT.match(f) for f in fonts),
         "big_images": page_big_images(data, page),
         "garbage": len(w) < max(5, len(layer.strip()) / 40),
         "layer_words": len(w)}
    q["partial"] = ("garbage layer" if q["garbage"] else "scanner OCR layer" if q["ocr_font"] else "form fields" if q["form"]
                    else "text over an image" if q["big_images"] else None)
    return q


# ── one page ─────────────────────────────────────────────────────────────────

def score_page(reading: str, key=None, others: dict = None, key_partial: str = None) -> dict:
    """One reading of one page against its key (a text page's layer, one
    text or both orderings) or, with no key, against the other readers'
    readings (`others`: family → text). `key_partial` names why the key
    is incomplete; a run on a partial key no other family has read is
    undecided (invented_fail None)."""
    others = others or {}
    other_texts = [t for t in others.values() if t]
    keys = _keys(key)
    am = amounts(reading)
    out = {"chars": len(reading or ""), "words": len(words(reading)), "amount_rows": amount_rows(reading),
           "parts_found": "".join(sorted(parts(reading))), "amounts_found": sum(am.values())}
    if keys:
        inv = invention(reading, keys, other_texts)
        lp = loops(reading, keys)
        key_text = "\n".join(keys)
        ka = amounts(keys[0])
        missing = sum((ka - am).values())
        extra = sum((am - ka).values())
        decided = key_partial is None or bool(other_texts)
        out.update(has_key=True, key_partial=key_partial, example_names=len(example_names(reading, key_text)),
                   invented_runs=len(inv["runs"]), invented_longest=max(inv["runs"]) if inv["runs"] else 0,
                   key_lacked=len(inv["key_lacked"]),
                   invented_fail=(bool(inv["runs"]) if decided else None),
                   loops=len(lp), loop_fail=bool(lp),
                   amounts_key=sum(ka.values()), amounts_missing=missing, amounts_extra=extra,
                   amounts_exact=(missing == 0 and extra == 0), parts_key="".join(sorted(parts(keys[0]))),
                   key_rows=amount_rows(keys[0]))
    else:
        lp = loops(reading, None, other_texts)
        union = Counter()
        for t in other_texts:
            union |= amounts(t)
        lone = sum((am - union).values()) if other_texts else None
        out.update(has_key=False, key_partial=None, example_names=len(example_names(reading)),
                   invented_runs=None, invented_longest=None, key_lacked=None, invented_fail=None,
                   loops=len(lp), loop_fail=bool(lp), amounts_key=None, amounts_missing=None, amounts_extra=None,
                   amounts_exact=None, parts_key=None, key_rows=None)
        out["amounts_lone"] = lone
    out.setdefault("amounts_lone", None)
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


SCORE_COLS = ["key", "document", "page", "reader", "model", "level", "dpi", "pass", "shape", "kind", "has_key", "key_partial",
              "chars", "words", "amount_rows", "key_rows", "parts_found", "parts_key", "example_names", "invented_runs",
              "invented_longest", "key_lacked", "invented_fail", "loops", "loop_fail", "amounts_key", "amounts_found",
              "amounts_missing", "amounts_extra", "amounts_exact", "amounts_lone"]
SCORE_TABLE = """
CREATE SCHEMA IF NOT EXISTS scratch_trial;
DROP TABLE IF EXISTS scratch_trial.page_scores;
CREATE TABLE scratch_trial.page_scores (
    key text PRIMARY KEY, document text, page int, reader text, model text, level text, dpi int, pass text,
    shape text, kind text, has_key boolean, key_partial text, chars int, words int, amount_rows int, key_rows int,
    parts_found text, parts_key text, example_names int, invented_runs int, invented_longest int, key_lacked int,
    invented_fail boolean, loops int, loop_fail boolean, amounts_key int, amounts_found int, amounts_missing int,
    amounts_extra int, amounts_exact boolean, amounts_lone int, at timestamptz NOT NULL DEFAULT now()
);
DROP TABLE IF EXISTS scratch_trial.page_agreement;
CREATE TABLE scratch_trial.page_agreement (
    document text, page int, shape text, kind text, has_key boolean,
    reader_a text, family_a text, reader_b text, family_b text,
    shared int, only_a int, only_b int, agree boolean, at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (document, page, reader_a, reader_b)
);
GRANT USAGE ON SCHEMA scratch_trial TO qv4_read;
GRANT SELECT ON ALL TABLES IN SCHEMA scratch_trial TO qv4_read;
ALTER DEFAULT PRIVILEGES IN SCHEMA scratch_trial GRANT SELECT ON TABLES TO qv4_read;
"""


def _reader_of(r: dict):
    from support.trials import readers
    return next((x for x in readers.READERS.values() if x.model == r["model"]), None)


def run(pass_name: str = None, reader_name: str = None, conn=None, log=print) -> list[dict]:
    from support.trials import pageset
    rows_out, pairs_out = [], []
    by_reader_shape = defaultdict(lambda: Counter())
    for doc in pageset.load():
        rs = [r for r in stored_readings(doc["sha256"]) if r.get("read_from") == "pixels"
              and (r.get("reader", "").startswith("support.trials") or r.get("reader", "").startswith("support.scheduler.reread"))]
        for r in rs:                      # the re-read job's page-1 readings (qv4-reread-pages) count as a pass of their own
            if r.get("reader", "").startswith("support.scheduler.reread"):
                r.setdefault("checks", {})["trial_pass"] = "reread"
        if not rs:
            continue
        data = has_form = None
        by_page = defaultdict(list)
        for r in rs:
            by_page[r["page"]].append(r)
        selected = {p["page"]: p for p in doc["selected_pages"]}
        for page, group in sorted(by_page.items()):
            is_text = selected.get(page, {}).get("read_from") == "text"
            keys, partial = None, None
            if is_text:
                data = data or pageset.read_bytes(doc["sha256"])
                has_form = document_has_form(data) if has_form is None else has_form
                keys = page_keys(data, page)
                partial = key_quality(data, page, keys, has_form)["partial"]
            # one text per family from the OTHER readers (the same pass first), for support and agreement
            fam_texts = defaultdict(dict)
            for r in group:
                rd_ = _reader_of(r)
                fam = rd_.family if rd_ else r["model"]
                fam_texts[fam][(r.get("checks") or {}).get("trial_pass")] = r.get("text") or ""
            for r in group:
                rd_ = _reader_of(r)
                this_pass = (r.get("checks") or {}).get("trial_pass")
                if pass_name and this_pass != pass_name:
                    continue
                if reader_name and (rd_ is None or rd_.name != reader_name):
                    continue
                fam = rd_.family if rd_ else r["model"]
                others = {}
                for f, by_pass in fam_texts.items():
                    if f == fam:
                        continue
                    others[f] = by_pass.get(this_pass) or next(iter(by_pass.values()))
                s = score_page(r.get("text") or "", keys, others, partial)
                rec = {"key": f"{doc['sha256']}/p{page}/{r['profile']}@{r['profile_version']}/{r['model']}/{_settings_hash(r['settings'])}",
                       "document": doc["sha256"], "page": page, "reader": rd_.name if rd_ else r["model"], "model": r["model"],
                       "level": (r.get("settings") or {}).get("level"), "dpi": (r.get("settings") or {}).get("dpi"),
                       "pass": this_pass, "shape": doc["shape"], "kind": doc["kind"], **s}
                rows_out.append(rec)
                shape = ("text-key" + ("-partial" if partial else "")) if s["has_key"] else doc["shape"]
                c = by_reader_shape[(rec["reader"], shape)]
                c["pages"] += 1
                c["invented_fail"] += int(bool(s.get("invented_fail")))
                c["undecided"] += int(s.get("invented_fail") is None and bool(s.get("invented_runs")))
                c["loop_fail"] += int(bool(s.get("loop_fail")))
                c["amounts_exact"] += int(bool(s.get("amounts_exact")))
                c["amounts_lone"] += int(s.get("amounts_lone") or 0)
                c["example_names"] += int(s.get("example_names") or 0)
            # every pair of readings on this page
            named = [(rd_.name if rd_ else r["model"], rd_.family if rd_ else r["model"], r.get("text") or "")
                     for r, rd_ in ((r, _reader_of(r)) for r in group)]
            for i in range(len(named)):
                for j in range(i + 1, len(named)):
                    a, b = named[i], named[j]
                    if a[0] == b[0]:
                        continue
                    ag = agreement(a[2], b[2])
                    pairs_out.append({"document": doc["sha256"], "page": page, "shape": doc["shape"], "kind": doc["kind"],
                                      "has_key": is_text, "reader_a": a[0], "family_a": a[1], "reader_b": b[0], "family_b": b[1], **ag})
    if conn is not None:
        conn.execute(SCORE_TABLE)
        for rec in rows_out:
            conn.execute(f"INSERT INTO scratch_trial.page_scores ({', '.join(SCORE_COLS)}) VALUES ({', '.join(['%s'] * len(SCORE_COLS))})",
                         [rec.get(c) for c in SCORE_COLS])
        pcols = ["document", "page", "shape", "kind", "has_key", "reader_a", "family_a", "reader_b", "family_b", "shared", "only_a",
                 "only_b", "agree"]
        for p in pairs_out:
            conn.execute(f"INSERT INTO scratch_trial.page_agreement ({', '.join(pcols)}) VALUES ({', '.join(['%s'] * len(pcols))}) "
                         f"ON CONFLICT DO NOTHING", [p.get(c) for c in pcols])
    log(f"{'reader':24s} {'shape':17s} {'pages':>5s} {'invented':>8s} {'undecid':>7s} {'loops':>5s} {'exact$':>6s} {'lone$':>5s} {'example':>7s}")
    for (reader, shape), c in sorted(by_reader_shape.items()):
        log(f"{reader:24s} {shape:17s} {c['pages']:5d} {c['invented_fail']:8d} {c['undecided']:7d} {c['loop_fail']:5d} "
            f"{c['amounts_exact']:6d} {c['amounts_lone']:5d} {c['example_names']:7d}")
    return rows_out


def _settings_hash(settings: dict) -> str:
    from support.reader import settings_hash
    return settings_hash(settings)


# ── the rows stage (3.7: amounts and tables after the text reader) ───────────

def cents(x) -> int | None:
    try:
        return int(round(float(x) * 100))
    except (TypeError, ValueError):
        return None


def rows_by_part(rows: list[dict]) -> dict:
    """part letter → list of cents, donation lines only (printed totals out)."""
    out = defaultdict(list)
    for r in rows or []:
        c = cents(r.get("amount"))
        if c is None or r.get("is_total"):
            continue
        out[(r.get("part") or "?").upper()[:1]].append(c)
    return out


def example_rows(rows: list[dict]) -> int:
    """Donation lines whose donor is one of the form's own printed examples."""
    n = 0
    for r in rows or []:
        d = " ".join(words(str(r.get("donor") or "")))
        if any(e in d for e in EXAMPLE_NAMES) and not r.get("is_total"):
            n += 1
    return n


def key_total(rec: dict) -> tuple:
    """(total in cents, source) for a page-set document from keys.jsonl: the
    return's own declaration first, the frozen site, then the Commission's
    table where it is not excepted; (None, None) without one."""
    if not rec:
        return None, None
    d = rec.get("declaration") or {}
    if d.get("total") is not None:
        return cents(d["total"]), "declaration"
    if d.get("nil"):
        return 0, "declaration"
    f = rec.get("frozen") or {}
    if f.get("total") is not None:
        return cents(f["total"]), "frozen"
    e = rec.get("ec_table") or {}
    if e.get("total_donations") is not None and not e.get("excepted"):
        return cents(e["total_donations"]), "commission"
    return None, None


def document_score(by_reader: dict, rec: dict, gold: list[dict] = None) -> list[dict]:
    """One document: `by_reader` maps a reader's (name, level, dpi, pass) to
    {"family", "pages": [{page, parts_named, declared_total, rows, unparsed}]}.
    Returns one score per reader. Pure."""
    kt, ksrc = key_total(rec)
    kparts = {k.upper()[:1]: cents(v) for k, v in ((rec or {}).get("declaration") or {}).get("parts", {}).items() if cents(v) is not None}
    gold_cells = {(g.get("part"), cents(g.get("value"))) for g in (gold or []) if g.get("field") == "amount" and cents(g.get("value")) is not None}
    fam_pairs = defaultdict(set)
    per = {}
    for who, d in by_reader.items():
        parts = defaultdict(list)
        named, declared, unparsed, rows_n, totals_n, ex = set(), None, 0, 0, 0, 0
        for p in d["pages"]:
            named |= set(p.get("parts_named") or [])
            if declared is None and p.get("declared_total") is not None:
                declared = cents(p["declared_total"])
            unparsed += int(bool(p.get("unparsed")))
            for k, v in rows_by_part(p.get("rows")).items():
                parts[k].extend(v)
            rows_n += sum(1 for r in p.get("rows") or [] if not r.get("is_total"))
            totals_n += sum(1 for r in p.get("rows") or [] if r.get("is_total"))
            ex += example_rows(p.get("rows"))
        pairs = {(k, c) for k, cs in parts.items() for c in cs}
        fam_pairs[d["family"]] |= pairs
        per[who] = {"family": d["family"], "parts": parts, "named": named, "declared": declared, "unparsed": unparsed,
                    "rows_n": rows_n, "totals_n": totals_n, "example_rows": ex, "pairs": pairs}
    out = []
    for who, s in per.items():
        others = set()
        for f, ps in fam_pairs.items():
            if f != s["family"]:
                others |= ps
        other_families = sum(1 for f in fam_pairs if f != s["family"])
        lone = {pr for pr in s["pairs"] if pr not in others} if other_families else set()
        compared = exact = breaking = 0
        for k, kc in kparts.items():
            mine = sum(s["parts"].get(k, []))
            compared += 1
            if mine == kc:
                exact += 1
            else:
                lone_here = sum(c for (pk, c) in lone if pk == k)
                if lone_here and mine - lone_here == kc:
                    breaking += sum(1 for (pk, c) in lone if pk == k)
        hits = sum(1 for g in gold_cells if g[1] in s["parts"].get(g[0], []))
        name, level, dpi, pass_name = who
        out.append({"reader": name, "level": level, "dpi": dpi, "pass": pass_name, "family": s["family"],
                    "pages": len(by_reader[who]["pages"]), "unparsed_pages": s["unparsed"], "rows": s["rows_n"],
                    "total_rows": s["totals_n"], "parts_named": "".join(sorted(s["named"])),
                    "declared_read": s["declared"], "key_total": kt, "key_source": ksrc,
                    "declared_match": (s["declared"] == kt) if (kt is not None and s["declared"] is not None) else None,
                    "parts_compared": compared, "parts_exact": exact,
                    "lone_rows": len(lone) if other_families else None, "lone_breaking": breaking if other_families else None,
                    "example_rows": s["example_rows"], "gold_cells": len(gold_cells), "gold_hits": hits if gold_cells else None})
    return out


ROWS_TABLE = """
CREATE SCHEMA IF NOT EXISTS scratch_trial;
DROP TABLE IF EXISTS scratch_trial.document_scores;
CREATE TABLE scratch_trial.document_scores (
    document text, kind text, shape text, reader text, level text, dpi int, pass text, family text,
    pages int, unparsed_pages int, rows int, total_rows int, parts_named text, declared_read bigint, key_total bigint,
    key_source text, declared_match boolean, parts_compared int, parts_exact int, lone_rows int, lone_breaking int,
    example_rows int, gold_cells int, gold_hits int, at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (document, reader, level, dpi, pass)
);
DROP TABLE IF EXISTS scratch_trial.page_rows;
CREATE TABLE scratch_trial.page_rows (
    document text, page int, reader text, level text, dpi int, pass text, rows int, total_rows int, parts text,
    unparsed boolean, at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (document, page, reader, level, dpi, pass)
);
GRANT USAGE ON SCHEMA scratch_trial TO qv4_read;
GRANT SELECT ON ALL TABLES IN SCHEMA scratch_trial TO qv4_read;
"""
ROWS_COLS = ["document", "kind", "shape", "reader", "level", "dpi", "pass", "family", "pages", "unparsed_pages", "rows", "total_rows",
             "parts_named", "declared_read", "key_total", "key_source", "declared_match", "parts_compared", "parts_exact", "lone_rows",
             "lone_breaking", "example_rows", "gold_cells", "gold_hits"]


def run_rows(conn=None, log=print) -> list[dict]:
    """Every document with rows readings (the text reader's, `rows.py`):
    the rows stage of the scoring. Donor names stay in the store."""
    from support.trials import keys, pageset
    krec = keys.load()
    out, page_rows = [], []
    tally = defaultdict(Counter)
    for doc in pageset.load():
        rs = stored_readings(doc["sha256"])
        pixels = {r.get("key") or _key_of(r): r for r in rs if r.get("read_from") == "pixels"}
        by_reader = {}
        for r in rs:
            if not str(r.get("reader", "")).startswith("support.trials.rows"):
                continue
            px = pixels.get((r.get("checks") or {}).get("of_key"))
            if px is None:
                continue
            rd_ = _reader_of(px)
            who = (rd_.name if rd_ else px["model"], (px.get("settings") or {}).get("level"), (px.get("settings") or {}).get("dpi"),
                   (px.get("checks") or {}).get("trial_pass"))
            try:
                head = json.loads(r.get("text") or "{}")
            except ValueError:
                head = {"unparsed": True}
            page = {"page": r["page"], "parts_named": head.get("parts_named") or [], "declared_total": head.get("declared_total"),
                    "rows": r.get("rows") or [], "unparsed": bool(head.get("unparsed"))}
            by_reader.setdefault(who, {"family": rd_.family if rd_ else px["model"], "pages": []})["pages"].append(page)
            page_rows.append({"document": doc["sha256"], "page": r["page"], "reader": who[0], "level": who[1], "dpi": who[2],
                              "pass": who[3], "rows": sum(1 for x in page["rows"] if not x.get("is_total")),
                              "total_rows": sum(1 for x in page["rows"] if x.get("is_total")),
                              "parts": "".join(sorted(set(page["parts_named"]))), "unparsed": page["unparsed"]})
        if not by_reader:
            continue
        gold = keys.gold_confirmed(doc["sha256"], doc.get("names")) if (krec.get(doc["sha256"]) or {}).get("gold_confirmed") else []
        for s in document_score(by_reader, krec.get(doc["sha256"]), gold):
            s.update(document=doc["sha256"], kind=doc["kind"], shape=doc["shape"])
            out.append(s)
            t = tally[s["reader"]]
            t["documents"] += 1
            t["declared_match"] += int(bool(s["declared_match"]))
            t["declared_compared"] += int(s["declared_match"] is not None)
            t["parts_exact"] += s["parts_exact"]
            t["parts_compared"] += s["parts_compared"]
            t["lone_rows"] += s["lone_rows"] or 0
            t["lone_breaking"] += s["lone_breaking"] or 0
            t["example_rows"] += s["example_rows"]
            t["gold_hits"] += s["gold_hits"] or 0
            t["gold_cells"] += s["gold_cells"] if s["gold_hits"] is not None else 0
            t["unparsed"] += s["unparsed_pages"]
    if conn is not None:
        conn.execute(ROWS_TABLE)
        for s in out:
            conn.execute(f"INSERT INTO scratch_trial.document_scores ({', '.join(ROWS_COLS)}) VALUES ({', '.join(['%s'] * len(ROWS_COLS))}) "
                         f"ON CONFLICT DO NOTHING", [s.get(c) for c in ROWS_COLS])
        pc = ["document", "page", "reader", "level", "dpi", "pass", "rows", "total_rows", "parts", "unparsed"]
        for p in page_rows:
            conn.execute(f"INSERT INTO scratch_trial.page_rows ({', '.join(pc)}) VALUES ({', '.join(['%s'] * len(pc))}) ON CONFLICT DO NOTHING",
                         [p.get(c) for c in pc])
    log(f"{'reader':24s} {'docs':>4s} {'declared=key':>12s} {'parts exact':>11s} {'lone':>5s} {'breaking':>8s} {'example':>7s} {'gold':>9s} {'unparsed':>8s}")
    for reader, t in sorted(tally.items()):
        log(f"{reader:24s} {t['documents']:4d} {t['declared_match']:5d}/{t['declared_compared']:<6d} {t['parts_exact']:5d}/{t['parts_compared']:<5d} "
            f"{t['lone_rows']:5d} {t['lone_breaking']:8d} {t['example_rows']:7d} {t['gold_hits']:4d}/{t['gold_cells']:<4d} {t['unparsed']:8d}")
    return out


def _key_of(r: dict) -> str:
    from support.reader import reading_key
    return reading_key(r["document"], r["page"], r["model"], r.get("settings") or {}, r["profile"], r.get("profile_version") or 0)


# ── the compression comparison (3.1: twenty pages at two levels) ─────────────

LEVEL_PAIRS = (("glm-ocr", "glm-ocr-f16"), ("ovisocr2", "ovisocr2-f16"), ("chandra-ocr-2", "chandra-ocr-2-q4"),
               ("infinity-parser2-pro", "infinity-parser2-pro-q8"))


def compare_texts(a: str, b: str) -> tuple[bool, float]:
    import difflib
    na, nb = " ".join((a or "").split()), " ".join((b or "").split())
    if na == nb:
        return True, 1.0
    return False, round(difflib.SequenceMatcher(None, na, nb, autojunk=False).ratio(), 4)


LEVELS_TABLE = """
CREATE SCHEMA IF NOT EXISTS scratch_trial;
DROP TABLE IF EXISTS scratch_trial.level_pairs;
CREATE TABLE scratch_trial.level_pairs (
    reader_a text, reader_b text, document text, page int, dpi int, equal boolean, ratio real, amounts_agree boolean,
    chars_a int, chars_b int, at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (reader_a, reader_b, document, page, dpi)
);
GRANT USAGE ON SCHEMA scratch_trial TO qv4_read;
GRANT SELECT ON ALL TABLES IN SCHEMA scratch_trial TO qv4_read;
"""


def run_levels(conn=None, log=print) -> list[dict]:
    """The same page read at two compression levels of one model, at the
    same resolution: equal, how near, and whether the amounts agree."""
    from support.trials import pageset
    out = []
    tally = defaultdict(Counter)
    for doc in pageset.load():
        by = {}
        for r in stored_readings(doc["sha256"]):
            if r.get("read_from") != "pixels" or not str(r.get("reader", "")).startswith("support.trials"):
                continue
            rd_ = _reader_of(r)
            if rd_:
                by.setdefault((rd_.name, r["page"], (r.get("settings") or {}).get("dpi")), r.get("text") or "")
        for a, b in LEVEL_PAIRS:
            for (name, page, dpi), ta in list(by.items()):
                if name != a or (b, page, dpi) not in by:
                    continue
                tb = by[(b, page, dpi)]
                eq, ratio = compare_texts(ta, tb)
                agree = amounts(ta) == amounts(tb)
                out.append({"reader_a": a, "reader_b": b, "document": doc["sha256"], "page": page, "dpi": dpi, "equal": eq, "ratio": ratio,
                            "amounts_agree": agree, "chars_a": len(ta), "chars_b": len(tb)})
                t = tally[(a, b)]
                t["pages"] += 1
                t["equal"] += int(eq)
                t["ratio"] += ratio
                t["amounts_agree"] += int(agree)
    if conn is not None:
        conn.execute(LEVELS_TABLE)
        cols = ["reader_a", "reader_b", "document", "page", "dpi", "equal", "ratio", "amounts_agree", "chars_a", "chars_b"]
        for s in out:
            conn.execute(f"INSERT INTO scratch_trial.level_pairs ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) ON CONFLICT DO NOTHING",
                         [s.get(c) for c in cols])
    log(f"{'levels':44s} {'pages':>5s} {'equal':>5s} {'mean ratio':>10s} {'amounts agree':>13s}")
    for (a, b), t in sorted(tally.items()):
        log(f"{a + ' vs ' + b:44s} {t['pages']:5d} {t['equal']:5d} {t['ratio'] / t['pages']:10.4f} {t['amounts_agree']:13d}")
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    pass_name = reader_name = None
    stages = set()
    i = 0
    while i < len(argv):
        if argv[i] == "--pass":
            pass_name = argv[i + 1]
            i += 2
        elif argv[i] == "--reader":
            reader_name = argv[i + 1]
            i += 2
        elif argv[i] in ("--rows", "--levels", "--pages"):
            stages.add(argv[i][2:])
            i += 1
        else:
            i += 1
    stages = stages or {"pages"}
    conn = None
    try:
        import support.db as db
        conn = db.connect(db.OWNER_KEY, "querynz_v4", autocommit=True)
    except Exception as e:  # noqa: BLE001
        print(f"score: no database ({type(e).__name__}); printing only", file=sys.stderr)
    if "pages" in stages:
        rows = run(pass_name, reader_name, conn=conn)
        print(f"score: {len(rows)} page readings scored")
    if "rows" in stages:
        ds = run_rows(conn=conn)
        print(f"score: {len(ds)} document scores from the rows stage")
    if "levels" in stages:
        ls = run_levels(conn=conn)
        print(f"score: {len(ls)} page pairs across compression levels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
