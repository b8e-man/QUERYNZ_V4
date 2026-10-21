"""Invented documents in the Department's two layouts (every name invented),
carrying each hard case the real ones carry, and `properties(mod)`: the
reading's rules, as a list of the ones a reading module breaks. The mutant
check runs it on read.py broken one way at a time."""
import csv
import io

from registers.grants import read

SHA = "d" * 64
PAGE_SHA = "e" * 64
VALID_NZBN = "9429000000017"
SOCIETY = ("invented-gaming-trust", ("Invented Gaming Trust", None, False))


def _line(row) -> str:
    b = io.StringIO(newline="")
    csv.writer(b, lineterminator="\r\n").writerow(row)
    return b.getvalue()


def dia_csv() -> bytes:
    head = read.profile(read.DIA_CSV)["recognise"]["header_exact"]
    rows = [
        # 1 accepted, an NZBN, a charity number, an amount in cents, dated d/mm/yyyy
        ["Invented Gaming Trust", "Kowhai Rowing Club Incorporated", "KOWHAI ROWING CLUB INCORPORATED", VALID_NZBN,
         "CC12345", "Accepted", "5000", "4500.50", "3/04/2023", "2023", "SPORT", "ROWING", "", "No", "", "", "AUCKLAND",
         "", "AUCKLAND"],
        # 2 declined, granted 0, a twelve-digit business-number field, a charity number in exponent form, the society
        #   named with 'The' and 'Limited' in capitals
        ["THE INVENTED GAMING TRUST LIMITED", "Totara Book Group", "", "942900000001", "1.23E+05", "Declined", "800",
         "0", "15/11/2022", "2022", "COMMUNITY", "BOOKS", "NULL", "No", "NULL", "", "NATIONAL", "", "Wellington"],
        # 3 a name no word or number shows to be an organisation; no decision date; a refund dated by a day number
        ["Invented Gaming Trust", "Aroha Example", "", "", "", "Accepted", "300", "300", "", "2021", "SPORT",
         "ATHLETICS", "46010", "Yes", "300", "", "", "", ""],
        # 4 a society form on no list: set aside
        ["Somebody Else's Trust", "Rimu Pony Club", "", "", "", "Accepted", "100", "100", "1/01/2024", "2024", "", "",
         "", "No", "", "", "", "", ""],
        # 5 no recipient: set aside
        ["Invented Gaming Trust", "", "", "", "", "Accepted", "100", "100", "1/01/2024", "2024", "", "", "", "No", "",
         "", "", "", ""],
        # 6 decided before the window (ruling 71): set aside
        ["Invented Gaming Trust", "Matai Bowls Club", "", "", "", "Accepted", "100", "100", "1/01/2016", "2016", "",
         "", "", "No", "", "", "", "", ""],
        # 7 thirteen digits that fail the NZBN's check digit: kept as published, no NZBN
        ["Invented Gaming Trust", "Puriri Swim Club", "", "9429000000018", "", "Accepted", "90", "90", "2/02/2024",
         "2024", "", "", "", "No", "", "", "", "", ""],
        # 8 a field in Windows-1252 in a UTF-8 file
        ["Invented Gaming Trust", "Kauri Café – Youth Trust", "", "", "", "Accepted", "250", "250",
         "28/02/2025", "2025", "", "", "", "No", "", "", "", "", ""],
    ]
    out = _line(head).encode("utf-8")
    for r in rows:
        line = _line(r)
        out += line.encode("cp1252") if "–" in line else line.encode("utf-8")
    return out


def lottery_page(heading="2025/26 round one Lottery Invented Committee record of grants", total=None,
                 footnote="*2 year multi-year grant", extra_row=None) -> bytes:
    rows = [("Kowhai Community Trust", "$60,000"), ("Totara Collective NZIncorporated", "$15,500*"),
            ("Rata Example", "$1,000")]
    body = "".join(f"<tr><td>{n}</td><td>{a}</td></tr>" for n, a in rows)
    if extra_row:
        body += extra_row
    if total:
        body += f"<tr><td>Total</td><td>{total}</td></tr>"
    return ("<!doctype html><html><head><title>x</title></head><body><h1><a href='/'><img alt='Community Matters'>"
            f"</a></h1><main><h1>{heading}</h1><table><thead><tr><th><strong>Name</strong></th><th><strong>Amount"
            f"</strong></th></tr></thead><tbody>{body}</tbody></table><p>{footnote}</p></main></body></html>").encode()


