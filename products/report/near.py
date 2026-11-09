"""Stage 2 of the one report: near links, on request (ruling 151; plan
docs/plan/step-9.md, tranche 8).

The first report follows confirmed links only. From a finished first
report the reader asks for a second pass, and this module makes it: it
takes the stage-1 records (every row the first report holds as
confirmed) and follows, one step and no further, the near links from
them: a name match without a confirming fact. Every item it returns is
graded near and carries its reason; a near item never enters the
confirmed set, and the first report's own items are never changed.

Two sources of near, both name matches with nothing to confirm them:

- `stored`: the links lane's near grade (`pub.links`, grade `near`), each
  with the rule that made it and the lane's reason (ruling 148's
  `lbp-number@1` among them: "the lack of a full match may indicate
  another rendering of the name"). A `name-only@1` link is one spoke of a
  star; the rest of the star is read through its centre (`walk.star_links`,
  links/spec.md's contract for readers), so what is listed never depends
  on which row the lane made the centre.
- `report`: the report's own name joins into views no link reaches yet
  (`walk.name_joined`: the Charities Register's officers, the regulators'
  parties, the Gazette's appointments; `walk.named_rows`: the expense
  releases by printed name), with the view's reason.

A row the first report already lists, at any grade, is not listed again;
the count of those is kept. Nothing is ranked: the order is the rule, then
the row's ref in byte order, never a size or a fame (prominence never
scores). What the pass leaves out at its limits is counted, never silent.
Reads `pub.*` only, on the reader it is handed."""
from __future__ import annotations

import copy

from products.report import catalogue as cat
from products.report import db, rules, walk

LIMITS = {"links": 600, "items": 400}
SECTION = {"name": "near_on_request", "heading": "Near links, on request: perhaps the same, never confirmed",
           "text": "The second pass, asked for from the first report: each line is a row joined to a record above by a name "
                   "and nothing that confirms it, with the rule and the reason it is only near. The lack of a full match may "
                   "indicate another rendering of the name, or another person or body of the same name; nothing here is "
                   "counted with the records above."}
BLANK = "none found in the links held: no near link leaves the records of the first report"
NO_REASON = {walk.NAME_ONLY: "the two rows share a first and last name and nothing else is filed to compare; the links lane stored no "
                             "further reason: near, never confirmed"}
NO_REASON_DEFAULT = "the rule that joined these rows grades the link near (the links lane stored no reason): near, never confirmed"
STORED, REPORT = "stored", "report"


#: a `name-only@1` link the lane stored with no reason whose evidence is a full name, middle name included (429 thousand on 9
#: November 2026: the star builder writes `rules.judge`'s reason, and judge gives none where it would confirm by `full-name@1`)
NO_REASON_FULL = ("the two rows share a first, middle and last name, and no rule joins them into one group; the links lane stored "
                  "no further reason: near, never confirmed")


def reason_for(link: dict) -> str:
    """The link's own reason, or the rule's when the lane stored none: a
    near line is never without one (presentation rule 8)."""
    r = (link.get("reason") or "").strip()
    if r:
        return r
    ev = link.get("evidence") if isinstance(link.get("evidence"), dict) else {}
    if link.get("rule") == walk.NAME_ONLY and ev.get("full_name") and ev.get("middle"):
        return NO_REASON_FULL
    return NO_REASON.get(link.get("rule"), NO_REASON_DEFAULT)


# ── what the first report holds ─────────────────────────────────────────────

def _all_items(report: dict, stage1_only: bool = True):
    """Every item of the report; with `stage1_only`, the second pass's own
    section left out (it is what the pass adds, never what it reads)."""
    if report.get("subject"):
        yield report["subject"]
    yield from report.get("members", [])
    for s in report.get("sections", []):
        if stage1_only and s.get("name") == SECTION["name"]:
            continue
        for it in s.get("items", []):
            yield it
            yield from it.get("people", ())
            if isinstance(it.get("entity"), dict):
                yield it["entity"]


def confirmed_refs(report: dict, stage1_only: bool = True) -> list:
    """The stage-1 records: every ref the report holds as confirmed (the
    subject is always one), byte order. With `stage1_only` false, every
    section is read, the second pass's too: the guard that no near item
    entered the confirmed set reads it that way."""
    out = set()
    for it in _all_items(report, stage1_only):
        if it.get("ref") and (it is report.get("subject") or it.get("grade") == "confirmed") and not it.get("missing"):
            out.add(it["ref"])
    return sorted(out)


def listed_refs(report: dict) -> set:
    """Every ref the report lists, whatever its grade."""
    return {it["ref"] for it in _all_items(report) if it.get("ref")}


def allowed_views(report: dict) -> set:
    return {r["view"] for r in (report.get("template") or {}).get("reads", [])}


