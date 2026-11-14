"""The societies' own lists, read from the real files sample.list names (held in
the document store; no model, no network): each reads as pinned, each is
recognised by exactly one layout, every total or count a list prints agrees
with its rows, application numbers counted afresh on the raw text layer agree
with the rows read, a list served twice is read once, and the comparison with
the national file covers only whole years. `society_properties(soc, table)`
lists the rules a society reader breaks; the mutant check runs it on
society.py and pdftable.py broken one way at a time."""
import os
import re
import subprocess

import pytest

from registers.grants import check, load, pdftable, read, society

#: sha256 prefix → (profile, records, accepted, declined, set aside, amount granted), read 22 October 2026
PINS = {
    "ad73854975284205": ("society-air-rescue-decisions-pdf", 212, 112, 100, 0, 2019522.03),
    "a3461bf629fddee2": ("society-air-rescue-applications-pdf", 480, 241, 239, 0, 5061638.03),
    "679b71fd97bd043a": ("society-pelorus-approved-pdf", 39, 39, 0, 0, 276844.0),
    "157fc6d637590e1c": ("society-pelorus-approved-pdf", 48, 48, 0, 0, 355118.78),
    "3a758581aa53ba44": ("society-pelorus-approved-pdf", 48, 48, 0, 0, 355118.78),
    "889b6441211df787": ("society-pelorus-declined-pdf", 35, 0, 35, 0, 0),
    "458f83243bf3fa9c": ("society-agt-quarter-distributions-pdf", 354, 354, 0, 0, 7561260.35),
    "ccb443d3be379bbf": ("society-trust-aoraki-meeting-outcome-pdf", 30, 24, 6, 0, 131097.14),
    "b50f894025d89ca1": ("society-trust-aoraki-successful-applications-pdf", 26, 24, 2, 0, 231919.57),
    "894e7f7b9ab8e616": ("society-milestone-recipients-pdf", 30, 23, 6, 1, 182234.2),
    "d2edd7faf5a75180": ("society-milestone-recipients-pdf", 22, 16, 6, 0, 105784.51),
    "5ffad08a26b4c2d8": ("society-new-horizon-approved-pdf", 104, 104, 0, 0, 1695404.68),
    "9365118f679ae395": ("society-new-horizon-unsuccessful-pdf", 18, 0, 18, 0, 0),
    "36737b65be81a624": ("society-we-care-quarter-approved-pdf", 26, 26, 0, 0, 834337.0),
    # Pelorus's export of October 2020 to September 2023, read 14 November 2026: names centred on their row, a name
    # three lines high cut by a page break (ff65…), a page's last line the next page's first name (ae90…)
    "921a1a3c0192d526": ("society-pelorus-published-approved-pdf", 48, 48, 0, 0, 301079.4),
    "ff650b775267bee1": ("society-pelorus-published-approved-pdf", 57, 57, 0, 0, 396234.24),
    "ae90ee17abd8be9d": ("society-pelorus-published-declined-pdf", 30, 0, 30, 0, 0),
    # Milestone's grants-system export, read 14 November 2026 (each month agrees with the national file, 2023 to 2025)
    "53f50075c6d1ddb3": ("society-milestone-grant-outcomes-pdf", 81, 49, 32, 0, 460442.1),
    "f89b206bdc559d30": ("society-milestone-grant-outcomes-pdf", 65, 42, 23, 0, 356122.06),
    "6d4ab22e356d2e68": ("society-milestone-grant-outcomes-pdf", 36, 25, 11, 0, 250730.46),
    "fb21f7374a44ed6c": ("society-milestone-grant-details-pdf", 31, 28, 3, 0, 311525.47),
    "c5eaa9f7a76d5169": ("society-milestone-grant-details-pdf", 15, 14, 1, 0, 103909.8),
    "1089afe221c06fdc": ("society-milestone-grant-details-pdf", 45, 35, 10, 0, 309385.55),
    "1c865cbef7b9efb4": ("society-milestone-recipients-2017-pdf", 17, 11, 6, 0, 86973.31),
    "0a84017cb559bfdd": ("society-milestone-recipients-2017-pdf", 7, 5, 2, 0, 61943.11),
    "e4b917254b76a42f": ("society-we-care-quarter-declined-pdf", 3, 0, 3, 0, 0),
    "6e805accda7ed8a4": (None, 1, 0, 0, 1, 0),        # a refund list
    "67eaf6bbf1794ddc": (None, 1, 0, 0, 1, 0),        # a scan
    "a6f109ebd728c7e8": (None, 1, 0, 0, 1, 0),        # side-by-side blocks, carded
}
#: application numbers as each layout prints them, for a count that does not use the reader
NUMBERS = {"society-pelorus-approved-pdf": r"\bGA\d{6}-\w{4}\b", "society-pelorus-declined-pdf": r"\bGA\d{6}-\w{4}\b",
           "society-trust-aoraki-meeting-outcome-pdf": r"\bG[AF]\d{6}-\w{4}\b",
           "society-pelorus-published-approved-pdf": r"\bPT\d{5}\b", "society-pelorus-published-declined-pdf": r"\bPT\d{5}\b",
           "society-milestone-grant-outcomes-pdf": r"\bG[AF]\d{6}-",
           "society-milestone-grant-details-pdf": r"\bM\d{5}\b|\bG[AF]\d{6}-\w{4}\b",
           "society-new-horizon-approved-pdf": r"\bNH\d{3,5}\b", "society-new-horizon-unsuccessful-pdf": r"\bNH\d{3,5}\b"}
