"""Stats NZ's electorate names (profile `statsnz-electorates-2020`) and
the join of the Commission's electorate names to them. Only the name and
code fields are read; the shapes are held, not used.

    statsnz(data)        [(code, name, layer)]: layer general | maori
    join(names, stats)   {name: (code, Stats NZ name, layer, basis)} for the names that join

A name joins when it is Stats NZ's exactly, or equal once diacritics,
case and the spacing of hyphens are folded (basis says which). Nothing
fuzzier: an abbreviation the two spell differently ("Mt" against "Mount")
stays unjoined and is a catch-log line.
"""
import json
import re

from keys.names import fold_diacritics

FIELDS = {"general": ("GED2020_V1_00", "GED2020_V1_00_NAME"), "maori": ("MED2020_V1_00", "MED2020_V1_00_NAME")}


def statsnz(data: bytes) -> list:
    out = []
    for f in json.loads(data)["features"]:
        p = f["properties"]
        for layer, (code, name) in FIELDS.items():
            if name in p:
                out.append((str(p[code]), p[name], layer))
    return out


def _fold(s: str) -> str:
    return re.sub(r"\s*-\s*", "-", re.sub(r"\s+", " ", fold_diacritics(s).lower())).strip()


def join(names: list, stats: list) -> dict:
    exact = {n: s for s in stats for n in [s[1]]}
    folded = {}
    for s in stats:
        folded.setdefault(_fold(s[1]), []).append(s)
    out = {}
    for n in names:
        if n in exact:
            s = exact[n]
            out[n] = (s[0], s[1], s[2], "exact")
        elif len(folded.get(_fold(n), [])) == 1:
            s = folded[_fold(n)][0]
            out[n] = (s[0], s[1], s[2], "diacritics, case and hyphen spacing folded")
    return out
