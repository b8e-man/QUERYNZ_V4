"""The reading: the four export parts → this lane's rows, each stamped with
its reader, its profile and version, and read from text. Nothing here calls a
model, so the fast tier runs the same code.

  entities            one per entity the package names, keyed by its NZBN
                      (the source's own identifier), or by its register's own
                      number where it has none (retirement villages)
  entity_states       an entity's state in an earlier file, where a later one changed it
  directors           one per director role; the window is the files it was in
                      (first_file to last_file) and the start as filed. The
                      file states no end, so `ended_on` stays empty: a role
                      that left the file is `in_latest` false, never dated
  shareholders        one per holding, the same way
  registered_offices  a company's registered address, which is published

Items in equal items out plus items set aside, twice over: every export line
is a row or a catch-log line; and each file's own line count, as the old
loader recorded it, is the rows from that file plus the lines it folded into
another (a catch-log line that carries the count). A reading that does not
reconcile raises and publishes nothing.

    read(part, data, sha, only=None, entities=None)   Result
    entity_key(register, nzbn, number)
"""
import datetime as dt
import gzip
import hashlib
import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field

from keys.dates import filed_date
from keys.numbers import nzbn as nzbn_ok
from support import profiles
from registers.companies import capture

HERE = os.path.dirname(os.path.abspath(__file__))
PROPOSED = os.path.join(HERE, "profile-proposed.jsonl")
PROFILE = "companies-register-export"
READER = "registers.companies.read 1"
TABLE_OF = {"entities": ("entities", "entity_states"), "directors": ("directors",),
            "shareholders": ("shareholders",), "addresses": ("registered_offices",)}
_NZBN = re.compile(r'"nzbn": (?:null|"([^"]*)")')
_NUMBER = re.compile(r'"number": (?:null|"([^"]*)")')
_ADDRESS_FIELDS = ("care_of", "line_1", "line_2", "line_3", "line_4", "postcode")


@dataclass
class Result:
    rows: dict = field(default_factory=lambda: defaultdict(list))   # table → [row]
    set_aside: list = field(default_factory=list)                   # (item, stage, reason, count)
    counts: dict = field(default_factory=dict)
    header: dict = field(default_factory=dict)


def profile_version(slug: str = PROFILE) -> int:
    """The ledger's version; until the integrator appends it, the lane's
    proposed line (merge request companies-1)."""
    p = profiles.profile(slug) or profiles.profile(slug, path=PROPOSED)
    if p is None:
        raise LookupError(f"no document profile {slug}")
    return int(p["version"])


def short(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]


def entity_key(register: str, nzbn, number) -> str:
    if nzbn:
        return f"companies/{nzbn}"
    return f"companies/{register}/{number}" if number else None


def lines_of(data: bytes, only=None):
    """(line number, object) for every line after the header; with `only`
    (a set of NZBNs and register numbers), the lines of those entities."""
    text = gzip.decompress(data).decode("utf-8")
    for n, l in enumerate(text.splitlines(), 1):
        if n == 1 or not l.strip():
            continue
        if only is not None:
            m = _NZBN.search(l)
            if m and m.group(1):
                if m.group(1) not in only:
                    continue
            else:           # no NZBN: the register's own number is the key
                k = _NUMBER.search(l)
                if not (k and k.group(1) in only):
                    continue
        yield n, json.loads(l)


def header_of(data: bytes) -> dict:
    with gzip.open(__import__("io").BytesIO(data), "rt", encoding="utf-8") as f:
        return json.loads(f.readline())


def _date(raw, item: str, what: str, out: Result, stage: str):
    """An ISO date as the old tables stored it, else a filed date read day
    first; one that is not a real day is empty and a catch-log line."""
    if raw in (None, ""):
        return None
    try:            # the old tables' own date columns: kept as they are, the 1800s included
        return dt.date.fromisoformat(str(raw)).isoformat()
    except ValueError:
        pass
    d = filed_date(str(raw))
    if d is None:
        out.set_aside.append((item, stage, f"{what} {raw!r} is not a real day: left empty", 1))
        return None
    return d.isoformat()


def _number(n):
    """Shares as filed, without float noise: '100', '2.5'."""
    if n is None:
        return None
    s = str(n)
    return s.rstrip("0").rstrip(".") if "." in s else s


