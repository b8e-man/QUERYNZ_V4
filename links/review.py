"""The review agent (track C): reads the evidence the registers hold for a
pair of person rows and says whether it can trust the link that joins them.

    python -m links.review --score [--limit N] [--kind K] [--part i/n] [--run-id ID] [--schema S]
        read every test pair (links.test_pairs) through the review model, record
        each verdict in links.readings and the figures in links.scores
    python -m links.review --report [--run-id ID] [--schema S]
        the figures of a scoring run, by truth, kind and band, and the pass mark
    python -m links.review --watched [--limit N] [--schema S]
        read confirmed links the watch flagged, oldest unread first; record only
    python -m links.review --job [--schema S]
        what the scheduler's qv4-links-review job runs: QV4_ARGS picks the mode
        ({"mode": "score"|"watched"|"apply", "limit": N, "schema": S})
    python -m links.review --apply [--schema S]
        add a decision for each recorded split (behind the switch; see below)
    python -m links.review --draw N [--seed 7] [--schema S]      the old sample of confirmed links, as evidence JSON lines
    python -m links.review --run FILE [--schema S]               read the links in FILE (the first catalogue command)
    python -m links.review --record FILE --agent NAME [--schema S]

THE THREE VERDICTS match the decisions table (track C): `not the same` (the
evidence shows two people: that decision is added and the groups rebuild),
`contested` (the agent cannot trust the link; it drops to near and products
show a possible namesake), `no reason to doubt` (the link stays and the
reading is recorded). Both `not the same` and `contested` take the link
out of the walk that makes the groups, so both count as a split when the
agent is scored. Splitting is the safe direction.

HOW IT READS. A screen runs first, deterministic, on what the registers
state outright (the old healer's screen-then-re-read pattern): a pair the
source's own identifier joins is not doubted, and a pair whose two rows
file different middle names is two people by the register's own filing.
Everything else goes to the model on the review profile, which answers
ONE JSON object under a grammar (the old lesson: constrain the structured
layer, do not trust prompt compliance). The model sees registered offices
and roles, never a home address (hard limits 11 and 15).

MEASURED BEFORE IT ACTS (plan 4.3; the old refuter was measured on 13
cases). `--score` reads every test pair; the pass mark, a default until
Arthur rules (queue: the-review-agent-s-pass-mark), is fewer than 1 in 100
known-one-person pairs wrongly split; the share of known-two-people pairs
caught is reported and has no minimum. A changed judgment is a new
measurement: `fingerprint()` hashes everything that decides a verdict, and
`links.scores` records it with the figures.

APPLYING IS BEHIND A SWITCH THAT IS OFF: `links.SETTINGS["review_applies"]`.
`apply()` refuses while it is off, and refuses while the latest score of
this judgment has not passed. `links.check` fails if a reading has ever
become a decision while the switch is off.

THE WEB is searched only for evidence that two rows are different people,
with a name and a public role at most (hard limits 12 and 26), through the
fetch gate; every citation must be a page fetched in that run (the old
refuter's cite-or-drop rule). The gate has no search route yet (card
the-fetch-gate-has-no-search-route), so no reading here searches, and every
reading says so (`web_searched` false). `web_query()` and `cite_check()`
are the two rules, built and tested, waiting on the route.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import inspect
import json
import os
import random
import sys
import time

import links
from links import rules

VERDICTS = ("no reason to doubt", "contested", "not the same")
SPLITS = ("contested", "not the same")          # a reading that would take the link out of the groups
AGENT_VERSION = "review-agent@2"
RULE_SOURCE = "source-identifier@1"
PASS_MARK = {"wrongly_split_per_100": 1.0}     # default until Arthur rules: fewer than 1 in 100 one-person pairs wrongly split
MAX_TOKENS = 2800                               # the profile's reasoning budget (2048) and the answer
SYSTEM = """You review one pair of rows from New Zealand public registers (the companies register, incorporated societies, the Electoral Commission's returns, the Gazette). The two rows carry one name, and the question is whether they are ONE person or TWO.

You are given only what the registers state: the names as filed (given, middle, family), the roles, the companies or bodies each role sits on with their registered offices (a company's office, never a home), the dates, and how many register rows carry this name. Use nothing else. A name alone is never identity. How well known anyone is counts for nothing.

Answer with ONE of three verdicts:
- "not the same": the evidence SHOWS two people. Different middle names filed for the same first and last name; two roles that cannot be one person (two directors of one name standing at once on one company; two candidates of one name in different electorates at one election; dates that make one life impossible).
- "contested": you cannot trust the link on this evidence. A common name with nothing joining the roles; roles in different regions at once with no shared company or office; an office shared by many companies (an accountant's or a lawyer's) as the only thing in common; a middle name on one row and none on the other.
- "no reason to doubt": a middle name filed the same on both rows, or roles on one company or at one quiet office, and nothing above contests it.

Doubt is the safe direction: when the evidence is thin, say "contested", not "no reason to doubt". Never say "not the same" without naming what shows two people.
Answer with one JSON object and nothing else: {"verdict": "...", "reasoning": "<two sentences at most, naming the evidence>"}"""
VERDICT_SCHEMA = {
    "type": "object",
    "properties": {"verdict": {"type": "string", "enum": list(VERDICTS)},
                   "reasoning": {"type": "string", "maxLength": 600}},
    "required": ["verdict", "reasoning"],
    "additionalProperties": False,
}


# ── the evidence ────────────────────────────────────────────────────────────

def _row(conn, s: str, ref: str) -> dict | None:
    r = conn.execute(f"""SELECT register, view, name_filed, given, middle, family, has_middle, politician, entity_ref,
                                started_on, ended_on, election, electorate, fl_key, full_key
                         FROM {s}.rows WHERE ref = %s""", (ref,)).fetchone()
    if not r:
        return None
    row = {"ref": ref, "register": r[0], "view": r[1], "name_as_filed": r[2], "given": r[3], "middle": r[4], "family": r[5],
           "middle_name_filed": bool(r[6]), "politician": bool(r[7]), "from": str(r[9] or ""), "to": str(r[10] or ""),
           "election": r[11], "electorate": r[12], "_fl": r[13], "_full": r[14], "_entity": r[8]}
    ent = r[8] or ""
    if ent.startswith("companies:"):
        key = ent.split(":", 1)[1]
        c = conn.execute("SELECT name, entity_type, status, registered_on, removed_on FROM pub.companies WHERE key = %s", (key,)).fetchone()
        if c:
            row["company"] = {"name": c[0], "type": c[1], "status": c[2], "registered": str(c[3] or ""), "removed": str(c[4] or "")}
        offices = conn.execute("""SELECT line_1, line_2, line_3, line_4, postcode, started_on, in_latest
                                  FROM pub.company_addresses WHERE entity_key = %s ORDER BY started_on NULLS FIRST""", (key,)).fetchall()
        row["registered_offices"] = [{"address": " ".join(p for p in a[:5] if p), "from": str(a[5] or ""), "current": bool(a[6])} for a in offices][:6]
        row["_office_keys"] = {k for (k,) in conn.execute(f"SELECT address_key FROM {s}.entity_addresses WHERE entity_ref = %s", (ent,)).fetchall()}
    elif ent.startswith("societies:"):
        c = conn.execute("SELECT name, status FROM pub.societies WHERE key = %s", (ent.split(":", 1)[1],)).fetchone()
        if c:
            row["society"] = {"name": c[0], "status": c[1]}
    elif ent.startswith("parties:"):
        row["party"] = ent.split(":", 1)[1]
    elif ent.startswith("candidate_returns:"):
        t = conn.execute("SELECT year, surname, given_names, electorate, party FROM pub.candidate_return_totals WHERE key = %s",
                         (ent.split(":", 1)[1],)).fetchone()
        if t:
            row["candidate_return"] = {"year": t[0], "candidate": f"{t[2] or ''} {t[1] or ''}".strip(), "electorate": t[3], "party": t[4]}
    return row


def _name_counts(conn, s: str, fl_key: str, full_key: str) -> dict:
    n_fl = conn.execute(f"SELECT count(*) FROM {s}.rows WHERE view = 'directors' AND fl_key = %s", (fl_key,)).fetchone()[0] if fl_key else 0
    n_full = conn.execute(f"SELECT count(*) FROM {s}.rows WHERE kind = 'person' AND full_key = %s", (full_key,)).fetchone()[0] if full_key else 0
    return {"director_rows_with_this_first_and_last_name": int(n_fl), "band": links.band_of(int(n_fl)),
            "register_rows_with_this_full_name": int(n_full)}


def _regions(conn, s: str, ref: str) -> list:
    r = conn.execute(f"SELECT regions FROM {s}.row_regions WHERE ref = %s", (ref,)).fetchone()
    return list(r[0]) if r and r[0] else []


def _public(row: dict) -> dict:
    return {k: v for k, v in row.items() if not k.startswith("_")}


def _overlap(a: dict, b: dict) -> bool:
    """Whether two roles' filed windows stand at once: an open end stands today."""
    def window(r):
        return (r.get("from") or "0000-00-00", r.get("to") or "9999-12-31")
    (fa, ta), (fb, tb) = window(a), window(b)
    return fa <= tb and fb <= ta


def evidence_for_pair(conn, s: str, row_a: str, row_b: str) -> dict:
    """What a reader sees for two rows: the rows, their roles and the
    registered offices of the companies those roles sit on; the link that
    joins them, if any, with the watch's flags; what the names share."""
    a, b = _row(conn, s, row_a), _row(conn, s, row_b)
    if not a or not b:
        raise LookupError(f"a row outside {s}.rows: {row_a if not a else row_b}")
    l = conn.execute(f"SELECT link_id, rule, evidence, grade FROM {s}.links WHERE row_a = %s AND row_b = %s AND grade = 'confirmed' "
                     f"ORDER BY CASE rule WHEN %s THEN 0 WHEN %s THEN 1 ELSE 2 END LIMIT 1",
                     (*links.pair(row_a, row_b), rules.RULE_FULL, rules.RULE_ADDRESS)).fetchone()
    out = {"rows": [_public(a), _public(b)], "name": _name_counts(conn, s, a["_fl"], a["_full"]),
           "link": None, "watch_flags": [], "_a": a, "_b": b}
    if l:
        w = conn.execute(f"SELECT flags FROM {s}.watch WHERE link_id = %s", (l[0],)).fetchone()
        out["link"] = {"link_id": int(l[0]), "rule": l[1], "rule_evidence": l[2]}
        out["watch_flags"] = list(w[0]) if w and w[0] else []
    shared = (a.get("_office_keys") or set()) & (b.get("_office_keys") or set())
    same_body = bool(a["_entity"] and a["_entity"] == b["_entity"])
    at_once = same_body and a["view"] == b["view"] and _overlap(a, b)
    out["shared"] = {"first_and_last_name": a["_fl"] == b["_fl"] and bool(a["_fl"]),
                     "same_role_on_same_body_at_once": at_once,     # a register lists one person once per body at a time
                     "full_name_with_middle": bool(a["middle_name_filed"] and b["middle_name_filed"] and a["_full"] == b["_full"]),
                     "middle_names_differ": bool(a["middle_name_filed"] and b["middle_name_filed"] and a["_full"] != b["_full"]),
                     "same_company_or_body": same_body,
                     "registered_offices_shared": len(shared),
                     "regions_of_current_roles": {"a": _regions(conn, s, row_a), "b": _regions(conn, s, row_b)}}
    return out


def evidence_for(conn, s: str, link_id: int) -> dict:
    """The evidence for one stored link (the first catalogue command's shape)."""
    l = conn.execute(f"SELECT row_a, row_b FROM {s}.links WHERE link_id = %s", (link_id,)).fetchone()
    if not l:
        raise LookupError(f"no link {link_id}")
    out = evidence_for_pair(conn, s, l[0], l[1])
    out["link_id"] = link_id
    return out


def shown(evidence: dict) -> dict:
    """What is sent to the model and recorded: the evidence without the private working keys."""
    return {k: v for k, v in evidence.items() if not k.startswith("_")}


# ── the screen ──────────────────────────────────────────────────────────────

def screen(evidence: dict) -> dict | None:
    """What the registers state outright, before any model is asked: a
    verdict with its reason, or None when the model must read. Kept to
    what no reader could reasonably contradict."""
    link, sh = evidence.get("link") or {}, evidence.get("shared") or {}
    if link.get("rule") in (RULE_SOURCE, rules.RULE_NUMBER):
        return {"verdict": "no reason to doubt", "reasoning": f"the source's own identifier joins the two rows ({link['rule']})", "screen": "source-identifier"}
    if sh.get("middle_names_differ"):
        return {"verdict": "not the same", "reasoning": "the two rows file different middle names for one first and last name", "screen": "middle-names-differ"}
    if sh.get("first_and_last_name") is False:
        return {"verdict": "not the same", "reasoning": "the two rows do not share a first and last name", "screen": "names-differ"}
    return None


# ── the model ───────────────────────────────────────────────────────────────

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
    """One reading through the review model on the boxes (support.modelclient),
    the answer held to the verdict grammar. Returns the verdict, the served
    model and the seconds."""
    from support import modelclient
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(shown(item), default=str, ensure_ascii=False)}]
    extra = {"temperature": 0.1, "max_tokens": MAX_TOKENS,
             "response_format": {"type": "json_schema", "json_schema": {"name": "verdict", "strict": True, "schema": VERDICT_SCHEMA}}}
    t0 = time.monotonic()
    out = modelclient.chat(url, lane="links", model=model, messages=messages, extra=extra, post=post)
    text = (out.get("choices") or [{}])[0].get("message", {}).get("content", "")
    v = parse_verdict(text)
    v.update(model=out.get("model") or model, seconds=round(time.monotonic() - t0, 1), screen="model")
    return v


