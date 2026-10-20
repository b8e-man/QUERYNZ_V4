"""Measure a change on every return, replay only (plan 4.1: a change to the
reading is measured on all the landed returns, never on the sample). Each
candidate file is read from the old folder, read-only, through
`read.read_return`; stored page readings are replayed, never asked for,
and any reading the run stores goes to a folder of the caller's, never the
shared reader store.

    python -m registers.party_returns.replay run OUT.json [--store DIR] [--snapshot]
    python -m registers.party_returns.replay compare BEFORE.json AFTER.json
    python -m registers.party_returns.replay shape SHA_PREFIX [PAGE ...]
    python -m registers.party_returns.replay rereads RUN.json

`rereads` lists, from a run, every return set aside at a stage a page
reading could mend, with its whole hash and the pages to ask for: pages the
page reader has no stored reading of, and pages it read column by column
or left a row unfinished on (a cell-scale re-read); the integrator queues
them (step 2.14). A return set aside for any other reason is listed with no
pages and its reason, so it is not mistaken for one a re-read would clear.

`run` resolves each label against the parties lane's names in the real
database, through the read-only login (`--snapshot`: today's register, as
the sample does without them), and writes one entry per document: the row's party, label, year and
totals, its Part A and Part H rows (name, amount, page, route) and its
set-aside lines; never an address. `compare` prints the Part A counts of
each and every return whose rows, set-aside stages or party changed.
`shape` prints a return's pages as the reading sees them (text layer, or
the stored page reading) with every word that is not the form's own, and
every figure that is not money, a date or a row number, turned to `x`: so
a session can look at a page's layout without a name or an address
entering it (hard limit 11).
"""
import hashlib
import json
import os
import re
import sys

from support import reader as rd
from support.docread import pages
from registers.party_returns import capture, read

#: what `shape` leaves readable: money, dates, Yes/No, part labels, page marks, a row number at the margin
KEEP = re.compile(r"\$?\s*\d[\d,]*\.\d{2}|\d{1,2}/\d{1,2}/?\d{2,4}|\b(?:YES|NO|Yes|No)\b|PART\s+[A-I]\b|"
                  r"Page:?\s*\d+|^\s{0,3}\d{1,3}(?=\s|$)")
#: the form's own words, left readable
FORM_WORDS = set("""part a b c d e f g h i donations donation donor donors donor's donor’s name names street address total
for of more than the and received date dates from another person yes no enter including gst page schedule schedules
attachment attachments see attached list listing party loans loan aggregated contributions contribution amount
amounts instructions nil lender lenders return returns full continued continuation sheet appendix refer to on in is
a an by or with any made anonymous overseas sum this form secretary declaration dd/mm/yyyy does contain""".split())


class Overlay(rd.Store):
    """The shared reader store for reading; `root` for writing."""

    def __init__(self, root: str):
        super().__init__(root)
        self.shared = rd.Store()

    def has(self, key):
        return super().has(key) or self.shared.has(key)

    def get(self, key):
        return super().get(key) if super().has(key) else self.shared.get(key)


def published_parties() -> list:
    from support import db
    with db.connect(db.READ_KEY, "querynz_v4") as conn:
        return read.party_rows(conn)


