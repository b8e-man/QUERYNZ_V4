"""The gates a version passes before it is recorded as built. Each returns
(ok, one line); the build stops at the first red and records it. Every
gate reads the written folder, so what is checked is what would be
published.

  snapshot      the manifest and the folder agree both ways; every kind
                the manifest counts is on disk; every file is one of the
                ten kinds or the manifest or an extra; every file parses;
                no factory surface is inside
"""
from __future__ import annotations

import json
import os

from products.published_site import paths, version

FACTORY = ("review", "gold", "identity", "residue", "private", "sealed")


def files_of(root: str) -> list:
    out = []
    for dirpath, dirs, names in os.walk(root):
        dirs.sort()
        for n in sorted(names):
            out.append(os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, "/"))
    return out


def snapshot(version_dir: str) -> tuple:
    try:
        m = version.manifest_of(version_dir)
    except (OSError, ValueError) as exc:
        return False, f"no readable manifest: {exc}"
    files = [f for f in files_of(version_dir) if f != version.MANIFEST]
    problems = []
    counted = {}
    for rel in files:
        top = rel.split("/")
        if any(seg in FACTORY for seg in top):
            problems.append(f"factory surface inside the version: {rel}")
        kind = paths.kind_of(rel)
        if not kind and not (len(top) == 2 and top[0] == paths.ROOT and top[1][:-5] in paths.EXTRA):
            problems.append(f"not one of the ten kinds: {rel}")
            continue
        name = kind or top[1][:-5]
        counted[name] = counted.get(name, 0) + 1
        try:
            with open(os.path.join(version_dir, rel), encoding="utf-8") as f:
                json.load(f)
        except (OSError, ValueError) as exc:
            problems.append(f"{rel} does not parse: {exc}")
    for kind, n in (m.get("written") or {}).items():
        if counted.get(kind, 0) != n:
            problems.append(f"manifest counts {n} {kind} file(s), the folder holds {counted.get(kind, 0)}")
    for kind, n in counted.items():
        if kind not in (m.get("written") or {}):
            problems.append(f"{n} {kind} file(s) on disk the manifest does not count")
    if m.get("files") != len(files):
        problems.append(f"manifest says {m.get('files')} files, the folder holds {len(files)}")
    if problems:
        return False, f"{len(problems)} problem(s): " + "; ".join(problems[:6])
    return True, f"{len(files)} files in {len(counted)} kinds agree with the manifest"


GATES = [("snapshot", snapshot)]


def run_all(version_dir: str, gates=None) -> list:
    """[(name, ok, line)], stopping at the first red."""
    out = []
    for name, fn in (gates or GATES):
        ok, line = fn(version_dir)
        out.append((name, ok, line))
        if not ok:
            break
    return out


# ── the four gates beside the snapshot gate ───────────────────────────────────
import re  # noqa: E402

from products.published_site import redact as R  # noqa: E402

#: address-shaped text: a street number and a street word, a box number, a rural delivery. The gate names the file
#: and the field a hit sits in, never the text (hard limit 11).
STREET = re.compile(r"\b\d{1,5}[A-Za-z]?(?:/\d{1,4})?\s+(?:[A-Z][^\W\d_'’\-]*[\w'’\-]*\s+){1,4}"
                    r"(?:Street|St|Road|Rd|Avenue|Ave|Drive|Dr|Place|Pl|Crescent|Cres|Lane|Ln|Terrace|Tce|Way|Highway|Hwy|Parade|Pde|"
                    r"Grove|Gr|Court|Ct|Close|Cl|Rise|Esplanade|Quay|Heights|Hts|Boulevard|Blvd)\b\.?(?:,|\s|$)")
BOX = re.compile(r"\b(?:P\.?\s?O\.?\s?Box|Private\s+Bag|RD\s?\d{1,2}\b|Rural\s+Delivery)\s*\d*", re.I)


