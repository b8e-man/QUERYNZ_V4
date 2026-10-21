"""The mutant check: the reading and the capture broken on purpose, one way
at a time, and each break must be caught. A mutant whose target text is no
longer in the source fails here too, so the check cannot go quietly stale."""
import os

import pytest

from registers.tenders import read
from registers.tenders.tests import fixtures
from registers.tenders.tests.test_tenders_capture import blocked_run_properties

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

READ_MUTANTS = {
    "an amount of 0 taken as a value": ("if int(s) == 0:", "if int(s) == -1:"),
    "historic day and month swapped": ("d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))",
                                       "d = dt.date(int(m.group(1)), int(m.group(3)), int(m.group(2)))"),
    "current dates read month first": ('d = filed_date(s) if "/" in s else None',
                                       'd = (lambda p: filed_date(f"{p[1]}/{p[0]}/{p[2]}"))(s.split("/")) if "/" in s else None'),
    "Windows-1252 bytes read as Latin-1": ('out = raw.decode("cp1252")', 'out = raw.decode("latin-1")'),
    "a supplier joined across eras": ('notice = by_key.get(f"tenders/{era}/{rfx}")',
                                      'notice = by_key.get(f"tenders/current/{rfx}") or by_key.get(f"tenders/historic/{rfx}")'),
    "exponent form taken as an NZBN": ('return None, "exponent form: digits lost"', 'return s, "nzbn"'),
    "a NULL region kept": ('if (region or "").lower() in NONE_WORDS:', "if region is None:"),
    "a repeated supplier keyed once": ('"key": base if repeats[base] == 1 else f"{base}/{repeats[base]}"', '"key": base'),
    "an orphan counted as typed": ('f"the RFx ID names no notice of the {era} notices file"))\n                    led["set_aside"] += 1\n                    continue',
                                   'f"the RFx ID names no notice of the {era} notices file"))\n                    led["typed"] += 1\n                    out.set_aside.pop()\n                    continue'),
    "the header not compared": ('head == r.get("header_exact") and len(head) == r.get("columns")', "True"),
    "the supplier's address read": ('"nzbn_form": form, "country"', '"nzbn_form": form, "full_address": g(f, "Full Address"), "country"'),
}


def mutant(path: str, name: str, old: str, new: str):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"mutant {name!r}: its target is not in {os.path.basename(path)} exactly once"
    mod = type(os)(f"qv4_tenders_mutant")
    mod.__file__ = path
    exec(compile(src.replace(old, new), f"{os.path.basename(path)} (mutant: {name})", "exec"), mod.__dict__)
    return mod


def test_the_reading_as_written_holds_every_property():
    assert fixtures.properties(read) == []


@pytest.mark.parametrize("name", sorted(READ_MUTANTS))
def test_each_broken_reading_is_caught(name):
    mod = mutant(os.path.join(LANE, "read.py"), name, *READ_MUTANTS[name])
    assert fixtures.properties(mod), f"the mutant {name!r} passed every property"


CAPTURE_MUTANTS = {
    "a block not stopping the run": ("if f.blocked:\n            self.aside(url, \"fetch\", f.blocked)\n            raise Stop(f.blocked)",
                                     "if False:\n            pass"),
    "the historic file asked again": ('if era == "historic":\n                    continue', 'if False:\n                    continue'),
    "no rest between requests": ("if gap > 0:\n                self.sleep(gap)", "if False:\n                pass"),
}


@pytest.mark.parametrize("name", sorted(CAPTURE_MUTANTS))
def test_each_broken_capture_is_caught(name):
    mod = mutant(os.path.join(LANE, "capture.py"), name, *CAPTURE_MUTANTS[name])
    assert blocked_run_properties(mod), f"the mutant {name!r} passed every property"
