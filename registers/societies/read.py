"""The reading: societies and their officers with windows, under the
register's own identifiers, each row stamped with its reader, its profile
and version, and read from text. Nothing here calls a model.

  societies       one per society, keyed by its NZBN (the register's own
                  identifier), else its incorporation number
  society_states  a society's earlier state, where the monthly file changed it
  officers        one per officer role; the window is the register's own
                  start and end, and read_on is the ask that listed it
  asks            one per ask of the register, whatever it found

Two documents feed it: the once-only export parts (`read_export`), and the
register's entity detail as one ask answered (`read_answer`). An officer's
address, where an answer carries one, goes to `private` keyed by the role's
key, and nowhere else: no row, no catch-log line, no count names it.

Items in equal items out plus items set aside: every export line, and every
role in an answer, is a row or a catch-log line, and each part's count
reconciles with the old table's own count in its header. Across parts, every
society's officers reconcile with what its last ask said it gave
(`reconcile`). A reading that does not reconcile raises and publishes nothing.

    read_export(part, data, sha, only=None, societies=None)   Result
    read_answer(data, sha, asked_at, societies=None)           Result
    reconcile(officers, asks)                                  (lines set aside, counts)
"""
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

from keys.dates import filed_date
from support import profiles
from registers.societies import capture

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
EXPORT_PROFILE = "societies-register-export"
ANSWER_PROFILE = "nzbn-entity-detail"
READER = "registers.societies.read 1"
TABLE_OF = {"societies": ("societies", "society_states"), "officers": ("officers",), "asks": ("asks",),
            "entity": ("officers", "asks")}
NZ = dt.timezone(dt.timedelta(hours=13))
_NZBN = re.compile(r'"nzbn": (?:null|"([^"]*)")')
_NUMBER = re.compile(r'"incorporation_number": (?:null|"([^"]*)")')


@dataclass
class Result:
    rows: dict = field(default_factory=lambda: defaultdict(list))   # table → [row]
    set_aside: list = field(default_factory=list)                   # (item, stage, reason, count)
    private: list = field(default_factory=list)                     # (key, address dict, document)
    counts: dict = field(default_factory=dict)
    header: dict = field(default_factory=dict)


