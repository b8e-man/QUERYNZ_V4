#!/usr/bin/env python3
"""PreToolUse safety hook: a TRIPWIRE on the irreversible shapes. It refuses
the spellings it can see whatever permission mode the session is in; a
program read from a file it cannot see can carry the same action past it,
which is why the real floor is the box (hard limit 3: no bypass mode).

Carried from the old estate's `denylist.py` (its audits of 2026-09-04 and
2026-09-14 are the shapes below):

  1. recursive delete              rm with -r/-R/--recursive in any spelling;
                                   `find … -delete`; inside xargs / find -exec
  2. DROP / TRUNCATE on a database  via psql -c, -f, `\\i FILE`, `< FILE`,
                                   `cat FILE | psql`, a heredoc, python; the
                                   file is read, and refused when it cannot be
  3. force or deleting push         --force / -f / --force-with-lease / +ref /
                                   --mirror / --delete / :ref / --prune
  4. credential reads               content of ~/.querynz/* in every spelling;
                                   /proc/*/environ; Grep/Glob over the dir.
                                   The sanctioned shape is VAR=$(grep ^KEY=
                                   file | cut …), never printed

Added for the new estate (plan step 1.1):

  5. `pi_release.py` without `--dry-run`: without the flag it publishes to
     the public site
  6. `pi_cloudflare.py`, `wrangler`, or any other deploy tool
  7. stopping, disabling or restarting a job without the `qv4-` prefix,
     unless the job is on the stop list of step 1.4
     (/home/user/querynzv4-work/live/stop-list.md), and NEVER a job in the
     carve-out, whatever the list says
  8. any write under the live old folder, except a founding session writing
     the step 1.5 freeze paths; any mutating git command there except by a
     founding session; any python or pytest run from inside it, except
     `pi_release.py --dry-run` by a founding session
  9. for a question session (step 1b.1): any commit, push, merge, installer
     run or job control, any edit inside the repository, and any credential
     file but the session reader's

Seen through: sudo, doas, env, nohup, nice, ionice, chrt, setsid, stdbuf,
timeout, time, systemd-run, xargs, eval; an absolute-path binary; a program
handed to `bash -c` / `sh -c` / `ssh` / `eval`, judged as if typed here.

KNOWN LIMITS (named, not silent): a program or list in a FILE; a DSN read from
the environment by a program that then DROPs; a unit's environment printed
back; encoded spellings; a wrapper not in the list above.

FAILS CLOSED: anything it cannot parse is refused (exit 2). Stdlib only.
Exit 0 = allow, exit 2 = refuse, stderr = why. Test: tests/test_hook_safety.py."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fence  # noqa: E402

CRED_DIR = re.compile(
    r"(~|\$HOME|\$\{HOME\}|/home/[^/\s'\"]+)/(\.querynz|\.[^/\s'\"]*[*?\[][^/\s'\"]*)(/|\b)"
    r"|(?<![\w.-])\.querynz/")
PROC_ENV = re.compile(r"/proc/(\d+|self|\*|\$\([^)]*\)|\$[^/\s]*|[^/\s]*[*?][^/\s]*)/environ\b")
READ_ONLY_ON_CREDS = {"ls", "stat", "wc", "file", "test", "[", "find", "du", "chmod", "chown"}
FIND_ACTS = {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls", "-fprint0"}
SQL_DDL = re.compile(
    r"\b(drop\s+(table|schema|database|index|view|materialized\s+view|sequence|role|type|extension)"
    r"\s+(if\s+exists\s+)?[\w\".]+"
    r"|truncate\s+(table\s+)?(only\s+)?[\w\".]+(\s*,\s*[\w\".]+)*\s*"
    r"((restart|continue)\s+identity|cascade|restrict|;|\)|\"|'|$))",
    re.I | re.M)
SQL_EXEC = re.compile(r"(^|[\s/;|&(])(psql|python3?|\.venv/bin/\S+|alembic|pg_restore|sqlite3)\b")
PSQL_INCLUDE = re.compile(r"\\(?:i|ir|include|include_relative)\s+(\S+)")
CAT_TO_PSQL = re.compile(r"\bcat\s+([^\s|;&]+)\s*\|\s*(?:sudo\s+(?:-\S+\s+)*)?(?:[\w./-]*/)?psql\b")
CREDS_TO_EXEC = re.compile(r"\.querynz[^|\n]*\|\s*(?:sudo\s+)?(xargs|parallel|while\b|bash|sh|zsh|python3?|perl)\b")
DEPLOY_TOOLS = {"pi_cloudflare.py", "wrangler"}
JOB_CONTROL = {"stop", "disable", "restart", "reload-or-restart", "try-restart", "try-reload-or-restart",
               "mask", "kill", "reset-failed"}
GIT_MUTATING = {"add", "commit", "tag", "push", "checkout", "switch", "restore", "reset", "stash", "rm", "mv",
                "merge", "rebase", "pull", "cherry-pick", "revert", "am", "apply", "clean", "worktree", "branch"}


def sql_view(text: str) -> str:
    t = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    t = re.sub(r"(?<![\w-])--[^\n]*", " ", t)
    return re.sub(r"[ \t]+", " ", t)


def block(why: str) -> None:
    sys.stderr.write(f"safety: {why}\n")
    sys.exit(2)


_SHELLS = {"bash", "sh", "zsh", "dash"}
_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'', re.S)


def split_segments(cmd: str) -> list:
    """Split on ; | && || and newlines OUTSIDE quotes."""
    out, cur, q, i = [], [], None, 0
    while i < len(cmd):
        c = cmd[i]
        if q:
            cur.append(c)
            if c == "\\" and q == '"' and i + 1 < len(cmd):
                cur.append(cmd[i + 1]); i += 1
            elif c == q:
                q = None
        elif c in ("'", '"'):
            q = c; cur.append(c)
        elif c == "\n" or c == ";" or c == "|" or (c == "&" and cmd[i:i + 2] == "&&"):
            out.append("".join(cur)); cur = []
            if cmd[i:i + 2] in ("&&", "||"):
                i += 1
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


def inner_programs(seg: str, toks: list) -> list:
    carrier = False
    raw = seg.strip().split()
    for k, t in enumerate(raw):
        b = os.path.basename(t)
        if b in ("ssh", "eval"):
            carrier = True
            break
        if b in _SHELLS and any(x.startswith("-") and not x.startswith("--") and "c" in x for x in raw[k + 1:k + 4]):
            carrier = True
            break
    if not carrier:
        return []
    progs = []
    for m in _QUOTED.finditer(seg):
        inner = m.group(1) if m.group(1) is not None else m.group(2)
        if m.group(1) is not None:
            inner = re.sub(r'\\(["\\$`])', r"\1", inner)
        if inner.strip():
            progs.append(inner)
    return progs


_WRAP_ARGS = {"sudo": "ugUhpCDrtT", "doas": "u", "env": "uCS", "nice": "n", "ionice": "cnp", "chrt": "",
              "setsid": "", "stdbuf": "ioe", "nohup": "", "time": "", "exec": "", "eval": "", "command": "",
              "builtin": "", "unbuffer": "", "xargs": "nIPLsdaE", "systemd-run": "pEutGH"}
_LONG_WITH_ARG = {"--unit", "--property", "--setenv", "--on-active", "--on-calendar", "--on-boot", "--description",
                  "--working-directory", "--uid", "--gid", "--nice", "--service-type", "--slice", "--timer-property",
                  "--max-args", "--max-procs", "--replace", "--delimiter", "--arg-file", "--chdir"}


def tokens(seg: str) -> list:
    """Tokens with wrappers, env assignments and `timeout N` stripped so
    toks[0] is the command word. Quotes are honoured, so a path with a space
    in it (the live old folder has one) stays one token."""
    try:
        toks = __import__("shlex").split(seg.strip())
    except ValueError:
        toks = seg.strip().split()
    while toks:
        hd = os.path.basename(toks[0])
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            toks.pop(0)
            continue
        if hd == "timeout":
            toks.pop(0)
            while toks and toks[0].startswith("-"):
                flag = toks.pop(0)
                if flag in ("-k", "-s", "--kill-after", "--signal") and toks:
                    toks.pop(0)
            if toks:
                toks.pop(0)
            continue
        if hd in _WRAP_ARGS:
            toks.pop(0)
            argflags = _WRAP_ARGS[hd]
            while toks and toks[0].startswith("-") and toks[0] != "--":
                flag = toks.pop(0)
                if flag.startswith("--"):
                    if flag in _LONG_WITH_ARG and toks:
                        toks.pop(0)
                elif argflags and re.match(rf"^-[a-zA-Z]*[{argflags}]$", flag) and toks:
                    toks.pop(0)
            if toks and toks[0] == "--":
                toks.pop(0)
            if hd in ("chrt", "ionice") and toks and toks[0].isdigit():
                toks.pop(0)
            continue
        break
    return toks


def _base(t: str) -> str:
    return os.path.basename(t) if t else t


# ── the carried refusals ─────────────────────────────────────────────────────
def check_pg_cli(seg: str, toks: list) -> None:
    if toks and _base(toks[0]) in ("dropdb", "dropuser"):
        block(f"{_base(toks[0])} against a live cluster: {seg.strip()!r}")


def check_rm(seg: str, toks: list) -> None:
    for i, t in enumerate(toks):
        if _base(t) == "rm":
            flags = "".join(f.lstrip("-") for f in toks[i + 1:] if f.startswith("-") and not f.startswith("--"))
            longs = {f for f in toks[i + 1:] if f.startswith("--")}
            if "r" in flags or "R" in flags or "--recursive" in longs:
                block(f"recursive delete: {seg.strip()!r}")
        if _base(t) == "find" and "-delete" in toks[i + 1:]:
            block(f"find -delete (a recursive delete): {seg.strip()!r}")


def _read_sql_file(path: str, cwd: str) -> None:
    if "$" in path or "`" in path:
        block(f"psql reading a file the hook cannot name: {path}")
    path = os.path.expanduser(path.strip("'\""))
    if not os.path.isabs(path):
        path = os.path.join(cwd, path)
    try:
        body = open(path).read()
    except OSError:
        block(f"psql on a file the hook cannot read: {path}")
    if SQL_DDL.search(sql_view(body)):
        block(f"DROP/TRUNCATE inside {path}")


def check_sql(seg: str, toks: list, cwd: str) -> None:
    if any(_base(t) == "psql" for t in toks):
        for i, t in enumerate(toks):
            if t in ("-f", "--file") and i + 1 < len(toks):
                _read_sql_file(toks[i + 1], cwd)
            elif t.startswith("--file="):
                _read_sql_file(t.split("=", 1)[1], cwd)
        noq = _QUOTED.sub(lambda m: (m.group(1) if m.group(1) is not None else m.group(2))
                          if not re.search(r"[\s<>|;&]", m.group(1) if m.group(1) is not None else m.group(2)) else "Q", seg)
        for m in re.finditer(r"(?<!<)<(?!<)\s*([^\s<>|;&()]+)", noq):
            _read_sql_file(m.group(1), cwd)
    if SQL_DDL.search(sql_view(seg)) and SQL_EXEC.search(seg):
        block(f"DROP/TRUNCATE against a live database: {seg.strip()!r}")


def check_push(seg: str, toks: list) -> None:
    if len(toks) >= 2 and _base(toks[0]) == "git" and "push" in toks:
        rest = toks[toks.index("push") + 1:]
        if any(t in ("-f", "--force", "--force-with-lease", "--force-if-includes", "--mirror", "--delete", "-d", "--prune") or
               (t.startswith("-") and not t.startswith("--") and ("f" in t or "d" in t)) or
               t.startswith(("+", ":")) or t.startswith("--force")
               for t in rest):
            block(f"force / deleting push: {seg.strip()!r}")


def check_creds(seg: str, toks: list, whole: str) -> None:
    if PROC_ENV.search(seg):
        block(f"a process environment carries credentials: {seg.strip()!r}")
    if not CRED_DIR.search(seg):
        return
    hd = _base(toks[0]) if toks else ""
    if hd in READ_ONLY_ON_CREDS and not (hd == "find" and FIND_ACTS & set(toks)):
        return
    for m in re.finditer(r"[A-Za-z_][A-Za-z0-9_]*=\$\((.*?)\)(?=\s|$|;)", whole, re.S):
        if CRED_DIR.search(m.group(1)) and m.group(1).strip().startswith(("grep", "awk", "sed", "cut", "cat")):
            if not re.search(r"\b(cat|less|more)\b", m.group(1)) or "|" in m.group(1):
                inner = m.group(1)
                seg_clean = CRED_DIR.sub("", seg)
                if CRED_DIR.search(inner) and not CRED_DIR.search(seg_clean):
                    return
    block(f"credential read outside VAR=$(...): {seg.strip()!r}")


def expand_assignments(cmd: str) -> str:
    for m in re.finditer(r"(?:^|[\s;&|(])(?:export\s+)?([A-Za-z_]\w*)=(\S+)", cmd):
        name, val = m.group(1), m.group(2).strip("'\"")
        if CRED_DIR.search(val):
            cmd = re.sub(rf"\$\{{{name}\}}|\${name}\b", val, cmd)
    return cmd


# ── the new estate's refusals ────────────────────────────────────────────────
def stop_list() -> set:
    """The jobs step 1.4 intends to stop: one unit name per line in the stop
    list, `#` lines ignored, `.service`/`.timer` stripped."""
    try:
        with open(fence.STOP_LIST, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return set()
    out = set()
    for ln in lines:
        ln = ln.strip().lstrip("-*").strip()
        if ln and not ln.startswith("#"):
            out.add(unit_name(ln.split()[0]))
    return out


def unit_name(u: str) -> str:
    u = u.strip("'\"")
    for suf in (".service", ".timer", ".socket", ".target", ".path"):
        if u.endswith(suf):
            u = u[: -len(suf)]
    return u


def in_carve_out(name: str) -> bool:
    base = name.split("@", 1)[0]
    return base in fence.CARVE_OUT or name.startswith(fence.CARVE_OUT_PREFIXES)


def _program(toks: list) -> str:
    """The program a segment runs: the command word, or the script an
    interpreter is handed. The word in prose (a grep pattern, a commit
    message) is not the program."""
    if not toks:
        return ""
    hd = _base(toks[0])
    if hd.startswith(("python", "pytest")) or "/.venv/bin/" in toks[0] or toks[0].startswith(".venv/bin/"):
        for t in toks[1:]:
            if not t.startswith("-"):
                return _base(t)
        return hd
    return hd


def check_release_and_deploy(seg: str, toks: list) -> None:
    prog = _program(toks)
    if prog in DEPLOY_TOOLS:
        block(f"deploy tool: nothing in the new estate publishes to the public site ({seg.strip()!r})")
    if prog == "pi_release.py" and "--dry-run" not in toks:
        block(f"pi_release.py without --dry-run publishes to the public site: {seg.strip()!r}")


def check_job_control(seg: str, toks: list) -> None:
    if not toks or _base(toks[0]) != "systemctl":
        return
    sub = next((t for t in toks[1:] if not t.startswith("-")), "")
    if sub not in JOB_CONTROL:
        return
    units = [t for t in toks[toks.index(sub) + 1:] if not t.startswith("-")]
    allowed = stop_list()
    for u in units:
        name = unit_name(u)
        if name.startswith("qv4-"):
            continue
        if in_carve_out(name):
            block(f"`{name}` is in the carve-out the public site stands on; it is never stopped, disabled or restarted ({seg.strip()!r})")
        if name in allowed:
            continue
        block(f"`{name}` has no qv4- prefix and is not on the stop list {fence.STOP_LIST} ({seg.strip()!r})")


QUESTION_GIT = {"add", "commit", "tag", "push", "merge", "rebase", "pull", "cherry-pick", "revert", "am", "apply",
                "worktree", "reset", "stash", "rm", "mv", "clean"}
QUESTION_JOB = {"start", "stop", "restart", "enable", "disable", "mask", "unmask", "kill", "reload", "reload-or-restart",
                "try-restart", "reset-failed", "daemon-reload"}
INSTALLERS = ("install-jobs", "installer", "support.installer")
CRED_FILE_NAME = re.compile(r"\.querynz/([A-Za-z0-9_.*?\[\]-]+)")


def check_question(seg: str, toks: list, weight: str) -> None:
    """A question session (1b.1) may not commit, push, merge, run the
    installer, control a job, or name a credential file other than the
    session reader's."""
    if weight != "question" or not toks:
        return
    hd = _base(toks[0])
    if hd == "git":
        sub = next((t for t in toks[1:] if not t.startswith("-")), "")
        if sub in QUESTION_GIT:
            block(f"a question session changes nothing: git {sub} ({seg.strip()!r})")
    if hd == "systemctl":
        sub = next((t for t in toks[1:] if not t.startswith("-")), "")
        if sub in QUESTION_JOB:
            block(f"a question session controls no job: systemctl {sub} ({seg.strip()!r})")
    if _program(toks) in INSTALLERS or any(_base(t) in INSTALLERS for t in toks):
        block(f"a question session never runs the installer ({seg.strip()!r})")
    if CRED_DIR.search(seg):
        for m in CRED_FILE_NAME.finditer(seg):
            if m.group(1) != fence.QUESTION_CRED_FILE:
                block(f"a question session may name only {fence.QUESTION_CRED_FILE} ({seg.strip()!r})")


