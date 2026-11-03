"""The document profile's contract (plan 1.9; docs/contracts/document-profile.md).

A document profile describes one kind of document: how to recognise it
(by shape, measured without reading: page count, text-layer presence,
image pages, landmarks), which pages need the page reader, how its tables
are laid out, and the prompt and checks the reader runs. A reading is made
FROM a profile and is stamped with the profile's slug and version, so a
profile is never edited: a new version is a new line in `profiles.jsonl`,
one higher, and every old version stays readable.

Fields (the old estate's, kept): kind, slug, version, at, by, title,
recognise, signals, ocr, tables, prompt, notes, role, applies_to, tooling,
config, process, gates, on_fail. `recognise` and `signals` are the
recognition markers the plan asks for before a reader is built
(memory: profiles before readers).

What a profile extracts (Arthur, 3 November 2026): `extract` lists every
field a reading of this kind takes, each item {field, iteration, by
('rules', 'pattern' or 'model'), ask (the instruction), private (true for
an identifier: held in a `*_private` schema, never published), kinds (a
closed vocabulary, or null), lands (the columns the field is written to,
"table.column" in the lane's own naming, a private table as
"<lane>_private.table.column"), links (the linking opportunities it offers,
each {key, to, rule}: what joins, what it could join, and the links rule id
that joins it today or null; an empty list for a field with no linking
value)}; `iteration` is the highest item's. A field
added, or a field's instruction changed, is an item with the next
iteration, in a new version; no field is ever dropped. A document records
the iteration each field was extracted at (`docs.extractions`, see
support/docstore/extraction.py), so a reader asks only for what a
document has not had: `wanted(profile, done)`.

    current()            slug → the newest version of every profile
    profile(slug)        the newest version of one
    history(slug)        every version, oldest first
    add_version(slug, fields, by)   append the next version; never edit
    reading_version(slug)  the version a reading of the kind is keyed and stamped by: a version that adds to the
                           extract list and changes nothing else reads as the one before it
"""
import datetime as dt
import json
import os
import re

PROFILES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles.jsonl")
FIELDS = ("title", "recognise", "signals", "signals_note", "ocr", "tables", "prompt", "notes", "role",
          "applies_to", "tooling", "config", "process", "gates", "on_fail", "extract", "iteration")
EXTRACT_BY = ("rules", "pattern", "model")
#: what a field can join on (an extract item's `links[].key`)
LINK_KEYS = ("name", "nzbn", "company_number", "charity_number", "email", "phone", "address", "po_box", "citation",
             "case_number", "url")
#: a lands column: "table.column", or a private table's "<lane>_private.table.column"
_LANDS = re.compile(r"^(?:[a-z][a-z0-9_]*_private\.)?[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")
#: a links rule id: "full-name@1"
RULE_ID = re.compile(r"^[a-z][a-z-]*@\d+$")
#: the fields of a version that say nothing about how a document is read: a version that changes only these leaves the
#: stored readings standing (`reading_version`)
NOT_READING = ("kind", "slug", "version", "at", "by", "extract", "iteration")
KIND = "document-profile"


