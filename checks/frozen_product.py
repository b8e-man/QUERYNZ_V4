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

5. **The carve-out's units** (plan 1.4: "`v3-audit`, once the watcher of 1.6
   covers the carve-out"). Every job the safety hook refuses to stop is asked
   of systemd on this box. Red when one of the units the release itself
   needs on the primary (MUST_RUN) is not running, or when a unit that has
   been seen running on this box since the watcher began is not running now.
   A unit never seen running here (node1's, while node1 is down) is reported
   and not alarmed. What has been seen is remembered in the state folder.

The old board's item reads the stop list of 1.4: once `v3-audit` is listed
there, its silence is on purpose and is not red.

The check returns a result the board renders and alarms on; it writes only
inside its state folder. Stdlib only. Tests: checks/tests/test_frozen_product.py."""
import datetime as dt
import hashlib
import json
import os
import subprocess

OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
LIVE = os.environ.get("QV4_LIVE") or "/home/user/querynzv4-work/live"
STATE_DIR = os.path.join(LIVE, "checks", "frozen-product")
WINDOW_HOURS = 26
NAME = "frozen-product"

#: The carve-out of plan 1.4, the names the safety hook refuses to stop. The
#: test pins this list to CARVE_OUT in .claude/hooks/fence.py so the two
#: cannot drift; checks may not import the hooks.
CARVE_OUT = ["ec-disclosures", "querynz-gpu-gateway", "querynz-agent-llm", "querynz-vision-ocr",
             "querynz-pi-publisher", "querynz-pi-web", "ftm-release", "ftm-feedback-drain",
             "offsite-push", "wal-archive-mirror", "wal-archive-prune",
             "querynz-deploy-node1", "querynz-residue-mirror", "querynz-vip", "querynz-vip-bridge"]
#: The database is a system unit (the hook's prefix "postgresql").
SYSTEM_UNITS = ["postgresql.service"]
#: What the daily release needs on the primary: red the moment one is not running.
MUST_RUN = {"querynz-pi-publisher.service", "querynz-pi-web.service", "querynz-gpu-gateway.service",
            "querynz-agent-llm.service", "querynz-vision-ocr.service", "postgresql.service",
            "ec-disclosures.timer", "ftm-release.timer", "ftm-feedback-drain.timer"}
SHOW_PROPS = "Id,LoadState,ActiveState,SubState,UnitFileState,NextElapseUSecRealtime"


def stop_list(live: str) -> set:
    """The jobs 1.4 intends to stop, as the safety hook reads them: one per
    line, `#` lines ignored, the unit suffix stripped."""
    out = set()
    try:
        with open(os.path.join(live, "stop-list.md"), encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                for suf in (".service", ".timer"):
                    if s.endswith(suf):
                        s = s[: -len(suf)]
                out.add(s)
    except OSError:
        pass
    return out


def parse_show(text: str) -> dict:
    """`systemctl show -p …` output, one blank-line-separated block per unit,
    into {Id: {property: value}}."""
    units = {}
    for block in text.split("\n\n"):
        props = {}
        for line in block.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
        if props.get("Id"):
            units[props["Id"]] = props
    return units


def carve_out_names() -> tuple:
    """(user units, system units) to ask about: each carve-out job as a
    service and a timer; the ones that do not exist come back `not-found`."""
    user = [f"{n}{suf}" for n in CARVE_OUT for suf in (".service", ".timer")]
    return user, list(SYSTEM_UNITS)


def live_states() -> dict:
    """Every carve-out unit's state from systemd on this box."""
    user, system = carve_out_names()
    states = {}
    for argv in (["systemctl", "--user", "show", "-p", SHOW_PROPS, *user],
                 ["systemctl", "show", "-p", SHOW_PROPS, *system]):
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            states[f"?{argv[1]}"] = {"Id": f"?{argv[1]}", "LoadState": "error", "ActiveState": str(exc)}
            continue
        states.update(parse_show(r.stdout))
    return states


def is_running(props: dict) -> bool:
    return props.get("LoadState") == "loaded" and props.get("ActiveState") == "active"


def carve_out_item(states: dict, state_dir: str) -> dict:
    """One board item for the carve-out. Remembers which units have ever been
    seen running on this box (`carve-out-seen.json`), so a unit that stops is
    red until it runs again, and one that was never here is only reported."""
    seen_path = os.path.join(state_dir, "carve-out-seen.json")
    try:
        with open(seen_path, encoding="utf-8") as f:
            seen = set(json.load(f))
    except (OSError, ValueError):
        seen = set()
    running, down_must, down_seen, absent, never = [], [], [], [], []
    for uid, props in sorted(states.items()):
        if uid.startswith("?") or props.get("LoadState") == "error":
            down_must.append(f"{uid[1:]}: systemctl could not be asked ({props.get('ActiveState')})")
            continue
        if props.get("LoadState") == "not-found":
            if uid in MUST_RUN:
                down_must.append(f"{uid} is not installed here")
            else:
                absent.append(uid)
            continue
        if is_running(props):
            running.append(uid)
            seen.add(uid)
        elif uid in MUST_RUN:
            down_must.append(f"{uid} {props.get('ActiveState')}/{props.get('SubState')}")
        elif uid in seen:
            down_seen.append(f"{uid} {props.get('ActiveState')}/{props.get('SubState')}")
        elif uid.endswith(".service") and states.get(uid[:-8] + ".timer", {}).get("LoadState") == "loaded":
            pass   # a one-shot service between runs of its timer
        else:
            never.append(uid)
    os.makedirs(state_dir, exist_ok=True)
    tmp = seen_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f)
    os.replace(tmp, seen_path)
    ok = not down_must and not down_seen
    must_up = sum(1 for u in running if u in MUST_RUN)
    parts = [f"{must_up} of {len(MUST_RUN)} must-run units running, {len(running)} carve-out units in all"]
    if down_must:
        parts.append("the release needs: " + "; ".join(down_must))
    if down_seen:
        parts.append("stopped since last seen running: " + "; ".join(down_seen))
    if never:
        parts.append("not running on this box (never seen running here): " + ", ".join(never))
    # a job is absent only when neither its service nor its timer exists here
    jobs_absent = sorted({u.rsplit(".", 1)[0] for u in absent}
                         - {u.rsplit(".", 1)[0] for u, p in states.items() if p.get("LoadState") == "loaded"})
    if jobs_absent:
        parts.append("not installed here: " + ", ".join(jobs_absent))
    return {"name": "carve-out", "ok": ok, "detail": "; ".join(parts)}


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


def check(now: dt.datetime = None, old_live: str = None, state_dir: str = None, hasher=sha256_file,
          states: dict = None, live: str = None) -> dict:
    """`states` is the carve-out's unit states ({Id: properties}); left out,
    systemd on this box is asked. `live` is the folder holding the stop list."""
    now = now or dt.datetime.now().astimezone()
    old_live = old_live or OLD_LIVE
    state_dir = state_dir or STATE_DIR
    live = live or LIVE
    os.makedirs(state_dir, exist_ok=True)
    items, alarms = [], []
    stopped_on_purpose = stop_list(live)

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
        if "v3-audit" in stopped_on_purpose:
            items.append({"name": "old-board", "ok": True,
                          "detail": f"v3-audit is on the 1.4 stop list; its last run was {age:.0f} h ago: "
                                    f"{board['failed']} of {board['checks']} red ({reds})"})
        elif age > WINDOW_HOURS:
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

    items.append(carve_out_item(states if states is not None else live_states(), state_dir))

    return {"check": NAME, "ok": all(i["ok"] for i in items), "items": items, "alarms": alarms}
