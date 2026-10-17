"""What the three launchers share (bin/start-session, bin/ask, bin/fix):
where things are, the scope file, the inbox, which folders a build session
holds, and whether a working copy is in use. Stdlib only."""
import os
import re
import subprocess
import sys

MAIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.environ.get("QV4_WORK") or "/home/user/querynzv4-work"
INBOX = os.path.join(WORK, "inbox")
INBOX_MERGE = os.path.join(INBOX, "merge-requests")
INBOX_CARDS = os.path.join(INBOX, "cards")
MODULE_ROOTS = ("keys", "support", "registers", "links", "products", "checks", "docs", "tests")
NAME = re.compile(r"^[a-z][a-z0-9-]{1,40}$")


def die(tool: str, msg: str) -> None:
    print(f"{tool}: {msg}", file=sys.stderr)
    sys.exit(1)


def git(*args, cwd=MAIN, check=True, tool="session") -> str:
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and p.returncode:
        die(tool, f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def scope_text(name: str, weight: str, scratch: str, folders) -> str:
    out = f"name: {name}\nweight: {weight}\nscratch: {scratch}\nfolders:\n"
    return out + "".join(f"  {f}\n" for f in folders)


def make_inbox() -> None:
    os.makedirs(INBOX_MERGE, exist_ok=True)
    os.makedirs(INBOX_CARDS, exist_ok=True)


def link_inbox(folder: str) -> None:
    make_inbox()
    link = os.path.join(folder, "merge-requests")
    if not os.path.lexists(link):
        os.symlink(INBOX_MERGE, link)


def read_scope(path: str) -> dict:
    """A scope file's name, weight and folders; {} when it cannot be read."""
    out = {"name": "", "weight": "", "folders": []}
    try:
        with open(path, encoding="utf-8") as f:
            block = False
            for ln in f.read().split("\n"):
                if block and ln.startswith("  "):
                    out["folders"].append(ln.strip().rstrip("/"))
                    continue
                block = False
                m = re.match(r"^(name|weight|scratch|folders):\s*(.*)$", ln)
                if m and m.group(1) == "folders":
                    block = True
                elif m:
                    out[m.group(1)] = m.group(2).strip()
    except OSError:
        return {}
    return out


def held_folders() -> dict:
    """folder → the build session's working copy that holds it: every scope
    file of weight build under the work folder (the integrator removes a
    copy after its last merge)."""
    out = {}
    try:
        names = sorted(os.listdir(WORK))
    except OSError:
        return out
    for n in names:
        sc = read_scope(os.path.join(WORK, n, ".scope"))
        if sc.get("weight") == "build":
            for f in sc["folders"]:
                out[f] = os.path.join(WORK, n)
    return out


def is_module_folder(folder: str) -> bool:
    """`keys`, `links`, or one folder under support/, registers/, products/
    or checks/ (bin/fix takes only these)."""
    f = folder.strip("/")
    parts = f.split("/")
    if f in ("keys", "links"):
        return os.path.isdir(os.path.join(MAIN, f))
    if len(parts) == 2 and parts[0] in ("support", "registers", "products", "checks"):
        return os.path.isdir(os.path.join(MAIN, f))
    return False


def in_use(folder: str) -> bool:
    """True when some process of ours has its working directory in `folder`
    (a session is sitting in it)."""
    folder = os.path.abspath(folder)
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return False
    for pid in pids:
        try:
            cwd = os.readlink(f"/proc/{pid}/cwd")
        except OSError:
            continue
        if cwd == folder or cwd.startswith(folder + os.sep):
            return True
    return False


def remove_copy(folder: str, tool: str) -> None:
    git("worktree", "remove", "--force", folder, check=False, tool=tool)
    git("worktree", "prune", check=False, tool=tool)
    if os.path.isdir(folder):
        import shutil
        shutil.rmtree(folder, ignore_errors=True)


def question_rules() -> str:
    """The rules for a question session, from the orientation file."""
    path = os.path.join(MAIN, "CLAUDE.md")
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return ""
    m = re.search(r"^## A question session\s*$(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else ""
