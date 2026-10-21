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
from registers.grants.tests.test_grants_society import _docs, society_properties

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
    "a block not stopping the host": ("            self.blocked[host] = why\n            raise Blocked(why, status)",
                                      "            return None"),
    # "the gate's marks only" left at the merge of fix-support-fetchgate-1 (22 October 2026): the gate now carries the
    # interstitial's marks itself, so a lane that drops MORE_CHALLENGE_MARKS is no longer broken; the lane's copy may go.
    "a blocked page left at the head of the frontier": ("                self.t.frontier_asked(host, url, exc.status)",
                                                        "                pass"),
    "a file before the window asked": ("    return bool(ys) and max(ys) < read.WINDOW_FROM", "    return False"),
    "a society's file asked again": ("            if self.t.last(\"society-file\", url) is not None:",
                                     "            if False:"),
    "a file of any name landed": ("            if GRANT_WORDS.search(path + \" \" + said) and u not in files:",
                                  "            if u not in files:"),
    "a redirect followed off the site": ("                if site_of(fg.host_of(location)) != site_of(host):", "                if False:"),
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


SOCIETY_MUTANTS = {
    "a deferred application taken as declined": ('return "Declined" if w in ("DECLINED", "DECLINE") else ""',
                                                 'return "Declined"'),
    "a total line read as a grant": ('        if layout.get("totals") and not _clean(row.get("recipient")):',
                                     '        if False:'),
    "the 'not' of a layout dropped": ('    if any(a.lower() in near for a in layout.get("absent", [])):',
                                      '    if False:'),
    "a printed summary not summed over its sections": ('            out.stated[key] = (str(sum(int(x) for x in found))',
                                                        '            out.stated[key] = (str(int(found[0]))'),
}
PDFTABLE_MUTANTS = {
    "a bottom-aligned fragment joined to the row above": ("                to = next((a for a in anchors if a > i), None)",
                                                          "                to = next((a for a in reversed(anchors) if a < i), None)"),
    "a figure placed by its left edge": ("at = w.x1 - EDGE_SLACK if is_money(w.text) else w.x0 + EDGE_SLACK",
                                         "at = w.x0 + EDGE_SLACK"),
    "a legend ending only its own page": ("                ended = True", "                ended = False"),
    "a name run into its figure not split": ("        m = RUN_ON.match(text)", "        m = None"),
    "a head's third line read as a row": ("            hi += 1                                 # the head's third line",
                                          "            pass                                    # the head's third line"),
    "a page-break tail left off its row": ('            if to is None and align == "top" and out.rows and (not anchors or i < anchors[0]):',
                                           '            if False:'),
}


@pytest.mark.parametrize("name", sorted(SOCIETY_MUTANTS))
def test_each_broken_society_reader_is_caught(name):
    docs = _docs()
    mod = mutant(os.path.join(LANE, "society.py"), name, *SOCIETY_MUTANTS[name])
    assert society_properties(mod, docs), f"the mutant {name!r} passed every property"


@pytest.mark.parametrize("name", sorted(PDFTABLE_MUTANTS))
def test_each_broken_table_reader_is_caught(name):
    docs = _docs()
    tab = mutant(os.path.join(LANE, "pdftable.py"), name, *PDFTABLE_MUTANTS[name])
    soc = mutant(os.path.join(LANE, "society.py"), "none", "READER = ", "READER = ")
    soc.pdftable = tab
    assert society_properties(soc, docs), f"the mutant {name!r} passed every property"