def _suffixed(rows: list, order) -> None:
    """Rows that share a base key get /2, /3… in a fixed order of their content,
    so the key is the same on every read of the same document."""
    by = defaultdict(list)
    for r in rows:
        by[r["key"]].append(r)
    for k, group in by.items():
        if len(group) > 1:
            group.sort(key=order)
            for i, r in enumerate(group[1:], 2):
                r["key"] = f"{k}/{i}"


def read(part: str, data: bytes, sha: str, only=None, entities=None, loaded_at: str = None) -> Result:
    """One export part. `only`: the NZBNs (and register numbers) to read, the
    sample's; None for all. `entities`: the entity keys the entities part
    gave, to log a role or address whose entity the package does not name."""
    loaded_at = loaded_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    out = Result(header=header_of(data))
    files = out.header["files"]
    latest = files[-1]
    version = profile_version()
    base = {"document": sha, "page": 1, "read_from": "text", "reader": READER, "profile": PROFILE,
            "profile_version": version, "loaded_at": loaded_at}
    stage = part
    lines = 0
    from_lines = 0          # catch-log lines that stand for one export line each
    in_file = defaultdict(int)

    def aside(item, why):
        nonlocal from_lines
        from_lines += 1
        out.set_aside.append((item, stage, why, 1))

    for n, r in lines_of(data, only):
        lines += 1
        item = f"{sha}/line {n}"
        ek = entity_key(r.get("register") or "companies", r.get("nzbn"), r.get("number"))
        if ek is None:
            aside(item, "no NZBN and no register number: no key")
            continue
        place = f"line {n}"
        if part == "entities":
            if not r.get("name"):
                aside(item, "no entity name")
                continue
            in_latest = r.get("in_latest") if r.get("in_latest") is not None else r["last_file"] == latest
            for f in r.get("files") or ():
                in_file[f] += 1
            row = {"key": ek, **base, "place": place, "filed": {
                "register": r["register"], "nzbn": r.get("nzbn"), "number": r.get("number"), "name": r["name"],
                "entity_type": r.get("type"), "status": r.get("status"),
                "registered_on": _date(r.get("registered_on"), item, "registered date", out, stage),
                "removed_on": _date(r.get("removed_on"), item, "removal date", out, stage),
                "in_latest": in_latest, "first_file": (r.get("files") or [None])[0], "last_file": r["last_file"],
                "extra": json.dumps(r["extra"], ensure_ascii=False, sort_keys=True) if r.get("extra") else None,
                "old_id": r.get("old_id"), "source_note": capture.EXPORT_NOTE}}
            if r.get("nzbn") and not nzbn_ok(r["nzbn"]):
                out.counts["nzbn_not_gs1"] = out.counts.get("nzbn_not_gs1", 0) + 1
            if r.get("also"):
                out.set_aside.append((item, stage, f"the latest file lists this entity {r['also'] + 1} times: "
                                      f"the last is kept", r["also"]))
            out.rows["entities"].append(row)
            for e in r.get("earlier") or ():
                out.rows["entity_states"].append({"key": f"{ek}/in/{e['file']}", **base, "place": place, "filed": {
                    "entity_key": ek, "file": e["file"], "name": e.get("name") or r["name"],
                    "entity_type": e.get("type"), "status": e.get("status"),
                    "registered_on": _date(e.get("registered_on"), item, "earlier registered date", out, stage),
                    "removed_on": _date(e.get("removed_on"), item, "earlier removal date", out, stage)}})
        elif part in ("directors", "shareholders"):
            fs = r.get("files") or []
            if not fs:
                aside(item, f"from {r.get('last_file')}, not a monthly file")
                continue
            for f in fs:
                in_file[f] += 1
            if part == "directors":
                names = [r.get("first_name"), r.get("middle_names"), r.get("last_name")]
                full = r.get("full_name") or " ".join(x for x in names if x)
                if not full:
                    aside(item, "a director role with no name")
                    continue
                content = "|".join(x or "" for x in names + [r.get("appointed_on")])
                filed = {"first_name": names[0], "middle_names": names[1], "last_name": names[2], "full_name": full,
                         "role_type": (r.get("role_type") or "").upper() or "DIRECTOR",
                         "appointed_on": _date(r.get("appointed_on"), item, "start date", out, stage),
                         "ended_on": None}
            else:
                name = r.get("full_name") or r.get("shareholder_entity_name")
                if not name:
                    aside(item, "a shareholding with no holder's name")
                    continue
                shares = _number(r.get("shares"))
                content = f"{name}|{shares}|{r.get('allocation_type') or ''}"
                filed = {"shareholder_type": r.get("shareholder_type"), "name": name,
                         "holder_nzbn": r.get("shareholder_nzbn"), "shares": shares,
                         "allocation_status": r.get("allocation_type")}
            if entities is not None and ek not in entities:
                out.counts["no_entity"] = out.counts.get("no_entity", 0) + 1
            kind = part[:-1]
            out.rows[part].append({"key": f"{ek}/{kind}/{short(content)}", **base, "place": place, "filed": {
                "entity_key": ek, "nzbn": r["nzbn"], "company_number": r.get("number"), **filed,
                "in_latest": fs[-1] == latest, "first_file": fs[0], "last_file": fs[-1],
                "suppressed": bool(r.get("suppressed")), "old_id": r.get("old_id"),
                "source_note": capture.EXPORT_NOTE}})
        elif part == "addresses":
            if not any(r.get(k) for k in _ADDRESS_FIELDS):
                aside(item, "a registered office line with no address in it")
                continue
            if entities is not None and ek not in entities:
                out.counts["no_entity"] = out.counts.get("no_entity", 0) + 1
            started = _date(r.get("start"), item, "start date", out, stage)
            out.rows["registered_offices"].append({
                "key": f"{ek}/registered-office/{started or 'undated'}/"
                       f"{short('|'.join(r.get(k) or '' for k in _ADDRESS_FIELDS + ('country',)))}", **base, "place": place, "filed": {
                    "entity_key": ek, "register": r["register"], "started_on": started,
                    **{k: r.get(k) for k in _ADDRESS_FIELDS}, "country": r.get("country"),
                    "in_latest": bool(r.get("in_latest")), "last_file": r["last_file"],
                    "source_note": capture.EXPORT_NOTE}})
        else:
            raise ValueError(f"no part {part}")

    if part == "addresses":
        # the old tables kept a body's registered office again when another field of its row changed: the same
        # address and start twice is one filed fact, so the current line is kept and the others logged
        keep = {}
        for row in sorted(out.rows["registered_offices"], key=lambda x: (not x["filed"]["in_latest"], x["place"])):
            if row["key"] in keep:
                aside(f"{sha}/{row['place']}", f"the same registered office as {keep[row['key']]['place']}")
            else:
                keep[row["key"]] = row
        out.rows["registered_offices"] = sorted(keep.values(), key=lambda x: int(x["place"].split()[1]))

    tables = TABLE_OF[part]
    order = lambda row: (not row["filed"].get("in_latest", True), json.dumps(row["filed"], sort_keys=True, default=str))
    for t in tables:
        _suffixed(out.rows[t], order)
        if len({x["key"] for x in out.rows[t]}) != len(out.rows[t]):
            raise AssertionError(f"companies {t}: two rows share a key")

    # every export line is a row or a catch-log line
    made = len(out.rows[tables[0]])
    if made + from_lines != lines:
        raise AssertionError(f"companies {part} does not reconcile: {lines} lines, {made} rows, {from_lines} set aside")
    # each file's own count is its rows plus the lines the old loader folded (whole reads only)
    folded = {}
    if only is None and part in ("entities", "directors", "shareholders"):
        for f in files:
            stated = out.header["runs"][f][part]
            got = in_file[f]
            if got > stated:
                raise AssertionError(f"companies {part}: {got} rows from {f}, more than the {stated} it had")
            if got < stated:
                folded[f] = stated - got
                out.set_aside.append((f"{sha}/{f}", stage, f"the old loader folded {stated - got} of the file's "
                                      f"{stated} lines into a line it already held (same company and "
                                      f"{'names and start' if part == 'directors' else 'holder, shares and status' if part == 'shareholders' else 'NZBN'}); "
                                      f"they cannot be recovered from its tables", stated - got))
    out.counts.update({"lines": lines, **{t: len(out.rows[t]) for t in tables},
                       "set_aside": len(out.set_aside), "set_aside_lines": from_lines,
                       **{f"in {f}": in_file[f] for f in files if in_file.get(f)},
                       **{f"folded in {f}": v for f, v in folded.items()}})
    return out