# ── the near links from a set of refs ───────────────────────────────────────

def near_links(conn, refs: list, listed: set = frozenset()) -> dict:
    """{'links', 'omitted', 'already'}: the stored near links touching any of
    `refs`, each {this, other, rule, evidence, grade 'near', reason, watch,
    decision, path?}, with the rest of every name-only star read through
    its centre. A link whose other end is one of `refs` or already `listed`
    is dropped and counted in 'already'. Confirmed and related links are
    never read here."""
    refs = sorted(set(refs))
    out = {"links": [], "omitted": 0, "already": 0}
    if not refs or not walk.links_built(conn):
        return out
    got = db.rows(conn, "select *, count(*) over () as total from pub.links where grade = 'near' and (row_a = any(%s) or row_b = any(%s)) "
                        'order by rule, row_a collate "C", row_b collate "C" limit %s', (refs, refs, LIMITS["links"]))
    total = got[0]["total"] if got else 0
    out["omitted"] = max(0, total - len(got))
    mine, seen = set(refs), set(refs) | set(listed)
    spokes, kept = [], {}
    for l in got:
        if l.get("grade") != "near":
            continue   # the query asks for near only; a reader never upgrades what it did not ask for
        this, other = (l["row_a"], l["row_b"]) if l["row_a"] in mine else (l["row_b"], l["row_a"])
        link = {"this": this, "other": other, "rule": l["rule"], "evidence": l.get("evidence"), "grade": "near",
                "reason": reason_for(l), "watch": l.get("watch") or [], "decision": l.get("decision"), "relation": None}
        if l["rule"] == walk.NAME_ONLY:
            spokes.append(link)
        if other in seen:
            out["already"] += 1
            continue
        if other in kept:
            continue   # one line per row reached; the first rule in order names it
        kept[other] = link
    star, star_omitted = walk.star_links(conn, spokes, seen | set(kept))
    for l in star:
        if l["other"] not in kept:
            l["grade"], l["reason"] = "near", reason_for(l)
            kept[l["other"]] = l
    out["omitted"] += star_omitted
    out["links"] = sorted(kept.values(), key=lambda l: (str(l["rule"]), l["other"]))
    return out


# ── the items ───────────────────────────────────────────────────────────────

def _as_near(it: dict, kind: str) -> dict:
    """Every stage-2 item: grade near with a reason, marked as the second
    pass's, whatever the walk's helper returned."""
    it["grade"] = "near"
    it["reason"] = (it.get("reason") or "").strip() or NO_REASON_DEFAULT
    it["near"] = True
    it["stage"] = 2
    it["near_kind"] = kind
    if isinstance(it.get("entity"), dict):   # the entity a near row sits on is reached through the near link: near too
        e = it["entity"]
        e["grade"], e["reason"], e["stage"], e["near"] = "near", walk.NEAR_THROUGH_NEAR.format(reason=it["reason"]), 2, True
    return it


def _people(conn, report: dict, cache: dict) -> list:
    """The confirmed person items of the first report a name join reads
    from, each with its row (a saved report carries none: read again)."""
    out = []
    for it in _all_items(report):
        if it.get("grade") != "confirmed" and it is not report.get("subject"):
            continue
        if it.get("view") not in walk.NAME_JOIN_FROM and it.get("view") not in walk.NAMED_ROWS:
            continue
        if it.get("suppressed"):
            continue
        if not it.get("row"):
            hit = walk.resolve(conn, it["ref"], cache)
            if not hit:
                continue
            it = dict(it, row=hit[1])
        out.append(it)
    seen, uniq = set(), []
    for p in out:
        if p["ref"] not in seen:
            seen.add(p["ref"])
            uniq.append(p)
    return uniq