WAIT_FOR_MODEL_S = 5400         # a session's scoring outlives a card swap: the planner may lend the card away and bring the profile back
RETRY_EVERY_S = 60


def read(evidence: dict, *, url: str = None, model: str = None, post=None, wait: float = 0, sleep=time.sleep, served=None, log=print) -> dict:
    """The agent's verdict on one pair: the screen, else the model. With
    `wait`, a model that has gone away (the card swapped, the server down)
    is retried every minute for that long before the error is raised."""
    v = screen(evidence)
    if v is not None:
        return {**v, "model": None, "seconds": 0.0}
    if not (url and model):
        raise RuntimeError("the model is needed and QV4_MODEL_URL / QV4_MODEL were not given")
    t0 = time.monotonic()
    while True:
        try:
            return ask(evidence, url=url, model=model, post=post)
        except Exception as exc:        # noqa: BLE001 — recorded by the model client; retried while the profile is away
            from support import modelclient
            if isinstance(exc, modelclient.Refused) or time.monotonic() - t0 >= wait:
                raise
            log(f"links.review: the model is away ({type(exc).__name__}: {str(exc)[:120]}); waiting for it")
            # wait on the server's model list (a read, no prompt sent), so no evidence goes to whatever holds the port meanwhile
            while time.monotonic() - t0 < wait:
                sleep(RETRY_EVERY_S)
                try:
                    if (served or modelclient.served_model)(url) == model:
                        break
                except Exception:       # noqa: BLE001 — nothing answers yet
                    pass
            else:
                raise


