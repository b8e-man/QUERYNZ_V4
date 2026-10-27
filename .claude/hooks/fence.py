#!/usr/bin/env python3
"""What the two hooks share: where things are, the scope file, and the scan
that finds every file a Bash command would write.

The scan is carried from the old estate's scope hook (`session_scope.py`,
ruling 254 and queue 4) and is a TRIPWIRE, not a floor: it refuses the write
shapes it can see, and a program read from a file it cannot see carries an
edit past it. What it sees:

  redirects `>` `>>` `&>` `>|`; `tee` files; `cp`/`mv`/`install`/`rsync`/`ln`
  destinations (a remote rsync `host:` is not a path); `dd of=`; `sed -i` /
  `perl -i` files; `rm` / `truncate` / `touch` args (a delete IS an edit);
  `patch FILE` (`-o OUT`); `git checkout -- P` / `restore P` / `mv A B` /
  `rm P`; the programs a command carries (`bash -c`, `sh -c`, `eval`, `ssh
  host '…'`, a heredoc fed to a shell or an interpreter, `python -c`,
  `perl -e`). A PYTHON BODY IS PARSED with `ast`: the paths that reach a write
  call are the targets, and a path it cannot resolve statically REFUSES.
  REFUSED OUTRIGHT: a target carrying an unexpanded `$VAR` or a backtick;
  `patch` with no file; `git stash pop/apply`, `git clean`, `git reset
  --hard`, `git apply`, `git am`, `git checkout .`.
  KNOWN LIMITS (not seen, by design): `bash script.sh` / `python script.py`;
  a path a non-python body builds at run time; `xargs` / `find -exec` /
  `find -delete` fan-out; `subprocess` inside a body; `COPY … TO 'file'`.

A relative target resolves against the directory the command is in: the
event's cwd, moved by each `cd` the command itself makes (applied only when
the destination exists on this box). Stdlib only: the hooks run with no venv.
"""
import os
import re
import shlex

REPO = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.abspath(REPO)
SCOPE_FILE = os.path.join(REPO, ".scope")
WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
INBOX = os.path.join(WORK, "inbox")
CARDS_INBOX = os.path.join(INBOX, "cards")               # notes from question sessions (1b.5)
MERGE_INBOX = os.path.join(INBOX, "merge-requests")
TIMES = os.path.join(WORK, "times", "session-times.jsonl")  # the timer (1b.9)
#: the only credential file a question session may name (1b.1): the session reader's
QUESTION_CRED_FILE = "v4-read.env"
STOP_LIST = os.environ.get("QV4_STOP_LIST") or os.path.join(WORK, "live", "stop-list.md")
# the live old folder: the frozen product runs from it (hard limits 19-22)
OLD_LIVE = os.environ.get("QV4_OLD_LIVE") or "/home/user/Git Repos/QueryNZ_V3"
# the reference copy of the old repository (step 1.2): a founding session makes
# it, installs its environment and moves it to the frozen tag; every session
# reads old code and runs old tests there, never in the live folder
REF_COPY = os.environ.get("QV4_REF_COPY") or "/home/user/qnz3-ref"
# the user unit folder: a founding or integrator session may place a job file
# there only under the `qv4-` prefix (hard limit 23); step 2's installer takes
# over once it exists
UNIT_DIR = os.environ.get("QV4_UNIT_DIR") or os.path.expanduser("~/.config/systemd/user")
# Claude Code keeps its notes per start folder under ~/.claude/projects/<slug>/memory,
# the slug being the folder's path with every non-alphanumeric character a dash; a
# founding or integrator session writes the one for the checkout it runs in (ruling 103)
MEMORY = os.environ.get("QV4_MEMORY") or os.path.join(
    os.path.expanduser("~/.claude/projects"), "".join(c if c.isalnum() else "-" for c in REPO), "memory")
