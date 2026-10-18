"""THE ANSWER KEYS (plan step 3.4). None needs a person.

    python -m support.trials.keys build      write keys.jsonl: one line per page-set document
    keys.load()                              sha256 → the keys held for it

1. TEXT PAGES AS A FREE KEY: a page with a text layer is rendered and read
   by each page reader; the text layer is the answer. Not stored here: it
   is the page's own bytes, read at scoring time (`score.run`).
2. EACH RETURN'S OWN PRINTED TOTAL: the declaration page's declared total
   and parts as the lane's declaration reader finds them in the text layer
   (text and image-declaration returns only; a scan's printed total comes
   from the readers themselves and is compared across them), and the old
   estate's Part A `stated_total` by sha256 from its page-read records.
3. DECLARED TOTALS FROM OUTSIDE: the Commission's published by-year table
   (captured page, parsed by year and party) and the frozen site's series
   (its `home.json`, by source file name → hash through the page set's
   names). KNOWN EXCEPTIONS where the Commission's table is wrong and is
   NOT a key: its 2020 figures for the Māori Party and Advance NZ (Part A
   alone).
4. THE OLD ANSWER SET: the confirmed tier only (142 cells a person
   confirmed; 5,348 machine-agreed cells are not truth), by stem → hash.
   Those cells carry donor names and addresses, so they are NOT copied
   here: `gold_confirmed(sha256)` reads them from the old folder at
   scoring time and returns amounts and parts only.

keys.jsonl holds figures, years, parties and hashes: no donor, no address.
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from collections import defaultdict

from support.trials import pageset

HERE = os.path.dirname(os.path.abspath(__file__))
KEYS = os.path.join(HERE, "keys.jsonl")
OLD_LIVE = pageset.OLD_LIVE
EC_BY_YEAR = os.path.join(OLD_LIVE, "var", "staging", "ec-donations", "index",
                          "live-mocracy-in-nz-political-parties-in-new-zealand-party-donations-and-loans-by-year.html")
HOME_JSON = os.path.join(OLD_LIVE, "var", "pi-snapshot", "current", "data", "home.json")
PAGEREAD = os.path.join(OLD_LIVE, "var", "staging", "ec-donations", "pageread")
GOLD = os.path.join(OLD_LIVE, "var", "audits", "docread-gold.jsonl")
# the Commission's table is wrong here (Part A alone): never a key
EC_TABLE_EXCEPTIONS = {(2020, "maori"), (2020, "advance")}
MONEY = re.compile(r"\$\s?([\d,]+\.\d{2})")


def norm_label(s: str) -> str:
    """A party label as letters and digits only, lower case, with the
    words a return's file name adds stripped, so the Commission's 'ACT New
    Zealand' and the file's 'ACT-New-Zealand-Annual-Return-2020' meet."""
    import unicodedata
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))      # Māori → Maori, so both spellings meet
    s = re.sub(r"(?i)(amended|annual|donation[s]?|loans?|and|return|of|party|the|final|supp|info|\b20[12]\d\b)", " ", s)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def same_party(a: str, b: str) -> bool:
    """Two labels name one party: the party key resolves both to one
    registered name, or one normalised label starts the other."""
    try:
        from keys import parties
        pa, pb = parties.party_name(a)[0], parties.party_name(b)[0]
        if pa and pb:
            return pa == pb
    except Exception:  # noqa: BLE001
        pass
    na, nb = norm_label(a), norm_label(b)
    return bool(na) and bool(nb) and (na.startswith(nb) or nb.startswith(na))


def _money(s: str):
    m = MONEY.search(s or "")
    if m:
        return float(m.group(1).replace(",", ""))
    if re.search(r"\bNIL\b", s or "", re.I):
        return 0.0
    return None


def ec_by_year(path: str = None) -> list[dict]:
    """[{year, party_label, total_donations, total_loans, excepted}] from the
    Commission's captured page: each table's year is the latest year named
    in the text just before it, which the page's own headings give."""
    with open(path or EC_BY_YEAR, encoding="utf-8", errors="replace") as f:
        t = f.read()
    out = []
    for m in re.finditer(r"<table.*?</table>", t, re.S):
        before = re.sub(r"<[^>]+>", " ", t[max(0, m.start() - 1500):m.start()])
        yrs = re.findall(r"\b(20[12]\d)\b", before)
        if not yrs:
            continue
        year = int(yrs[-1]) if int(yrs[-1]) < max(int(y) for y in yrs[-3:]) else int(yrs[-1]) - 1
        # the heading reads "<N> party donation returns" (N = the filing year) over returns for year N-1
        years_near = [int(y) for y in yrs[-6:]]
        year = min(years_near) if len(set(years_near)) > 1 else int(yrs[-1]) - 1
        rows = re.findall(r"<tr.*?</tr>", m.group(0), re.S)
        for r in rows:
            cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
            if len(cells) < 3 or cells[0].lower() == "party":
                continue
            label = re.sub(r"\s*\(PDF.*$", "", cells[0]).strip()
            key = norm_label(label)
            excepted = any(y == year and k in key for (y, k) in EC_TABLE_EXCEPTIONS)
            out.append({"year": year, "party_label": label, "total_donations": _money(cells[1]), "total_loans": _money(cells[2]),
                        "excepted": excepted})
    return out


