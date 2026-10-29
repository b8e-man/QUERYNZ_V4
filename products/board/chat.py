"""The chat pane's server half (ruling 122): a question about the published
registers, answered by the chat model from what the board's own functions
return, each fact cited as a row of a view.

The browser posts the whole thread (it lives in the browser's
sessionStorage, static/chat.js) to POST /chat; the server keeps no table of
questions and logs no question text. The answer comes from the chat model
(Flash-Next on Radiance, ruling 121) through support.modelclient.chat, lane
`board-chat`: the model named and read back, a local address only, every
call in the calls ledger with no prompt (hard limit 10). The model may call
four tools, at most ROUNDS model calls a question:

  registers  the catalogue: each register held, its views, each view's rows
  search     the board's own search over the pub views (search.search, the
             term, the registers and the fields a reader could type), the
             rows grouped by register with their view, key and title, and
             the entity groups they fall in (people.gather), cut to a size
  row        one row's shown fields through panes.shown (a suppressed name
             or a withheld text never leaves), its citation, its far rows
  dossier    an entity's (or a lone row's) rows and money, as dossier.gather
             gives them

Every tool reads on the product reader, the pub views alone. A column whose
name says it is an address is read only where catalogue.ADDRESS_COLUMNS
lists it, as the field search reads one, and a text a lane's shape check
flags as naming an address (a diary's location among them, ruling 102) is
not passed to the model.

The answer's citations, `[view:key]`, become the board's own row links
(panes.href with that one step); a citation naming no published row is
shown struck, "not a row". With the model down or another model answering,
the answer is NOT_RUNNING and nothing else changes."""
from __future__ import annotations

import datetime as dt
import decimal
import json
import os
import re
import threading
import time
import urllib.error

from support import modelclient
from products.board import catalogue as cat
from products.board import db, dossier, panes, people, search

URL = os.environ.get("QV4_CHAT_URL") or "http://127.0.0.1:8060/v1/chat/completions"
MODEL = os.environ.get("QV4_CHAT_MODEL") or "qwen4exp"
LANE = "board-chat"
ROUNDS = 6                  # model calls a question, at most; the last is asked to answer with no tool
CALL_S = 60.0               # one model call's time limit
NOT_RUNNING = "the chat model is not running"
NOT_A_ROW = "not a row"
THREAD_TURNS = 12           # the newest messages of the thread passed to the model
TURN_CHARS = 4000           # one message of the thread, cut to this
QUESTION_CHARS = 2000       # the question itself
RESULT_CHARS = 6000         # one tool's answer as the model reads it (the model holds 16,384 tokens in all)
SEARCH_ROWS = 8             # rows read per view by the search tool
SEARCH_ENTITIES = 15        # entity groups the search tool lists
DOSSIER_ROWS = 40           # rows the dossier tool lists
TEXT_CHARS = 1200           # a long text column, cut, in the row tool
ANSWER_TOKENS = 1500
CHILD_ROWS = 25             # rows of each join (a company's directors, its shareholders) the row tool lists
ANSWER_NOW = ("No more lookups: answer now from the tool results above, in the style the system message asks, "
              "citing rows as [view:key]. Write prose, not a tool call.")
#: a column whose name says it holds an address: read only where catalogue.ADDRESS_COLUMNS lists it
ADDRESS_NAME = re.compile(r"address|residential|street|suburb|postal", re.I)
WITHHELD_ADDRESS = "not passed to the chat: the lane's shape check says it names an address"