def check_old_live(seg: str, toks: list, cwd: str, weight: str) -> None:
    """Mutating git in the live old folder, and any python run from it."""
    if not toks:
        return
    hd = _base(toks[0])
    here = cwd
    if hd == "git":
        for i, t in enumerate(toks):
            if t == "-C" and i + 1 < len(toks):
                here = os.path.expanduser(toks[i + 1].strip("'\""))
        sub = next((t for t in toks[1:] if not t.startswith("-") and t != here and not t.startswith(("/", "~"))), "")
        if sub in GIT_MUTATING and fence.under(here, fence.OLD_LIVE) and weight != "founding":
            block(f"git {sub} in the live old folder is a change to the frozen product (hard limit 19): {seg.strip()!r}")
        return
    runs_python = hd.startswith(("python", "pytest")) or "/.venv/bin/" in toks[0] or toks[0].startswith(".venv/bin/")
    if not runs_python:
        return
    args = [os.path.expanduser(t.strip("'\"")) for t in toks[1:] if not t.startswith("-")]
    script_in_old = any(fence.under(a if os.path.isabs(a) else os.path.join(here, a), fence.OLD_LIVE)
                        for a in args if a and ("/" in a or a.endswith(".py")))
    if fence.under(here, fence.OLD_LIVE) or script_in_old or fence.under(os.path.expanduser(toks[0]), fence.OLD_LIVE):
        if weight == "founding" and any(_base(t) == "pi_release.py" for t in toks) and "--dry-run" in toks:
            return
        block(f"a program run from the live old folder can write into its var/ or its live tables; use the reference copy ({seg.strip()!r})")


