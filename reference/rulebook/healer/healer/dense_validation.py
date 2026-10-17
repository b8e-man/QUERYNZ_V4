"""R3a — the DENSE-MODEL VALIDATION PASS (plan B4b, ruling 27, 2026-08-22).

Same shape as the refuter: a DIFFERENT model cross-checking the fleet's
output, so neither certifies itself. The fleet self-disagrees on ~6% of
verdicts (94% label agreement across three baseline pairings,
var/audits/spec-decoding-2026-08-20/). Before any rule is mined from the
verdict corpus, this pass puts a MEASURED validity number on it:

  sample   — a seeded, pattern-stratified sample of judged `mint_review`
             rows (acronym-org, type-multiplicity: the one-shot patterns)
  re-judge — the SAME prompt the fleet would build today
             (`crawler.build_prompt`) sent to the second endpoint
             (`reviewer.model.judge_at`), schema-constrained like the fleet's
  report   — agreement (dense label == fleet label) overall and per pattern,
             churn (fleet verdict vs the row's own stored reasoning is NOT
             re-run; churn here = fleet label vs dense label), dissent rows
             listed with both reasonings, written to var/audits/r3a-<stamp>.json

DISPOSITION (RULED: ruling 110, Arthur 2026-08-24): dissent ANNOTATES — the
report names the rows; nothing here writes to the graph or to mint_review.
A rule-miner refuses to run without a fresh r3a artifact (the gate lives
with the miner when it is built; the artifact is the contract).

The dense Qwen3.8-27B needs GPU0, which the agent lane holds: the live
run is an ARTHUR_RUNSHEET item (swap the lane, run, swap back). The
module is tested on a scripted endpoint.
"""
from __future__ import annotations

import json
import os
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone

from reviewer import model

from . import crawler

PATTERNS = ("crawler-acronym-org", "crawler-type-multiplicity")
OUT_DIR = "var/audits"


