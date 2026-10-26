"""The reading of the Hansard export (profile `hansard-export`), from text,
no model. One pass over the export's lines:

  member   one row of `members`, keyed by Parliament's member id
  section  one row of `sections` with its text, after its text is hashed
           against the old `body_hash` (SHA-1); and one row of `turns` per
           entry of its speaker list, in printed order. The label is the
           old capture's reading of the page; the member id and roster name
           are what it carried. Nothing is matched by name here
  sitting  one row of `sittings`: the old row's own counts, beside the same
           counts made again from the sections read
  speech   one row of `old_speeches`, the old derivation, for the check

Every row is "taken from the old estate's tables; original not held" and
cites the export's hash, page 1, and its place: `sitting <day> section <n>`
(`turn <k>` after it for a turn). `only` (a set of sitting days) reads those
days alone, with every member: the sample's way and a re-read of one day.

Items in (lines) equal items out (rows) plus items set aside.
"""
import datetime as dt
import hashlib
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field

from support import profiles
from registers.hansard import capture

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "hansard-export"
READER = "registers.hansard.read 1"
PAGE = 1


@dataclass
class Result:
    members: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    turns: list = field(default_factory=list)
    sittings: list = field(default_factory=list)
    old_speeches: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)      # (item, stage, reason)
    counts: dict = field(default_factory=dict)


def profile_version(slug: str = PROFILE) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request hansard-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def place(day: str, index=None, ordinal=None) -> str:
    out = f"sitting {day}"
    if index is not None:
        out += f" section {index}"
    if ordinal is not None:
        out += f" turn {ordinal}"
    return out


def _int(v):
    return None if v in (None, "") else int(v)


def read(data: bytes, sha: str, only=None) -> Result:
    res, version = Result(), profile_version()
    cite = {"source_note": capture.EXPORT_NOTE, "document": sha, "page": PAGE, "read_from": "text",
            "reader": READER, "profile": PROFILE, "profile_version": version}
    lines = data.decode("utf-8").splitlines()
    roster, sittings, seen = {}, [], set()
    by_day = defaultdict(list)
    n_in = 0
    for i, line in enumerate(lines, 1):
        try:
            r = json.loads(line)
        except ValueError:
            n_in += 1
            res.set_aside.append((f"line {i}", "read", "not a JSON object"))
            continue
        kind = r.get("kind")
        if kind == "member":
            n_in += 1
            roster[r["member_id"]] = r
            res.members.append({"key": r["member_id"], "display_name": r.get("display_name"),
                                "sort_name": r.get("sort_name"), "parliaments": r.get("parliaments"),
                                "place": f"member {r['member_id']}", **cite})
            continue
        day = r.get("sitting_date")
        if only is not None and day not in only:
            continue
        n_in += 1
        if kind == "sitting":
            sittings.append(r)
        elif kind == "section":
            key = f"{day}/{r['section_index']}"
            if key in seen:
                res.set_aside.append((key, "read", "a second line for the same sitting and section"))
                continue
            seen.add(key)
            text = r.get("text") or ""
            if hashlib.sha1(text.encode("utf-8")).hexdigest() != r.get("body_hash"):
                res.set_aside.append((key, "read", "the text does not hash to the old body_hash"))
                continue
            by_day[day].append(r)
            res.sections.append({
                "key": key, "sitting_on": day, "section_index": r["section_index"], "parliament": _int(r.get("parliament")),
                "volume": _int(r.get("volume")), "proceeding": r.get("proceeding"), "subject": r.get("subject"),
                "bill_title": r.get("bill_title"), "bill_id": r.get("bill_id"), "progress": r.get("progress"),
                "old_status": r.get("status"), "text": text, "chars": len(text), "text_sha1": r["body_hash"],
                "turns": len(r.get("speakers") or []), "url": r.get("url"), "captured_at": r.get("fetched_at"),
                "old_id": r.get("old_id"), "place": place(day, r["section_index"]), **cite})
            for k, e in enumerate(r.get("speakers") or [], 1):
                e = e or {}
                mid = e.get("member_id") or None
                res.turns.append({
                    "key": f"{key}/{k}", "section": key, "sitting_on": day, "section_index": r["section_index"],
                    "ordinal": k, "label": e.get("label"), "member_id": mid, "roster_name": e.get("name"),
                    "role": e.get("role"), "in_roster": False, "place": place(day, r["section_index"], k), **cite})
        elif kind == "speech":
            res.old_speeches.append({
                "key": str(r["old_id"]), "sitting_on": day, "section_index": r["section_index"],
                "member_id": r.get("member_id"), "speaker_label": r.get("speaker_label"),
                "speaker_name": r.get("speaker_name"), "speech_count": r.get("speech_count"),
                "retired_at": r.get("retired_at"), "document": sha})
        else:
            res.set_aside.append((f"line {i}", "read", f"a line of unknown kind {kind!r}"))
    for t in res.turns:
        t["in_roster"] = t["member_id"] in roster if t["member_id"] else False
    for r in sittings:
        day = r["sitting_date"]
        secs = by_day.get(day, [])
        turns = [e or {} for s in secs for e in (s.get("speakers") or [])]
        attributed = [e["member_id"] for e in turns if e.get("member_id")]
        urls = sorted({s.get("url") for s in secs if s.get("url")})
        if len(urls) > 1:
            res.set_aside.append((day, "read", f"the day's sections name {len(urls)} pages; the first is cited"))
        res.sittings.append({
            "key": day, "sitting_on": day, "parliament": _int(r.get("parliament")), "volume": _int(r.get("volume")),
            "progress": r.get("progress"), "url": urls[0] if urls else None, "sections": len(secs),
            "turns": len(turns), "attributed": len(attributed), "unattributed": len(turns) - len(attributed),
            "speakers": len(set(attributed)), "old_sections": r.get("sections"), "old_speeches": r.get("speeches"),
            "old_unattributed": r.get("unattributed"), "old_speakers": r.get("speakers"),
            "old_derived_at": r.get("derived_at"),
            "captured_at": max((s["fetched_at"] for s in secs if s.get("fetched_at")), default=None,
                               key=lambda v: dt.datetime.fromisoformat(v)),
            "place": place(day), **cite})
    held = {s["key"] for s in res.sittings}
    for day in sorted(set(by_day) - held):
        res.set_aside.append((day, "read", "sections held for a day the old sittings table has no row for"))
    res.counts = {"lines": n_in, "members": len(res.members), "sections": len(res.sections),
                  "sittings": len(res.sittings), "old_speeches": len(res.old_speeches), "turns": len(res.turns),
                  "set_aside": len(res.set_aside)}
    return res


def balanced(res: Result) -> bool:
    """Items in equal items out plus items set aside (the day-level notes are
    about rows that were read, so they are not items)."""
    out = res.counts["members"] + res.counts["sections"] + res.counts["sittings"] + res.counts["old_speeches"]
    aside = sum(1 for item, stage, why in res.set_aside if item.startswith("line ") or item.count("/") == 1)
    return res.counts["lines"] == out + aside
