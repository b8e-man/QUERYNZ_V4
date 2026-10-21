"""Invented files in the ministry's layouts (every name invented), built from
the profiles' own headers, carrying each hard case the real files carry: an
RFx ID in both eras, an amount of 0, a Windows-1252 byte in a UTF-8 file's
neighbour, a business number in exponent form, NULL fields, the same
supplier twice on one notice, a supplier of an RFx ID the notices lack."""
import csv
import io

from registers.tenders import read

SHA = {k: c * 64 for k, c in zip([(s, e) for s in read.SETS for e in read.ERAS], "0123456789abcdef")}
VALID_NZBN = "9429000000017"


def _csv(header, rows, bom=False, cp1252_title=False) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerow(header)
    for r in rows:
        w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    if cp1252_title:
        data = data.replace("Cafe fit-out".encode(), b"Caf\xe9 fit\x96out")
    return (b"\xef\xbb\xbf" if bom else b"") + data


def header(slug):
    return read.profile(slug)["recognise"]["header_exact"]


def notice(rfx, title, opened, awarded, award_type, amount=None, era="current"):
    row = ["Ministry of Examples", rfx, "Request for Tenders", "Open Competition", title, "REF-1", opened, opened,
           awarded, "", "Sole Agency", "No", "", "An overview\nover two lines", award_type, "A comment"]
    return row + ([amount] if era == "current" else []) + ["20260715" if era == "current" else "20201117"]


def files() -> dict:
    cur, his = "20260715", "20201117"
    out = {
        ("notices", "current"): _csv(header("gets-award-notices-current"), [
            notice("30000001", "Build a hall", "5/03/2024", "20/04/2024", "Awarded", "150000"),
            notice("30000002", "Mow the lawns", "1/11/2023", "13/11/2023", "Awarded", "0"),
            notice("30000003", "Paint a fence", "2/02/2022", "9/03/2022", "Not Awarded", "0"),
            notice("30000009", "Second round", "3/01/2020", "25/02/2020", "Awarded", "0"),
        ], bom=True),
        ("notices", "historic"): _csv(header("gets-award-notices-historic"), [
            notice("30000009", "Cafe fit-out", "20180301", "20180412", "Awarded", era="historic"),
            notice("30000010", "Survey", "20170801", "20170825", "Not Awarded", era="historic"),
        ], cp1252_title=True),
        ("suppliers", "current"): _csv(header("gets-supplier-data"), [
            ["30000001", "9.42904E+12", "Example Builders Limited", "1 Invented Road, Exampletown", "New Zealand", "www.example.nz", cur],
            ["30000001", "9.42904E+12", "Example Builders Limited", "1 Invented Road, Exampletown", "New Zealand", "www.example.nz", cur],
            ["30000001", VALID_NZBN, "Numbered Limited", "2 Invented Road", "New Zealand", "", cur],
            ["30000002", "NULL", "A Sole Trader", "3 Home Street, Exampletown", "NULL", "", cur],
            ["30000009", "1234567", "Current Round Limited", "", "Australia", "", cur],
        ]),
        ("suppliers", "historic"): _csv(header("gets-supplier-data"), [
            ["30000009", "", "Old Supplier Limited", "", "", "", his],
            ["39999999", "", "Orphan Limited", "", "", "", his],
        ]),
        ("regions", "current"): _csv(header("gets-region-by-tender"), [
            ["30000001", "Auckland", cur], ["30000001", "NULL", cur], ["30000001", "Auckland", cur],
            ["30000002", "Canterbury", cur]]),
        ("regions", "historic"): _csv(header("gets-region-by-tender"), [["30000009", "Wellington", his]]),
        ("categories", "current"): _csv(header("gets-product-categories"), [
            ["30000001", "72101500", "Building construction", cur]]),
        ("categories", "historic"): _csv(header("gets-product-categories"), [["30000009", "8010", "Management", his]]),
    }
    return {k: (SHA[k], v) for k, v in out.items()}


CHALLENGE = (b"<html>\r\n<head>\r\n<META NAME=\"robots\" CONTENT=\"noindex,nofollow\">\r\n"
             b"<script src=\"/_Incapsula_Resource?SWJIYLWA=x\"></script></head><body></body></html>")


