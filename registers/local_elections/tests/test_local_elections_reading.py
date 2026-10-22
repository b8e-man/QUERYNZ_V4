"""The listing reader and the register's rules on pages written to each shape a council uses, and mutants each
rule must catch. No store, no network, no model."""
import datetime as dt

import pytest

from registers.local_elections import capture, check, load, read

U = "https://www.example.govt.nz/elections/returns"

LISTING = """<html><head><title>Electoral donations and expenses 2025</title></head><body>
<nav><a href="/x.pdf">Menu file return</a></nav>
<main><h1>Electoral donations and expenses 2025</h1>
<button>Coastal Central General Constituency</button><h3>Candidate declarations</h3>
<ul><li><a href="/media/ab12cd34/coastal_smith-jane.pdf">SMITH Jane - electoral donations and expenses (PDF 120 KB)</a></li>
<li><a href="/media/ef56gh78/coastal_kitchen-colin.pdf">KITCHEN Colin (Toss) - electoral donations and expenses (PDF 1.2 MB)</a></li></ul>
<button>Mayor</button><h3>Candidate declarations</h3>
<ul><li><a href="/media/aa11bb22/mayor_brown.pdf">BROWN Bob - nil return</a></li></ul>
<h2>Forms</h2><ul><li><a href="/media/zz/blank.pdf">Return of electoral donations and expenses form (blank)</a></li>
<li><a href="/media/zz/guide.pdf">Candidate guide</a></li></ul>
<h2>2016 returns</h2><ul><li><a href="/media/old/2016-jones.pdf">JONES Ann 2016 - electoral donations and expenses</a></li></ul>
</main><footer><a href="mailto:x@example.govt.nz">email</a></footer></body></html>""".encode()

RESULTS = """<main><h1>2022 election results</h1><h2>Northern Ward</h2><table>
<tr><td>SMITH, Jane</td><td>1,234</td><td><a href="/assets/a.pdf">View return</a></td></tr>
<tr><td>BROWN Bob</td><td>99</td><td><a href="/assets/b.pdf">View return (PDF 120KB)</a></td></tr></table>
<h2>Ōpaki Community Board by-election 2023</h2><table>
<tr><td>GREY Tui</td><td>12</td><td><a href="/assets/c.pdf">Return</a></td></tr></table></main>""".encode()

COMBINED = """<main><h1>Candidate donations and expense returns</h1><h2>2025</h2>
<p><a href="/files/2025-waihemo.pdf">Waihemo Ward returns 2025</a></p>
<p><a href="/files/2022-1-8.pdf">Expense returns 1-8</a></p>
<h2>Elections 2019</h2><p><a href="/files/smith.pdf">Jane Smith</a></p></main>""".encode()

FOLDER = """<main><h1>Return of electoral expenses and donations</h1><ul>
<li><a href="/elections/returns?path=Elections/Candidate Expenses/2025"><strong>2025</strong></a></li>
<li><a href="/elections/returns?path=Elections/Candidate Expenses/2022"><strong>2022</strong></a></li>
<li><a href="/about/contact">Contact us</a></li></ul></main>""".encode()


def rows(page, url=U, council="Example District Council", seed_year=None):
    return read.read_listing(page, url, council, seed_year)


def test_a_listing_reads_one_row_per_candidate_with_its_seat_and_year():
    out = rows(LISTING)
    got = [(r["candidate_as_listed"], r["position"], r["election_year"], r["return_kind"]) for r in out["rows"]]
    assert ("SMITH Jane", "Coastal Central General Constituency", 2025, "donations and expenses") in got
    assert ("KITCHEN Colin (Toss)", "Coastal Central General Constituency", 2025, "donations and expenses") in got
    assert ("BROWN Bob", "Mayor", 2025, "nil") in got


def test_forms_guides_and_the_navigation_are_not_returns():
    out = rows(LISTING)
    assert all("blank" not in r["file_url"] and "guide" not in r["file_url"] and "/x.pdf" not in r["file_url"]
               for r in out["rows"])
    assert out["not_returns"].get("form") == 1 and out["not_returns"].get("guide") == 1


def test_an_old_return_is_read_with_its_own_year_and_held_out_of_the_window_by_the_load():
    old = [r for r in rows(LISTING)["rows"] if "2016" in r["file_url"]]
    assert old and old[0]["election_year"] == 2016


def test_a_results_table_takes_the_name_from_its_row_and_drops_the_votes():
    out = rows(RESULTS)
    got = [(r["candidate_as_listed"], r["position"], r["election_year"], r["by_election"]) for r in out["rows"]]
    assert got[0] == ("SMITH, Jane", "Northern Ward", 2022, False)
    assert got[1][0] == "BROWN Bob"
    assert got[2][0] == "GREY Tui" and got[2][2] == 2023 and got[2][3] is True
    assert load.shape_of(out) == "council-returns-results-table"
    assert load.shape_of(rows(LISTING)) == "council-returns-listing"


def test_a_combined_file_names_nobody_and_says_so():
    out = rows(COMBINED)
    by = {r["file_url"].rsplit("/", 1)[1]: r for r in out["rows"]}
    assert by["2025-waihemo.pdf"]["covers"] == "several candidates" and by["2025-waihemo.pdf"]["candidate_as_listed"] == ""
    assert by["2022-1-8.pdf"]["covers"] == "several candidates"
    assert by["smith.pdf"]["covers"] == "one candidate" and by["smith.pdf"]["election_year"] == 2019


def test_a_folder_page_is_followed_not_read():
    out = rows(FOLDER, url="https://www.example.govt.nz/elections/returns")
    assert out["rows"] == [] and len(out["follow"]) == 2
    assert load.shape_of(out) == "council-returns-hub"