#: application numbers as a row must carry them whole, where the text layer wraps them
WHOLE_NUMBERS = {"society-milestone-grant-outcomes-pdf": r"G[AF]\d{6}-\w{4}",
                 "society-milestone-grant-details-pdf": r"M\d{5}|G[AF]\d{6}-\w{4}",
                 "society-pelorus-published-approved-pdf": r"PT\d{5}", "society-pelorus-published-declined-pdf": r"PT\d{5}"}
#: names a reader must keep whole: (sha256 prefix, application number or None) → the name as printed
NAMES = {
    ("ccb443d3be379bbf", "GA250715-0307"): "Life Education Trust Mid and South Canterbury",     # cut by a page break
    ("5ffad08a26b4c2d8", "NH0070"): "COUNTIES INDOOR BOWLING CENTRE INCORPORATED",            # its number a line below
    ("889b6441211df787", "GA260326-7051"): "Wellington Hockey Association Incorporated",       # a legend follows it
    ("a3461bf629fddee2", None): "Cancer Society of New Zealand Canterbury-West Coast Division Incorporated",  # run on
    ("921a1a3c0192d526", "PT13967"): "CCS DISABILITY ACTION NELSON MARLBOROUGH INCORPORATED",  # two lines about its row
    ("921a1a3c0192d526", "PT13465"): "The Nest Collective NZ Charitable Trust",                # the first under a head
    ("ff650b775267bee1", "PT15050"): "He Whanau Manaaki o Tararua Free Kindergarten Association Incorporated",  # cut
    ("ff650b775267bee1", "PT15607"): "Hoop Club Hutt Valley",                                  # the page above's tail
    ("ae90ee17abd8be9d", "PT20726"): "South Auckland Group Riding For The Disabled Association Incorporated",  # foot
    ("ae90ee17abd8be9d", "PT20744"): "Saints Softball Club",                                   # one line, at a foot
}
LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _docs():
    from support.docstore.landing import path_for, read_bytes
    shas = [ln.strip() for ln in open(os.path.join(LANE, "sample.list"), encoding="utf-8")
            if re.fullmatch(r"[0-9a-f]{64}", ln.strip()) and ln.strip()[:16] in PINS]
    if len(shas) != len(PINS) or not all(os.path.exists(path_for(s)) for s in shas):
        pytest.skip("the document store does not hold the sample's society files here")
    return {s: read_bytes(s) for s in shas}


def contact_kept(soc, data, slug, out, col) -> bool:
    """Whether a cell of the column `col` (Milestone's contact person, its short description) reaches a kept field:
    whole anywhere in a name, a number, a purpose, a reason or a conflict, or opening any field. Nothing of a cell is
    printed."""
    lay = soc.LAYOUTS[slug]
    ws = soc.pdftable.words(data)
    first = next(iter(soc.pdftable.pages_of([w for w in ws if w.page == 1]).values()), [])
    heads = next(h for h in soc._heads(lay) if soc._head(first, h, lay) is not None)
    if col not in heads:
        return False
    t = soc.pdftable.table(data, heads, lay["anchor"], lay["align"], ws=ws, skip=lay.get("skip", ()),
                           stop=lay.get("stop", ()), mode=lay.get("edge_mode", "left"),
                           total_lines=lay.get("total_lines", "figures"), head_tail=lay.get("head_tail"),
                           shift=tuple(lay.get("shift", ())))
    cells = {soc._clean(r.get(col)) for r in t.rows} - {""}
    if not cells:
        return True                    # the column's cells were read into another: its edge was lost
    for g in out.grants:
        if any(k == col or col in k for k in g):
            return True
        for k, v in g.items():
            if not isinstance(v, str):
                continue
            if any(v.startswith(cc) for cc in cells):
                return True
            if k in ("recipient_as_published", "application_as_published", "category_1", "purpose_as_published",
                     "reason_as_published", "interest_as_published") and any(cc in v for cc in cells):
                return True
    return False