def properties(mod) -> list:
    """What the reading must do on the fixtures, as a list of what broke
    (empty when every property holds). The mutant check needs each broken
    copy of the reading to make this say something."""
    out = []
    try:
        r = mod.read(files())
    except Exception as exc:  # noqa: BLE001 — a reading that raises is a reading that broke
        return [f"the reading raised {type(exc).__name__}: {exc}"]
    n = {x["key"]: x for x in r.notices}
    want = {"tenders/current/30000001", "tenders/current/30000002", "tenders/current/30000003",
            "tenders/current/30000009", "tenders/historic/30000009", "tenders/historic/30000010"}
    if set(n) != want:
        out.append(f"notices {sorted(n)}")
        return out
    if n["tenders/current/30000001"]["value_nzd"] != 150000:
        out.append("a published amount is not the value")
    if n["tenders/current/30000002"]["value_nzd"] is not None:
        out.append("an amount of 0 became a value")
    if n["tenders/historic/30000009"]["awarded_on"] != "2018-04-12":
        out.append(f"historic award date {n['tenders/historic/30000009']['awarded_on']}")
    if n["tenders/historic/30000010"]["awarded_on"] != "2017-08-25":
        out.append("a historic day after the 12th is lost")
    if n["tenders/current/30000002"]["awarded_on"] != "2023-11-13":
        out.append("a current date is not read day first")
    if n["tenders/historic/30000009"]["title"] != "Café fit\u2013out":
        out.append(f"a Windows-1252 field read as {n['tenders/historic/30000009']['title']!r}")
    if n["tenders/current/30000001"]["regions"] != ["Auckland"]:
        out.append(f"regions {n['tenders/current/30000001']['regions']}")
    if n["tenders/historic/30000009"]["categories"] != [{"code": "8010", "description": "Management"}]:
        out.append("historic categories")
    s = r.suppliers
    if len({x["key"] for x in s}) != len(s):
        out.append("two supplier rows share a key")
    by_notice = {}
    for x in s:
        by_notice.setdefault(x["notice_key"], []).append(x)
    if len(by_notice.get("tenders/current/30000001", [])) != 3:
        out.append("the current notice's three supplier records are not three rows")
    forms = {x["business_name"]: (x["nzbn"], x["nzbn_form"]) for x in s}
    if forms.get("Example Builders Limited") != (None, "exponent form: digits lost"):
        out.append(f"exponent form read as {forms.get('Example Builders Limited')}")
    if forms.get("Numbered Limited") != (VALID_NZBN, "nzbn"):
        out.append("a valid NZBN is not kept")
    if forms.get("A Sole Trader") != (None, "NULL"):
        out.append("a NULL business number")
    if forms.get("Current Round Limited", (None, ""))[1] != "7 digits":
        out.append("a company number taken for something else")
    old = [x for x in s if x["business_name"] == "Old Supplier Limited"]
    if not old or old[0]["notice_key"] != "tenders/historic/30000009":
        out.append("a historic supplier joined to another era's notice")
    if any(x["business_name"] == "Orphan Limited" for x in s):
        out.append("a supplier of no notice became a row")
    if [a["stage"] for a in r.set_aside] != ["join"]:
        out.append(f"catch log {[(a['set_name'], a['stage']) for a in r.set_aside]}")
    if n["tenders/current/30000001"]["suppliers_named"] != 3 or n["tenders/current/30000003"]["suppliers_named"] != 0:
        out.append("suppliers_named")
    for row in r.notices + r.suppliers:
        bad = [k for k in row if any(w in k for w in ("address", "website", "overview", "comment"))]
        if bad:
            out.append(f"a row carries {bad}")
            break
    for led in r.ledger:
        rows = sum(1 for x in s if x["era"] == led["era"]) if led["set_name"] == "suppliers" else None
        if rows is not None and rows != led["typed"]:
            out.append(f"suppliers {led['era']}: {rows} rows, the ledger typed {led['typed']}")
    if mod.recognise(CHALLENGE) is not None:
        out.append("a challenge page was recognised as a file")
    if mod.recognise(files()[("notices", "historic")][1], ["gets-award-notices-current"]) is not None:
        out.append("the historic layout was recognised as the current one")
    return out