SYSTEM = """You answer Arthur's questions about QueryNZ, an estate of New Zealand public records: registers copied \
from public sources (companies, charities, party donation returns, the Gazette, Parliament, ministers' diaries and \
more), each published as views of rows. Every row has a view and a key and cites the document it came from.

You answer ONLY from what your tools return in this conversation: registers (what is held), search (the board's own \
search), row (one row's fields and citation), dossier (an entity's rows and money). Use the tools before answering; \
search first, then open rows or dossiers you need. Never answer from your own knowledge.

Cite every fact with the row it came from, written exactly [view:key] using the view and key the tools gave, for \
example [companies:9429037782269]. Several rows: [view:key][view:key]. A line you cannot cite to a row, write \
"(uncited)" at its end.

Never guess a link between people: the same name in two registers is not the same person. Say two rows belong \
together only where the tools show them in one entity group. Treat a \
suppressed name as suppressed; never try to recover it.

When the registers do not hold the answer, say so in one sentence.

Answer in very concise prose: one to three plain sentences carrying the facts asked for, each cited inline, and \
nothing else. Do not describe the registers, the estate, the links lane, your tools or your search, and do not \
explain how you found the answer or what else the registers hold, unless the question asks. No preamble, no \
heading, no closing remark, no table; a list only when the question asks for several items, one short line each. \
Arthur reads many answers a day: the shortest correct answer is the right one."""

TOOLS = [
    {"type": "function", "function": {
        "name": "registers",
        "description": "The catalogue: each register the estate holds, its published views and each view's row count.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "search",
        "description": ("The board's search over every published view: rows whose text holds every word of the term, "
                        "grouped by register, each with its view, key and title, and the entity groups (the links "
                        "lane's) the rows fall in. Optional fields narrow it as the board's expanded search does."),
        "parameters": {"type": "object", "properties": {
            "term": {"type": "string", "description": "words to find, e.g. a person's or company's name"},
            "registers": {"type": "array", "items": {"type": "string"},
                          "description": "register names from the registers tool; omit to search all"},
            "first": {"type": "string"}, "middle": {"type": "string"}, "last": {"type": "string"},
            "org": {"type": "string", "description": "an organisation's name"},
            "year": {"type": "string"}},
            "required": ["term"]}}},
    {"type": "function", "function": {
        "name": "row",
        "description": "One row's fields as the board shows them, its source citation, and the rows it names.",
        "parameters": {"type": "object", "properties": {
            "ref": {"type": "string", "description": "view:key, as search gave it"}}, "required": ["ref"]}}},
    {"type": "function", "function": {
        "name": "dossier",
        "description": ("An entity's dossier: its names as filed, its rows across registers, its donations by year "
                        "as filed. Give an entity id (entity:<group id>) from search, or a row's view:key."),
        "parameters": {"type": "object", "properties": {
            "id": {"type": "string", "description": "entity:<group id> or view:key"}}, "required": ["id"]}}},
]


# ── the tools ───────────────────────────────────────────────────────────────

def plain(x):
    """A value as JSON can carry it."""
    if isinstance(x, (dt.date, dt.datetime)):
        return x.isoformat()
    if isinstance(x, decimal.Decimal):
        return str(x)
    if isinstance(x, (list, tuple)):
        return [plain(y) for y in x]
    if isinstance(x, dict):
        return {str(k): plain(y) for k, y in x.items()}
    return x


def ref_of(v: cat.View, r: dict) -> str:
    return f"{v.name}:{r['key']}"


def readable(v: cat.View, column: str) -> bool:
    """Whether the chat may read this column: an address-named column only
    where ADDRESS_COLUMNS lists it, as the field search reads one."""
    return not ADDRESS_NAME.search(column) or (v.name, column) in cat.ADDRESS_COLUMNS


def flagged(v: cat.View, r: dict, column: str) -> bool:
    """A text the lane's shape check flags as naming an address (ruling 102)."""
    return any(c == column and r.get(flag) for c, flag, _ in v.flags)


def value_of(v: cat.View, r: dict, column: str, cut: int = 0):
    """What the chat reads of one column: panes.shown's value (a suppressed
    name and a withheld text replaced), or None where it may not read it."""
    if not readable(v, column):
        return None
    if flagged(v, r, column):
        return WITHHELD_ADDRESS
    x = plain(panes.shown(v, r, column))
    if cut and isinstance(x, str) and len(x) > cut:
        x = x[:cut] + f"… ({len(x):,} characters; the rest on the row's pane)"
    return x


