"""The review tab (Arthur, 15 November 2026: "a review tab with a really good interface that gives me the question I'm
answering and the information i need to answer it concisely and easily").

    GET  /review                         the sets waiting, or the one set's next unanswered question
    GET  /review?set=<name>&q=<id>       one question (answered or not); &after=<id>: the next unanswered after it
    POST /review/answer                  set, q, choice, note: one answer, added to board.answers; then the next

A set is a JSON file a session writes into QV4_REVIEW_DIR (default /home/user/querynzv4-work/live/review/), for
example registers/news/gold/questions.py. The file is data the board reads; the board imports nothing of the lane
that wrote it. Each question carries its own wording, the sentence or two that answer it with the words it asks
about marked, its choices, and the article behind a fold. What each side of a comparison said (`sides`) is never
shown while a question is open; the tally at the end of a set compares Arthur's answers with them.

Answers are only ever added (state.answer): answering again adds a newer answer, and the newest counts. One page,
no script but static/review.js (the keys: 1 to 9 answer, N a note, S skip, B back).
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
from pathlib import Path

from products.board import panes, state
from products.board.panes import esc

TAB = "review"
PATH = "/review"
ANSWER = "/review/answer"
DIR = Path(os.environ.get("QV4_REVIEW_DIR") or "/home/user/querynzv4-work/live/review")
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,80}$")

CSS = """
.review{max-width:54rem;margin:0 auto;width:100%;padding:0 .5rem 3rem}
.rv-top{display:flex;flex-wrap:wrap;gap:.5rem 1rem;align-items:baseline;margin:.25rem 0 .5rem}
.rv-top h2{font-size:15px;margin:0;font-weight:600}
.rv-bar{height:6px;background:#232833;border-radius:3px;overflow:hidden;margin:.25rem 0 .75rem}
.rv-bar i{display:block;height:100%;background:#5aa9ff}
.rv-kinds{display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:1rem}
.rv-kinds a{font-size:12px;padding:.1rem .55rem;border:1px solid #3a404c;border-radius:999px;text-decoration:none;color:#aab1bc}
.rv-kinds a.on{border-color:#5aa9ff;color:#e8eaed}
.rv-kinds a b{color:#e8eaed;font-weight:600}
.rv-card{background:#161a20;border:1px solid #3a404c;border-radius:8px;padding:1.25rem 1.5rem}
.rv-kind{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#aab1bc}
.rv-ask{font-size:21px;line-height:1.35;margin:.35rem 0 1rem;font-weight:500}
.rv-ctx{font-size:17px;line-height:1.6;margin:0 0 1rem;padding:.75rem 1rem;border-left:3px solid #5a6270;background:#0e1014;border-radius:0 4px 4px 0}
.rv-src{font-size:12px;color:#aab1bc;margin-bottom:1rem}
.rv-src details{margin-top:.35rem}
.rv-src summary{cursor:pointer;color:#8cb8ff}
.rv-src .body{white-space:pre-wrap;font-size:14px;line-height:1.5;color:#e8eaed;max-height:26rem;overflow-y:auto;margin-top:.5rem;padding:.5rem .75rem;background:#0e1014;border-radius:4px}
mark{color:inherit;border-radius:3px;padding:0 .1em}
mark.who{background:#1f3a66;box-shadow:inset 0 -2px #5aa9ff}
mark.role{background:#5a4512;box-shadow:inset 0 -2px #e0b84d}
mark.org{background:#173f2a;box-shadow:inset 0 -2px #4cc38a}
mark.quote{background:#3b2a5c;box-shadow:inset 0 -2px #b48cff}
.rv-choices{display:grid;grid-template-columns:repeat(auto-fit,minmax(10.5rem,1fr));gap:.5rem;margin:.25rem 0 .75rem}
.rv-choices button{font-size:15px;text-align:left;padding:.6rem .75rem;border-radius:6px;border:1px solid #5a6270;background:#232833;cursor:pointer}
.rv-choices button:hover,.rv-choices button:focus{border-color:#5aa9ff;background:#1b2a40}
.rv-choices button.was{border-color:#4cc38a;background:#173f2a}
.rv-tags{display:flex;flex-direction:column;gap:.15rem;margin:.3rem 0}.rv-tags b{font-weight:500;color:#d8dde5}
.rv-choices button.bad{border-style:dashed;border-color:#c38a4c}
kbd{display:inline-block;min-width:1.2em;text-align:center;font:12px ui-monospace,monospace;padding:0 .3em;margin-right:.5em;border:1px solid #5a6270;border-bottom-width:2px;border-radius:3px;color:#aab1bc}
.rv-note{width:100%;box-sizing:border-box;font-size:14px;padding:.45rem .6rem;margin-bottom:.75rem}
.rv-nav{display:flex;justify-content:space-between;font-size:13px}
.rv-nav a{text-decoration:none}
.rv-was{font-size:12px;color:#4cc38a;margin-bottom:.5rem}
.rv-done table{border-collapse:collapse;margin:.5rem 0}
.rv-done td,.rv-done th{padding:.2rem .9rem .2rem 0;text-align:left;font-size:14px}
.rv-help{font-size:12px;color:#aab1bc;margin-top:1rem}
"""


def sets() -> list:
    if not DIR.is_dir():
        return []
    return sorted(p.stem for p in DIR.glob("*.json") if NAME.match(p.stem))


def load(name: str) -> dict | None:
    if not NAME.match(name or ""):
        return None
    p = DIR / f"{name}.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def href(name: str, q: str = "", after: str = "") -> str:
    return PATH + "?" + urllib.parse.urlencode([("set", name)] + ([("q", q)] if q else []) + ([("after", after)] if after else []))


def _runs(parts: list) -> str:
    return "".join(f'<mark class="{esc(p["mark"])}">{esc(p["text"])}</mark>' if p.get("mark") else esc(p.get("text") or "").replace("\n", "<br>")
                   for p in parts or [] if p.get("text"))


def _mark_body(body: str, parts: list) -> str:
    """The whole article with the context's marked words marked again, so the fold opens on the same picture."""
    words = {}
    for p in parts or []:
        if p.get("mark") and len(p.get("text") or "") > 2:
            words.setdefault(p["text"], p["mark"])
    if not words:
        return esc(body)
    rx = re.compile("|".join(re.escape(w) for w in sorted(words, key=len, reverse=True)))
    out, at = [], 0
    for m in rx.finditer(body):
        out.append(esc(body[at:m.start()]))
        out.append(f'<mark class="{esc(words[m.group(0)])}">{esc(m.group(0))}</mark>')
        at = m.end()
    out.append(esc(body[at:]))
    return "".join(out)


def next_open(qs: list, done: dict, after: str = "", kind: str = "") -> dict | None:
    """The first unanswered question in the set's order (after `after`, wrapping round; of `kind` when given)."""
    ids = [q["id"] for q in qs]
    start = ids.index(after) + 1 if after in ids else 0
    for q in qs[start:] + qs[:start]:
        if q["id"] not in done and (not kind or q["kind"] == kind) and q["id"] != after:
            return q
    return None


def _kinds(name: str, qs: list, done: dict, on: str) -> str:
    seen, out = [], []
    for q in qs:
        if q["kind"] not in seen:
            seen.append(q["kind"])
    for k in seen:
        mine = [q for q in qs if q["kind"] == k]
        left = sum(1 for q in mine if q["id"] not in done)
        first = next_open(qs, done, kind=k) or mine[0]
        out.append(f'<a class="{"on" if k == on else ""}" href="{esc(href(name, first["id"]))}">{esc(mine[0].get("label") or k)} '
                   f'<b>{left}</b> left of {len(mine)}</a>')
    return '<div class="rv-kinds">' + "".join(out) + "</div>"


def _done(name: str, d: dict, done: dict) -> str:
    """The end of a set: how often Arthur's answer matched each side, by kind."""
    tally = {}
    for q in d["questions"]:
        a = done.get(q["id"])
        if not a or a["choice"] == "unsure":
            continue
        t = tally.setdefault(q.get("label") or q["kind"], {"n": 0})
        t["n"] += 1
        for side, said in (q.get("sides") or {}).items():
            t[side] = t.get(side, 0) + int(said == a["choice"] or (said == "missing" and a["choice"] == "no"))
    sides = sorted({s for q in d["questions"] for s in (q.get("sides") or {})})
    label = {"gold": "my hand labels", "model": "the model"}
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{t['n']}</td>" + "".join(
        f"<td>{100 * t.get(s, 0) // max(t['n'], 1)}%</td>" for s in sides) + "</tr>" for k, t in tally.items())
    return (f'<div class="rv-card rv-done"><div class="rv-kind">Done</div><p class="rv-ask">Every question in this set is answered.</p>'
            f'<p>How often your answer matched each side (a "can\'t tell" is left out):</p><table><tr><th>Question</th><th>Answered</th>'
            + "".join(f"<th>{esc(label.get(s, s))}</th>" for s in sides) + f"</tr>{rows}</table>"
            f'<p class="rv-help">Any question can be answered again from the counts above; the newest answer counts.</p></div>')


def render_set(name: str, d: dict, done: dict, qid: str = "", after: str = "") -> str:
    qs = d["questions"]
    q = next((x for x in qs if x["id"] == qid), None) if qid else next_open(qs, done, after)
    n_done = sum(1 for x in qs if x["id"] in done)
    pct = 100 * n_done // max(len(qs), 1)
    top = (f'<div class="rv-top"><h2>{esc(d.get("title") or name)}</h2><span class="meta">{n_done} of {len(qs)} answered</span>'
           f'<span class="meta">{esc(d.get("about") or "")}</span></div><div class="rv-bar"><i style="width:{pct}%"></i></div>')
    if q is None:
        return top + _kinds(name, qs, done, "") + _done(name, d, done)
    art = (d.get("articles") or {}).get(q.get("article")) or {}
    i = [x["id"] for x in qs].index(q["id"])
    prev = qs[i - 1]["id"] if i else ""
    was = done.get(q["id"])
    keyed = [(0 if c["key"] == "bad" else n, c) for n, c in enumerate([c for c in q["choices"] if c["key"] != "bad"], 1)]
    keyed += [(0, c) for c in q["choices"] if c["key"] == "bad"]      # "bad question" is always 0, and last
    buttons = "".join(
        f'<button name="choice" value="{esc(c["key"])}" data-key="{n}" class="{"was" if was and was["choice"] == c["key"] else ""}{" bad" if c["key"] == "bad" else ""}">'
        f'<kbd>{n}</kbd>{esc(c["label"])}</button>' for n, c in keyed)
    src = ""
    if art:
        tg = art.get("tags") or {}
        tags = ""
        if tg:
            mine = " · ".join(x for x in [tg.get("model_type") or "", ", ".join(tg.get("model_themes") or []),
                                          f'wire: {tg["model_wire"]}' if tg.get("model_wire") else ""] if x)
            site = ", ".join(dict.fromkeys(list(tg.get("site_categories") or []) + list(tg.get("site_sections") or [])))
            tags = (f'<div class="rv-tags"><span>Model tagged: <b>{esc(mine or "nothing")}</b></span>'
                    f'<span>Site tagged: <b>{esc(site or "nothing")}</b></span></div>')
        src = (f'<div class="rv-src">From <b>{esc(art.get("title") or "")}</b> · {esc(art.get("site") or "")} · {esc(art.get("date") or "")}{tags}'
               f'<details><summary>the whole article</summary><div class="body">{_mark_body(art.get("body") or "", q.get("context"))}</div></details></div>')
    card = (f'<div class="rv-card"><div class="rv-kind">{esc(q.get("label") or q["kind"])} · question {i + 1} of {len(qs)}</div>'
            f'<div class="rv-ask">{_runs(q.get("ask"))}</div>'
            f'<blockquote class="rv-ctx">{_runs(q.get("context"))}</blockquote>{src}'
            + (f'<div class="rv-was">You answered: {esc(next((c["label"] for c in q["choices"] if c["key"] == was["choice"]), was["choice"]))}'
               + (f' — “{esc(was["note"])}”' if was.get("note") else "") + "</div>" if was else "")
            + f'<form method="post" action="{ANSWER}" id="rv-form"><input type="hidden" name="set" value="{esc(name)}">'
            f'<input type="hidden" name="q" value="{esc(q["id"])}"><div class="rv-choices">{buttons}</div>'
            f'<input class="rv-note" name="note" id="rv-note" maxlength="2000" placeholder="A note, if you want one (N)"></form>'
            f'<div class="rv-nav"><a id="rv-back" href="{esc(href(name, prev)) if prev else "#"}">← back <kbd>B</kbd></a>'
            f'<a id="rv-skip" href="{esc(href(name, after=q["id"]))}">skip <kbd>S</kbd> →</a></div></div>'
            '<p class="rv-help">Answer from the article only, not from what you know. Press a number to answer.</p>')
    return top + _kinds(name, qs, done, q["kind"]) + card


def render(qs: dict) -> str:
    one = lambda k: (qs.get(k) or [""])[0].strip()[:100]
    from products.board import assets
    script = f'<script src="{esc(assets.url("review.js"))}" defer></script>'
    name = one("set")
    names = sets()
    if name and name not in names:
        name = ""                     # a retired set's address (an open tab) opens what is waiting now
    if not name and len(names) == 1:
        name = names[0]
    if not name:
        body = ("<div class=\"rv-card\"><div class=\"rv-kind\">Review</div>"
                + ("<p class=\"rv-ask\">Nothing waiting for review.</p>" if not names else
                   "<p class=\"rv-ask\">Sets waiting for you</p><ul>" + "".join(
                       f'<li><a href="{esc(href(n))}">{esc((load(n) or {}).get("title") or n)}</a></li>' for n in names) + "</ul>")
                + "</div>")
    else:
        d = load(name)
        if d is None:
            body = '<div class="rv-card"><p class="rv-ask">No such set.</p></div>'
        else:
            body = render_set(name, d, state.answers(name), one("q"), one("after"))
    return panes.page("", [], [f'<style>{CSS}</style><section class="review">{body}</section>{script}'], tab=TAB)


def take(form: dict) -> str:
    """One answer added; the address to go to next."""
    get = lambda k: (form.get(k) or [""])[0]
    name, qid, choice = get("set").strip(), get("q").strip(), get("choice").strip()
    d = load(name)
    if d is None:
        raise ValueError("no such set")
    q = next((x for x in d["questions"] if x["id"] == qid), None)
    if q is None or choice not in {c["key"] for c in q["choices"]}:
        raise ValueError("no such question or choice")
    state.answer(name, qid, choice, get("note").strip())
    return href(name, after=qid)


#: where `--export` writes each set's answers, for a lane that measures against them (a lane never reads board.answers)
ANSWERS = DIR / "answers"


def export(names: list, out: Path = None) -> list:
    """Each set's newest answers written to OUT/<set>.json as {question id: {"choice", "note"}}; returns the paths."""
    out = Path(out or ANSWERS)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for name in names:
        got = {q: {"choice": a["choice"], "note": a["note"]} for q, a in state.answers(name).items()}
        p = out / f"{name}.json"
        p.write_text(json.dumps(got, indent=1, ensure_ascii=False) + "\n")
        paths.append(p)
    return paths


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    if args[:1] != ["--export"] or len(args) < 2:
        print("usage: python -m products.board.review --export SET [SET ...]")
        raise SystemExit(2)
    for p in export(args[1:]):
        print(p)
