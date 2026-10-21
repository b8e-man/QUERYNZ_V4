"""The two trust settings, read from settings.toml beside this file: how far
a chain of links is trusted, and what a path through more than one person
is graded. Defaults until Arthur rules; the runner records what was in force
in every run (`in_force`), so a list can always say which rule graded it."""
from __future__ import annotations

import os
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(HERE, "settings.toml")
CHOICES = {"chains": ("follow", "direct"), "through_people": ("near", "confirmed")}
DEFAULTS = {"chains": "follow", "through_people": "near"}
STATUSES = ("default in force", "ruled")


def load(path: str = FILE) -> dict:
    with open(path, "rb") as f:
        t = tomllib.load(f)
    out = {}
    for name, choices in CHOICES.items():
        s = t.get(name) or {}
        value, status, ruling = s.get("value"), s.get("status"), str(s.get("ruling") or "")
        if value not in choices:
            raise ValueError(f"settings.toml: {name} is one of {choices}, not {value!r}")
        if status not in STATUSES:
            raise ValueError(f"settings.toml: {name}: status is one of {STATUSES}, not {status!r}")
        if status == "ruled" and not ruling:
            raise ValueError(f"settings.toml: {name} is marked ruled without the ruling's number")
        if status != "ruled" and value != DEFAULTS[name]:
            raise ValueError(f"settings.toml: {name} is {value!r} without a ruling; the default is {DEFAULTS[name]!r}")
        out[name] = {"value": value, "status": status, "ruling": ruling, "default": DEFAULTS[name]}
    return out


def in_force(path: str = FILE) -> dict:
    """{setting: value} as recorded in a run, with the status beside."""
    return {k: {"value": v["value"], "status": v["status"] + (f" ({v['ruling']})" if v["ruling"] else "")} for k, v in load(path).items()}