def test_the_seed_year_is_the_last_resort():
    page = b"<main><h1>Returns</h1><a href='/a/jones.pdf'>JONES Ann - return</a></main>"
    assert rows(page, seed_year=2022)["rows"][0]["election_year"] == 2022
    assert rows(page)["rows"][0]["election_year"] is None


@pytest.mark.parametrize("value,bad", [
    ("SMITH Jane", False), ("KITCHEN Colin (Toss)", False), ("Coastal Central General Constituency", False),
    ("Ward 3 Highway Board", False),
    ("jane@example.co.nz", True), ("021 234 5678", True), ("12 Kauri Street", True), ("4B Te Awa Road", True)])
def test_the_value_rule_knows_an_address_by_its_shape(value, bad):
    assert bool(check.value_problems([("k", "candidate_as_listed", value)])) is bad


class FakeTables:
    def __init__(self, wanted):
        self._wanted, self.files, self.pages, self.passes = list(wanted), {}, [], []

    def new_pass(self, mode):
        self.passes.append(mode)
        return len(self.passes)

    def end_pass(self, *a):
        pass

    def page(self, pid, council, url, seed_year, depth, status, sha, state, why=None):
        self.pages.append((url, state))

    def want(self, council, url, listing_url, year):
        if url not in [w[0] for w in self._wanted] and url not in self.files:
            self._wanted.append((url, council, year))

    def wanted(self):
        return sorted([w for w in self._wanted if w[0] not in self.files], key=lambda w: (w[2] or 9999, w[1], w[0]))

    def file(self, pid, url, status, sha, kind, size, state, why=None):
        self.files[url] = state


class Got:
    def __init__(self, body=b"%PDF-1.4", status=200):
        self.body, self.status, self.blocked, self.location = body, status, "", ""


class Ref:
    sha256, kind, size = "0" * 64, "pdf", 8


NIGHT = lambda: dt.datetime(2026, 10, 22, 23, 0, tzinfo=capture.NZ)
NOON = lambda: dt.datetime(2026, 10, 22, 12, 0, tzinfo=capture.NZ)


def test_no_file_is_asked_by_day():
    asked = []
    t = FakeTables([("https://a.govt.nz/1.pdf", "A", 2019)])
    run = capture.Run(t, land_fn=lambda *a, **k: (Ref, True), fetch_fn=lambda u, m: asked.append(u), clock=NOON,
                      log=lambda *a: None)
    assert run.files()["stopped"] == "daytime" and asked == []


def test_files_go_oldest_election_first_and_a_blocked_host_is_not_asked_again():
    asked = []

    def fetch(u, m):
        asked.append(u)
        if "b.govt.nz" in u:
            return Got(status=403), "blocked", "HTTP 403"
        return Got(), "landed", None
    t = FakeTables([("https://a.govt.nz/2025.pdf", "A", 2025), ("https://b.govt.nz/x.pdf", "B", 2019),
                    ("https://b.govt.nz/y.pdf", "B", 2019), ("https://a.govt.nz/2019.pdf", "A", 2019)])
    run = capture.Run(t, land_fn=lambda *a, **k: (Ref, True), fetch_fn=fetch, clock=NIGHT, log=lambda *a: None)
    out = run.files()
    assert asked == ["https://a.govt.nz/2019.pdf", "https://b.govt.nz/x.pdf", "https://a.govt.nz/2025.pdf"]
    assert t.files["https://b.govt.nz/x.pdf"] == "blocked" and "https://b.govt.nz/y.pdf" not in t.files
    assert out["landed"] == 2


def test_a_landed_file_is_never_asked_twice():
    asked = []
    t = FakeTables([("https://a.govt.nz/1.pdf", "A", 2019)])
    f = lambda u, m: (asked.append(u), (Got(), "landed", None))[1]
    for _ in range(2):
        capture.Run(t, land_fn=lambda *a, **k: (Ref, True), fetch_fn=f, clock=NIGHT, log=lambda *a: None).files()
    assert asked == ["https://a.govt.nz/1.pdf"]


def test_the_listings_pass_follows_a_folder_and_wants_only_in_window_returns():
    pages = {"https://www.example.govt.nz/elections/returns": FOLDER,
             "https://www.example.govt.nz/elections/returns?path=Elections/Candidate%20Expenses/2025": LISTING,
             "https://www.example.govt.nz/elections/returns?path=Elections/Candidate%20Expenses/2022": RESULTS}
    t = FakeTables([])
    f = lambda u, m: (Got(pages[u]), "landed", None) if u in pages else (Got(status=404), "not found", "HTTP 404")
    run = capture.Run(t, land_fn=lambda *a, **k: (Ref, True), fetch_fn=f, clock=NIGHT, log=lambda *a: None,
                      seed_list=[("Example District Council", [], "https://www.example.govt.nz/elections/returns")])
    out = run.listings()
    urls = [w[0] for w in t._wanted]
    assert out["returns_listed"] == 6 and not any("2016" in u for u in urls)


def test_a_hyphenated_or_macron_name_is_one_candidate():
    page = ("<main><h1>2025</h1><h3>Te Raki Māori Constituency</h3><a href='/media/a1b2c3d4/jones.pdf'>JONES "
            "Peter-Lucas - electoral donations and expenses (PDF 99 KB)</a><a href='/media/a1b2c3d5/t.pdf'>TE "
            "WHAREAU Tūī - electoral donations and expenses</a></main>").encode()
    got = [(r["covers"], r["candidate_as_listed"], r["position"]) for r in rows(page)["rows"]]
    assert got == [("one candidate", "JONES Peter-Lucas", "Te Raki Māori Constituency"),
                   ("one candidate", "TE WHAREAU Tūī", "Te Raki Māori Constituency")]
