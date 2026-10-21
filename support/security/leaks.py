"""The leak finder (track H.2): where secret-shaped values sit, as places.

    python -m support.security.leaks --git /home/user/qnz3-ref \\
        --path ~/.claude/projects --path ~/.bash_history --journal --journal-user \\
        --report docs/security/leaks-run.md

It reads a repository's whole history (every added line of every commit on
every branch, and every commit message), files and folders line by line,
and the system journal, and runs every shape in `shapes.py` over each
line. What it prints is a place (file and line, commit and path, journal
time and unit), the kind of secret, and a liveness verdict. Never a value:
`--show-context` adds a short window around each hit with every
secret-shaped span redacted, and nothing else leaves the process.

Liveness, verdicts only. `--live NAME,NAME` takes the current value of
each named variable from the process environment, keeps a hash of its
comparison key (a DSN's password, an alarm address's topic, a token
itself), forgets the variable, and marks each hit "matches the current
NAME" or "differs from every current value given". The standing shape
puts a value there without showing it:

    CF_API_TOKEN=$(grep '^CF_API_TOKEN=' <the credential file> | cut -d= -f2-) \\
        python -m support.security.leaks --live CF_API_TOKEN ...

It never opens the credential directory itself and skips it when walking.
Stdlib only. Tests: support/security/tests/test_leaks.py (on a generated
fixture, never a committed value)."""
import argparse
import hashlib
import os
import re
import subprocess
import sys

from support.security import shapes