_COUNTS = {"at": 0.0, "answer": None}
_COUNTS_LOCK = threading.Lock()
COUNTS_S = 600              # the catalogue's row counts are read once in this long


def tool_registers(conn) -> dict:
    with _COUNTS_LOCK:
        if _COUNTS["answer"] is not None and time.monotonic() - _COUNTS["at"] < COUNTS_S:
            return _COUNTS["answer"]
        held = db.pub_views(conn)
        out = []
        for register, words in cat.REGISTERS:
            views = [v for v in cat.views_of(register) if v.name in held]
            if not views:
                out.append({"register": register, "name": words, "held": False})
                continue
            out.append({"register": register, "name": words, "held": True,
                        "views": [{"view": v.name, "kind": v.kind,
                                   "rows": int(db.rows(conn, f"select count(*) as n from pub.{v.name}")[0]["n"])} for v in views]})
        _COUNTS.update(at=time.monotonic(), answer={"registers": out})
        return _COUNTS["answer"]


def tool_search(conn, term: str = "", registers=None, **fields) -> dict:
    term = " ".join(str(term or "").split())[:200]
    held = db.pub_views(conn)
    regs = search.held_registers(held)
    if registers:
        regs = [r for r in regs if r in set(registers)]
    asked = {f: " ".join(str(fields.get(f) or "").split())[:search.FIELD_MAX] for f, _ in search.FIELDS if fields.get(f)}
    if not regs:
        return {"error": "no register of that name is held; call registers for the names"}
    if not (term or asked):
        return {"error": "give a term"}
    res = search.search(conn, term, limit=SEARCH_ROWS, registers=tuple(regs), fields=asked)
    out, hits = {}, []
    for register in regs:
        for v, total, rows in res.get(register) or ():
            out.setdefault(register, []).append({"view": v.name, "rows_matching": total, "shown": len(rows),
                                                 "rows": [{"ref": ref_of(v, r), "title": panes.title_of(v, r)} for r in rows]})
            hits += [(v, r) for r in rows]
    g = people.gather(conn, hits, people.named_groups(conn, term, asked, regs))
    ents = []
    for gid, d in list(g["entity"].items())[:SEARCH_ENTITIES]:
        ents.append({"id": people.entity_id(gid), "label": d["label"], "size": d["count"], "what": d.get("what") or "",
                     "registers": d.get("registers_named") or [], "contested": d.get("contested", False),
                     "matching_rows": sorted(nid for nid, x in g["group"].items() if x == gid)})
    return {"term": term, "fields": asked, "by_register": out, "entity_groups": ents,
            "entity_groups_more": max(0, len(g["entity"]) - SEARCH_ENTITIES),
            "note": "an entity group is the links lane's; rows in no group are not linked to anyone"}