def _read(soc, data, sha):
    slug = soc.recognise(data)
    if slug is None:
        return None, read.read_document(data, sha)
    return slug, soc.read_file(data, sha, slug)


def society_properties(soc=society, docs=None) -> list:
    """The rules, as a list of the ones a society reader `soc` (with its `pdftable`) breaks on the sample files."""
    broken = set()
    docs = docs if docs is not None else _docs()
    for sha, data in docs.items():
        want = PINS[sha[:16]]
        slug, out = _read(soc, data, sha)
        got = (slug, out.records, sum(g["status"] == "Accepted" for g in out.grants),
               sum(g["status"] == "Declined" for g in out.grants), len(out.set_aside),
               round(sum(g["amount_nzd"] or 0 for g in out.grants), 2))
        if got != want:
            broken.add("each sample file reads as pinned")
        if slug is None:
            continue
        first = next(iter(soc.pdftable.pages_of([w for w in soc.pdftable.words(data) if w.page == 1]).values()))
        claims = [s for s, lay in soc.LAYOUTS.items() if soc._title_match(first, lay) is not None and (
            lay.get("edges") or any(soc._head(first, h, lay) is not None for h in soc._heads(lay)))]
        if claims != [slug]:
            broken.add("each file is recognised by exactly one layout")
        st = out.stated
        for col in ("requested", "granted"):
            want = soc.money(st[f"total_{col}"]) if st.get(f"total_{col}") is not None else None
            if st.get(f"total_{col}") is not None and (want is None or abs(want - st[f"rows_{col}"]) > 0.5):
                broken.add("every total a list prints equals its rows")
        for key, status in (("count_all", None), ("count_accepted", "Accepted"), ("count_declined", "Declined")):
            if key in st and int(st[key]) != sum(1 for g in out.grants if status in (None, g["status"])):
                broken.add("every count a list prints equals its rows")
        if slug in NUMBERS:
            text = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data, capture_output=True).stdout.decode()
            if len(re.findall(NUMBERS[slug], text)) != len(out.grants) + len(out.set_aside):
                broken.add("application numbers on the text layer equal the rows read")
        whole = WHOLE_NUMBERS.get(slug)
        if whole and not all(re.fullmatch(whole, g["application_as_published"] or "") for g in out.grants):
            broken.add("an application number wrapped over two lines is read whole")
        for col in soc.LAYOUTS[slug].get("never_read", ()):
            if contact_kept(soc, data, slug, out, col):
                broken.add("a column never read reaches no kept field")
        names = {g["recipient_as_published"] for g in out.grants}
        apps = {g["application_as_published"]: g["recipient_as_published"] for g in out.grants}
        for (pre, app), name in NAMES.items():
            if pre == sha[:16] and (name not in names if app is None else apps.get(app) != name):
                broken.add("a name wrapped, cut by a page, or run into its figure is read whole")
        for g in out.grants:
            cells = " ".join(g[c] or "" for c in ("recipient_as_published", "amount_requested_as_published",
                                                  "amount_granted_as_published"))
            if re.search(r"\b(?:Amount|Requested|Approved)\b", cells) or re.search(
                    r"\[[AD]\d+\]", g["recipient_as_published"]):
                broken.add("no head word, decision code or legend runs into a name or an amount")
            if g["status"] not in ("Accepted", "Declined") or (g["status"] == "Declined" and g["amount_nzd"]):
                broken.add("a status is Accepted or Declined, and only an accepted grant carries an amount")
            if re.search(r"\$\s?\d|@|\bPowered by\b|\+64", g["recipient_as_published"]):
                broken.add("no figure, footer or contact line runs into a recipient's name")
            if g["publisher_key"] != g["grantor_key"] or g["grantor_key"] != soc.LAYOUTS[slug]["society"]:
                broken.add("the society is publisher and grantor of every row")
            if g["period"] < str(read.WINDOW_FROM):
                broken.add("nothing before 2017 (ruling 71)")
    return sorted(broken)


def test_the_society_readers_as_written_hold_every_property():
    assert society_properties() == []


def test_a_list_served_twice_is_read_once():
    docs = _docs()
    pair = [s for s in docs if s[:16] in ("157fc6d637590e1c", "3a758581aa53ba44")]
    seen, outs = {}, []
    for sha in pair:
        out = read.read_document(docs[sha], sha)
        load.repeat(out, seen)
        outs.append(out)
    assert [len(o.grants) for o in outs] == [48, 0] and len(outs[1].set_aside) == 48
    assert {a["stage"] for a in outs[1].set_aside} == {"repeat"}