def fingerprint() -> str:
    """A hash of everything that decides a verdict (the old refuter's lesson:
    a measurement authorises the judgment it measured, not the file that has
    since replaced it). The model name is recorded beside it, not in it."""
    h = hashlib.sha256()
    h.update(SYSTEM.encode())
    h.update(json.dumps(VERDICT_SCHEMA, sort_keys=True).encode())
    h.update(f"{AGENT_VERSION}|{MAX_TOKENS}|{SPLITS}".encode())
    for fn in (screen, evidence_for_pair, _overlap, _row, _name_counts, parse_verdict, ask):   # not read(): its waiting is operational
        h.update(inspect.getsource(fn).encode())
    return h.hexdigest()[:16]


# ── the web, held until the gate has a search route ─────────────────────────

def web_query(name: str, role: str = "") -> str:
    """The one shape a web query may take: a name and a public role at most
    (hard limit 12). Nothing else is ever passed: no address, no company
    number, nothing from the sealed store."""
    q = " ".join((name or "").split())
    if not q:
        raise ValueError("a query carries a name")
    if role:
        q += " " + " ".join(role.split())
    if any(ch.isdigit() for ch in q):
        raise ValueError("a query carries a name and a public role at most; a number is neither")
    return q


def cite_check(citations: list, fetched: set) -> tuple:
    """(kept, dropped): a citation is kept only if its page was fetched in
    this run (the old refuter's cite-or-drop rule)."""
    kept = [c for c in (citations or []) if str(c) in fetched]
    return kept, [c for c in (citations or []) if str(c) not in fetched]


