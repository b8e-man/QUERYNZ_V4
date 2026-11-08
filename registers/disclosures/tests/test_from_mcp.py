"""The lane's files from the ingest MCP first, the old folder filling its gaps (9 November 2026)."""
from types import SimpleNamespace

from registers.disclosures import capture, from_mcp as M

A, B, C, D, E, F, G, H = (ch * 64 for ch in "abcdefgh")
SITE = "https://elections.nz/democracy-in-nz/political-parties-in-new-zealand/donations-exceeding-20000/"
ASSETS = "https://elections.nz/assets/2026-20k+-donations/"
OLD = "/old/var/staging/ec-donations/"


def ref(sha):
    return SimpleNamespace(sha256=sha)


def test_the_two_tables_and_a_declaration_are_known_by_their_address():
    assert M.listing_of(SITE) == capture.LISTINGS[0]
    assert M.listing_of(SITE + "donations-exceeding-30000") == capture.LISTINGS[1]
    assert M.listing_of("democracy-in-nz/political-parties-in-new-zealand/donations-exceeding-20000/"
                        "donations-exceeding-30000") == capture.LISTINGS[1]          # an address the MCP holds bare
    assert M.commission_name(ASSETS + "Rank-Group_05.11.2026_.pdf") == "Rank-Group_05.11.2026_.pdf"
    assert M.commission_name("https://elections.nz/assets/Donation-returns/2023/X%20Y.JPG") == "X Y.JPG"
    assert M.commission_name(SITE) is None


def test_the_mcp_answers_first_the_old_folder_fills_a_challenge_page_and_one_file_answers_each_name():
    mcp = [(ASSETS + "J-Swap_05.11.2026_.pdf", A, 10, "application/pdf"),      # only the MCP has it
           (ASSETS + "Rank-Group_05.11.2026_.pdf", B, 11, "text/html"),         # a challenge page: the old copy fills
           (ASSETS + "Both.pdf", C, 3, "application/pdf"), (ASSETS + "Both.pdf", D, 12, "application/pdf"),
           (ASSETS + "Blocked.pdf", H, 13, "text/html; charset=utf-8"),         # held nowhere else: set aside
           (SITE, E, 20, "text/html")]
    landed = [("declaration", ref(F), OLD + "residue/donations_20k/Rank-Group_05.11.2026_.pdf", False),
              ("declaration", ref(G), OLD + "archive/2026-20k+-donations__Both.pdf", False),
              ("listing", ref("9" * 64), OLD + "index/" + capture.LISTINGS[0], False),
              ("listing", ref("8" * 64), OLD + "index/" + capture.LISTINGS[1], False)]
    when = {E: "2026-11-08T09:45:14", "9" * 64: "2026-11-08T14:37:13", "8" * 64: "2026-11-08T14:37:16"}
    listings, declarations, aside = M.documents(mcp, landed, [(OLD + "archive/x.pdf", "cut at 1 MiB")], when.get)
    assert declarations == sorted([(A, "J-Swap_05.11.2026_.pdf"), (D, "Both.pdf"), (F, "Rank-Group_05.11.2026_.pdf")])
    assert aside == [("Blocked.pdf", "a challenge page the MCP saved under a document's name"),
                     ("x.pdf", "cut at 1 MiB")]
    assert listings == [("9" * 64, capture.LISTINGS[0]), ("8" * 64, capture.LISTINGS[1])]   # the old copies: newer
    when[E] = "2026-11-09T09:00:00"
    listings, _, _ = M.documents(mcp, landed, [], when.get)
    assert listings[0] == (E, capture.LISTINGS[0])                                       # the MCP's: newer
