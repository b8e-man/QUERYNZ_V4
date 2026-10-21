"""Measure a change on every held document, replay only (plan 4.1: a change
to a reading is measured on all the landed documents, never on the
sample). Each expense return, promoter return, allocation page and
financial statement is read from the old folder, read-only; stored page
readings are replayed, never asked for, and any reading the run stores
goes to a folder of the caller's, never the shared reader store. No
database, no listing: every held document of the four kinds is read,
linked or not.

    python -m registers.party_finance.replay run OUT.json [--store DIR]
    python -m registers.party_finance.replay compare BEFORE.json AFTER.json

`run` writes one entry per document: its kind, the figures read with their
check and `issue` (ruling 66), and its set-aside lines; never a name, an
email or an address. `compare` prints every document whose outcome changed
and, per kind, how many set-asides became reconciled with an issue, how
many stay set aside, and the largest difference now admitted.
"""
import hashlib
import json
import os
import re
import sys

from support import reader as rd
from registers.party_finance import broadcasting, capture, expenses, promoter_returns, statements

KINDS = ("expense-return", "promoter-return", "allocation-page", "financial-statements")
YEAR = re.compile(r"__(\d{4})__")


class Overlay(rd.Store):
    """The shared reader store for reading; `root` for writing."""

    def __init__(self, root: str):
        super().__init__(root)
        self.shared = rd.Store()

    def has(self, key):
        return super().has(key) or self.shared.has(key)

    def get(self, key):
        return super().get(key) if super().has(key) else self.shared.get(key)


def entry(kind: str, path: str, data: bytes, sha: str, store) -> dict:
    if kind == "expense-return":
        r = expenses.read_return(data, sha, store)
        return {"read": [["total", r.total, r.total_check, getattr(r, "issue", None)]] if r.total is not None else [],
                "set_aside": [list(x) for x in r.set_aside]}
    if kind == "promoter-return":
        m = YEAR.search(os.path.basename(path))
        r = promoter_returns.read_return(data, sha, store, int(m.group(1)) if m else None)
        return {"read": [[k, p.figure, p.check, getattr(p, "issue", None)] for k, p in sorted(r.parts.items())
                         if p.figure is not None],
                "set_aside": [list(x) for x in r.set_aside]}
    if kind == "allocation-page":
        b = broadcasting.read(data)
        issues = getattr(b, "issues", {})
        return {"read": [[f"round {i + 1}", None, "rows-sum", issues.get(i)] for i in range(len(b.rounds))
                         if i not in b.failed_rounds],
                "set_aside": [[f"round {i + 1}", "rows do not add to the printed total"] for i in b.failed_rounds]}
    r = statements.read_statement(data, sha)
    return {"read": [[n, f.amount, f.check, getattr(f, "issue", None)] for n, f in sorted(r.figures.items())],
            "set_aside": [list(x) for x in r.set_aside]}


def run(out_path: str, store_dir: str) -> dict:
    store = Overlay(store_dir)
    out = {}
    for kind, path in capture.candidate_files():
        if kind not in KINDS:
            continue
        with open(path, "rb") as f:
            data = f.read()
        sha = hashlib.sha256(data).hexdigest()
        if sha in out:
            continue
        out[sha] = {"kind": kind, **entry(kind, path, data, sha, store)}
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    return out


DIFF = re.compile(r"^([+-][\d,]+\.\d\d):")


def compare(a: dict, b: dict) -> list:
    lines, per = [], {}
    for sha in sorted(set(a) | set(b)):
        x, y = a.get(sha) or {"read": [], "set_aside": []}, b.get(sha) or {"read": [], "set_aside": []}
        kind = (y.get("kind") or x.get("kind"))
        k = per.setdefault(kind, {"aside_before": 0, "now_with_issue": 0, "still_aside": 0, "largest": (0.0, None)})
        k["aside_before"] += len(x["set_aside"])
        k["still_aside"] += len(y["set_aside"])
        before = {r[0] for r in x["read"]}
        for r in y["read"]:
            if r[3] and r[0] not in before:
                k["now_with_issue"] += 1
            for m in (DIFF.match(p) for p in (r[3] or "").split("; ")):
                if m and abs(float(m.group(1).replace(",", ""))) > abs(k["largest"][0]):
                    k["largest"] = (float(m.group(1).replace(",", "")), f"{sha[:12]} {r[0]}: {r[3]}")
        if x != y:
            lines.append(f"{sha[:12]} {kind}: read {[r[0] for r in x['read']]} -> {[r[0] for r in y['read']]}; "
                         f"set aside {len(x['set_aside'])} -> {len(y['set_aside'])}")
    for kind, k in sorted(per.items()):
        lines.append(f"{kind}: {k['aside_before']} set aside before; {k['now_with_issue']} figures now reconciled with "
                     f"an issue; {k['still_aside']} set aside now; largest admitted {k['largest'][1] or 'none'}")
    return lines


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv[:1] == ["run"] and len(argv) >= 2:
        store = argv[argv.index("--store") + 1] if "--store" in argv else os.path.join(
            os.path.dirname(os.path.abspath(argv[1])), "store")
        d = run(argv[1], store)
        print(f"{len(d)} documents")
        return 0
    if argv[:1] == ["compare"] and len(argv) == 3:
        a, b = (json.load(open(p, encoding="utf-8")) for p in argv[1:])
        for line in compare(a, b):
            print("  " + line)
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
