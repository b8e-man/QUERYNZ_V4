"""The shape's own reading of its template file (imports run one way: a
shape reaches only support, so it reads `products/templates/ftm/ftm.json`
as data and never imports the templates package; that package's own tests
hold the file to the template contract).

    load(path=PATH) -> SimpleNamespace   name, version, owner, shape, reads (each .table/.licence/.attribution/.refresh),
                                         sections, rules, known_limits, settings
    races(settings) / race_of(year, settings)
"""
import json
import os
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(os.path.dirname(HERE), "templates", "ftm", "ftm.json")
KINDS = ("home", "parties", "electorates", "pickers", "subject", "electorate", "donor", "board-member", "size-bands", "cite")
NEEDED = ("window_from", "named_from", "races", "line", "headline_parties")


def load(path: str = PATH) -> SimpleNamespace:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    t = SimpleNamespace(name=d["name"], version=int(d.get("version", 0)), owner=d.get("owner", ""), shape=d.get("shape", ""),
                        use_case=int(d.get("use_case", 0)), sections=tuple(d.get("sections", [])), rules=tuple(d.get("rules", [])),
                        known_limits=d.get("known_limits", ""), reads=tuple(SimpleNamespace(**r) for r in d.get("reads", [])),
                        settings=dict(d.get("settings", {})))
    if t.shape != "published-site" or not t.reads or t.version < 1 or not t.known_limits.strip():
        raise ValueError(f"{path}: not a published-site template with reads, a version and a known-limits page")
    if any(not r.table.startswith("pub.") for r in t.reads):
        raise ValueError(f"{path}: a template reads only pub.* views")
    if t.sections != KINDS:
        raise ValueError(f"{path}: the sections are the ten kinds of published file, in order: {KINDS}")
    for key in NEEDED:
        if key not in t.settings:
            raise ValueError(f"{path}: the settings lack {key}")
    return t


def races(s: dict) -> dict:
    out = {}
    for race, years in s["races"].items():
        out[int(race)] = [int(y) for y in years if int(y) >= int(s["window_from"])]
    return out


def race_of(year: int, s: dict):
    for race, years in races(s).items():
        if int(year) in years:
            return race
    return None