# the only paths in the live old folder a founding session may write: the two
# freeze commits of step 1.5 and what the old pre-push gate asks for with them
OLD_LIVE_FREEZE = [
    "ingestion/newsscrapers/registry.py",
    "ingestion/SOURCES.md",          # its generated status section, which the old gate checks
    "ops/systemd/MANIFEST.json",
    "data-layer/docs/ledger/",
    "data-layer/docs/FLEET.md",
    "docs/INDEX.md",
]
# the carve-out (step 1.4): the jobs the public site stands on. The safety hook
# refuses to stop, disable or restart any of them whatever the stop list says.
CARVE_OUT = {
    "ec-disclosures", "querynz-gpu-gateway", "querynz-agent-llm", "querynz-vision-ocr",
    "querynz-pi-publisher", "ftm-release", "ftm-feedback-drain",
    # 18 October: the release's search gate (ops/pi_search_gate.py) reads the
    # product's own instance on :8300; stopped in batch 2, the release ran red
    "querynz-pi-web",
    "offsite-push", "wal-archive-mirror", "wal-archive-prune",
    "querynz-deploy-node1", "querynz-residue-mirror",
    "querynz-vip", "querynz-vip-bridge",
}
CARVE_OUT_PREFIXES = ("postgresql",)
WEIGHTS = ("founding", "integrator", "build", "fix", "question")
MAIN_WEIGHTS = ("founding", "integrator")
# always allowed inside the repository, whatever the scope says
ALWAYS = ["cards/", "lessons/", "docs/status/", "docs/decisions/queue/", "merge-requests/"]
# generated at the merge and edited by nobody but a main-checkout session
GENERATED = ["docs/board.md", "docs/parking.md", "lessons/INDEX.md", "docs/jobs.md",
             "docs/status.md", "docs/decisions/queue.md"]
# only a founding or integrator session may edit these, whatever its scope file says
PROTECTED = [".claude/", "bin/", "docs/plan/", "CLAUDE.md", ".scope"]
UNRESOLVABLE = "?"   # prefix of a pseudo-target: a write whose files the hook cannot see


class ScopeError(Exception):
    pass


