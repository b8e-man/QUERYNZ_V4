#!/usr/bin/env python3
"""PreToolUse scope hook: the fence around a session (plan: "Starting a
session", "Three additions to the fence").

It reads the scope file `.scope` in the working copy (CLAUDE_PROJECT_DIR)
and judges every write the tools would make:

  no scope file               → refuse every write, inside the repository or out
  weight question             → no edit inside the repository at all; outside,
                                only its scratch folder and inbox/cards/ (1b.1)
  inside the repository       → allowed under a folder the scope file names,
                                or under an always-allowed path (cards/,
                                lessons/, docs/status/, docs/decisions/queue/,
                                merge-requests/). Generated files are never
                                allowed, and .claude/, bin/, docs/plan/, the
                                orientation file and the scope file only for
                                a founding or integrator session, whatever the
                                scope file says
  outside the repository      → only under the session's scratch folder (the
                                one the scope file names, or this session's
                                own harness scratchpad), the inbox's
                                merge-requests/, and for a founding session
                                the stop list, the reference copy of the old
                                repository and the step 1.5 freeze paths in
                                the live old folder; for a founding or
                                integrator session a `qv4-` job file in the
                                user unit folder; an integrator may also
                                tidy the working copies under querynzv4-work

Edit/Write/MultiEdit/NotebookEdit are judged by file_path; Bash by the write
scan in fence.py. A scope file the hook cannot parse refuses everything but a
write to the scope file itself, so the fix path stays open. Exit 0 = allow,
exit 2 = refuse, stderr = why. Stdlib only. Test: tests/test_hook_scope.py."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fence  # noqa: E402

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def refuse(why: str) -> int:
    print(f"scope: {why}", file=sys.stderr)
    return 2


def harness_scratchpad(session_id: str, path: str) -> bool:
    """`/tmp/claude-<uid>/<slug>/<session_id>/…` — Claude Code's own
    per-session scratch directory."""
    if not session_id:
        return False
    parts = os.path.normpath(path).split(os.sep)
    return len(parts) > 4 and parts[1] == "tmp" and parts[2].startswith("claude-") and parts[4] == session_id


def judge(target: str, scope: dict, session_id: str) -> str:
    """'' when the write is allowed, else the reason it is not."""
    if target.startswith(fence.UNRESOLVABLE):
        return f"{target[1:]} — the hook cannot see which files this writes; name the files, or use a shape it can see"
    if "$" in target.replace("$HOME", "") or "`" in target:
        return f"target `{target}` carries an unexpanded variable; write a literal absolute path"
    path = os.path.abspath(os.path.expanduser(target.replace("$HOME", os.path.expanduser("~"))))
    r = fence.rel(path)
    weight = scope["weight"]
    main = weight in fence.MAIN_WEIGHTS
    if weight == "question":
        # a question session changes nothing (1b.1): no edit inside the repository,
        # the always-allowed paths included; outside, its scratch and a note in inbox/cards/
        if r is not None:
            return f"`{r}`: a question session changes nothing inside the repository; a fault goes as a note into {fence.CARDS_INBOX}"
        if (scope["scratch"] and fence.under(path, scope["scratch"])) or harness_scratchpad(session_id, path) \
                or fence.under(path, fence.CARDS_INBOX):
            return ""
        return f"`{path}`: a question session writes only its scratch folder and {fence.CARDS_INBOX}"
    if r is not None:
        if not main and fence.matches(r, fence.GENERATED):
            return f"`{r}` is generated at the merge and edited by nobody"
        if not main and fence.matches(r, fence.PROTECTED):
            return f"`{r}` may be edited only by a founding or integrator session"
        if fence.matches(r, scope["folders"]) or fence.matches(r, fence.ALWAYS):
            return ""
        return f"`{r}` is outside this session's scope ({scope['name']}: {', '.join(scope['folders'])}). Found outside scope → a card, never a fix"
    if scope["scratch"] and fence.under(path, scope["scratch"]):
        return ""
    if harness_scratchpad(session_id, path):
        return ""
    if fence.under(path, os.path.join(fence.INBOX, "merge-requests")):
        return ""
    if main and os.path.dirname(os.path.abspath(path)) == os.path.abspath(fence.UNIT_DIR):
        if os.path.basename(path).startswith("qv4-"):
            return ""
        return f"`{path}` is a job file without the qv4- prefix: the new estate never touches one (hard limit 23)"
    if weight == "founding":
        if fence.under(path, os.path.dirname(fence.STOP_LIST)):
            return ""
        if fence.under(path, fence.REF_COPY):
            return ""
        if fence.under(path, fence.OLD_LIVE):
            old_rel = fence.rel(path, fence.OLD_LIVE)
            if old_rel is not None and fence.matches(old_rel, fence.OLD_LIVE_FREEZE):
                return ""
            return f"`{path}` is in the live old folder and not one of the step 1.5 freeze paths"
    if weight == "integrator" and fence.under(path, fence.WORK):
        return ""
    if fence.under(path, fence.OLD_LIVE):
        return f"`{path}` is in the live old folder: the frozen product runs from it (hard limit 19)"
    return f"`{path}` is outside the repository and not under this session's scratch folder ({scope['scratch'] or 'none set'})"


def main() -> int:
    try:
        ev = json.load(sys.stdin)
    except Exception:
        return 0  # not our event shape; the safety hook judges parse failures
    tool = ev.get("tool_name", "")
    inp = ev.get("tool_input", {}) or {}
    cwd = ev.get("cwd") or fence.REPO
    targets: list = []
    if tool in EDIT_TOOLS:
        p = inp.get("file_path") or inp.get("notebook_path")
        if p:
            targets.append(p)
    elif tool == "Bash":
        targets = fence.bash_targets(inp.get("command", "") or "", cwd=cwd)
    else:
        return 0
    if not targets:
        return 0
    try:
        scope = fence.read_scope()
    except fence.ScopeError as e:
        if all(os.path.abspath(os.path.expanduser(t)) == fence.SCOPE_FILE for t in targets):
            return 0
        return refuse(f"the scope file {fence.SCOPE_FILE} cannot be used ({e}); a write to the scope file itself is allowed for the fix")
    if scope is None:
        return refuse(f"no scope file at {fence.SCOPE_FILE} — nothing may be written. Start the session with bin/start-session")
    for t in targets:
        why = judge(t, scope, ev.get("session_id", ""))
        if why:
            return refuse(why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
