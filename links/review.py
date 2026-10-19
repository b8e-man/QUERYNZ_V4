"""The review agent's reading of confirmed links (plan 4.2, measurement 3;
track C builds the agent proper and measures it before it acts alone).

    python -m links.review --draw 100 [--seed 7] [--schema S]   write the sample's evidence as JSON lines to the scratch folder
    python -m links.review --run FILE [--schema S]               read each link in FILE through the review model (the scheduler's
                                                                 worker gives QV4_MODEL_URL and QV4_MODEL) and record the verdicts
    python -m links.review --record FILE --agent NAME [--schema S]  record verdicts a reader wrote into FILE (one JSON object per line:
                                                                 link_id, verdict, reasoning)

The agent reads the evidence the registers hold for a link: the two rows'
names as filed, their registers, the companies or bodies each role sits on
with their registered offices and dates, and the rule that joined them. It
answers one of three verdicts (track C): `no reason to doubt`, `contested`
(it cannot trust the link), `not the same`. Splitting is the safe direction.
Verdicts are recorded in `links.readings` and not applied: until track C
passes the agent on the test pairs, nothing here adds a decision.

Web search: the agent may search only for evidence that two rows are
different people, with a name and a public role at most (hard limits 12
and 26). This module does not search: the fetch gate has no search route
yet, and a reading that searched would say so in `web_searched`. No home
address is read: the evidence is registered offices, which companies publish.
"""
from __future__ import annotations

import json
import os
import random
import sys

import links

VERDICTS = ("no reason to doubt", "contested", "not the same")
AGENT_VERSION = "review-agent@1"
SYSTEM = """You review one link between two rows of New Zealand public registers.
The link says the two rows are the same person. Your only job is to look for
reasons to DOUBT that, from the evidence given: a very common name, roles far
apart in place or time with nothing joining them, a middle name that differs,
a company address that is an accountant's office shared by many companies,
a date that makes one person impossible. You never confirm from fame or
prominence; a name alone is never identity. Answer with one JSON object:
{"verdict": "no reason to doubt" | "contested" | "not the same", "reasoning": "<two sentences at most>"}
"contested" means you cannot trust the link on this evidence; "not the same"
means the evidence shows two people. Splitting is the safe direction."""


def evidence_for(conn, s: str, link_id: int) -> dict:
    """What a reader sees for one link: the two rows, their roles and the
    registered offices of the companies those roles sit on."""
    l = conn.execute(f"SELECT link_id, row_a, row_b, rule, evidence, grade FROM {s}.links WHERE link_id = %s", (link_id,)).fetchone()
    if not l:
        raise LookupError(f"no link {link_id}")
    out = {"link_id": l[0], "rule": l[3], "grade": l[5], "rule_evidence": l[4], "rows": []}
    for ref in (l[1], l[2]):
        r = conn.execute(f"""SELECT register, view, name_filed, given, middle, family, entity_ref, started_on, ended_on, election, electorate
                             FROM {s}.rows WHERE ref = %s""", (ref,)).fetchone()
        if not r:
            out["rows"].append({"ref": ref, "note": "an organisation row or a row outside links.rows"})
            continue
        row = {"ref": ref, "register": r[0], "view": r[1], "name_as_filed": r[2], "entity": r[6], "from": str(r[7] or ""), "to": str(r[8] or ""),
               "election": r[9], "electorate": r[10]}
        if r[6] and r[6].startswith("companies:"):
            key = r[6].split(":", 1)[1]
            c = conn.execute("SELECT name, entity_type, status, registered_on, removed_on FROM pub.companies WHERE key = %s", (key,)).fetchone()
            if c:
                row["company"] = {"name": c[0], "type": c[1], "status": c[2], "registered": str(c[3] or ""), "removed": str(c[4] or "")}
            row["registered_offices"] = [{"address": " ".join(p for p in (a[0], a[1], a[2], a[3], a[4]) if p), "from": str(a[5] or ""), "latest": a[6]}
                                         for a in conn.execute("""SELECT line_1, line_2, line_3, line_4, postcode, started_on, in_latest
                                                                  FROM pub.company_addresses WHERE entity_key = %s ORDER BY started_on NULLS FIRST""",
                                                               (key,)).fetchall()][:6]
            row["other_roles_under_this_exact_name"] = int(conn.execute(
                f"SELECT count(*) FROM {s}.rows WHERE full_key = (SELECT full_key FROM {s}.rows WHERE ref = %s) AND view = 'directors'", (ref,)).fetchone()[0])
        elif r[6] and r[6].startswith("societies:"):
            key = r[6].split(":", 1)[1]
            c = conn.execute("SELECT name, status FROM pub.societies WHERE key = %s", (key,)).fetchone()
            if c:
                row["society"] = {"name": c[0], "status": c[1]}
        out["rows"].append(row)
    w = conn.execute(f"SELECT flags FROM {s}.watch WHERE link_id = %s", (link_id,)).fetchone()
    out["watch_flags"] = w[0] if w else []
    return out


