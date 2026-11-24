"""The news reader's gates (registers.news.gates) measured on Arthur's judged answers: for each gated kind, the model
right among the items judged, before and after the gate, and the share of all the model's output the gate keeps.

    python -m products.board.review --export news-gold-2 ... news-gold-7     (the board's answers, written out)
    python -m registers.news.gold.gates_check

Reads the stored trial runs (each tranche's own run) and the answers the board exported (the newest per question, in
<review>/answers/<set>.json; a lane never reads the board's tables); "bad" and "can't tell" answers are left out.
Prints counts only, never article text.
"""
from __future__ import annotations

import glob
import json
import sys

from registers.news import gates as G
from registers.news.gold import questions as Q, trial as T2
from registers.news.gold.sample import _conn

ANSWERS = "/home/user/querynzv4-work/live/review/answers"
SETS = ("/home/user/querynzv4-work/live/review-retired/news-gold-*.json", "/home/user/querynzv4-work/live/review/news-gold-*.json")
#: kind in the reading → (question kind, the question's key for an item)
KEYS = {
    "quotes": ("quote", lambda x: ("quote", (x.get("text") or "").strip()[:80])),
    "roles": ("role", lambda x: (x.get("who"), x.get("role"), x.get("of"))),
    "claims": ("claim", lambda x: ("claim2", (x.get("statement") or "").strip().rstrip(".")[:80])),
    "sentiment": ("sentiment", lambda x: ("tone", x.get("toward"), x.get("from"))),
}


def measure() -> dict:
    out = {k: {"judged": 0, "right": 0, "kept": 0, "kept_right": 0, "output": 0, "output_kept": 0} for k in KEYS}
    ans = {}
    for f in glob.glob(f"{ANSWERS}/news-gold-*.json"):
        name = f.rsplit("/", 1)[1][:-5]
        ans.update({(name, q): a["choice"] for q, a in json.load(open(f)).items()})
    if not ans:
        raise SystemExit("no exported answers: run python -m products.board.review --export news-gold-2 ... first")
    with _conn() as c:
        for f in sorted({p for g in SETS for p in glob.glob(g)}):
            d = json.load(open(f))
            tranche = int(d["set"].rsplit("-", 1)[1])
            if tranche < 2:
                continue          # tranche 1 asked about the hand labels, not the model's records
            run, qs = d.get("run") or "run6", {q["id"]: q for q in d["questions"]}
            for aid in {q["article"] for q in d["questions"]}:
                p = T2.OUT / f"tranche-{tranche}" / run / f"{aid}.json"
                if not p.exists():
                    continue
                got = json.loads(p.read_text()).get("parsed") or {}
                text = T2._text(c, aid)
                body = text.split("\n\n", 1)[1] if "\n\n" in text else text
                G.apply(got, body)
                for kind, (qkind, key) in KEYS.items():
                    m = out[kind]
                    for x in got.get(kind) or []:
                        if not isinstance(x, dict) or "gate" not in x:
                            continue
                        if kind == "roles" and not x.get("of"):
                            continue          # only bound roles were asked
                        m["output"] += 1
                        m["output_kept"] += x["gate"]["kept"]
                        qid = Q._qid(qkind, aid, key(x))
                        q, ch = qs.get(qid), ans.get((d["set"], qid))
                        if q is None or ch is None or ch in ("bad", "unsure"):
                            continue
                        right = ch == q["sides"]["model"] or ch in q["sides"].get("also", ())
                        m["judged"] += 1
                        m["right"] += right
                        if x["gate"]["kept"]:
                            m["kept"] += 1
                            m["kept_right"] += right
    return out


def main(argv=None) -> int:
    pct = lambda a, b: f"{100 * a / b:.0f}%" if b else "n/a"
    print(f"{'kind':<10} {'judged':>6} {'right':>6} {'kept':>5} {'right after':>11} {'output kept':>11}")
    for kind, m in measure().items():
        print(f"{kind:<10} {m['judged']:>6} {pct(m['right'], m['judged']):>6} {m['kept']:>5} "
              f"{pct(m['kept_right'], m['kept']):>11} {pct(m['output_kept'], m['output']):>11}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