def tool_row(conn, ref: str = "") -> dict:
    view, _, key = str(ref or "").strip().strip("[]").partition(":")
    v = cat.BY_NAME.get(view)
    r = search.row(conn, view, key) if v and key else None
    if r is None:
        return {"error": f"{ref!r} is not a row of a published view"}
    fields = {}
    for label, c in v.fields:
        x = value_of(v, r, c)
        if x not in (None, ""):
            fields[label] = x
    for label, c in v.dates:
        if r.get(c) not in (None, ""):
            fields[label] = plain(r.get(c))
    for label, c, _ in v.text:
        x = value_of(v, r, c, cut=TEXT_CHARS)
        if x not in (None, ""):
            fields[label] = x
    cite = {"document": r.get("document"), "page": plain(r.get("page")), "place": plain(r.get("place")),
            "read_from": r.get("read_from")}
    cite.update({c: r.get(c) for c in v.urls if r.get(c)})
    cite.update({label: plain(r.get(c)) for label, c in v.cite if r.get(c) not in (None, "")})
    far = []
    pointed = search.far_rows(conn, [(v, r)])
    labels = {c: label for label, c in v.fields}
    for c, (fv, fc) in cat.pointers(v).items():
        x = r.get(c)
        if x in (None, ""):
            continue
        fr = pointed.get((fv, fc, str(x)))
        far.append({"field": labels.get(c, c), "ref": ref_of(cat.BY_NAME[fv], fr), "title": panes.title_of(cat.BY_NAME[fv], fr)}
                   if fr else {"field": labels.get(c, c), "value": plain(x), "note": "row not held"})
    under = []                                     # the rows the pane lists under this one: a company's directors, shareholders
    for j, total, rows in search.children(conn, v, r, limit=CHILD_ROWS):
        if not total:
            continue
        jv = cat.BY_NAME[j.view]
        under.append({"join": j.label, "view": j.view, "total": total, "shown": len(rows),
                      "rows": [child_of(jv, x) for x in rows]})
    return {"ref": ref_of(v, r), "register": v.register, "title": panes.title_of(v, r),
            "suppressed": panes.is_suppressed(v, r), "withdrawn_by_source": panes.is_withdrawn(v, r),
            "fields": fields, "citation": {k: x for k, x in cite.items() if x not in (None, "")},
            "far_rows": far, "rows_under": under, "says": panes.says_of(v, r), "note": v.note}


def child_of(v: cat.View, r: dict) -> dict:
    """A joined row as one line: its ref, its title (a suppressed name stays
    suppressed through panes.shown) and its dates and plain fields set."""
    out = {"ref": ref_of(v, r), "title": panes.title_of(v, r)}
    for label, c in v.fields:
        x = value_of(v, r, c)
        if x not in (None, "") and x is not True and x is not False:
            out[label] = x
    for label, c in v.dates:
        if r.get(c) not in (None, ""):
            out[label] = plain(r.get(c))
    return out


def tool_dossier(conn, id: str = "") -> dict:   # noqa: A002 — the tool's own parameter name
    x = dossier.gather(conn, str(id or "").strip().strip("[]"))
    if x["kind"] in ("none", "suppressed", "fold"):
        return {"error": x.get("why") or "no dossier for that id"}
    d = x["describe"]
    rows = []
    for ref, v, r in x["rows"][:DOSSIER_ROWS]:
        rows.append({"ref": ref_of(v, r), "register": v.register, "title": panes.title_of(v, r),
                     "when": dossier.when_text(v, r)})
    adds = dossier.addends(x)
    money = [{"year": y, "sum_of_added": str(total), "added": n,
              "rows": [{"ref": ref_of(a["v"], a["r"]), "amount": plain(a["amount"]), "what": a["what"],
                        "to": panes.title_of(*a["to"]) if a["to"] else "", "not_added": a["not_added"]} for a in items[:10]]}
             for y, items, total, n in dossier.by_year(adds)]
    if x.get("many"):
        money = [{"year": y, "sum_of_added": str(total), "added": n, "rows_filed": k} for y, total, n, k in x["money_counted"]]
    return {"id": x["chosen"], "kind": x["kind"], "label": d["label"], "size": d["count"], "contested": d.get("contested", False),
            "names_as_filed": x["names"][:15], "rows": rows, "rows_more": max(0, len(x["rows"]) - DOSSIER_ROWS),
            "rows_by_view": [{"view": v.name, "rows": k} for v, k in x.get("views") or ()],
            "money_as_filed": money, "money_note": dossier.MONEY_NOTE,
            "note": "the group is the links lane's (pub.groups); the board makes no link"}


CALLS = {"registers": tool_registers, "search": tool_search, "row": tool_row, "dossier": tool_dossier}


