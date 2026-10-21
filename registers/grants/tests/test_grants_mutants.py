"""The mutant check: the reading, the capture and the check broken on
purpose, one way at a time, and each break must be caught. A mutant whose
target text is no longer in the source fails here too, so the check cannot
go quietly stale."""
import os
import types

import pytest

from registers.grants import capture
from registers.grants.tests import fixtures
from registers.grants.tests.test_grants_capture import run_properties

LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

READ_MUTANTS = {
    "the window not applied": ("if int(year) < WINDOW_FROM:", "if False:"),
    "dates read month first": ('d = filed_date(s) if re.fullmatch', 'd = (lambda p: filed_date(f"{p[1]}/{p[0]}/{p[2]}"))(s.split("/")) if re.fullmatch'),
    "Windows-1252 read as Latin-1": ('return raw.decode("cp1252")', 'return raw.decode("latin-1")'),
    "any 13 digits taken as an NZBN": ('nz = nzbn_ok(nz_pub) if', 'nz = nz_pub if'),
    "exponent form taken as a charity number": ('cc = charity_number(cc_pub) if cc_pub and re.fullmatch(r"(?i)cc\\s*\\d{5,6}", cc_pub) else None',
                                                'cc = cc_pub'),
    "a declined grant given its amount": ('"amount_nzd": granted if status == "Accepted" and granted else None',
                                          '"amount_nzd": granted'),
    "an unknown society guessed": ('''            out.set_aside.append({"document": sha, "place": place, "stage": "read",
                                  "reason": "the society named is not on the lane's list of name forms"})
            continue''', '''            soc = "air-rescue-services"'''),
    "spreadsheet day numbers off by one": ("EXCEL_EPOCH = dt.date(1899, 12, 30)", "EXCEL_EPOCH = dt.date(1899, 12, 31)"),
    "a name not shown to be an organisation called one": ('return "not shown to be an organisation"',
                                                          'return "organisation (by its name)"'),
    "the header not compared": ('if _first_line(data) == profile(DIA_CSV)["recognise"]["header_exact"]:',
                                'if data[:12] == b"Society_Name":'),
    "the asterisk ignored": ('"multi_year": (multi_year_note or "asterisk") if mm.group("star") else None',
                             '"multi_year": None'),
    "a Total row read as a grant": ('if re.fullmatch(r"(?i)total", name):', 'if False:'),
    "the round not read": ('r = _ROUND.search(heading)', 'r = None'),
    "a wrong-width row read": ('if len(cells) != 2:', 'if len(cells) < 2:'),
}


def mutant(path: str, name: str, old: str, new: str):
    with open(path, encoding="utf-8") as f:
        src = f.read()
    assert src.count(old) == 1, f"mutant {name!r}: its target is not in {os.path.basename(path)} exactly once"
    mod = types.ModuleType("qv4_grants_mutant")
    mod.__file__ = path
    exec(compile(src.replace(old, new), f"{os.path.basename(path)} (mutant: {name})", "exec"), mod.__dict__)
    return mod


@pytest.mark.parametrize("name", sorted(READ_MUTANTS))
def test_each_broken_reading_is_caught(name):
    mod = mutant(os.path.join(LANE, "read.py"), name, *READ_MUTANTS[name])
    assert fixtures.properties(mod), f"the mutant {name!r} passed every property"


CAPTURE_MUTANTS = {
    "a block not stopping the host": ("            self.blocked[host] = why\n            raise Blocked(why)",
                                      "            return None"),
    "the gate's marks only": ("    for mark in MORE_CHALLENGE_MARKS:", "    for mark in ():"),
    "a redirect followed off the host": ("                if fg.host_of(location) != host:", "                if False:"),
    "no rest between requests": ("self.pacer.wait(dec.host, max(dec.floor, REST_S if self.failures.get(host) else FLOOR_S))",
                                 "pass"),
    "the file asked every night": ("        if last is not None and page_same:", "        if False:"),
    "the walk leaves its host": ("or fg.host_of(u) != host or", "or"),
    "off-peak ignored": ("if not self.anytime and not off_peak(self.now()):", "if False:"),
}


@pytest.mark.parametrize("name", sorted(CAPTURE_MUTANTS))
def test_each_broken_capture_is_caught(name, monkeypatch):
    mod = mutant(os.path.join(LANE, "capture.py"), name, *CAPTURE_MUTANTS[name])
    monkeypatch.setattr(mod.fg, "check", lambda url, positions_dir=None: types.SimpleNamespace(
        host=capture.fg.host_of(url), floor=5.0))
    assert run_properties(mod), f"the mutant {name!r} passed every property"