def search(query: str):
    raise NotImplementedError("the fetch gate has no search route (card the-fetch-gate-has-no-search-route); no reading searches")


# ── recording ───────────────────────────────────────────────────────────────

def record_reading(conn, s: str, *, row_a: str, row_b: str, link_id: int, verdict: dict, evidence: dict, agent: str,
                   run_id: str, pair: dict = None) -> int:
    with conn.cursor() as w:
        w.execute(f"""INSERT INTO {s}.readings (link_id, row_a, row_b, agent, verdict, reasoning, web_searched, run_id, pair_id,
                                                kind, truth, band, screen, evidence, citations, model, seconds)
                      VALUES (%s, %s, %s, %s, %s, %s, false, %s, %s, %s, %s, %s, %s, %s::jsonb, '[]'::jsonb, %s, %s) RETURNING reading_id""",
                  (int(link_id or 0), row_a, row_b, agent, verdict["verdict"], (verdict.get("reasoning") or "")[:2000], run_id,
                   (pair or {}).get("pair_id"), (pair or {}).get("kind"), (pair or {}).get("truth"), (pair or {}).get("band"),
                   verdict.get("screen") or "model", json.dumps(shown(evidence), default=str), verdict.get("model"), verdict.get("seconds")))
        rid = w.fetchone()[0]
    conn.commit()
    return int(rid)