def frozen_series(path: str = None) -> list[dict]:
    """[{party, year, total, basis, source_file}] from the frozen site."""
    with open(path or HOME_JSON, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for p in d.get("parties") or []:
        for s in ((p.get("window") or {}).get("series") or []):
            out.append({"party": p.get("party"), "year": s.get("year"), "total": s.get("total"), "basis": s.get("basis"),
                        "source_file": s.get("source_file")})
    return out


def old_pageread(sha256s: set) -> dict:
    """sha256 → {stated_total (Part A), nil, rows_n, gate, model} from the old
    page-read records, by the hash they carry (never by their file name)."""
    out = {}
    if not os.path.isdir(PAGEREAD):
        return out
    for dirpath, dirs, files in os.walk(PAGEREAD):
        for f in files:
            if not f.endswith(".json"):
                continue
            try:
                with open(os.path.join(dirpath, f), encoding="utf-8") as fh:
                    d = json.load(fh)
            except (OSError, ValueError):
                continue
            sha = d.get("sha256")
            if sha in sha256s:
                out[sha] = {"stated_total_a": d.get("stated_total"), "nil": d.get("nil"), "rows": len(d.get("rows") or []),
                            "gate": d.get("gate"), "model": d.get("model"), "method": d.get("method"), "ocr": d.get("ocr")}
    return out


def gold_confirmed(sha256: str, names: list = None) -> list[dict]:
    """The confirmed cells for a document, amounts and parts only: the
    person-confirmed tier of the old answer set, by stem → hash."""
    names = names or next((d["names"] for d in pageset.load() if d["sha256"] == sha256), [])
    stems = {os.path.splitext(os.path.basename(n))[0] for n in names}
    out = []
    try:
        with open(GOLD, encoding="utf-8") as f:
            for line in f:
                try:
                    g = json.loads(line)
                except ValueError:
                    continue
                if g.get("tier") != "confirmed" or g.get("stem") not in stems:
                    continue
                out.append({"part": g.get("part"), "n": g.get("n"), "page": g.get("page"), "field": g.get("field"),
                            "value": g.get("value") if g.get("field") == "amount" else None})
    except OSError:
        pass
    return out


def declaration_key(data: bytes, chars: dict) -> dict | None:
    """The return's own printed total and parts from its text layer, where
    page 1 has one (the lane's declaration reader)."""
    from registers.party_returns import declaration
    from support.docread import pages as pg
    if int(chars.get("1", chars.get(1, 0)) or 0) < pg.PAGE_TEXT_MIN:
        return None
    dec = declaration.read(pg.page_text(data, 1))
    return {"year": dec.year, "total": dec.total, "parts": dec.parts, "nil": dec.total_is_nil, "problems": dec.problems()}


def build(out_path: str = None, log=print) -> list[dict]:
    docs = pageset.load()
    by_sha = {d["sha256"]: d for d in docs}
    ec = ec_by_year()
    ec_by_year_ = defaultdict(list)
    for r in ec:
        ec_by_year_[r["year"]].append(r)
    frozen = frozen_series()
    frozen_by_name = {r["source_file"]: r for r in frozen if r.get("source_file")}
    old = old_pageread(set(by_sha))
    out = []
    n_dec = n_ec = n_frozen = n_old = n_gold = 0
    for d in docs:
        rec = {"sha256": d["sha256"], "kind": d["kind"], "year": d["year"], "label": d["label"], "declaration": None,
               "ec_table": None, "frozen": None, "old_pageread": old.get(d["sha256"]), "gold_confirmed": 0}
        if d["kind"] == "party-return":
            try:
                rec["declaration"] = declaration_key(pageset.read_bytes(d["sha256"]), d["chars"])
            except Exception as e:  # noqa: BLE001
                rec["declaration"] = {"error": type(e).__name__}
            n_dec += int(bool(rec["declaration"] and rec["declaration"].get("total") is not None))
            hits = [r for r in ec_by_year_.get(d["year"], []) if same_party(r["party_label"], d["label"])]
            if hits:
                h = hits[0]
                rec["ec_table"] = {"total_donations": h["total_donations"], "party_label": h["party_label"],
                                   "excepted": h["excepted"], "candidates": len(hits)}
                n_ec += 1
            for n in d["names"]:
                fz = frozen_by_name.get(os.path.basename(n))
                if fz:
                    rec["frozen"] = {"party": fz["party"], "year": fz["year"], "total": fz["total"], "basis": fz["basis"]}
                    n_frozen += 1
                    break
        rec["gold_confirmed"] = len(gold_confirmed(d["sha256"], d["names"]))
        n_gold += int(rec["gold_confirmed"] > 0)
        n_old += int(rec["old_pageread"] is not None)
        out.append(rec)
    out_path = out_path or KEYS
    with open(out_path, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    log(f"keys: {len(out)} documents; declaration totals {n_dec}; Commission table {n_ec}; frozen site {n_frozen}; "
        f"old page-read {n_old}; with confirmed gold cells {n_gold} → {out_path}")
    return out


def load(path: str = None) -> dict:
    out = {}
    try:
        with open(path or KEYS, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    out[r["sha256"]] = r
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "build":
        build()
        return 0
    k = load()
    print(f"keys: {len(k)} documents")
    return 0


if __name__ == "__main__":
    sys.exit(main())