def profile_version(slug: str) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request societies-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def short(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def society_key(nzbn, number):
    if nzbn:
        return f"societies/{nzbn}"
    return f"societies/number/{number}" if number else None


def officer_content(first, middle, last, start) -> str:
    return "|".join(x or "" for x in (first, middle, last, start))


def header_of(data: bytes) -> dict:
    with gzip.open(io.BytesIO(data), "rt", encoding="utf-8") as f:
        return json.loads(f.readline())


def lines_of(data: bytes, only=None):
    """(line number, object) for every line after the header; with `only`
    (a set of NZBNs and incorporation numbers), the lines of those societies."""
    text = gzip.decompress(data).decode("utf-8")
    for n, l in enumerate(text.splitlines(), 1):
        if n == 1 or not l.strip():
            continue
        if only is not None:
            m = _NZBN.search(l)
            if m and m.group(1):
                if m.group(1) not in only:
                    continue
            else:
                k = _NUMBER.search(l)
                if not (k and k.group(1) in only):
                    continue
        yield n, json.loads(l)


def _date(raw, item: str, what: str, out: Result, stage: str):
    """An ISO date as the old tables or the register gave it, else a filed
    date read day first; one that is not a real day is empty and logged."""
    if raw in (None, ""):
        return None
    s = str(raw)
    try:
        return dt.date.fromisoformat(s[:10]).isoformat()
    except ValueError:
        pass
    d = filed_date(s)
    if d is None:
        out.set_aside.append((item, stage, f"{what} {raw!r} is not a real day: left empty", 1))
        return None
    return d.isoformat()


def _nz_day(ts: str) -> str:
    """The New Zealand day of a timestamp as the old tables printed it."""
    t = dt.datetime.fromisoformat(str(ts).replace(" ", "T"))
    return (t.astimezone(NZ) if t.tzinfo else t).date().isoformat()


def _suffixed(rows: list) -> None:
    """Rows that share a base key get /2, /3… in a fixed order of their
    content, so the key is the same on every read of the same document."""
    by = defaultdict(list)
    for r in rows:
        by[r["key"]].append(r)
    for k, group in by.items():
        if len(group) > 1:
            group.sort(key=lambda row: json.dumps(row["filed"], sort_keys=True, default=str))
            for i, r in enumerate(group[1:], 2):
                r["key"] = f"{k}/{i}"


def _base(sha: str, profile: str, loaded_at: str) -> dict:
    return {"document": sha, "page": 1, "read_from": "text", "reader": READER, "profile": profile,
            "profile_version": profile_version(profile), "loaded_at": loaded_at}


def _officer_row(base, sk, nzbn, place, names, full, role, item, out, stage, read_on, note, **extra):
    first, middle, last = names
    started = _date(role.get("start"), item, "start date", out, stage)
    ended = _date(role.get("end"), item, "end date", out, stage)
    return {"key": f"{sk}/officer/{short(officer_content(first, middle, last, started))}", **base, "place": place,
            "filed": {"society_key": sk, "nzbn": nzbn, "first_name": first, "middle_names": middle,
                      "last_name": last, "full_name": full, "role_type": role.get("type") or "Officer",
                      "role_status": role.get("status"), "started_on": started, "ended_on": ended,
                      "ended_on_stated": ended is not None, "first_read_on": read_on, "last_read_on": read_on,
                      "suppressed": bool(role.get("suppressed")), "unique_identifier": role.get("uid"),
                      "source_note": note, **extra}}


def read_export(part: str, data: bytes, sha: str, only=None, societies=None, loaded_at: str = None) -> Result:
    """One export part. `only`: the NZBNs (and incorporation numbers) to
    read, the sample's; None for all. `societies`: the society keys the
    societies part gave, to count an officer or ask whose society it does not name."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result(header=header_of(data))
    base = _base(sha, EXPORT_PROFILE, loaded_at)
    lines = from_lines = 0
    by_society = defaultdict(list)

    def aside(item, why):
        nonlocal from_lines
        from_lines += 1
        out.set_aside.append((item, part, why, 1))

    for n, r in lines_of(data, only):
        lines += 1
        item, place = f"{sha}/line {n}", f"line {n}"
        sk = society_key(r.get("nzbn"), r.get("incorporation_number"))
        if sk is None:
            aside(item, "no NZBN and no incorporation number: no key")
            continue
        if societies is not None and part != "societies" and sk not in societies:
            out.counts["no_society"] = out.counts.get("no_society", 0) + 1
        if part == "societies":
            if not r.get("entity_name"):
                aside(item, "no society name")
                continue
            by_society[sk].append((n, r))
        elif part == "officers":
            names = (r.get("first_name"), r.get("middle_names"), r.get("last_name"))
            full = r.get("full_name") or " ".join(x for x in names if x)
            if not full:
                aside(item, "an officer role with no name")
                continue
            out.rows["officers"].append(_officer_row(
                base, sk, r["nzbn"], place, names, full,
                {"type": r.get("role_type"), "status": r.get("role_status"), "start": r.get("start_date"),
                 "end": r.get("end_date"), "uid": r.get("unique_identifier")},
                item, out, part, _nz_day(r["imported_at"]), capture.EXPORT_NOTE, old_id=r.get("old_id")))
        elif part == "asks":
            at = str(r["asked_at"]).replace(" ", "T")
            out.rows["asks"].append({"key": f"{sk}/ask/{at[:19]}", **base, "place": place, "filed": {
                "society_key": sk, "nzbn": r["nzbn"], "asked_at": at, "answered": bool(r.get("ok")),
                "officers": int(r.get("officers") or 0), "note": _ask_note(r.get("note")),
                "source_note": capture.EXPORT_NOTE}})
        else:
            raise ValueError(f"no part {part}")

    if part == "societies":
        for sk in sorted(by_society):
            group = by_society[sk]
            current = [(n, r) for n, r in group if r.get("vanished_at") is None]
            gone = [(n, r) for n, r in group if r.get("vanished_at") is not None]
            n, head = (current or gone)[-1]
            item = f"{sha}/line {n}"
            if len(current) > 1:
                for m, _ in current[:-1]:
                    aside(f"{sha}/line {m}", f"the file lists this society again at line {n}: the last is kept")
            out.rows["societies"].append({"key": sk, **base, "place": f"line {n}", "filed": {
                "nzbn": head.get("nzbn"), "number": head.get("incorporation_number"), "name": head["entity_name"],
                "status": head.get("entity_status"),
                "registered_on": _date(head.get("registration_date"), item, "registered date", out, part),
                "removed_on": _date(head.get("deregistration_date"), item, "deregistration date", out, part),
                "act": head.get("incorporated_societies_act"),
                "reregistered_on": _date(head.get("incsoc2022act_reregistration_date"), item,
                                         "re-registration date", out, part),
                "charity_number": head.get("charities_register_number"),
                "in_latest": bool(current), "last_file": head["file"],
                "party_society": capture.is_party_society(head["entity_name"], head.get("entity_status")),
                "source_note": capture.EXPORT_NOTE}})
            for m, g in (gone if current else gone[:-1]):
                gi = f"{sha}/line {m}"
                out.rows["society_states"].append({"key": f"{sk}/in/{g['file']}", **base, "place": f"line {m}",
                    "filed": {"society_key": sk, "file": g["file"], "name": g["entity_name"],
                              "status": g.get("entity_status"),
                              "registered_on": _date(g.get("registration_date"), gi, "earlier registered date",
                                                     out, part),
                              "removed_on": _date(g.get("deregistration_date"), gi, "earlier deregistration date",
                                                  out, part),
                              "vanished_at": g.get("vanished_at")}})

    for t in TABLE_OF[part]:
        _suffixed(out.rows[t])
        if len({x["key"] for x in out.rows[t]}) != len(out.rows[t]):
            raise AssertionError(f"societies {t}: two rows share a key")

    made = len(out.rows[TABLE_OF[part][0]]) + len(out.rows["society_states"]) if part == "societies" \
        else len(out.rows[TABLE_OF[part][0]])
    if made + from_lines != lines:
        raise AssertionError(f"societies {part} does not reconcile: {lines} lines, {made} rows, {from_lines} set aside")
    if only is None:
        c = out.header["counts"]
        stated = c["current"] + c["vanished"] if part == "societies" else c["rows"]
        if stated != lines:
            raise AssertionError(f"societies {part}: {lines} lines, but the old table held {stated}")
    out.counts.update({"lines": lines, **{t: len(out.rows[t]) for t in TABLE_OF[part]},
                       "set_aside": len(out.set_aside), "set_aside_lines": from_lines})
    if part == "societies":
        out.counts["party_societies"] = sum(1 for r in out.rows["societies"] if r["filed"]["party_society"])
    return out


def _ask_note(note):
    """A failed ask's note, cut at the first line: the old log appended the
    library's help text, and a URL with our key in it never reaches a row."""
    if not note:
        return None
    first = str(note).splitlines()[0]
    return re.sub(r"https?://\S+", lambda m: m.group(0).split("?")[0], first)[:200]


def reconcile(officers: Result, asks: Result) -> tuple:
    """Every society's officer rows against what its last ask said it gave.
    Returns (catch-log lines, counts); raises where the two cannot both be
    true. The old sweep replaced a society's officers only when an ask parsed
    some, so a society whose last ask gave none keeps an earlier ask's rows:
    those are counted and logged, not an error."""
    held = defaultdict(int)
    for r in officers.rows["officers"]:
        held[r["filed"]["society_key"]] += 1
    lines, counts = [], defaultdict(int)
    last = {}
    for a in asks.rows["asks"]:
        f = a["filed"]
        if f["society_key"] not in last or f["asked_at"] > last[f["society_key"]]["asked_at"]:
            last[f["society_key"]] = f
    bad = []
    for sk, a in sorted(last.items()):
        n = held.get(sk, 0)
        if a["answered"] and a["officers"] == n:
            counts["equal"] += 1
        elif a["officers"] == 0 and n > 0:
            counts["kept_from_an_earlier_ask"] += 1
            lines.append((f"{sk}/ask", "reconcile", f"its last ask ({'answered' if a['answered'] else 'failed'}) "
                          f"gave no officers; {n} kept from an earlier ask", n))
        elif a["officers"] == 0 and n == 0:
            counts["none_given"] += 1
        else:
            bad.append(f"{sk}: last ask gave {a['officers']}, {n} held")
    for sk in sorted(set(held) - set(last)):
        counts["never_asked"] += 1
        lines.append((sk, "reconcile", f"{held[sk]} officers held and no ask recorded", held[sk]))
    if bad:
        raise AssertionError(f"societies: {len(bad)} societies' officers do not reconcile with their last ask: "
                             + "; ".join(bad[:5]))
    return lines, dict(counts)


# --- the register's own answer ----------------------------------------------------------------------------------

#: the address fields an answer's role may carry; read into `private` and nowhere else
_ADDRESS_KEYS = ("roleAddress", "roleAsicAddress", "address", "addresses", "residentialAddress")


def read_answer(data: bytes, sha: str, asked_at: str, societies=None, loaded_at: str = None) -> Result:
    """One entity detail as the register answered (profile nzbn-entity-detail).
    Every role is a row or a catch-log line; an officer that is a body, not a
    person, is logged by kind. One ask row records the answer."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result()
    raw = json.loads(data)
    nzbn = str(raw.get("nzbn") or "")
    sk = society_key(nzbn, None)
    if not sk:
        raise ValueError(f"{sha}: an entity detail with no NZBN")
    base = _base(sha, ANSWER_PROFILE, loaded_at)
    read_on = _nz_day(asked_at)
    roles = raw.get("roles") or []
    made = 0
    for i, role in enumerate(roles, 1):
        item, place = f"{sha}/roles {i}", f"roles {i}"
        rtype = role.get("roleType") or ""
        if rtype.lower() != "officer":
            out.set_aside.append((item, "entity", f"a {rtype or 'untyped'} role, not an officer", 1))
            continue
        p = role.get("rolePerson") or {}
        if not p:
            out.set_aside.append((item, "entity", "an officer that is a body, not a person: not read yet", 1))
            continue
        names = (p.get("firstName"), p.get("middleNames"), p.get("lastName"))
        full = " ".join(x for x in names if x)
        if not full:
            out.set_aside.append((item, "entity", "an officer role with no name", 1))
            continue
        row = _officer_row(base, sk, nzbn, place, names, full,
                           {"type": rtype, "status": role.get("roleStatus"), "start": role.get("startDate"),
                            "end": role.get("endDate"), "uid": role.get("uniqueIdentifier"),
                            "suppressed": role.get("suppressed") or p.get("suppressed")},
                           item, out, "entity", read_on, capture.API_NOTE)
        addr = {k: role[k] for k in _ADDRESS_KEYS if role.get(k)}
        addr.update({k: p[k] for k in _ADDRESS_KEYS if p.get(k)})
        if addr:
            row["_address"] = addr
        out.rows["officers"].append(row)
        made += 1
    _suffixed(out.rows["officers"])
    for row in out.rows["officers"]:
        if "_address" in row:
            out.private.append((row["key"], row.pop("_address"), sha))
            row["filed"]["private_ref"] = row["key"]
    if made + len(out.set_aside) != len(roles):
        raise AssertionError(f"societies answer {sha}: {len(roles)} roles, {made} rows, {len(out.set_aside)} set aside")
    out.rows["asks"].append({"key": f"{sk}/ask/{asked_at[:19]}", **base, "place": "whole", "filed": {
        "society_key": sk, "nzbn": nzbn, "asked_at": asked_at, "answered": True, "officers": made, "note": None,
        "source_note": capture.API_NOTE}})
    if societies is not None and sk not in societies:
        out.counts["no_society"] = 1
    out.counts.update({"roles": len(roles), "officers": made, "set_aside": len(out.set_aside),
                       "private": len(out.private), "entity_status": raw.get("entityStatusDescription")})
    return out