def record(conn, s: str, readings: list, agent: str, web_searched: bool = False) -> int:
    """Verdicts a reader wrote into a file, one per link (the first command's shape)."""
    n = 0
    with conn.cursor() as w:
        for r in readings:
            l = conn.execute(f"SELECT row_a, row_b FROM {s}.links WHERE link_id = %s", (int(r["link_id"]),)).fetchone()
            if not l or r.get("verdict") not in VERDICTS:
                continue
            w.execute(f"""INSERT INTO {s}.readings (link_id, row_a, row_b, agent, verdict, reasoning, web_searched, screen)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, 'file')""",
                      (int(r["link_id"]), l[0], l[1], agent, r["verdict"], (r.get("reasoning") or "")[:2000], web_searched))
            n += 1
    conn.commit()
    return n


def agent_name(model: str = None) -> str:
    return f"{AGENT_VERSION} ({model})" if model else AGENT_VERSION


def new_run_id(prefix: str) -> str:
    return f"{prefix}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"


# ── scoring on the test pairs ───────────────────────────────────────────────

def score(conn, s: str, *, url: str = None, model: str = None, run_id: str = None, limit: int = None, kind: str = None,
          part: str = None, post=None, log=print) -> dict:
    """Read every test pair through the agent and record each verdict under
    `run_id`. Resumable: a pair already read in this run is skipped, so a
    run that lost its model carries on where it stopped. `part` is "i/n":
    this process takes the pairs whose id leaves i modulo n, so one run can
    use every slot of the profile. Then `report`."""
    run_id = run_id or new_run_id("score")
    agent = agent_name(model)
    q = f"SELECT pair_id, kind, truth, band, row_a, row_b FROM {s}.test_pairs WHERE NOT EXISTS (SELECT 1 FROM {s}.readings r WHERE r.run_id = %s AND r.pair_id = test_pairs.pair_id)"
    args = [run_id]
    if kind:
        q += " AND kind = %s"
        args.append(kind)
    if part:
        i, n = (int(x) for x in part.split("/"))
        q += f" AND mod(pair_id, {n}) = {i}"
    q += " ORDER BY kind, band, pair_id"
    if limit:
        q += f" LIMIT {int(limit)}"
    todo = conn.execute(q, args).fetchall()
    t0 = time.monotonic()
    n = skipped = 0
    for pair_id, kind_, truth, band, a, b in todo:
        try:
            ev = evidence_for_pair(conn, s, a, b)
        except LookupError as e:
            log(f"links.review: pair {pair_id}: {e}")
            skipped += 1
            continue
        v = read(ev, url=url, model=model, post=post, wait=WAIT_FOR_MODEL_S if post is None else 0, log=log)
        link_id = (ev.get("link") or {}).get("link_id") or 0
        record_reading(conn, s, row_a=a, row_b=b, link_id=link_id, verdict=v, evidence=ev, agent=agent, run_id=run_id,
                       pair={"pair_id": pair_id, "kind": kind_, "truth": truth, "band": band})
        n += 1
        if n % 25 == 0:
            log(f"links.review: {run_id}: {n} of {len(todo)} read ({time.monotonic() - t0:.0f} s)")
    out = {"run_id": run_id, "read": n, "skipped": skipped, "seconds": round(time.monotonic() - t0, 1)}
    out["report"] = report(conn, s, run_id, model=model, log=log)
    return out