def _read(path: str = None) -> list:
    out = []
    try:
        with open(path or PROFILES, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    except OSError:
        return []
    return out


def history(slug: str, path: str = None) -> list:
    rows = [r for r in _read(path) if r.get("slug") == slug and r.get("kind") == KIND]
    return sorted(rows, key=lambda r: int(r.get("version") or 0))


def current(path: str = None) -> dict:
    """The newest version of every slug, by version and not by position in
    the file (the ledger is append-only and may be restored out of order)."""
    out = {}
    for r in _read(path):
        if r.get("kind") != KIND:
            continue
        cur = out.get(r["slug"])
        if cur is None or int(r.get("version") or 0) >= int(cur.get("version") or 0):
            out[r["slug"]] = r
    return out


def profile(slug: str, path: str = None):
    return current(path).get(slug)


def valid_slug(slug: str) -> bool:
    return bool(slug) and all(ch.isalnum() or ch in "-_" for ch in slug) and slug == slug.lower()


def reading_version(slug: str, path: str = None):
    """The version a reading of `slug` is keyed and stamped by: the current version, or, where the newest versions
    differ only in what they list they extract (`NOT_READING`), the earliest of them. A reading is keyed by its
    profile's version (support.reader.reading_key), so a version that only adds to the extract list would otherwise
    orphan every stored reading; what has been extracted is recorded per document in docs.extractions instead."""
    hist = history(slug, path)
    if not hist:
        return None
    sig = lambda r: {k: v for k, v in r.items() if k not in NOT_READING and v is not None}  # noqa: E731
    cur, version = sig(hist[-1]), int(hist[-1]["version"])
    for r in reversed(hist[:-1]):
        if sig(r) != cur:
            break
        version = int(r["version"])
    return version


def add_version(slug: str, fields: dict, by: str, path: str = None, at: str = None) -> dict:
    """Append the next version of `slug`. The version is read at write time,
    so two writers cannot both write version 3. Nothing is ever edited."""
    if not valid_slug(slug):
        raise ValueError("a profile slug is lower-case letters, digits, - and _")
    if not by:
        raise ValueError("a version says who made it")
    path = path or PROFILES
    have = history(slug, path)
    check_extract(fields.get("extract"), have[-1].get("extract") if have else None)
    if fields.get("extract"):
        fields = {**fields, "iteration": iteration({"extract": fields["extract"]})}
    rec = {"kind": KIND, "slug": slug, "version": (int(have[-1]["version"]) if have else 0) + 1,
           "at": at or dt.datetime.now().astimezone().isoformat(timespec="seconds"), "by": by}
    for k in FIELDS:
        rec[k] = fields.get(k)
    for k, v in fields.items():
        rec.setdefault(k, v)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# --- what a profile extracts ----------------------------------------------------------------------------------------

def check_extract(items, before=None) -> None:
    """ValueError unless `items` is a well-formed extract list that keeps every field `before` had, at the same or a
    higher iteration, and moves no field's instruction without moving its iteration."""
    if not items:
        if before:
            raise ValueError("a version drops the extract list its predecessor had")
        return
    seen = set()
    for it in items:
        f, n = it.get("field"), it.get("iteration")
        if not f or not isinstance(n, int) or n < 1:
            raise ValueError(f"an extract item needs a field and an iteration from 1: {it!r}")
        if (f, n) in seen:
            raise ValueError(f"the field {f} is listed twice at iteration {n}")
        seen.add((f, n))
        if it.get("by") not in EXTRACT_BY:
            raise ValueError(f"the field {f}: `by` is one of {EXTRACT_BY}")
        if not (it.get("ask") or "").strip():
            raise ValueError(f"the field {f} has no instruction (`ask`)")
        if not isinstance(it.get("private"), bool):
            raise ValueError(f"the field {f}: `private` is true or false")
        _check_lands(f, it)
        _check_links(f, it.get("links"))
    new = latest(items)
    for f, old in latest(before or []).items():
        if f not in new:
            raise ValueError(f"the field {f} is dropped; a field is never dropped")
        if new[f]["iteration"] < old["iteration"]:
            raise ValueError(f"the field {f} goes back an iteration")
        if new[f]["iteration"] == old["iteration"] and new[f] != old:
            raise ValueError(f"the field {f} changed without a new iteration")


def _check_lands(f: str, it: dict) -> None:
    lands = it.get("lands")
    if not isinstance(lands, list) or not lands:
        raise ValueError(f"the field {f}: `lands` lists the columns it is written to")
    for col in lands:
        if not isinstance(col, str) or not _LANDS.match(col):
            raise ValueError(f"the field {f}: a `lands` column is \"table.column\" or \"<lane>_private.table.column\": {col!r}")
    if len(set(lands)) != len(lands):
        raise ValueError(f"the field {f}: a `lands` column is listed twice")
    if it["private"] and any(col.count(".") != 2 for col in lands):
        raise ValueError(f"the field {f} is private: every column it lands in is a `_private` table's")


def _check_links(f: str, links) -> None:
    if not isinstance(links, list):
        raise ValueError(f"the field {f}: `links` is a list (empty for a field with no linking value)")
    seen = set()
    for ln in links:
        if not isinstance(ln, dict) or set(ln) != {"key", "to", "rule"}:
            raise ValueError(f"the field {f}: a `links` entry is {{key, to, rule}}: {ln!r}")
        if ln["key"] not in LINK_KEYS:
            raise ValueError(f"the field {f}: a `links` key is one of {LINK_KEYS}: {ln['key']!r}")
        if not (isinstance(ln["to"], str) and ln["to"].strip()):
            raise ValueError(f"the field {f}: a `links` entry says what it could join (`to`)")
        if ln["rule"] is not None and not (isinstance(ln["rule"], str) and RULE_ID.match(ln["rule"])):
            raise ValueError(f"the field {f}: a `links` rule is a links rule id such as \"full-name@1\", or null: {ln['rule']!r}")
        if (ln["key"], ln["to"]) in seen:
            raise ValueError(f"the field {f}: the opportunity {ln['key']} → {ln['to']} is listed twice")
        seen.add((ln["key"], ln["to"]))


def latest(items) -> dict:
    """field → its newest item (the highest iteration)."""
    out = {}
    for it in items or []:
        if it["field"] not in out or it["iteration"] > out[it["field"]]["iteration"]:
            out[it["field"]] = it
    return out


def iteration(prof: dict) -> int:
    """The profile's iteration: its highest extract item's, 0 for a profile with no extract list."""
    return max((it["iteration"] for it in prof.get("extract") or []), default=0)


def wanted(prof: dict, done: dict) -> list:
    """The items a document still needs: each field's newest item whose iteration is above the one the document was
    extracted at (`done`: field → iteration, from extraction.done)."""
    return [it for f, it in sorted(latest(prof.get("extract")).items()) if it["iteration"] > done.get(f, 0)]