def sample(g, n: int = 300, seed: int = 20260822, patterns=PATTERNS) -> list[dict]:
    """n judged rows, split evenly across patterns, seeded."""
    rng = random.Random(seed)
    per = max(1, n // len(patterns))
    out = []
    for p in patterns:
        rows = g.execute("""
            SELECT entity_id, name, type, pattern, verdict, confidence, reasoning
            FROM mint_review WHERE pattern = %s AND verdict IS NOT NULL
              AND status IN ('judged', 'retyped', 'cleared', 'observed', 'merged', 'parked', 'quarantined')
            ORDER BY entity_id LIMIT 20000""", (p,)).fetchall()
        rows = [dict(r) for r in rows]
        rng.shuffle(rows)
        out += rows[:per]
    return out


CHECKPOINT_EVERY = 25


def rejudge(g, rows: list[dict], url: str, model_name: str | None, judge=None,
            checkpoint=None, done: list[dict] | None = None) -> list[dict]:
    """Re-judge each row at the second endpoint with the fleet's own prompt.
    `judge` is scripted by tests (signature: (url, system, user, schema, model_name)).
    `checkpoint(rows_so_far)` is called every CHECKPOINT_EVERY verdicts —
    ledgered 2026-08-24: run 1 died OOM at 241/300 six hours in and left
    NOTHING (the artifact was written only at the end). `done` seeds rows a
    previous partial already judged (resume): they are kept, not re-sent."""
    judge = judge or (lambda url, system, user, schema, model_name:
                      model.judge_at(url, system, user, schema=schema, model_name=model_name))
    out = list(done or [])
    have = {r["entity_id"] for r in out}
    for r in rows:
        if r["entity_id"] in have:
            continue
        try:
            system, user, schema = crawler.build_prompt(g, r)
            v = judge(url, system, user, schema, model_name)
            dense = {"verdict": v.get("verdict"), "confidence": v.get("confidence"),
                     "reasoning": v.get("reasoning"), "model": v.get("model")}
        except Exception as e:  # noqa: BLE001 — one dead row must not kill the pass
            dense = {"verdict": "error", "confidence": None, "reasoning": f"{type(e).__name__}: {e}"[:300],
                     "model": None}
        out.append({**r, "dense": dense})
        if checkpoint and len(out) % CHECKPOINT_EVERY == 0:
            checkpoint(out)
    return out


def report(rows: list[dict]) -> dict:
    """Agreement and dissent. A row with dense 'error' counts in n but in
    neither agreement nor dissent (reported separately).

    C261 (2026-10-07): `abstain_one_side` used to be a SCALAR while dissent was
    recorded row by row. So the 2026-08-23 artifact said 110 of 300 and could not
    say WHICH 300 — and the card raised off that number ("how much of the 110 is
    the reasoning budget?") was unanswerable from the artifact it came from. The
    abstaining rows are now listed the same way the dissenting ones are. A count
    nobody can resolve back to rows cannot be investigated, only repeated.
    """
    by_pattern: dict[str, Counter] = defaultdict(Counter)
    dissent, abstain = [], []
    for r in rows:
        d = r["dense"]["verdict"]
        c = by_pattern[r["pattern"]]
        c["n"] += 1
        if d == "error":
            c["error"] += 1
        elif d == r["verdict"]:
            c["agree"] += 1
        elif d == "abstain" or r["verdict"] == "abstain":
            c["abstain_one_side"] += 1
            abstain.append({"entity_id": r["entity_id"], "name": r["name"],
                            "pattern": r["pattern"], "fleet": r["verdict"],
                            "fleet_conf": r["confidence"], "dense": d,
                            "dense_conf": r["dense"]["confidence"],
                            "which": "dense" if d == "abstain" else "fleet"})
        else:
            c["dissent"] += 1
            dissent.append({"entity_id": r["entity_id"], "name": r["name"], "pattern": r["pattern"],
                            "fleet": r["verdict"], "fleet_conf": r["confidence"],
                            "dense": d, "dense_conf": r["dense"]["confidence"],
                            "fleet_reasoning": (r.get("reasoning") or "")[:300],
                            "dense_reasoning": (r["dense"]["reasoning"] or "")[:300]})
    total = Counter()
    for c in by_pattern.values():
        total.update(c)
    judged = total["n"] - total["error"]
    return {"n": total["n"], "errors": total["error"],
            "agreement": (total["agree"] / judged) if judged else None,
            "dissent_rate": (total["dissent"] / judged) if judged else None,
            "abstain_one_side": total["abstain_one_side"],
            "abstain": abstain,
            "per_pattern": {p: {k: c[k] for k in ("n", "agree", "dissent", "abstain_one_side", "error")}
                            | {"agreement": (c["agree"] / (c["n"] - c["error"])) if c["n"] - c["error"] else None}
                            for p, c in by_pattern.items()},
            "dissent": dissent}


def run(g, url: str, model_name: str | None, n: int = 300, seed: int = 20260822, judge=None,
        out_dir: str = OUT_DIR, resume: str | None = None) -> tuple[dict, str]:
    """`resume` = a partial file from a killed run (r3a-partial-<stamp>.json);
    its judged rows are kept and only the remainder is re-sent. A partial is
    written every CHECKPOINT_EVERY verdicts and deleted on success."""
    rows = sample(g, n=n, seed=seed)
    done = []
    if resume:
        with open(resume) as f:
            done = json.load(f)["rows"]
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    partial_path = os.path.join(out_dir, f"r3a-partial-{stamp}.json")

    def checkpoint(rows_so_far: list[dict]) -> None:
        tmp = partial_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"seed": seed, "requested": n, "endpoint": url, "rows": rows_so_far}, f, ensure_ascii=False)
        os.replace(tmp, partial_path)

    rows = rejudge(g, rows, url, model_name, judge=judge, checkpoint=checkpoint, done=done)
    rep = report(rows)
    if os.path.exists(partial_path):
        os.remove(partial_path)
    # the RESUME input is spent too (2026-08-24 card: only this run's own
    # partial was removed, so killed-run partials accumulated in var/audits)
    if resume and resume != partial_path and os.path.exists(resume):
        os.remove(resume)
    doc = {"built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "endpoint": url,
           "model": model_name, "seed": seed, "requested": n, **rep}
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"r3a-{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H%M%SZ')}.json")
    with open(path, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    return doc, path