def report(conn, s: str, run_id: str, model: str = None, log=print) -> dict:
    """The figures of a scoring run: by truth and band, by kind, and by
    whether the screen or the model decided; the pass mark; written to
    `links.scores` with the judgment's fingerprint."""
    rows = conn.execute(f"""SELECT kind, truth, band, screen, verdict, (evidence->'shared'->>'full_name_with_middle')::boolean
                            FROM {s}.readings WHERE run_id = %s AND pair_id IS NOT NULL""", (run_id,)).fetchall()
    if not rows:
        return {"run_id": run_id, "pairs": 0, "note": "no readings under this run"}

    def tally(sel) -> dict:
        t = {"pairs": 0, "not the same": 0, "contested": 0, "no reason to doubt": 0, "by the screen": 0}
        for kind, truth, band, scr, v, _ in sel:
            t["pairs"] += 1
            t[v] += 1
            if scr != "model":
                t["by the screen"] += 1
        t["split"] = t["not the same"] + t["contested"]
        if t["pairs"]:
            t["split_per_100"] = round(100.0 * t["split"] / t["pairs"], 2)
        return t

    out = {"run_id": run_id, "agent": AGENT_VERSION, "fingerprint": fingerprint(), "model": model, "pairs": len(rows),
           "pass_mark": {**PASS_MARK, "on": "pairs known to be one person; a split is `not the same` or `contested`",
                         "note": "a default until Arthur rules (queue: the-review-agent-s-pass-mark)"},
           "one_person": {}, "two_people": {}, "by_kind": {}, "model_alone": {}}
    for truth, key in (("one person", "one_person"), ("two people", "two_people")):
        sel = [r for r in rows if r[1] == truth]
        out[key]["all"] = tally(sel)
        for band in ("rare", "middling", "common"):
            bsel = [r for r in sel if r[2] == band]
            if bsel:
                out[key][band] = tally(bsel)
        msel = [r for r in sel if r[3] == "model"]
        if msel:
            out["model_alone"][key] = tally(msel)
            for band in ("rare", "middling", "common"):
                bsel = [r for r in msel if r[2] == band]
                if bsel:
                    out["model_alone"][f"{key}_{band}"] = tally(bsel)
    for kind in sorted({r[0] for r in rows}):
        ksel = [r for r in rows if r[0] == kind]
        out["by_kind"][kind] = {"truth": ksel[0][1], **tally(ksel)}
        if kind == "two-directors-one-company":
            clean = [r for r in ksel if not r[5]]
            out["by_kind"][kind]["without_identical_full_name_and_middle"] = tally(clean)
    one = out["one_person"].get("all") or {}
    two = out["two_people"].get("all") or {}
    out["wrongly_split_per_100_one_person_pairs"] = one.get("split_per_100")
    out["caught_per_100_two_people_pairs"] = two.get("split_per_100")
    out["passed"] = bool(one.get("pairs")) and one["split_per_100"] < PASS_MARK["wrongly_split_per_100"]
    conn.execute(f"""INSERT INTO {s}.scores (run_id, agent, fingerprint, model, figures, passed) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
                     ON CONFLICT (run_id) DO UPDATE SET figures = EXCLUDED.figures, passed = EXCLUDED.passed, model = EXCLUDED.model,
                     fingerprint = EXCLUDED.fingerprint, scored_at = now()""",
                 (run_id, AGENT_VERSION, out["fingerprint"], model, json.dumps(out, default=str), out["passed"]))
    conn.commit()
    log(f"links.review: {run_id}: one-person pairs {one.get('pairs', 0)}, wrongly split {one.get('split', 0)} "
        f"({one.get('split_per_100')} per 100); two-people pairs {two.get('pairs', 0)}, caught {two.get('split', 0)} "
        f"({two.get('split_per_100')} per 100); {'PASSED' if out['passed'] else 'not passed'}")
    return out


# ── the watched links, recorded only ────────────────────────────────────────

