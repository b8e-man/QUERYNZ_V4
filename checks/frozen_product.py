"""The first check on the board: the frozen product is watched (plan 1.6).

Four things, each read from the live old folder and nothing else:

1. **The release ran and was green.** `ops/pi_release.py` appends a
   `publish` row to `var/pi-snapshot/RELEASES.jsonl` only after every gate
   passed, the deploy and the flip succeeded and the public URL served the
   new version. So "green" is a `publish` row inside the window, and the
   `current` link pointing at that version. A window of 26 hours, not "after
   06:15 today": an outage, a hand re-run and a restart all break a window
   tuned to a timer (old lesson, 4-capture-sources.md:660).
2. **The old checks board ran.** `var/audits/board_state.json` carries
   `ran_at`. Its reds are reported, not alarmed: after step 1.4 the stopped
   jobs make it red on purpose.
3. **The site's mail.** `data-layer/docs/ledger/feedback.json` is what
   `ftm-feedback-drain` collects. A key not seen before raises an alarm
   saying *that* something arrived (when, which page) and never what it
   said; the key is then remembered in the state folder so it alarms once.
4. **A listing of the captured documents at each release.** The first time
   a published version is seen, every file under `var/staging/` is listed
   with its path, size, modification time and sha256 into
   `<state>/listings/<version>.jsonl`; a cache keyed on (path, size, mtime)
   means an unchanged file is never hashed twice. Step 4.5 builds from these.

The check returns a result the board renders and alarms on; it writes only
inside its state folder. Stdlib only. Tests: checks/tests/test_frozen_product.py."""
import datetime as dt
import hashlib
import json
import os

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
STATE_DIR = os.path.join(LIVE, "checks", "frozen-product")
WINDOW_HOURS = 26
NAME = "frozen-product"


def parse_when(s: str, tz=None) -> dt.datetime:
    """An ISO time; a naive one is the box's local time (the old release log
    mixes both)."""
    t = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    if t.tzinfo is None:
        t = t.replace(tzinfo=tz) if tz else t.astimezone()
    return t


def latest_publish(old_live: str, tz=None):
    path = os.path.join(old_live, "var", "pi-snapshot", "RELEASES.jsonl")
    best = None
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("action") == "publish" and row.get("at") and row.get("version"):
                    best = {"at": parse_when(row["at"], tz), "version": row["version"]}
    except OSError:
        return None
    return best


def current_version(old_live: str):
    link = os.path.join(old_live, "var", "pi-snapshot", "current")
    try:
        return os.path.basename(os.path.realpath(link)) if os.path.exists(link) else None
    except OSError:
        return None