def strings_of(obj, path=""):
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from strings_of(v, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings_of(v, f"{path}.{k}" if path else k)


def payloads(version_dir: str):
    for rel in files_of(version_dir):
        if rel.endswith(".json") and rel != version.MANIFEST:
            with open(os.path.join(version_dir, rel), encoding="utf-8") as f:
                yield rel, json.load(f)


def addresses(version_dir: str, ctx=None) -> tuple:
    """No payload carries address-shaped text (hard limit 15: never shown or extractable)."""
    hits, looked = [], 0
    for rel, obj in payloads(version_dir):
        for field, s in strings_of(obj):
            looked += 1
            if len(s) < 8 or s.startswith(("data/", "http", "/assets")):
                continue
            if STREET.search(s) or BOX.search(s):
                hits.append(f"{rel} at {field}")
    if hits:
        return False, f"{len(hits)} address-shaped string(s) in the payloads: " + "; ".join(hits[:5]) + " (the text itself is not printed)"
    return True, f"{looked:,} strings read, none address-shaped"


def suppressed(version_dir: str, ctx=None) -> tuple:
    """No suppressed form appears on any surface."""
    forms = (ctx or {}).get("suppressed_forms") or []
    if not forms:
        return True, "no suppressed names in force (the list's view is not published yet; carded)"
    found = []
    for rel, obj in payloads(version_dir):
        n = R.find(obj, forms)
        if n:
            found.append(f"{rel} ({n})")
    if found:
        return False, f"{len(found)} file(s) still carry a suppressed form: " + "; ".join(found[:5])
    return True, f"{len(forms)} suppressed form(s) checked against every payload: none shown"


def donor_fold(version_dir: str, ctx=None) -> tuple:
    """One donor, one name, on every surface: every donor row a party page shows is on exactly one donor page,
    and no two donor pages share a name key."""
    by_ref, by_key, problems = {}, {}, []
    for rel, obj in payloads(version_dir):
        if paths.kind_of(rel) != "donor":
            continue
        nk = obj.get("name_key")
        if nk in by_key:
            problems.append(f"{rel} and {by_key[nk]} share the name key")
        by_key[nk] = rel
        for row in obj.get("history", []):
            if row["ref"] in by_ref:
                problems.append(f"{row['ref']} is on two donor pages")
            by_ref[row["ref"]] = rel
    rows_seen = 0
    for rel, obj in payloads(version_dir):
        if paths.kind_of(rel) == "subject" and obj.get("kind") == "party":
            for row in obj.get("donations_received", []) + obj.get("disclosures", []):
                rows_seen += 1
                if row["ref"] not in by_ref:
                    problems.append(f"{rel}: {row['ref']} has no donor page")
        if paths.kind_of(rel) in ("home", "pickers"):
            for d in obj.get("donors", []):
                if d.get("name_key") not in by_key:
                    problems.append(f"{rel}: donor {d.get('name_key')!r} has no page")
    if problems:
        return False, f"{len(problems)} problem(s): " + "; ".join(problems[:5])
    return True, f"{rows_seen:,} donor rows on party pages, each on exactly one of {len(by_key):,} donor pages"


def commission(version_dir: str, ctx=None) -> tuple:
    """A figure from outside the estate: the Commission's own published table of large donations, summed again
    by SQL through the connection (never through the figures' code path), equals what the version shows per
    party-year and for the open year."""
    conn = (ctx or {}).get("conn")
    if conn is None:
        return False, "no connection to read the Commission's table with; the gate cannot pass by default"
    try:
        with open(os.path.join(version_dir, paths.path("home")), encoding="utf-8") as f:
            home = json.load(f)
    except (OSError, ValueError) as exc:
        return False, f"no home file to check: {exc}"
    years = (ctx or {}).get("years") or []
    if not years:
        return False, "the window's years are not known to the gate"
    cur = conn.execute("select party, extract(year from coalesce(received_on, given_on))::int as y, sum(amount)::float, count(*) "
                       "from pub.disclosures where withdrawn_on is null and coalesce(amendment, '') <> 'amendment withdrawn' "
                       "and extract(year from coalesce(received_on, given_on)) >= %s group by 1, 2", (years[0],))
    table = {(r[0], r[1]): (r[2] or 0.0, r[3]) for r in cur}
    shown = {}
    for p in home.get("parties", []):
        for y, v in (p.get("disclosed_by_year") or {}).items():
            shown[(p["party"], int(y))] = float(v or 0)
    diffs, equal = [], 0
    for key, (total, n) in table.items():
        if key[0] is None:
            continue
        mine = shown.get(key)
        if mine is None:
            diffs.append(f"{key[0]} {key[1]}: the Commission's table holds ${total:,.2f} ({n}), the version shows nothing")
        elif abs(mine - total) > 0.005:
            diffs.append(f"{key[0]} {key[1]}: version ${mine:,.2f}, the Commission's table ${total:,.2f}")
        else:
            equal += 1
    for key, mine in shown.items():
        if key not in table and mine:
            diffs.append(f"{key[0]} {key[1]}: version shows ${mine:,.2f}, the Commission's table has no row")
    open_year = home.get("recent_disclosures", {}).get("year")
    open_total = sum(t for (p, y), (t, n) in table.items() if y == open_year and p is not None)
    if abs(open_total - float(home.get("recent_disclosures", {}).get("total") or 0)) > 0.005:
        diffs.append(f"open year {open_year}: version ${home['recent_disclosures']['total']:,.2f}, the Commission's table ${open_total:,.2f}")
    unresolved = [k for k in table if k[0] is None]
    if diffs:
        return False, f"{len(diffs)} party-year(s) differ from the Commission's table ({equal} equal): " + "; ".join(diffs[:4])
    return True, f"{equal} party-years and the open year equal the Commission's table to the cent" + (f"; {len(unresolved)} year(s) of unresolved-party rows not shown" if unresolved else "")


def donor_totals_of(version_dir: str) -> dict:
    out = {}
    for rel, obj in payloads(version_dir):
        if paths.kind_of(rel) == "donor":
            out[obj.get("name_key") or rel] = float((obj.get("totals") or {}).get("total") or 0)
    return out


def compare(version_dir: str, ctx=None) -> tuple:
    """The before-and-after arm (4.4): against the version built before this one, a donor page's total that fell
    is a red unless the build was told to allow a drop. The 2026-10-03 shape: $8,024,342 across 110 donors, every
    gate green because every gate read one artefact."""
    prev = (ctx or {}).get("previous")
    if not prev:
        return True, "no earlier version to compare against"
    o, n = donor_totals_of(prev), donor_totals_of(version_dir)
    if not o or not n:
        return False, f"comparison impossible: {len(o)} donor page(s) before, {len(n)} now; an empty side passes anything"
    fell = {k: (v, n.get(k, 0.0)) for k, v in o.items() if n.get(k, 0.0) < v - 0.005}
    gone = sorted(set(o) - set(n))
    rose = sum(1 for k, v in o.items() if n.get(k, 0.0) > v + 0.005)
    lost = sum(b - a for b, a in fell.values())
    line = f"{len(o):,} → {len(n):,} donor pages; {len(fell)} total(s) fell (${lost:,.2f}), {rose} rose, {len(gone)} page(s) gone"
    if fell and not (ctx or {}).get("allow_drop"):
        return False, line + " — a fall is refused unless the build is told --allow-drop for a recorded correction"
    return True, line + (" (--allow-drop)" if fell else "")


GATES = [("snapshot", snapshot), ("addresses", addresses), ("suppressed", suppressed), ("donor-fold", donor_fold),
         ("commission", commission), ("compare", compare)]


def run_all(version_dir: str, gates=None, ctx=None) -> list:  # noqa: F811 — the full list replaces the first definition
    out = []
    for name, fn in (gates or GATES):
        try:
            ok, line = fn(version_dir, ctx) if fn.__code__.co_argcount > 1 else fn(version_dir)
        except Exception as exc:  # noqa: BLE001 — a crashed gate is a red gate
            ok, line = False, f"the gate crashed: {type(exc).__name__}: {exc}"
        out.append((name, ok, line))
        if not ok:
            break
    return out