def watched(conn, s: str, *, url: str = None, model: str = None, limit: int = 200, run_id: str = None, post=None, log=print) -> dict:
    """Read confirmed name links the watch flagged, those with no reading by
    this agent first, oldest link first. Recorded, never applied here."""
    run_id = run_id or new_run_id("watched")
    agent = agent_name(model)
    todo = conn.execute(f"""SELECT l.link_id, l.row_a, l.row_b FROM {s}.links l JOIN {s}.watch w ON w.link_id = l.link_id
                            WHERE l.grade = 'confirmed' AND w.flags <> '[]'::jsonb
                              AND NOT EXISTS (SELECT 1 FROM {s}.readings r WHERE r.row_a = l.row_a AND r.row_b = l.row_b AND r.agent LIKE %s)
                            ORDER BY l.link_id LIMIT %s""", (AGENT_VERSION + "%", int(limit))).fetchall()
    n = 0
    tally = {v: 0 for v in VERDICTS}
    for link_id, a, b in todo:
        ev = evidence_for_pair(conn, s, a, b)
        v = read(ev, url=url, model=model, post=post, wait=WAIT_FOR_MODEL_S if post is None else 0, log=log)
        record_reading(conn, s, row_a=a, row_b=b, link_id=link_id, verdict=v, evidence=ev, agent=agent, run_id=run_id)
        tally[v["verdict"]] += 1
        n += 1
    log(f"links.review: {run_id}: {n} watched links read: {tally}")
    return {"run_id": run_id, "read": n, "verdicts": tally}


# ── the apply path, behind the switch ───────────────────────────────────────

def applies() -> bool:
    return links.SETTINGS.get("review_applies") == "on"


def latest_pass(conn, s: str) -> dict | None:
    """The latest score of THIS judgment (agent and fingerprint) that passed, or None."""
    r = conn.execute(f"SELECT run_id, figures FROM {s}.scores WHERE agent = %s AND fingerprint = %s AND passed ORDER BY scored_at DESC LIMIT 1",
                     (AGENT_VERSION, fingerprint())).fetchone()
    return {"run_id": r[0], "figures": r[1]} if r else None


def apply(conn, s: str, log=print, rebuild=None) -> dict:
    """A split is a decision added, then a rebuild. Refuses while the switch
    is off, and while the latest score of this judgment has not passed.
    Each recorded split (a reading of a watched link, not of a test pair)
    without a decision by this agent becomes one decision, `made_by` this
    agent, `made_on` the reading; then the groups rebuild."""
    if not applies():
        raise RuntimeError("links.SETTINGS['review_applies'] is off: readings are recorded and never applied")
    passed = latest_pass(conn, s)
    if not passed:
        raise RuntimeError(f"no passing score of {AGENT_VERSION} at fingerprint {fingerprint()}: the agent has not been measured as it stands")
    rows = conn.execute(f"""SELECT r.reading_id, r.row_a, r.row_b, r.verdict, r.reasoning, r.run_id, r.evidence, r.citations
                            FROM {s}.readings r
                            WHERE r.pair_id IS NULL AND r.agent LIKE %s AND r.verdict IN ('contested', 'not the same')
                              AND NOT EXISTS (SELECT 1 FROM {s}.decisions d WHERE d.row_a = r.row_a AND d.row_b = r.row_b AND d.made_by = %s)
                            ORDER BY r.reading_id""", (AGENT_VERSION + "%", AGENT_VERSION)).fetchall()
    n = 0
    with conn.cursor() as w:
        for rid, a, b, v, reasoning, run_id, evidence, citations in rows:
            made_on = {"reading_id": int(rid), "run_id": run_id, "reasoning": reasoning, "evidence": evidence, "citations": citations or [],
                       "applied_under": {"switch": "on", "score_run": passed["run_id"], "fingerprint": fingerprint()}}
            errs = links.check_decision(v, AGENT_VERSION, made_on)
            if errs:
                raise ValueError(f"reading {rid}: {errs}")
            w.execute(f"INSERT INTO {s}.decisions (row_a, row_b, verdict, made_by, made_on) VALUES (%s, %s, %s, %s, %s::jsonb)",
                      (a, b, v, AGENT_VERSION, json.dumps(made_on, default=str)))
            n += 1
    conn.commit()
    out = {"decisions_added": n, "score_run": passed["run_id"]}
    if n:
        from links import build
        out["groups"] = (rebuild or build.build_groups)(conn, s, log)
    log(f"links.review: applied {n} decisions under score {passed['run_id']}")
    return out


# ── the first command's sample of confirmed links ───────────────────────────