CRED_DIR_NAME = "." + "querynz"   # never walked; spelt so no line here names it
COMMIT = re.compile(r"^commit [0-9a-f]{40} \d{4}-\d{2}-\d{2}$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
JOURNAL_LINE = re.compile(r"^(\S+) (\S+) ([^:\[ ]+)(?:\[\d+\])?:")
WINDOW = 48
SCANNED = {}   # source label -> lines read, so an empty result is told from an unread source


class Finding:
    __slots__ = ("kind", "name", "place", "source", "digest", "context")

    def __init__(self, kind, name, place, source, digest, context):
        self.kind, self.name, self.place, self.source, self.digest, self.context = kind, name, place, source, digest, context


def digest(kind: str, value: str) -> str:
    return hashlib.sha256(shapes.compare_key(kind, value).encode("utf-8", "replace")).hexdigest()


def hits_on(line: str, place: str, source: str, context: bool):
    SCANNED[source] = SCANNED.get(source, 0) + 1
    for h in shapes.scan(line):
        ctx = ""
        if context:
            lo, hi = max(0, h.start - WINDOW), min(len(line), h.end + WINDOW)
            ctx = shapes.redact(line[lo:hi]).replace("\t", " ").strip()
        yield Finding(h.kind, h.name, place, source, digest(h.kind, h.value), ctx)


# ── sources ──────────────────────────────────────────────────────────────────
def _lines(stream):
    for raw in stream:
        yield raw.decode("utf-8", "replace").rstrip("\r\n")


def git_source(repo: str, label: str = None, rev_range: str = None, context: bool = False):
    """Every added line of every commit on every branch, and every commit
    message. Place: `<label> <commit> <date> <path>:<line>`."""
    label = label or os.path.basename(repo.rstrip("/"))
    cmd = ["git", "-C", repo, "log", "-p", "--no-color", "--no-renames", "--format=commit %H %cs%n%B"]
    cmd += [rev_range] if rev_range else ["--all"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    sha = date = path = None
    lineno = 0
    in_message = False
    for line in _lines(proc.stdout):
        if COMMIT.match(line):
            _, sha, date = line.split()
            path, in_message = None, True
            continue
        if line.startswith("diff --git "):
            in_message, path = False, None
            continue
        if line.startswith("+++ "):
            path = None if line == "+++ /dev/null" else line[6:]
            continue
        if line.startswith("--- ") or line.startswith("index ") or line.startswith("Binary files"):
            continue
        m = HUNK.match(line)
        if m:
            lineno = int(m.group(1)) - 1
            continue
        if in_message:
            yield from hits_on(line, f"{label} {sha[:12]} {date} (commit message)", label, context)
            continue
        if path is None:
            continue
        if line.startswith("+"):
            lineno += 1
            yield from hits_on(line[1:], f"{label} {sha[:12]} {date} {path}:{lineno}", label, context)
        elif line.startswith(" "):
            lineno += 1
    proc.wait()


def _is_binary(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            return b"\0" in f.read(8192)
    except OSError:
        return True


def file_source(path: str, label: str = None, context: bool = False):
    """Every line of one file. Place: `<path>:<line>`."""
    label = label or path
    try:
        with open(path, "rb") as f:
            for i, line in enumerate(_lines(f), 1):
                yield from hits_on(line, f"{path}:{i}", label, context)
    except OSError:
        return


def dir_source(root: str, label: str = None, excludes=(), context: bool = False):
    """Every text file under a folder, the credential directory skipped."""
    label = label or root
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != CRED_DIR_NAME and d != ".git")
        for name in sorted(files):
            p = os.path.join(dirpath, name)
            if any(x in p for x in excludes) or os.path.islink(p) or not os.path.isfile(p) or _is_binary(p):
                continue
            yield from file_source(p, label, context)


def journal_source(user: bool = False, context: bool = False):
    """The system (or user) journal. Place: `journal <time> <unit or program>`."""
    cmd = ["journalctl", "--no-pager", "-q", "--all", "-o", "short-iso"] + (["--user"] if user else [])
    label = "journal(user)" if user else "journal(system)"
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return
    for line in _lines(proc.stdout):
        m = JOURNAL_LINE.match(line)
        place = f"{label} {m.group(1)} {m.group(3)}" if m else f"{label} (unparsed line)"
        yield from hits_on(line, place, label, context)
    proc.wait()


# ── liveness ─────────────────────────────────────────────────────────────────
def take_live(names) -> dict:
    """{digest: NAME} for each named variable in the environment, which is
    then forgotten so no child process inherits it."""
    out = {}
    for n in names:
        v = os.environ.pop(n, None)
        if v:
            out[hashlib.sha256(shapes.live_key(n, v).encode("utf-8", "replace")).hexdigest()] = n
    return out


def verdict(f: Finding, live: dict) -> str:
    if not live:
        return "not compared"
    if f.digest in live:
        return f"matches the current {live[f.digest]}"
    return "differs from every current value given"


# ── the run ──────────────────────────────────────────────────────────────────
def run(sources, live: dict, out=sys.stdout, report: str = None, context: bool = False) -> list:
    seen, findings = set(), []
    by_kind, by_source = {}, {}
    for src in sources:
        for f in src:
            key = (f.kind, f.place)
            if key in seen:
                continue
            seen.add(key)
            v = verdict(f, live)
            findings.append((f, v))
            by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
            by_source[f.source] = by_source.get(f.source, 0) + 1
            line = f"{f.kind}\t{f.name or '-'}\t{f.place}\t{v}"
            if context and f.context:
                line += f"\t{f.context}"
            print(line, file=out)
            out.flush()
    print(f"findings: {len(findings)}", file=out)
    for k, n in sorted(by_kind.items()):
        print(f"  kind {k}: {n}", file=out)
    for s, n in sorted(by_source.items()):
        print(f"  source {s}: {n}", file=out)
    for s, n in sorted(SCANNED.items()):
        print(f"  scanned {s}: {n} lines", file=out)
    if report:
        with open(report, "w", encoding="utf-8") as fh:
            fh.write("| kind | variable | place | liveness |\n| --- | --- | --- | --- |\n")
            for f, v in findings:
                fh.write(f"| {f.kind} | {f.name or '-'} | `{f.place}` | {v} |\n")
    return findings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="where secret-shaped values sit; places only")
    ap.add_argument("--git", action="append", default=[], metavar="REPO[=RANGE]", help="a repository's history; RANGE narrows it (e.g. a..b)")
    ap.add_argument("--path", action="append", default=[], help="a file or folder")
    ap.add_argument("--journal", action="store_true", help="the system journal")
    ap.add_argument("--journal-user", action="store_true", help="the user journal")
    ap.add_argument("--exclude", action="append", default=[], help="skip paths containing this")
    ap.add_argument("--live", default="", help="NAME,NAME: current values from the environment, compared by hash, verdicts only")
    ap.add_argument("--show-context", action="store_true", help="a short redacted window around each hit")
    ap.add_argument("--report", help="write a markdown table of the places here")
    a = ap.parse_args(argv)
    live = take_live([n for n in a.live.split(",") if n])
    sources = []
    for g in a.git:
        repo, _, rng = g.partition("=")
        sources.append(git_source(os.path.expanduser(repo), rev_range=rng or None, context=a.show_context))
    for p in a.path:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            sources.append(dir_source(p, excludes=a.exclude, context=a.show_context))
        else:
            sources.append(file_source(p, context=a.show_context))
    if a.journal:
        sources.append(journal_source(False, a.show_context))
    if a.journal_user:
        sources.append(journal_source(True, a.show_context))
    if not sources:
        ap.error("name at least one source")
    findings = run(sources, live, report=a.report, context=a.show_context)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
