"""The project settings register both hooks for every tool that can touch a
file or run a command, back the hook with native deny rules, allow no
bypass, and grant nothing that reaches outside the local network or stops an
old job (plan step 1.1: the list of allowed commands)."""
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS = os.path.join(REPO, ".claude", "settings.json")


def _settings():
    with open(SETTINGS) as f:
        return json.load(f)


def test_both_hooks_registered():
    hooks = _settings()["hooks"]["PreToolUse"]
    for script, tools in (("safety.py", ("Bash", "Read", "Grep", "Glob", "Edit", "Write", "MultiEdit", "NotebookEdit")),
                          ("scope.py", ("Bash", "Edit", "Write", "MultiEdit", "NotebookEdit"))):
        matchers = [h["matcher"] for h in hooks if any(script in c.get("command", "") for c in h["hooks"])]
        assert matchers, f"{script} not registered"
        for tool in tools:
            assert any(re.fullmatch(m, tool) for m in matchers), f"{script} does not cover {tool}"


def test_native_deny_rules_back_the_hook():
    deny = set(_settings()["permissions"]["deny"])
    for rule in ("Read(~/.querynz/**)", "Bash(rm -rf *)", "Bash(git push --force *)", "Bash(git push -f *)"):
        assert rule in deny, rule


def test_no_bypass_and_nothing_irreversible_or_remote_is_allowed():
    s = _settings()
    assert s.get("permissions", {}).get("defaultMode") != "bypassPermissions"
    allow = s["permissions"]["allow"]
    bad = [a for a in allow if re.search(r"\b(rm|sudo|scp|rsync|nohup|kill|pkill|ssh|curl|wget|bash -c)\b", a)]
    assert not bad, bad
    assert not any(a.startswith("Bash(git push") and "origin" not in a for a in allow), "a push must name origin"


def test_job_control_is_allowed_only_for_qv4_jobs():
    for a in _settings()["permissions"]["allow"]:
        m = re.fullmatch(r"Bash\(systemctl (?:--user )?(start|stop|restart|enable|disable|mask|kill) (.*)\)", a)
        if m:
            assert m.group(2).startswith("qv4-"), a


def test_remote_and_fetch_commands_ask():
    ask = set(_settings()["permissions"]["ask"])
    for rule in ("Bash(ssh *)", "Bash(curl *)", "Bash(wget *)", "Bash(sudo *)"):
        assert rule in ask, rule


def test_the_timer_is_registered_on_prompt_and_stop():
    hooks = _settings()["hooks"]
    for ev in ("UserPromptSubmit", "Stop"):
        assert any("timer.py" in h.get("command", "") for g in hooks.get(ev, []) for h in g["hooks"]), ev