def call_tool(conn, name: str, arguments) -> str:
    """One tool's answer as the model reads it, JSON cut to RESULT_CHARS; a
    failure is said to the model, never raised."""
    fn = CALLS.get(name)
    if fn is None:
        return json.dumps({"error": f"no tool {name!r}; the tools are {', '.join(CALLS)}"})
    try:
        args = json.loads(arguments) if isinstance(arguments, str) and arguments.strip() else (arguments or {})
        if not isinstance(args, dict):
            args = {}
        allowed = fn.__code__.co_varnames[1:fn.__code__.co_argcount] if name != "search" else None
        if allowed is not None:
            args = {k: x for k, x in args.items() if k in allowed}
        else:
            args = {k: x for k, x in args.items() if k in ("term", "registers") or k in dict(search.FIELDS)}
        with LOCK:
            out = fn(conn, **args)
    except Exception as exc:  # noqa: BLE001 — said to the model, which may try again
        out = {"error": f"the tool failed: {type(exc).__name__}"}
    s = json.dumps(plain(out), ensure_ascii=False, separators=(",", ":"))
    return s if len(s) <= RESULT_CHARS else s[:RESULT_CHARS] + '…"(cut: ask a narrower question or open one row)"'


LOCK = threading.Lock()     # the server's RENDER_LOCK, set by server.py: one page or tool at a time on the connections


# ── the thread and the answer ───────────────────────────────────────────────

def thread_of(body) -> list:
    """The thread the browser posted, as the model's messages: user and
    assistant turns alone, each cut, the newest THREAD_TURNS; [] when the
    last is not a question."""
    turns = body.get("thread") if isinstance(body, dict) else None
    out = []
    for t in turns if isinstance(turns, list) else ():
        if isinstance(t, dict) and t.get("role") in ("user", "assistant") and isinstance(t.get("content"), str) and t["content"].strip():
            out.append({"role": t["role"], "content": t["content"].strip()[:TURN_CHARS]})
    out = out[-THREAD_TURNS:]
    if not out or out[-1]["role"] != "user":
        return []
    out[-1]["content"] = out[-1]["content"][:QUESTION_CHARS]
    while out and out[0]["role"] != "user":
        out.pop(0)
    return out


def down(exc: Exception) -> bool:
    """The model server is not there, or another model answered."""
    return isinstance(exc, (modelclient.WrongModel, modelclient.Refused, urllib.error.URLError, ConnectionError,
                            TimeoutError, OSError))


def ask(thread: list, connect=None, url: str = None, model: str = None, post=None, ledger: str = None) -> dict:
    """{'ok', 'answer', 'rounds', 'tools', 'seconds'}: the model's answer to
    the thread's last question, its tools run on `connect()` (the product
    reader). With the model down: ok false and NOT_RUNNING."""
    t0 = time.monotonic()
    url, model = url or URL, model or MODEL
    messages = [{"role": "system", "content": SYSTEM}] + thread
    used = []
    conn = None
    try:
        for i in range(ROUNDS):
            last = i == ROUNDS - 1
            extra = {"tools": TOOLS, "max_tokens": ANSWER_TOKENS, "temperature": 0.2}
            if last:                               # no tool offered and told so: with tools offered and refused the model wrote a raw tool call as its answer
                del extra["tools"]
                messages.append({"role": "system", "content": ANSWER_NOW})
            try:
                out = modelclient.chat(url, lane=LANE, model=model, messages=messages, extra=extra, timeout=CALL_S,
                                       post=post, ledger=ledger)
            except Exception as exc:  # noqa: BLE001
                if down(exc):
                    return {"ok": False, "answer": NOT_RUNNING, "rounds": i, "tools": used, "seconds": round(time.monotonic() - t0, 1)}
                raise
            msg = ((out.get("choices") or [{}])[0].get("message")) or {}
            calls = msg.get("tool_calls") or []
            if not calls or last:
                text = (msg.get("content") or "").strip()
                text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
                text = re.sub(r"<tool_call>.*?(</tool_call>|\Z)", "", text, flags=re.S).strip()   # a tool call written as text is not an answer
                return {"ok": True, "answer": text or "(the model gave no answer)", "rounds": i + 1, "tools": used,
                        "seconds": round(time.monotonic() - t0, 1)}
            messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
            if conn is None:
                conn = (connect or db.scan_connect)()
            for c in calls:
                fn = c.get("function") or {}
                used.append(fn.get("name") or "?")
                messages.append({"role": "tool", "tool_call_id": c.get("id") or "", "name": fn.get("name") or "",
                                 "content": call_tool(conn, fn.get("name") or "", fn.get("arguments"))})
        return {"ok": True, "answer": "(the model gave no answer)", "rounds": ROUNDS, "tools": used,
                "seconds": round(time.monotonic() - t0, 1)}
    finally:
        if conn is not None:
            conn.close()


