"""The Follow the Money template (plan 4.4): use case 1 on the published-site
shape. The template is data, `ftm.json` beside this file, held to the
template contract (`products/templates`): the published views it reads,
its ten sections (the ten kinds of published file), its rules, its
known-limits page, its owner and version.

Its settings are the frozen site's, as design.md fixes them ("The Follow
the Money template's own settings"): the window from 1 January 2017
(ruling 364; the brief's 2019 of ruling 347 was superseded and the frozen
site stands at 2017), the three races and the named-donor start of the
2020 race (rulings 361, 363, 366), the seven front-page parties by their
registration keys, the $15,000 line for the second figure.

    load() -> Template          validated; raises ValueError on a defect
    settings() -> dict          the template's settings alone
"""
import os

import products.templates as tp

HERE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(HERE, "ftm.json")
KINDS = ("home", "parties", "electorates", "pickers", "subject", "electorate", "donor", "board-member", "size-bands", "cite")


def load(path: str = PATH) -> tp.Template:
    t = tp.load(path)
    problems = tp.validate(t)
    if problems:
        raise ValueError("the Follow the Money template fails its contract: " + "; ".join(problems))
    if tuple(t.sections) != KINDS:
        raise ValueError(f"the template's sections are the ten kinds of published file, in order: {KINDS}")
    s = t.settings
    for key in ("window_from", "named_from", "races", "line", "headline_parties"):
        if key not in s:
            raise ValueError(f"the template's settings lack {key}")
    return t


def settings(path: str = PATH) -> dict:
    return dict(load(path).settings)


def races(s: dict) -> dict:
    """{race year: [calendar years]} with integer keys, inside the window."""
    out = {}
    for race, years in s["races"].items():
        out[int(race)] = [int(y) for y in years if int(y) >= int(s["window_from"])]
    return out


def race_of(year: int, s: dict):
    """The race a calendar year belongs to, or None (2017 is no race)."""
    for race, years in races(s).items():
        if int(year) in years:
            return race
    return None