def check_old_live_writes(cmd: str, cwd: str, weight: str) -> None:
    for t in fence.bash_targets(cmd, cwd=cwd):
        if t.startswith(fence.UNRESOLVABLE) or "$" in t or "`" in t:
            continue
        p = os.path.abspath(os.path.expanduser(t))
        if fence.under(p, fence.OLD_LIVE):
            r = fence.rel(p, fence.OLD_LIVE)
            if weight == "founding" and r is not None and fence.matches(r, fence.OLD_LIVE_FREEZE):
                continue
            block(f"a write under the live old folder: {p} (hard limit 19; only the step 1.5 freeze paths, by a founding session)")


def weight_of_session() -> str:
    try:
        scope = fence.read_scope()
    except fence.ScopeError:
        return ""
    return scope["weight"] if scope else ""


def judge(cmd: str, cwd: str, weight: str, depth: int = 0) -> None:
    for seg in split_segments(cmd):
        toks = tokens(seg)
        if not toks:
            continue
        inner = inner_programs(seg, toks) if depth < 3 else []
        seg_cwd = fence.cwd_after(cmd.split(seg, 1)[0], cwd) if seg in cmd else cwd
        check_pg_cli(seg, toks)
        check_rm(seg, toks)
        check_sql(seg, toks, cwd)
        check_push(seg, toks)
        check_release_and_deploy(seg, toks)
        check_job_control(seg, toks)
        check_question(seg, toks, weight)
        check_old_live(seg, toks, seg_cwd, weight)
        if inner:
            for prog in inner:
                judge(prog, cwd, weight, depth + 1)
        else:
            check_creds(seg, toks, cmd)