def draw(conn, s: str, n: int = 100, seed: int = 7) -> list:
    """`n` confirmed name links (rules 1 and 2) at random, with their evidence."""
    ids = [r[0] for r in conn.execute(f"SELECT link_id FROM {s}.links WHERE grade = 'confirmed' AND rule IN (%s, %s) ORDER BY link_id",
                                      (rules.RULE_FULL, rules.RULE_ADDRESS)).fetchall()]
    random.Random(seed).shuffle(ids)
    return [shown(evidence_for(conn, s, i)) for i in ids[:n]]


def run(conn, s: str, items: list, *, url: str, model: str, post=None, log=print) -> list:
    out = []
    for item in items:
        v = ask(item, url=url, model=model, post=post)
        out.append({"link_id": item["link_id"], "verdict": v["verdict"], "reasoning": v["reasoning"]})
        log(f"links.review: {item['link_id']}: {v['verdict']}")
    record(conn, s, out, agent_name(model))
    return out


# ── the command line ────────────────────────────────────────────────────────

def _model_env() -> tuple:
    url, model = os.environ.get("QV4_MODEL_URL"), os.environ.get("QV4_MODEL")
    if not (url and model):
        print("links.review: QV4_MODEL_URL and QV4_MODEL are the worker's to give; refusing to pick a model server", file=sys.stderr)
        return None, None
    return url, model


def _opt(argv: list, flag: str, default=None):
    return argv[argv.index(flag) + 1] if flag in argv else default


def main(argv=None) -> int:
    from support import db
    argv = sys.argv[1:] if argv is None else argv
    args = {}
    if "--job" in argv:
        try:
            args = json.loads(os.environ.get("QV4_ARGS") or "{}")
        except ValueError:
            args = {}
    s = _opt(argv, "--schema", args.get("schema") or links.SCHEMA)
    scratch = os.environ.get("QV4_SCRATCH") or os.path.join("/home/user/querynzv4-work/scratch", "links")
    mode = args.get("mode", "watched") if "--job" in argv else None
    url = model = None
    if any(a in argv for a in ("--score", "--watched", "--run")) or mode in ("score", "watched"):
        url, model = _model_env()
        if not url:
            return 2
    with db.connect(db.OWNER_KEY, "querynz_v4") as conn:
        conn.execute("SET statement_timeout = 0")
        if "--part" not in argv:         # parts run side by side; two DDL passes at once deadlock on the same table
            conn.execute(links.ddl(s))
            conn.commit()
        if "--score" in argv or mode == "score":
            limit = _opt(argv, "--limit", args.get("limit"))
            out = score(conn, s, url=url, model=model, run_id=_opt(argv, "--run-id", args.get("run_id")),
                        limit=int(limit) if limit else None, kind=_opt(argv, "--kind", args.get("kind")), part=_opt(argv, "--part", args.get("part")))
            print(json.dumps(out, indent=1, default=str))
            return 0
        if "--report" in argv:
            run_id = _opt(argv, "--run-id")
            if not run_id:
                r = conn.execute(f"SELECT run_id FROM {s}.scores ORDER BY scored_at DESC LIMIT 1").fetchone()
                run_id = r[0] if r else None
            print(json.dumps(report(conn, s, run_id, model=_opt(argv, "--model")) if run_id else {"note": "no scoring run"}, indent=1, default=str))
            return 0
        if "--watched" in argv or mode == "watched":
            print(json.dumps(watched(conn, s, url=url, model=model, limit=int(_opt(argv, "--limit", args.get("limit") or 200))), default=str))
            return 0
        if "--apply" in argv or mode == "apply":
            print(json.dumps(apply(conn, s), default=str))
            return 0
        if "--draw" in argv:
            n, seed = int(_opt(argv, "--draw")), int(_opt(argv, "--seed", 7))
            items = draw(conn, s, n, seed)
            os.makedirs(scratch, exist_ok=True)
            path = os.path.join(scratch, f"review-sample-{seed}.jsonl")
            with open(path, "w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, default=str, ensure_ascii=False) + "\n")
            print(json.dumps({"drawn": len(items), "file": path}))
            return 0
        if "--run" in argv:
            with open(_opt(argv, "--run"), encoding="utf-8") as f:
                items = [json.loads(l) for l in f if l.strip()]
            print(json.dumps({"read": len(run(conn, s, items, url=url, model=model))}))
            return 0
        if "--record" in argv:
            with open(_opt(argv, "--record"), encoding="utf-8") as f:
                readings = [json.loads(l) for l in f if l.strip()]
            print(json.dumps({"recorded": record(conn, s, readings, _opt(argv, "--agent"))}))
            return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