def read_scope(path: str = SCOPE_FILE):
    """The scope file: `name:`, `weight:`, `scratch:` and a `folders:` block
    of repo-relative folders, one per indented line. None when there is no
    file; ScopeError when there is one the hook cannot use."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    out = {"name": "", "weight": "", "scratch": "", "folders": []}
    block = False
    for ln in lines:
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if block and ln.startswith("  "):
            out["folders"].append(ln.strip().rstrip("/") or ".")
            continue
        block = False
        m = re.match(r"^(name|weight|scratch|folders):\s*(.*)$", ln)
        if not m:
            raise ScopeError(f"line not understood: {ln!r}")
        key, val = m.group(1), m.group(2).strip()
        if key == "folders":
            block = True
            if val:
                out["folders"].extend(v.rstrip("/") or "." for v in val.split())
        else:
            out[key] = val
    if out["weight"] not in WEIGHTS:
        raise ScopeError(f"weight {out['weight']!r} is not one of {', '.join(WEIGHTS)}")
    if not out["name"] or not out["scratch"]:
        raise ScopeError("name: and scratch: are required")
    if out["weight"] in MAIN_WEIGHTS:
        out["folders"] = ["."]
    if out["weight"] in ("build", "fix") and not out["folders"]:
        raise ScopeError("a build or fix session needs a folders: block")
    return out


def under(path: str, root: str) -> bool:
    """True when `path` is `root` or inside it (both absolute, textual — a
    symlink such as merge-requests/ is judged by the name used)."""
    path = os.path.normpath(path)
    root = os.path.normpath(root)
    return path == root or path.startswith(root + os.sep)


def rel(path: str, root: str = REPO):
    """Root-relative path, or None when the path is outside the root."""
    p = os.path.abspath(os.path.join(root, os.path.expanduser(path)))
    r = os.path.abspath(root)
    if p == r or p.startswith(r + os.sep):
        return os.path.relpath(p, r)
    return None


def matches(relpath: str, globs) -> bool:
    for g in globs:
        g = g.rstrip("/")
        if g == ".":
            return True
        if relpath == g or relpath.startswith(g + "/"):
            return True
    return False


# ── the Bash write-target scan ───────────────────────────────────────────────
_HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n(.*?)^\s*\1\s*$", re.S | re.M)
_PATHY = (".py", ".md", ".sh", ".toml", ".json", ".sql", ".ts", ".txt", ".yml", ".yaml", ".html", ".css", ".env", ".ini", ".service", ".timer")
_WRAPPERS = {"sudo", "env", "nohup", "time", "exec", "nice", "ionice", "stdbuf", "setsid", "command", "builtin"}
_SHELLS = {"bash", "sh", "zsh", "dash"}
_INTERPRETERS = ("python", "perl", "ruby", "node")
_WRITE_HINT = re.compile(
    r"""open\([^)\n]*['"][wax]|['"]r\+['"]|\.write_(text|bytes)\(|\.write\(|\bwritelines\(|"""
    r"""os\.(remove|unlink|rename|replace|makedirs|mkdir|rmdir|truncate)\(|shutil\.(move|copy\w*|rmtree)\(|"""
    r"""\.(unlink|rename|replace|touch|mkdir|rmdir)\(\)|\.(rename|replace)\(|json\.dump\(|\.to_csv\(|\bsavefig\(|"""
    r"""\bunlink\b|open\s*\(\s*[^,)]*,\s*['"]>""")
_STR_LIT = re.compile(r"""'([^'\n]+)'|"([^"\n]+)\"""")
_CD_FLAGS = {"-P", "-L", "-e", "-@", "--"}


def strip_heredocs(cmd: str) -> str:
    return _HEREDOC.sub(lambda m: m.group(0).split("\n", 1)[0] + "\n", cmd)


def tokens(cmd: str) -> list:
    """Shell tokens with operators split out and quotes honoured; a plain
    split on unbalanced quotes."""
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return cmd.split()


def _is_op(t: str) -> bool:
    return bool(t) and all(ch in "();<>|&" for ch in t)


def _arg_end(toks, j) -> bool:
    if j >= len(toks) or _is_op(toks[j]):
        return True
    return toks[j].isdigit() and j + 1 < len(toks) and _is_op(toks[j + 1]) and ">" in toks[j + 1]


def _looks_like_path(a: str) -> bool:
    return bool(a) and not a.startswith("-") and ("/" in a or a.endswith(_PATHY)) and not re.search(r"[|\\]", a)


def head(toks: list) -> str:
    """The command word with wrappers, env assignments, `timeout N` and
    directories stripped."""
    i = 0
    while i < len(toks):
        t = toks[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", t) or t in _WRAPPERS:
            i += 1
            if t in ("sudo", "nice", "ionice", "stdbuf"):
                while i < len(toks) and toks[i].startswith("-"):
                    flag = toks[i]
                    i += 1
                    if re.match(r"^-[a-zA-Z]*[ugUhpnc]$", flag) and i < len(toks):
                        i += 1
            continue
        if t == "timeout":
            i += 2
            while i < len(toks) and toks[i].startswith("-"):
                i += 1
            continue
        return os.path.basename(t)
    return ""


def _positional(toks, j, takes_arg=(), stop_at_dd=False):
    args, seen_dd, skip = [], False, False
    while not _arg_end(toks, j):
        a = toks[j]
        if skip:
            skip = False
        elif a == "--" and not seen_dd:
            seen_dd = True
            if stop_at_dd:
                args = []
        elif not seen_dd and a in takes_arg:
            skip = True
        elif not seen_dd and a.startswith("-"):
            pass
        else:
            args.append(a)
        j += 1
    return args, j, seen_dd


def _plausible_repo_path(s: str, root: str) -> bool:
    if "://" in s or "{" in s or "%" in s or s.startswith(("s/", "y/")) or "\n" in s:
        return False
    if s.startswith(("/", "~")):
        return rel(s, root) is not None
    if re.match(r"^\.?\.?/?[\w.-]+/", s) or s.endswith(_PATHY):
        return os.path.isdir(os.path.join(root, os.path.dirname(s) or "."))
    return False


# ── python bodies: parsed, not scanned ───────────────────────────────────────
_PY_WRITE_FUNCS = {
    "remove": (0,), "unlink": (0,), "rename": (0, 1), "replace": (0, 1),
    "makedirs": (0,), "mkdir": (0,), "rmdir": (0,), "truncate": (0,),
    "move": (0, 1), "copy": (0, 1), "copy2": (0, 1), "copyfile": (0, 1),
    "copytree": (0, 1), "rmtree": (0,), "write_text": (), "write_bytes": (),
}
_PY_SURE_METHODS = {"write_text", "write_bytes", "touch", "mkdir", "rmdir", "unlink"}
_PY_MAYBE_METHODS = {"rename", "replace"}
_PY_BARE_OK = {"rmtree", "move", "copyfile", "copytree", "makedirs", "unlink", "remove"}
_PY_PATH_CTORS = {"Path", "PurePath", "PosixPath", "join", "expanduser", "abspath", "realpath"}
_PY_FS_MODULES = {"os", "shutil", "pathlib", "path"}


def _product(sets):
    out = [()]
    for s in sets:
        out = [c + (v,) for c in out for v in s]
    return out


def _py_const(node, env: dict):
    import ast
    if isinstance(node, ast.Constant):
        return {node.value} if isinstance(node.value, str) else None
    if isinstance(node, ast.Name):
        return env.get(node.id)
    if isinstance(node, ast.JoinedStr):
        acc = {""}
        for v in node.values:
            got = {v.value} if isinstance(v, ast.Constant) else _py_const(v, env)
            if got is None:
                return None
            acc = {a + str(b) for a in acc for b in got}
        return acc
    if isinstance(node, ast.FormattedValue):
        return _py_const(node.value, env)
    if isinstance(node, ast.BinOp):
        left, right = _py_const(node.left, env), _py_const(node.right, env)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return {a + b for a in left for b in right}
        if isinstance(node.op, ast.Div):
            return {os.path.join(a, b) for a in left for b in right}
        return None
    if isinstance(node, ast.Call):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name not in _PY_PATH_CTORS:
            return None
        acc = {""} if name == "join" else None
        vals = []
        for a in node.args:
            got = _py_const(a, env)
            if got is None:
                return None
            vals.append(got)
        if not vals:
            return None
        if name == "join":
            for v in vals:
                acc = {os.path.join(a, b) for a in acc for b in v}
            return acc
        return vals[0] if len(vals) == 1 else {os.path.join(*c) for c in _product(vals)}
    return None


def _py_module_call(fn) -> bool:
    import ast
    if not isinstance(fn, ast.Attribute):
        return False
    v = fn.value
    if isinstance(v, ast.Name):
        return v.id in _PY_FS_MODULES
    return isinstance(v, ast.Attribute) and v.attr in _PY_FS_MODULES


def _py_env(tree) -> dict:
    import ast
    env: dict = {}
    seqs: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, (ast.Tuple, ast.List, ast.Dict, ast.Set)):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    seqs[t.id] = node.value

    def bind(target, value_sets):
        if isinstance(target, ast.Name):
            prev = env.get(target.id)
            if target.id in env and prev is None:
                return
            env[target.id] = None if value_sets is None else (prev or set()) | value_sets
        elif isinstance(target, (ast.Tuple, ast.List)):
            for el in target.elts:
                bind(el, None)

    def container(node):
        if isinstance(node, ast.Name):
            return seqs.get(node.id)
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if nm in ("items", "keys", "values") and isinstance(fn, ast.Attribute):
                return container(fn.value)
            if nm in ("sorted", "list", "reversed", "tuple") and node.args:
                return container(node.args[0])
            return None
        return node if isinstance(node, (ast.Tuple, ast.List, ast.Dict, ast.Set)) else None

    def rows(node, iter_expr):
        wants_items = (isinstance(iter_expr, ast.Call) and isinstance(iter_expr.func, ast.Attribute)
                       and iter_expr.func.attr == "items")
        if isinstance(node, ast.Dict):
            if any(k is None for k in node.keys):
                return None
            return [[k, None] for k in node.keys] if wants_items else [[k] for k in node.keys]
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            return [list(el.elts) if isinstance(el, (ast.Tuple, ast.List)) else [el] for el in node.elts]
        return None

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            got = _py_const(node.value, env) if node.value is not None else None
            for t in targets:
                bind(t, got)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            cont = container(node.iter)
            got = rows(cont, node.iter) if cont is not None else None
            names = node.target.elts if isinstance(node.target, (ast.Tuple, ast.List)) else [node.target]
            if got is None:
                for nm in names:
                    bind(nm, None)
                continue
            cols: list = [set() for _ in names]
            for row in got:
                for k in range(len(names)):
                    sub = row[k] if k < len(row) else None
                    val = _py_const(sub, env) if sub is not None else None
                    if val is None:
                        cols[k] = None
                    elif cols[k] is not None:
                        cols[k] |= val
            for k, nm in enumerate(names):
                bind(nm, cols[k])
    return env


def _py_body_targets(body: str, root: str):
    import ast
    try:
        tree = ast.parse(body)
    except SyntaxError:
        return None, 0
    env = _py_env(tree)
    targets: set = set()
    unresolved = 0

    def take(node):
        nonlocal unresolved
        got = _py_const(node, env)
        if got is None:
            unresolved += 1
        else:
            targets.update(got)

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name == "open" and node.args:
            mode = None
            if len(node.args) > 1:
                mode = _py_const(node.args[1], env)
            for kw in node.keywords:
                if kw.arg == "mode":
                    mode = _py_const(kw.value, env)
            if mode is None and len(node.args) == 1 and not any(k.arg == "mode" for k in node.keywords):
                continue
            if mode is not None and not any(c in m for m in mode for c in "wax+"):
                continue
            take(node.args[0])
        elif _py_module_call(fn) and name in _PY_WRITE_FUNCS:
            for k in _PY_WRITE_FUNCS[name]:
                if len(node.args) > k:
                    take(node.args[k])
        elif isinstance(fn, ast.Attribute) and name in _PY_SURE_METHODS:
            take(fn.value)
            if name in ("rename", "replace") and node.args:
                take(node.args[0])
        elif isinstance(fn, ast.Attribute) and name in _PY_MAYBE_METHODS:
            got = _py_const(fn.value, env)
            if got and all(_plausible_repo_path(g, root) for g in got):
                targets.update(got)
                if node.args:
                    take(node.args[0])
        elif name in _PY_WRITE_FUNCS and (isinstance(fn, ast.Attribute) or name in _PY_BARE_OK):
            for k in _PY_WRITE_FUNCS[name]:
                if len(node.args) > k:
                    take(node.args[k])
    return sorted(targets), unresolved


def _read_context(body: str, m) -> bool:
    before = body[max(0, m.start() - 12):m.start()]
    after = body[m.end():m.end() + 24]
    if before.rstrip().endswith("open(") and re.match(r"\s*(\)|,\s*['\"]rb?['\"]\s*\)|,\s*encoding=)", after):
        return True
    return bool(re.match(r"\)\.(read|read_text|read_bytes|exists|is_file|is_dir|stat|glob|iterdir)\(", after))


def _body_targets(body: str, root: str) -> list:
    parsed, unresolved = _py_body_targets(body, root)
    if parsed is not None:
        return list(parsed) + [UNRESOLVABLE + "a python body writes to a path built at run time"] * min(unresolved, 1)
    if not _WRITE_HINT.search(body):
        return []
    out = []
    for m in _STR_LIT.finditer(body):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if _plausible_repo_path(s, root) and not _read_context(body, m):
            out.append(s)
    return out


def _resolve_against(t: str, cwd: str) -> str:
    if not t or t.startswith(UNRESOLVABLE) or t.startswith(("/", "~")):
        return t
    if "$" in t or "`" in t or re.match(r"^[^/]+:", t):
        return t
    return os.path.normpath(os.path.join(cwd, t))


def _cd_to(cwd: str, d: str) -> str:
    """Apply one `cd`, only when the destination exists on this box: a remote
    `ssh host 'cd … && …'` keeps being judged at our own path."""
    d = os.path.expanduser(d)
    nxt = d if os.path.isabs(d) else os.path.normpath(os.path.join(cwd, d))
    return nxt if os.path.isdir(nxt) else cwd


def cwd_after(prefix: str, start: str) -> str:
    """The directory in effect after every `cd` in `prefix`."""
    try:
        toks = tokens(strip_heredocs(prefix))
    except Exception:
        return start
    cwd = start
    for i, t in enumerate(toks):
        if t not in ("cd", "pushd"):
            continue
        j = i + 1
        while j < len(toks) and toks[j] in _CD_FLAGS:
            j += 1
        if j >= len(toks) or _is_op(toks[j]):
            continue
        d = toks[j]
        if "$" in d or "`" in d:
            continue
        cwd = _cd_to(cwd, d)
    return cwd


class _Targets(list):
    def __init__(self, cwd_ref):
        super().__init__()
        self._cwd = cwd_ref

    def append(self, t):
        super().append(_resolve_against(t, self._cwd[0]))

    def extend(self, items):
        for t in items:
            self.append(t)


def _heredoc_targets(cmd: str, depth: int, cwd0: str, root: str) -> list:
    out: list = []
    for m in _HEREDOC.finditer(cmd):
        opening = cmd[:m.start()].rsplit("\n", 1)[-1]
        hd = head(tokens(opening.rsplit("|", 1)[-1].rsplit(";", 1)[-1].rsplit("&&", 1)[-1]))
        cwd = cwd_after(cmd[:m.start()], start=cwd0)
        if hd in _SHELLS:
            out.extend(bash_targets(m.group(2), depth + 1, cwd=cwd, root=root))
        elif hd.startswith(_INTERPRETERS):
            out.extend(_resolve_against(t, cwd) for t in _body_targets(m.group(2), root))
    return out


def bash_targets(cmd: str, depth: int = 0, cwd: str = None, root: str = None) -> list:
    """Every file a Bash command would write, as far as the scan can see. A
    pseudo-target `?<what>` marks a write the hook cannot resolve."""
    root = root or REPO
    cwd = cwd or root
    if depth > 3:
        return []
    here = [cwd]
    out = _Targets(here)
    list.extend(out, _heredoc_targets(cmd, depth, cwd0=cwd, root=root))
    cmd = strip_heredocs(cmd)
    toks = tokens(cmd)
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in ("cd", "pushd"):
            j = i + 1
            while j < len(toks) and toks[j] in _CD_FLAGS:
                j += 1
            if j < len(toks) and not _is_op(toks[j]) and "$" not in toks[j] and "`" not in toks[j]:
                here[0] = _cd_to(here[0], toks[j])
        base = os.path.basename(t) if t and not _is_op(t) else t
        if _is_op(t) and ">" in t:
            if t not in (">&",) and i + 1 < len(toks) and not _is_op(toks[i + 1]) and not toks[i + 1].startswith(("=", "&")):
                out.append(toks[i + 1])
                i += 2
                continue
            i += 1
            continue
        if base == "tee":
            args, i, _ = _positional(toks, i + 1)
            out.extend(args)
            continue
        if base in ("cp", "mv", "ln"):
            args, i, _ = _positional(toks, i + 1, takes_arg=("-t", "--target-directory", "-S", "--suffix"))
            if len(args) >= 2:
                out.append(args[-1])
            continue
        if base == "install":
            start = i + 1
            args, i, _ = _positional(toks, start, takes_arg=("-m", "-o", "-g", "-t", "--target-directory", "-S", "--suffix", "--mode", "--owner", "--group"))
            flags = [x for x in toks[start:i] if x.startswith("-")]
            tdir = next((toks[k + 1] for k in range(start, i - 1) if toks[k] in ("-t", "--target-directory")), None)
            tdir = tdir or next((x.split("=", 1)[1] for x in flags if x.startswith("--target-directory=")), None)
            if tdir:
                out.append(tdir)
            elif any(re.match(r"^-[a-zA-Z]*d", x) or x == "--directory" for x in flags):
                out.extend(args)
            elif len(args) >= 2:
                out.append(args[-1])
            continue
        if base == "rsync":
            args, i, _ = _positional(toks, i + 1, takes_arg=("-e", "--rsh", "--exclude", "--include", "--exclude-from", "--files-from", "--log-file"))
            if len(args) >= 2 and not re.match(r"^[^/]+:", args[-1]):
                out.append(args[-1])
            continue
        if base == "dd":
            args, i, _ = _positional(toks, i + 1)
            out.extend(a[3:] for a in args if a.startswith("of="))
            continue
        if base in ("rm", "truncate", "touch"):
            args, i, _ = _positional(toks, i + 1, takes_arg=("-s", "--size", "-r", "--reference", "-d", "--date", "-t"))
            out.extend(args)
            continue
        if base == "patch":
            start = i + 1
            args, i, _ = _positional(toks, start, takes_arg=("-i", "--input", "-d", "--directory", "-o", "--output", "-p", "--strip", "-D", "--ifdef", "-r", "--reject-file", "-B", "--prefix", "-z", "--suffix", "-Y", "--basename-prefix", "-F", "--fuzz"))
            outs = [toks[k + 1] for k in range(start, i - 1) if toks[k] in ("-o", "--output")]
            out.extend(outs)
            if args:
                out.append(args[0])
            elif not outs:
                out.append(UNRESOLVABLE + "patch (the files are inside the diff)")
            continue
        if base == "sed":
            j = i + 1
            inplace = False
            skip = False
            files = []
            while not _arg_end(toks, j):
                a = toks[j]
                if skip:
                    skip = False
                elif a in ("-e", "--expression", "-f", "--file"):
                    skip = True
                elif a.startswith("-"):
                    if re.match(r"^-[a-zA-Z]*i", a) or a.startswith("--in-place"):
                        inplace = True
                elif re.match(r"^\d*[sy].", a) and not os.path.exists(a):
                    pass
                elif os.path.exists(a) or _looks_like_path(a):
                    files.append(a)
                j += 1
            if inplace:
                out.extend(files)
            i = j
            continue
        if base == "perl":
            start = i + 1
            takes = tuple(x for x in toks[start:] if re.match(r"^-[a-zA-Z.]*[eEIMmxC0]$", x))
            args, i, _ = _positional(toks, start, takes_arg=takes)
            flags = [x for x in toks[start:i] if x.startswith("-")]
            codes = [toks[k + 1] for k in range(start, i - 1) if re.match(r"^-[a-zA-Z.]*[eE]$", toks[k])]
            if any(re.match(r"^-[a-zA-Z]*i", f) for f in flags):
                out.extend(args)
            else:
                for c in codes:
                    out.extend(_body_targets(c, root))
            continue
        if base.startswith("python"):
            start = i + 1
            args, i, _ = _positional(toks, start, takes_arg=("-c", "-m", "-W", "-X"))
            codes = [toks[k + 1] for k in range(start, i - 1) if toks[k] == "-c"]
            for c in codes:
                out.extend(_body_targets(c, root))
            continue
        if base in _SHELLS or base == "eval":
            j = i + 1
            progs = []
            while not _arg_end(toks, j):
                a = toks[j]
                if base == "eval" or (j > i + 1 and toks[j - 1].startswith("-") and "c" in toks[j - 1]):
                    if not a.startswith("-"):
                        progs.append(a)
                j += 1
            for p in progs:
                if " " in p or ">" in p:
                    out.extend(bash_targets(p, depth + 1, cwd=here[0], root=root))
            i = j
            continue
        if base == "ssh":
            j = i + 1
            while not _arg_end(toks, j):
                a = toks[j]
                if not a.startswith("-") and (" " in a or ">" in a):
                    out.extend(bash_targets(a, depth + 1, cwd=here[0], root=root))
                j += 1
            i = j
            continue
        if base == "git":
            j = i + 1
            while not _arg_end(toks, j) and (toks[j].startswith("-")):
                if toks[j] in ("-C", "-c", "--git-dir", "--work-tree"):
                    j += 1
                j += 1
            sub = toks[j] if not _arg_end(toks, j) else ""
            if sub == "checkout":
                args, i, dd = _positional(toks, j + 1, takes_arg=("-b", "-B", "--orphan", "--conflict"), stop_at_dd=True)
                if dd:
                    out.extend(args)
                else:
                    out.extend(a for a in args if a == "." or _looks_like_path(a))
            elif sub == "restore":
                args, i, _ = _positional(toks, j + 1, takes_arg=("-s", "--source"))
                out.extend(args)
            elif sub in ("mv", "rm"):
                args, i, _ = _positional(toks, j + 1)
                out.extend(args)
            elif sub in ("stash", "clean", "apply", "am") or (sub == "reset" and "--hard" in toks[j:]):
                args, i, _ = _positional(toks, j + 1)
                if sub != "stash" or (args and args[0] in ("pop", "apply")):
                    out.append(UNRESOLVABLE + f"git {sub} (the files it writes are not named in the command)")
            else:
                i = j + 1
            continue
        i += 1
    keep = ("/dev/null", "/dev/stderr", "/dev/stdout")
    return [x for x in (y.strip("'\"") for y in out) if x and x not in keep and not x.startswith("&")]