def test_a_scan_a_refund_list_and_a_carded_layout_are_told_apart():
    docs = _docs()
    carded = check.unprofiled()
    for sha, data in docs.items():
        if PINS[sha[:16]][0] is not None:
            continue
        out = read.read_document(data, sha)
        scan = out.stated["text_words"] < read.SCAN_WORDS
        assert scan == (sha[:16] == "67eaf6bbf1794ddc")
        assert (sha[:16] in carded) == (sha[:16] == "a6f109ebd728c7e8")


def test_only_whole_years_inside_one_year_are_compared():
    q = ["2021-01-01/2021-03-31", "2021-04-01/2021-06-30", "2021-07-01/2021-09-30", "2021-10-01/2021-12-31",
         "2022-01-01/2022-03-31", "2022-07-01/2022-09-30", "2024-06-01/2025-05-31", "2025-06-01/2026-05-31",
         "2023-03-10"]
    assert check._covered_years(q) == {2021}


def test_a_page_reads_its_columns_by_head_and_figures_by_right_edge():
    line = pdftable.Line(1, 100.0, [pdftable.Word(1, 50, 100, 120, "Kowhai"), pdftable.Word(1, 122, 100, 160, "Club"),
                                    pdftable.Word(1, 230, 100, 290, "$20,000.00"), pdftable.Word(1, 306, 100, 330, "[D1]")])
    head = pdftable.Line(1, 90.0, [pdftable.Word(1, 50, 90, 100, "Name"), pdftable.Word(1, 260, 90, 300, "Amount"),
                                   pdftable.Word(1, 305, 90, 330, "Code")])
    found = pdftable.find_head([head, line], {"name": "Name", "amount": "Amount", "code": "Code"})
    assert found and pdftable._cells(line, found[1]) == {"name": "Kowhai Club", "amount": "$20,000.00", "code": "[D1]"}
    assert pdftable.RUN_ON.match("Incorporated$25,000.00").groups() == ("Incorporated", "$25,000.00")
    assert society.money("$ 5,865.00") == 5865.0 and society.money("$3,000.00 (START)") == 3000.0
    assert society.money("$5,000.00 $103,131.34") is None


def test_a_name_centred_on_its_row_is_one_row_with_its_application_number():
    """Pelorus's export of 2020 to 2023 centres a wrapped name on its row: the number and the figures stand on the
    middle line, a two-line name half a line above and below it. A wrapped name split into two rows, or read
    without its number, fails here."""
    docs = _docs()
    for pre in ("921a1a3c0192d526", "ff650b775267bee1", "ae90ee17abd8be9d"):
        sha = next(s for s in docs if s.startswith(pre))
        out = society.read_file(docs[sha], sha, society.recognise(docs[sha]))
        apps = [g["application_as_published"] for g in out.grants]
        assert all(a and re.fullmatch(r"PT\d{5}", a) for a in apps) and len(apps) == len(set(apps))
        text = subprocess.run(["pdftotext", "-layout", "-", "-"], input=docs[sha], capture_output=True).stdout.decode()
        assert sorted(apps) == sorted(re.findall(r"\bPT\d{5}\b", text))
        assert out.stated["total_requested"] and abs(society.money(out.stated["total_requested"])
                                                      - out.stated["rows_requested"]) < 0.5
    by = {(pre, g["application_as_published"]): g["recipient_as_published"]
          for pre in ("921a1a3c0192d526",) for s in docs if s.startswith(pre)
          for g in society.read_file(docs[s], s, society.recognise(docs[s])).grants}
    assert by[("921a1a3c0192d526", "PT13967")] == "CCS DISABILITY ACTION NELSON MARLBOROUGH INCORPORATED"
    assert "MARLBOROUGH INCORPORATED" not in by.values() and "CCS DISABILITY ACTION NELSON" not in by.values()


def test_the_contact_person_is_never_kept():
    """Milestone prints its applicants' contact persons in a column of their own (2020 to 2026). The column is read
    for its edge only: no grant carries a field for it, and no cell of it reaches a name, a number, a purpose, a
    reason or a conflict, nor opens any field. Nothing of a cell is printed."""
    docs = _docs()
    checked = 0
    for sha, data in docs.items():
        slug = society.recognise(data)
        if slug is None or "contact" not in society.LAYOUTS[slug].get("never_read", ()):
            continue
        out = society.read_file(data, sha, slug)
        first = next(iter(pdftable.pages_of([w for w in pdftable.words(data) if w.page == 1]).values()))
        heads = next(h for h in society._heads(society.LAYOUTS[slug]) if society._head(first, h, society.LAYOUTS[slug]))
        if "contact" in heads:
            checked += 1
        assert not contact_kept(society, data, slug, out, "contact")
        assert all("contact" not in k for g in out.grants for k in g)
    assert checked >= 3          # the 2022 to 2026 export (two months) and April 2022 print the column