# ── citations ───────────────────────────────────────────────────────────────

CITE = re.compile(r"\[([^\[\]\n]{3,400})\]")
ONE = re.compile(r"^\s*([a-z][a-z0-9_]*):(\S(?:[^,;]*\S)?)\s*$")


def cited_refs(answer: str) -> list:
    """Every view:key the answer cites, in order, once each."""
    out = []
    for m in CITE.finditer(answer or ""):
        for part in re.split(r"[,;]\s*", m.group(1)):
            one = ONE.match(part)
            if one and f"{one.group(1)}:{one.group(2)}" not in out:
                out.append(f"{one.group(1)}:{one.group(2)}")
    return out


def resolver(conn):
    """ref -> True where it names a row of a published view the catalogue knows."""
    held = db.pub_views(conn)
    memo = {}

    def known(ref: str) -> bool:
        if ref not in memo:
            view, _, key = ref.partition(":")
            memo[ref] = view in cat.BY_NAME and view in held and search.row(conn, view, key) is not None
        return memo[ref]
    return known


def parts(answer: str, known) -> list:
    """The answer as the pane builds it: {'t': text}, {'c': ref, 'href': the
    row's pane} for a citation of a real row, {'x': ref} for one that names
    no row (struck, NOT_A_ROW). The browser makes text nodes of each; no HTML
    passes."""
    out, at = [], 0
    for m in CITE.finditer(answer or ""):
        pieces = [p for p in re.split(r"[,;]\s*", m.group(1))]
        if not all(ONE.match(p) for p in pieces):
            continue
        if m.start() > at:
            out.append({"t": answer[at:m.start()]})
        for p in pieces:
            one = ONE.match(p)
            ref = f"{one.group(1)}:{one.group(2)}"
            out.append({"c": ref, "href": panes.href("", [ref])} if known(ref) else {"x": ref})
        at = m.end()
    if at < len(answer or ""):
        out.append({"t": answer[at:]})
    return out


def respond(body, connect=None, url: str = None, model: str = None, post=None, ledger: str = None) -> dict:
    """POST /chat's answer: {'ok', 'answer', 'parts', 'cited', 'resolved', 'seconds', 'rounds', 'tools'}."""
    thread = thread_of(body)
    if not thread:
        return {"ok": False, "answer": "ask a question", "parts": [{"t": "ask a question"}], "cited": 0, "resolved": 0}
    got = ask(thread, connect, url, model, post, ledger)
    if not got["ok"]:
        got.update(parts=[{"t": got["answer"]}], cited=0, resolved=0)
        return got
    refs = cited_refs(got["answer"])
    if refs:
        with (connect or db.scan_connect)() as conn, LOCK:
            known = resolver(conn)
            got["parts"] = parts(got["answer"], known)
    else:
        got["parts"] = [{"t": got["answer"]}]
    got["cited"] = len(refs)
    got["resolved"] = len({p["c"] for p in got["parts"] if "c" in p})
    return got