def run(out_path: str, store_dir: str, files=None, parties=None) -> dict:
    store = Overlay(store_dir)
    out = {}
    for path in files or capture.candidate_files():
        with open(path, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        r = read.read_return(data, sha, store, loaded_at="replay", parties=parties)
        row = None
        if r.row:
            f_ = r.row["filed"]
            row = {k: f_.get(k) for k in ("party", "party_key", "party_label", "party_basis", "year", "declared_total", "part_a",
                                          "donors_check", "loans_check")}
        out[sha] = {"path": os.path.relpath(path, capture.FOLDER), "row": row,
                    "donors": [[d["name"], d["amount"], d["page"], d["paired_by"]] for d in r.donors],
                    "loans": [[x["name"], x["amount"]] for x in r.loans], "set_aside": r.set_aside}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    return out


def counts(d: dict) -> dict:
    pub = [s for s, v in d.items() if v["row"] and v["row"]["donors_check"] == "parts-sum"]
    return {"rows": sum(1 for v in d.values() if v["row"]), "published": len(pub),
            "donor_rows": sum(len(d[s]["donors"]) for s in pub),
            "nil": sum(1 for v in d.values() if v["row"] and v["row"]["donors_check"] == "declared-nil"),
            "set_aside": sum(1 for v in d.values() if any(st == "part-a" for st, _ in v["set_aside"]))}


def compare(a: dict, b: dict) -> list:
    tag = lambda v: f"{(v['row'] or {}).get('party_label')!r} {(v['row'] or {}).get('year')}"
    out = []
    for s in sorted(set(a) | set(b)):
        x, y = a.get(s), b.get(s)
        if x is None or y is None:
            out.append(f"{s[:12]}: only in {'after' if x is None else 'before'}")
            continue
        if x["donors"] != y["donors"]:
            old = {(n, m) for n, m, *_ in x["donors"]}
            new = {(n, m) for n, m, *_ in y["donors"]}
            out.append(f"{s[:12]} {tag(y)}: Part A rows {len(x['donors'])} -> {len(y['donors'])} "
                       f"(name and amount pairs gone {len(old - new)}, new {len(new - old)})")
        if [t for t, _ in x["set_aside"]] != [t for t, _ in y["set_aside"]]:
            out.append(f"{s[:12]} {tag(y)}: set aside {[t for t, _ in x['set_aside']]} -> {[t for t, _ in y['set_aside']]}")
        if x["loans"] != y["loans"]:
            out.append(f"{s[:12]} {tag(y)}: Part H rows {len(x['loans'])} -> {len(y['loans'])}")
        if (x["row"] or {}).get("party") != (y["row"] or {}).get("party"):
            out.append(f"{s[:12]} {tag(y)}: party {(x['row'] or {}).get('party')!r} -> {(y['row'] or {}).get('party')!r} "
                       f"({(y['row'] or {}).get('party_basis')})")
    return out


PAGE_FAULT = re.compile(r"page (\d+): (?:the cells and the figures do not pair|a row carried over the page break)")


def rereads(d: dict) -> list:
    """[(sha256, party, year, stage, pages, why)] for every set-aside stage."""
    out = []
    for sha, v in sorted(d.items(), key=lambda x: x[1]["path"]):
        r = v["row"] or {}
        for stage, why in v["set_aside"]:
            pages_ = sorted({int(p) for p in PAGE_FAULT.findall(why)})
            m = re.search(re.escape(read.REREAD) + r" [0-9a-f]{64} pages ([\d, ]+)", why)
            if m:
                pages_ = sorted(set(pages_) | {int(p) for p in m.group(1).split(",")})
            m = re.search(r"pages ([\d, …]+)\): ask for a re-read", why)
            if stage == "read" and m:
                pages_ = sorted(int(p) for p in re.findall(r"\d+", m.group(1)))
            kind = ("no stored reading" if stage == "read" or read.REREAD in why else "cell-scale re-read") if pages_ else "not a reading fault"
            out.append((sha, r.get("party") or r.get("party_label") or v["path"].rsplit("/", 1)[-1], r.get("year"), stage,
                        pages_, kind if pages_ else why[:160]))
    return out


def shape_line(line: str) -> str:
    out, last = [], 0
    for m in KEEP.finditer(line):
        out += [re.sub(r"\S", "x", line[last:m.start()]), m.group(0)]
        last = m.end()
    out.append(re.sub(r"\S", "x", line[last:]))
    res = list("".join(out))
    for w in re.finditer(r"\S+", line):
        if w.group(0).lower().strip("(),.:;") in FORM_WORDS:
            res[w.start():w.end()] = w.group(0)
    return "".join(res)


def shape(prefix: str, want=(), store_dir: str = None) -> None:
    store = Overlay(store_dir) if store_dir else rd.Store()
    for path in capture.candidate_files():
        with open(path, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        if not sha.startswith(prefix):
            continue
        texts = pages.text_pages(data)
        for p in want or sorted(texts):
            t, src = texts.get(p) or "", "text"
            if len(t.strip()) < 50:
                r = read.stored_page(store, sha, p)
                t, src = (r.text, "pixels") if r else ("", "no reading")
            print(f"===== {sha[:12]} page {p} of {len(texts)} ({src})")
            for line in t.splitlines():
                if line.strip():
                    print(shape_line(line))


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv[:1] == ["run"] and len(argv) >= 2:
        store = argv[argv.index("--store") + 1] if "--store" in argv else os.path.join(os.path.dirname(argv[1]), "store")
        d = run(argv[1], store, parties=None if "--snapshot" in argv else published_parties())
        print(f"{len(d)} documents: {counts(d)}")
        return 0
    if argv[:1] == ["compare"] and len(argv) == 3:
        a, b = (json.load(open(p, encoding="utf-8")) for p in argv[1:])
        print(f"before: {counts(a)}\nafter:  {counts(b)}")
        for line in compare(a, b):
            print("  " + line)
        return 0
    if argv[:1] == ["rereads"] and len(argv) == 2:
        for sha, party, year, stage, pages_, why in rereads(json.load(open(argv[1], encoding="utf-8"))):
            print(f"{sha}\t{party}\t{year}\t{stage}\t{','.join(map(str, pages_)) or '-'}\t{why}")
        return 0
    if argv[:1] == ["shape"] and len(argv) >= 2:
        shape(argv[1], [int(p) for p in argv[2:]])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