def stage2_items(conn, report: dict) -> dict:
    """{'items', 'by_kind', 'omitted', 'already', 'skipped', 'from'}: the near
    items from the first report's records, every one graded near."""
    refs = confirmed_refs(report)
    listed = listed_refs(report)
    allowed = allowed_views(report)
    cache, skipped, items, taken = {}, [], [], set(listed)
    got = near_links(conn, refs, listed)
    omitted, already = got["omitted"], got["already"]
    for i, l in enumerate(got["links"]):
        if len(items) >= LIMITS["items"]:   # each row read costs queries: stop at the limit and count the rest
            omitted += len(got["links"]) - i
            break
        it = walk.link_item(conn, l, cache, allowed, skipped, via=l["this"])
        if it is None or it.get("missing") or it["ref"] in taken:
            continue
        taken.add(it["ref"])
        it["reason"] = l["reason"]
        it["rule"] = l["rule"]
        items.append(_as_near(it, STORED))
    people = _people(conn, report, cache)
    joined, j_omitted = walk.name_joined(conn, [p for p in people if p["view"] in walk.NAME_JOIN_FROM], allowed, skipped)
    omitted += j_omitted
    for ref in sorted(joined):
        for it in joined[ref]:
            if it["ref"] in taken:
                already += 1
                continue
            taken.add(it["ref"])
            items.append(_as_near(it, REPORT))
    for p in people:
        if p["view"] not in walk.NAMED_ROWS:
            continue
        for it in walk.named_rows(conn, cat.BY_NAME[p["view"]], p["row"], allowed, skipped, p["ref"]):
            if "omitted" in it:
                omitted += it["omitted"]
                continue
            if it["ref"] in taken:
                already += 1
                continue
            taken.add(it["ref"])
            items.append(_as_near(it, REPORT))
    items.sort(key=lambda it: (it["near_kind"], str(it.get("rule") or ""), it["ref"]))
    if len(items) > LIMITS["items"]:
        omitted += len(items) - LIMITS["items"]
        items = items[:LIMITS["items"]]
    by_kind = {}
    for it in items:
        k = f"{it['near_kind']}:{it.get('rule') or ''}"
        by_kind[k] = by_kind.get(k, 0) + 1
    return {"items": items, "by_kind": dict(sorted(by_kind.items())), "omitted": omitted, "already": already,
            "skipped": sorted(set(skipped)), "from": len(refs)}


# ── the second report ───────────────────────────────────────────────────────

def stage2(conn, report: dict) -> dict:
    """The finished first report with the second pass added: one more
    section, `near`, after the first report's own, and `report['stage2']`
    counting what it found, by kind, and what it left out. The first
    report is not changed (a copy is returned), its confirmed records stay
    exactly what they were, and the presentation rules are run again over
    the whole. A report that was not found is returned as it is."""
    out = copy.copy(report)
    out["sections"] = [dict(s) for s in report.get("sections", []) if s.get("name") != SECTION["name"]]
    out["citations"] = list(report.get("citations", []))
    out["problems"] = [p for p in report.get("problems", [])]
    if not report.get("found"):
        return out
    before = confirmed_refs(report)
    got = stage2_items(conn, report)
    items = got["items"]
    number = {(c["view"], c["key"]): c["n"] for c in out["citations"]}
    for it in items:
        c = it["citation"]
        key = (c["view"], c["key"])
        if key not in number:
            number[key] = len(number) + 1
            out["citations"].append({"n": number[key], **c})
        it["cite"] = number[key]
    sec = {**SECTION, "views": sorted({it["view"] for it in items}), "items": items, "confirmed": 0, "near": len(items),
           "omitted": got["omitted"], "omitted_views": [], "blank": None if items else BLANK, "not_held": [], "own": None,
           "statuses": [], "changed": False, "new": None, "cannot_say": None, "stage": 2}
    out["sections"].append(sec)
    out["stage"] = 2
    out["stage2"] = {"from_records": got["from"], "near": len(items), "by_kind": got["by_kind"], "omitted": got["omitted"],
                     "already_listed": got["already"], "skipped": got["skipped"], "limits": dict(LIMITS)}
    after = confirmed_refs(out, stage1_only=False)
    if after != before:   # a near item in the confirmed set is a fault, never a report
        raise AssertionError(f"stage 2 changed the confirmed set: {len(set(after) - set(before))} added, {len(set(before) - set(after))} lost")
    out["problems"] = rules.problems(out)
    return out


def summary(report: dict) -> str:
    """What the second pass read and left out, as plain text, for the end of
    the memo (the memo's own printer prints the near section's lines with
    the rest of the report)."""
    s2 = report.get("stage2")
    if not s2:
        return "NEAR LINKS: not asked for (the first report follows confirmed links only)\n"
    out = ["NEAR LINKS, THE SECOND PASS",
           f"  {s2['near']:,} near row(s) from {s2['from_records']:,} confirmed record(s) of the first report"]
    out += [f"  - {k.replace(':', ', rule ', 1) if k.split(':', 1)[1] else k.split(':', 1)[0]}: {n:,}" for k, n in s2["by_kind"].items()]
    if s2.get("omitted"):
        out.append(f"  and {s2['omitted']:,} more near link(s) past the limits ({s2['limits']['links']} links read, {s2['limits']['items']} rows "
                   "listed), not listed: start a report from one of the records to go on")
    if s2.get("already_listed"):
        out.append(f"  {s2['already_listed']:,} near link(s) reach a row the first report already lists; not listed again")
    if s2.get("skipped"):
        out.append("  views reached but not read, because the template does not name them: " + ", ".join("pub." + v for v in s2["skipped"]))
    return "\n".join(out) + "\n"