def hours_ago(now: dt.datetime, then: dt.datetime) -> float:
    return (now - then).total_seconds() / 3600


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_listing(old_live: str, version: str, state_dir: str, hasher=sha256_file) -> dict:
    """List every file under var/staging by path, size, mtime and hash into
    listings/<version>.jsonl, atomically. Returns a summary."""
    staging = os.path.join(old_live, "var", "staging")
    cache_path = os.path.join(state_dir, "hash-cache.json")
    try:
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    files, total, hashed = 0, 0, 0
    rows = []
    for dirpath, dirs, names in os.walk(staging):
        dirs.sort()
        for name in sorted(names):
            full = os.path.join(dirpath, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            st = os.stat(full)
            rel = os.path.relpath(full, staging)
            key = [st.st_size, st.st_mtime_ns]
            hit = cache.get(rel)
            if hit and hit[:2] == key:
                digest = hit[2]
            else:
                digest = hasher(full)
                hashed += 1
            cache[rel] = [st.st_size, st.st_mtime_ns, digest]
            rows.append({"path": rel, "bytes": st.st_size, "mtime": dt.datetime.fromtimestamp(
                st.st_mtime).astimezone().isoformat(timespec="seconds"), "sha256": digest})
            files += 1
            total += st.st_size
    os.makedirs(os.path.join(state_dir, "listings"), exist_ok=True)
    out = os.path.join(state_dir, "listings", f"{version}.jsonl")
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps({"version": version, "listed_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                            "root": staging, "files": files, "bytes": total}) + "\n")
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, out)
    tmp = cache_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    os.replace(tmp, cache_path)
    return {"files": files, "bytes": total, "hashed": hashed, "path": out}


def reader_mail(old_live: str, state_dir: str):
    """(new entries, total) in the site's feedback file; remembers what it
    has seen. Each new entry is (when, page) only."""
    path = os.path.join(old_live, "data-layer", "docs", "ledger", "feedback.json")
    seen_path = os.path.join(state_dir, "feedback-seen.json")
    try:
        with open(path, encoding="utf-8") as f:
            entries = json.load(f)
    except OSError:
        return None, 0
    except ValueError:
        return [("unreadable", "feedback.json could not be parsed")], 0
    if isinstance(entries, dict):
        entries = list(entries.values())
    try:
        with open(seen_path, encoding="utf-8") as f:
            seen = set(json.load(f))
    except (OSError, ValueError):
        seen = set()
    new = []
    keys = set()
    for e in entries:
        if not isinstance(e, dict):
            continue
        key = str(e.get("key") or f"{e.get('at')}|{e.get('page')}")
        keys.add(key)
        if key not in seen:
            new.append((str(e.get("at", "?")), str(e.get("page", "?"))[:80]))
    os.makedirs(state_dir, exist_ok=True)
    tmp = seen_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sorted(seen | keys), f)
    os.replace(tmp, seen_path)
    return new, len(entries)


def old_board(old_live: str, tz=None):
    path = os.path.join(old_live, "var", "audits", "board_state.json")
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        return {"ran_at": parse_when(d["ran_at"], tz), "failed": d.get("failed"), "checks": d.get("checks"),
                "red": d.get("red", [])}
    except (OSError, ValueError, KeyError, TypeError):
        return None


def check(now: dt.datetime = None, old_live: str = None, state_dir: str = None, hasher=sha256_file) -> dict:
    now = now or dt.datetime.now().astimezone()
    old_live = old_live or OLD_LIVE
    state_dir = state_dir or STATE_DIR
    os.makedirs(state_dir, exist_ok=True)
    items, alarms = [], []

    pub = latest_publish(old_live, now.tzinfo)
    cur = current_version(old_live)
    if pub is None:
        items.append({"name": "release", "ok": False, "detail": "no publish row in RELEASES.jsonl, or the file is missing"})
    else:
        age = hours_ago(now, pub["at"])
        if age > WINDOW_HOURS:
            items.append({"name": "release", "ok": False,
                          "detail": f"last green release {pub['version']} was {age:.0f} h ago (window {WINDOW_HOURS} h)"})
        elif cur != pub["version"]:
            items.append({"name": "release", "ok": False,
                          "detail": f"last publish is {pub['version']} but current points at {cur}"})
        else:
            items.append({"name": "release", "ok": True,
                          "detail": f"{pub['version']} published {age:.1f} h ago and is current"})

    board = old_board(old_live, now.tzinfo)
    if board is None:
        items.append({"name": "old-board", "ok": False, "detail": "board_state.json missing or unreadable"})
    else:
        age = hours_ago(now, board["ran_at"])
        reds = ", ".join(board["red"]) if board["red"] else "none"
        if age > WINDOW_HOURS:
            items.append({"name": "old-board", "ok": False, "detail": f"v3-audit last ran {age:.0f} h ago (window {WINDOW_HOURS} h)"})
        else:
            items.append({"name": "old-board", "ok": True,
                          "detail": f"v3-audit ran {age:.1f} h ago: {board['failed']} of {board['checks']} red ({reds})"})

    new, total = reader_mail(old_live, state_dir)
    if new is None:
        items.append({"name": "reader-mail", "ok": True, "detail": "no feedback file"})
    else:
        items.append({"name": "reader-mail", "ok": True, "detail": f"{total} entries, {len(new)} new"})
        for when, page in new:
            alarms.append(("reader mail on the site form",
                           f"a message arrived at {when} on page {page}; a suppression request has a 24-hour clock, "
                           "a correction five working days. Read it in the old folder's ledger."))

    if pub is not None and cur:
        listing = os.path.join(state_dir, "listings", f"{cur}.jsonl")
        if os.path.exists(listing):
            items.append({"name": "listing", "ok": True, "detail": f"{cur} already listed"})
        else:
            try:
                s = write_listing(old_live, cur, state_dir, hasher)
                items.append({"name": "listing", "ok": True,
                              "detail": f"{cur}: {s['files']} files, {s['bytes']:,} bytes, {s['hashed']} newly hashed"})
            except OSError as exc:
                items.append({"name": "listing", "ok": False, "detail": f"listing failed: {exc}"})

    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": alarms}