def properties(mod) -> list:
    """The rules the reading keeps; the names of the ones `mod` breaks."""
    broken = []
    mod.NAME_FORMS["invented gaming trust"] = SOCIETY[0]
    mod.SOCIETIES[SOCIETY[0]] = SOCIETY[1]
    try:
        if mod.recognise(dia_csv()) != mod.DIA_CSV:
            broken.append("the national file is recognised by its header")
        other = dia_csv().replace(b"Organisation_Name,Final_Organisation_Name", b"Organisation_Name,Other_Name", 1)
        if mod.recognise(other) is not None:
            broken.append("a file whose header differs is not recognised")
        try:
            r = mod.read_dia_csv(dia_csv(), SHA)
        except Exception as exc:  # noqa: BLE001 — a reading that raises breaks every rule after it
            return broken + [f"the national file reads without raising ({type(exc).__name__}: {exc})"]
        g = {x["place"]: x for x in r.grants}
        if r.records != 8 or len(r.grants) != 5 or len(r.set_aside) != 3:
            broken.append("eight records in: five grants, three set aside")
        e = g.get("record 7", {})
        if e.get("nzbn") is not None or e.get("nzbn_as_published") != "9429000000018":
            broken.append("thirteen digits failing the check digit are no NZBN")
        stages = {a["place"]: a["stage"] for a in r.set_aside}
        if stages.get("record 6") != "window":
            broken.append("a decision before 2017 is set aside by the window")
        a = g.get("record 1", {})
        if a.get("nzbn") != VALID_NZBN or a.get("charity_number") != "CC12345" or a.get("amount_nzd") != 4500.50:
            broken.append("a valid NZBN, a charity number and an amount in cents are read")
        if str(a.get("decided_on")) != "2023-04-03":
            broken.append("a decision date is read day first")
        if a.get("grantor_key") != SOCIETY[0] or a.get("publisher_key") != "dia":
            broken.append("the grantor is the society, the publisher the Department")
        b = g.get("record 2", {})
        if b.get("grantor_key") != SOCIETY[0]:
            broken.append("a society's name form with 'The' and 'Limited' maps to the society")
        if b.get("nzbn") is not None or b.get("nzbn_as_published") != "942900000001":
            broken.append("a twelve-digit business-number field is kept as published and is no NZBN")
        if b.get("charity_number") is not None or b.get("charity_number_as_published") != "1.23E+05":
            broken.append("a charity number in exponent form is kept as published and is no charity number")
        if b.get("amount_nzd") is not None or b.get("status") != "Declined":
            broken.append("a declined grant carries no amount granted")
        if b.get("refunded_on") is not None or b.get("refunded_on_as_published") is not None:
            broken.append("a NULL refund date is no date")
        c = g.get("record 3", {})
        if c.get("recipient_kind") != "not shown to be an organisation" or c.get("recipient_as_published") != "Aroha Example":
            broken.append("a name shown to be no organisation is kept as printed and marked so")
        if str(c.get("refunded_on")) != "2025-12-19":
            broken.append("a spreadsheet day number is read as its date")
        if c.get("decided_on") is not None or c.get("period") != "2021":
            broken.append("no decision date leaves the date empty and the year as the period")
        if g.get("record 8", {}).get("recipient_as_published") != "Kauri Café – Youth Trust":
            broken.append("a Windows-1252 field is decoded as Windows-1252")
        if any("address" in k for x in r.grants for k in x):
            broken.append("no address is read")

        if mod.recognise(lottery_page()) != mod.LOTTERY_PAGE:
            broken.append("a record of grants is recognised by its heading and table")
        if mod.recognise(lottery_page(heading="Lottery Invented Committee")) is not None:
            broken.append("a page whose heading is no record of grants is not recognised")
        p = mod.read_lottery_page(lottery_page(), PAGE_SHA)
        if [x["amount_nzd"] for x in p.grants] != [60000.0, 15500.0, 1000.0]:
            broken.append("every row is a grant with its dollar amount")
        if [bool(x["multi_year"]) for x in p.grants] != [False, True, False]:
            broken.append("an asterisk marks a multi-year grant")
        if len(p.grants) == 3 and p.grants[1]["multi_year"] != "*2 year multi-year grant":
            broken.append("the multi-year grant carries the page's own footnote")
        if p.grants and (p.grants[0]["period"] != "2025/26" or p.grants[0]["round"] != "round one"
                         or p.grants[0]["committee"] != "Invented Committee"):
            broken.append("the period, round and committee come from the heading")
        if len(p.grants) == 3 and p.grants[1]["recipient_as_published"] != "Totara Collective NZIncorporated":
            broken.append("a name is kept exactly as printed")
        t = mod.read_lottery_page(lottery_page(total="$76,500"), PAGE_SHA)
        if t.stated.get("total") != "$76,500" or len(t.grants) != 3:
            broken.append("a Total row is the page's stated total, not a grant")
        try:
            x = mod.read_lottery_page(lottery_page(extra_row="<tr><td>Odd</td><td>$1</td><td>x</td></tr>"), PAGE_SHA)
            if len(x.set_aside) != 1 or len(x.grants) != 3:
                broken.append("a row of the wrong width is set aside")
        except Exception:  # noqa: BLE001
            broken.append("a row of the wrong width is set aside, not raised on")
        old = mod.read_lottery_page(lottery_page(heading="2015/16 round one Lottery Invented record of grants"),
                                    PAGE_SHA)
        if old.grants:
            broken.append("a record before 2017 is not read (ruling 71)")
    finally:
        mod.NAME_FORMS.pop("invented gaming trust", None)
        mod.SOCIETIES.pop(SOCIETY[0], None)
    return broken