def draw(conn, s: str, n: int = 100, seed: int = 7) -> list:
    """`n` confirmed name links (rules 1 and 2) at random, with their evidence."""
    ids = [r[0] for r in conn.execute(f"SELECT link_id FROM {s}.links WHERE grade = 'confirmed' AND rule IN ('full-name@1', 'name-and-address@1') ORDER BY link_id").fetchall()]
    random.Random(seed).shuffle(ids)
    return [evidence_for(conn, s, i) for i in ids[:n]]


def parse_verdict(text: str) -> dict:
    """The model's one JSON object; anything else is `contested` with the text kept (the safe direction)."""
    t = (text or "").strip()
    start, end = t.find("{"), t.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(t[start:end + 1])
            if obj.get("verdict") in VERDICTS:
                return {"verdict": obj["verdict"], "reasoning": str(obj.get("reasoning") or "")[:1000]}
        except ValueError:
            pass
    return {"verdict": "contested", "reasoning": f"unreadable answer: {t[:300]}"}


def ask(item: dict, *, url: str, model: str, post=None) -> dict:
    """One reading through the review model on the boxes (support.modelclient)."""
    from support import modelclient
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(item, default=str, ensure_ascii=False)}]
    out = modelclient.chat(url, lane="links", model=model, messages=messages, extra={"temperature": 0.2, "max_tokens": 600}, post=post)
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content", "")
    return parse_verdict(text)


def record(conn, s: str, readings: list, agent: str, web_searched: bool = False) -> int:
    n = 0
    with conn.cursor() as w:
        for r in readings:
            l = conn.execute(f"SELECT row_a, row_b FROM {s}.links WHERE link_id = %s", (int(r["link_id"]),)).fetchone()
            if not l or r.get("verdict") not in VERDICTS:
                continue
            w.execute(f"""INSERT INTO {s}.readings (link_id, row_a, row_b, agent, verdict, reasoning, web_searched)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                      (int(r["link_id"]), l[0], l[1], agent, r["verdict"], (r.get("reasoning") or "")[:2000], web_searched))
            n += 1
    conn.commit()
    return n


def run(conn, s: str, items: list, *, url: str, model: str, post=None, log=print) -> list:
    out = []
    for item in items:
        v = ask(item, url=url, model=model, post=post)
        out.append({"link_id": item["link_id"], **v})
        log(f"links.review: {item['link_id']}: {v['verdict']}")
    record(conn, s, out, f"{AGENT_VERSION} ({model})")
    return out


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    s = argv[argv.index("--schema") + 1] if "--schema" in argv else links.SCHEMA
    scratch = os.environ.get("QV4_SCRATCH") or os.path.join("/home/user/querynzv4-work/scratch", "links")
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        if "--draw" in argv:
            n = int(argv[argv.index("--draw") + 1])
            seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 7
            items = draw(conn, s, n, seed)
            os.makedirs(scratch, exist_ok=True)
            path = os.path.join(scratch, f"review-sample-{seed}.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, default=str, ensure_ascii=False) + "\n")
            print(json.dumps({"drawn": len(items), "file": path}))
            return 0
        if "--run" in argv:
            url, model = os.environ.get("QV4_MODEL_URL"), os.environ.get("QV4_MODEL")
            if not (url and model):
                print("links.review: QV4_MODEL_URL and QV4_MODEL are the worker's to give; refusing to pick a model server", file=sys.stderr)
                return 2
            with open(argv[argv.index("--run") + 1], encoding="utf-8") as f:
                items = [json.loads(l) for l in f if l.strip()]
            out = run(conn, s, items, url=url, model=model)
            print(json.dumps({"read": len(out)}))
            return 0
        if "--record" in argv:
            agent = argv[argv.index("--agent") + 1]
            with open(argv[argv.index("--record") + 1], encoding="utf-8") as f:
                readings = [json.loads(l) for l in f if l.strip()]
            print(json.dumps({"recorded": record(conn, s, readings, agent)}))
            return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