def main() -> None:
    try:
        ev = json.load(sys.stdin)
        name = ev["tool_name"]
        inp = ev["tool_input"]
        if not isinstance(inp, dict):
            raise ValueError("tool_input not an object")
    except Exception as e:  # noqa: BLE001 — closed by design
        block(f"unparseable event ({e.__class__.__name__}: {e})")
    cwd = ev.get("cwd") or os.getcwd()
    if name in ("Read", "Edit", "Write", "MultiEdit", "NotebookEdit", "Grep", "Glob"):
        path = str(inp.get("file_path") or inp.get("notebook_path") or inp.get("path") or "")
        pat = str(inp.get("pattern") or "") if name == "Glob" else ""
        for p in (path, pat):
            if p and (CRED_DIR.search(p) or PROC_ENV.search(p) or "/.querynz/" in os.path.realpath(os.path.expanduser(p)) + "/"):
                block(f"credential file: {p}")
        if path and name in ("Edit", "Write", "MultiEdit", "NotebookEdit") and weight_of_session() == "question":
            if fence.rel(os.path.abspath(os.path.expanduser(path))) is not None:
                block(f"a question session changes nothing inside the repository: {path}")
        if name in ("Edit", "Write", "MultiEdit", "NotebookEdit") and path:
            p = os.path.abspath(os.path.expanduser(path))
            if fence.under(p, fence.OLD_LIVE):
                r = fence.rel(p, fence.OLD_LIVE)
                if not (weight_of_session() == "founding" and r is not None and fence.matches(r, fence.OLD_LIVE_FREEZE)):
                    block(f"a write under the live old folder: {p} (hard limit 19)")
        sys.exit(0)
    if name != "Bash":
        sys.exit(0)
    cmd = inp.get("command")
    if not isinstance(cmd, str):
        block("Bash event without a command string")
    cmd = expand_assignments(cmd)
    view = sql_view(cmd)
    if SQL_DDL.search(view) and SQL_EXEC.search(cmd):
        block(f"DROP/TRUNCATE reaches a database executor: {cmd.strip()!r}")
    if SQL_DDL.search(view) and any((tokens(s) or [""])[0].startswith("$") for s in split_segments(cmd)):
        block(f"DROP/TRUNCATE handed to an executor the hook cannot see ($VAR): {cmd.strip()!r}")
    if re.search(r"\bpsql\b", cmd):
        for m in PSQL_INCLUDE.finditer(cmd):
            _read_sql_file(m.group(1), cwd)
        for m in CAT_TO_PSQL.finditer(cmd):
            _read_sql_file(m.group(1), cwd)
    if CREDS_TO_EXEC.search(cmd):
        block(f"credential paths piped into an executor: {cmd.strip()!r}")
    weight = weight_of_session()
    check_old_live_writes(cmd, cwd, weight)
    judge(cmd, cwd, weight)
    sys.exit(0)


if __name__ == "__main__":
    main()
