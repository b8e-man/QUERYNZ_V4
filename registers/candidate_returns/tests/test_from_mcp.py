"""The lane's files from the ingest MCP's copies (9 November 2026)."""
from registers.candidate_returns import from_mcp as M
from registers.candidate_returns import load

A, B, C, D, E, F = (ch * 64 for ch in "abcdef")
ROOT = "https://elections.nz/assets/"
L20 = ("https://elections.nz/democracy-in-nz/historical-events/2020-general-election-and-referendums/"
       "candidate-expenses-and-donations-for-the-2020-general-election?Year=2020&start=")


def test_an_address_is_named_as_the_old_folder_named_it():
    assert M.name_of(ROOT + "candidate-returns/2020/Labour-Party/X.pdf") == "candidate-returns__2020__Labour-Party__X.pdf"
    assert M.name_of(ROOT + "Uploads/Lim-P-Ohariu-amended-220224.pdf") == "Uploads__Lim-P-Ohariu-amended-220224.pdf"
    assert M.name_of("https://www.elections.nz/assets/Uploads/Y.pdf") == "Uploads__Y.pdf"
    assert M.name_of(L20 + "0") is None


def test_every_copy_of_an_in_window_return_is_taken_and_an_older_election_is_not():
    held = [(ROOT + "Uploads/Manning-R-Tukituki.pdf", A, 202), (ROOT + "Uploads/Manning-R-Tukituki.pdf", B, 902),
            (ROOT + "candidate-returns/2023/ACT-New-Zealand/2023_ACT_X.pdf", C, 5),
            (ROOT + "candidate-returns/2017/Green-Party/2017_Green_Y.pdf", D, 6),
            (ROOT + "candidate-returns/2022/Tauranga/Z.pdf", E, 7)]
    got = M.returns(held)
    assert got == {A: ["Uploads__Manning-R-Tukituki.pdf"], B: ["Uploads__Manning-R-Tukituki.pdf"],
                   C: ["candidate-returns__2023__ACT-New-Zealand__2023_ACT_X.pdf"],
                   E: ["candidate-returns__2022__Tauranga__Z.pdf"]}
    assert load.year_of(got[C]) == 2023 and load.year_of(got[A]) is None


def test_a_listing_page_is_its_newest_copy_in_page_order_and_a_sheet_is_found_by_its_own_name():
    held = [(L20 + "100", A, 1), (L20 + "0", B, 2), (L20 + "100", C, 9),
            (ROOT + "pagecomponent-file-files/2020-Candidate-Returns.xlsx", D, 3),
            (ROOT + "pagecomponent-file-files/2023-candidate-returns-updated-24092024.xlsx", E, 4),
            (ROOT + "pagecomponent-file-files/2023-candidate-returns-updated-01022024.xlsx", F, 8)]
    store = {s: s[:1].encode() for s in (A, B, C, D, E, F)}
    ls = M.listings(held, store.__getitem__)
    assert [(n.rsplit("=", 1)[1], t()) for n, t in ls[2020]] == [("0", (B, b"b")), ("100", (C, b"c"))]
    sh = M.sheets(held, store.__getitem__)
    assert [t()[0] for _, t in sh[2020]] == [D]
    assert [t()[0] for _, t in sh[2023]] == [F, E]                  # oldest version first: 1 Feb, then 24 Sep 2024


def test_the_statements_read_files_from_anywhere():
    page = b"<html><body>no table</body></html>"
    st = load.statements_of({2020: [("p", lambda: (A, page))]}, {})
    assert st.listing == [] and st.catch and st.catch[0][0] == A and st.catch[0][1].startswith("p: ")
