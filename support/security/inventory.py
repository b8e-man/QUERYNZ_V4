"""The credential inventory's checker (track H.1).

`docs/security/inventory.md` names every secret: the file and variable
that hold it on each box, what reads it, its reach, its last rotation and
its wave. It never holds a value. Two things are checked, in the fast tier
(`support/security/tests/test_inventory.py`) and on the command line:

    python -m support.security.inventory          verdicts only

1. Every credential file a `qv4-` unit names, and every variable name the
   new estate's code reads out of a credential file, is in the inventory.
   The code is read statically: a module that names a credential file
   (a `*.env` or `*.key` literal, the credential directory, or
   `CRED_DIR`) contributes every whole-string literal shaped like a
   variable name. Settings that are not secrets ride along and the
   inventory says so; a name missing from it fails.
2. No line under `docs/security/` carries a value-shaped string
   (`support/security/shapes.py`).

Stdlib only; reads the repository, never the credential directory."""
import glob
import os
import re
import sys

from support.security import shapes

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INVENTORY = os.path.join(ROOT, "docs", "security", "inventory.md")
DOCS = os.path.join(ROOT, "docs", "security")
UNIT_DIR = os.environ.get("QV4_UNIT_DIR") or os.path.expanduser("~/.config/systemd/user")
SKIP_DIRS = {".git", ".venv", "node_modules", "reference", "__pycache__", "tests", "scratch", "var", "live"}

NAME = re.compile(r"^[A-Z][A-Z0-9_]{3,}$")
BACKTICK = re.compile(r"`([^`\n]+)`")
CRED_FILE = re.compile(r"[\"']([A-Za-z0-9_./-]*\.(?:env|key))[\"']")
MENTIONS_CREDS = re.compile(r"CRED_DIR|\.querynz|\.env[\"']|\.key[\"']|EnvironmentFile")
# A name is read from a credential file when it is a key into an env
# mapping (`env["X"]`, `self.env.get("X")`, `read_env(f)["X"]`), the value
# of a `*KEY*` constant (`KEY_NAME = "X"`, `OWNER_KEY, READ_KEY = "X", "Y"`),
# or a line prefix (`"X="`). `os.environ` is the process environment, not
# a file, and is left alone.
KEY_CONTEXTS = [
    re.compile(r"\benv(?!iron)(?:\.get)?\s*[\[\(]\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']"),
    re.compile(r"\)\s*\[\s*[\"']([A-Z][A-Z0-9_]{3,})[\"']\s*\]"),
    re.compile(r"[\"']([A-Z][A-Z0-9_]{3,})=[\"']"),
]
KEY_LINE = re.compile(r"^\s*[A-Z_]*KEY[A-Z_, ]*=\s*(.+)$", re.M)
WHOLE_LITERAL = re.compile(r"[\"']([A-Z][A-Z0-9_]{3,})[\"']")
ENV_FILE_LINE = re.compile(r"^EnvironmentFile=-?(\S+)", re.M)
NOT_CREDENTIAL_FILES = {"jobs.toml"}


def _py_files(root: str = ROOT):
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(dirpath, f)


def names_read_by_code(root: str = ROOT) -> dict:
    """{variable name: [files]} for every whole-string literal shaped like a
    variable name in a module that names a credential file, plus
    {credential file name: [files]} under the key '__files__'."""
    names, files = {}, {}
    for path in _py_files(root):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        if not MENTIONS_CREDS.search(text):
            continue
        rel = os.path.relpath(path, root)
        for m in CRED_FILE.finditer(text):
            base = os.path.basename(m.group(1))
            if base in NOT_CREDENTIAL_FILES or base.startswith("."):
                continue
            files.setdefault(base, []).append(rel)
        found = set()
        for pat in KEY_CONTEXTS:
            found |= set(pat.findall(text))
        for m in KEY_LINE.finditer(text):
            found |= set(WHOLE_LITERAL.findall(m.group(1)))
        for n in found:
            names.setdefault(n, []).append(rel)
    out = {k: sorted(set(v)) for k, v in names.items()}
    out["__files__"] = {k: sorted(set(v)) for k, v in files.items()}
    return out


def unit_files(root: str = ROOT, unit_dir: str = UNIT_DIR) -> list:
    """Every qv4- unit file: shipped in the repository and installed on this box."""
    out = []
    for dirpath, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        out += [os.path.join(dirpath, f) for f in fs if f.startswith("qv4-") and f.endswith((".service", ".timer", ".conf"))]
    if os.path.isdir(unit_dir):
        out += glob.glob(os.path.join(unit_dir, "qv4-*.service")) + glob.glob(os.path.join(unit_dir, "qv4-*.timer"))
        out += glob.glob(os.path.join(unit_dir, "qv4-*.d", "*.conf"))
    return sorted(set(out))


def env_files_named_by_units(root: str = ROOT, unit_dir: str = UNIT_DIR) -> dict:
    """{credential file basename: [unit files]} from EnvironmentFile= lines."""
    out = {}
    for path in unit_files(root, unit_dir):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue
        for m in ENV_FILE_LINE.finditer(text):
            out.setdefault(os.path.basename(m.group(1)), []).append(path)
    return out


def inventoried(path: str = INVENTORY) -> dict:
    """The names the inventory carries, from its backticked tokens:
    {'names': set, 'files': set}."""
    names, files = set(), set()
    with open(path, encoding="utf-8") as f:
        for tok in BACKTICK.findall(f.read()):
            tok = tok.strip()
            if NAME.match(tok):
                names.add(tok)
            elif re.fullmatch(r"[A-Za-z0-9_./~-]*\.(env|key|json)", tok):
                files.add(os.path.basename(tok))
    return {"names": names, "files": files}


def missing(root: str = ROOT, inventory: str = INVENTORY, unit_dir: str = UNIT_DIR) -> dict:
    """What the inventory lacks: {'names': {name: files}, 'files': {file: readers}}."""
    have = inventoried(inventory)
    code = names_read_by_code(root)
    code_files = code.pop("__files__")
    units = env_files_named_by_units(root, unit_dir)
    miss_names = {n: v for n, v in code.items() if n not in have["names"]}
    miss_files = {f: v for f, v in {**code_files, **units}.items() if f not in have["files"]}
    return {"names": miss_names, "files": miss_files}


def values_in_docs(docs: str = DOCS) -> list:
    """Every (file, line number, kind) where a value-shaped string sits under docs/security."""
    out = []
    for dirpath, _, fs in os.walk(docs):
        for name in sorted(fs):
            path = os.path.join(dirpath, name)
            try:
                with open(path, encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        for h in shapes.scan(line):
                            out.append((os.path.relpath(path, ROOT), i, h.kind))
            except (OSError, UnicodeDecodeError):
                continue
    return out


def main(argv=None) -> int:
    miss = missing()
    vals = values_in_docs()
    ok = True
    if miss["names"] or miss["files"]:
        ok = False
        for n, where in sorted(miss["names"].items()):
            print(f"not in the inventory: variable {n} (read by {', '.join(where)})")
        for n, where in sorted(miss["files"].items()):
            print(f"not in the inventory: file {n} (named by {', '.join(os.path.relpath(w, ROOT) if w.startswith(ROOT) else w for w in where)})")
    else:
        print("inventory covers every name the new estate reads: yes")
    if vals:
        ok = False
        for path, line, kind in vals:
            print(f"value-shaped string: {path}:{line} ({kind})")
    else:
        print("docs/security names no value: yes")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
